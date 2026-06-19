#!/usr/bin/env python3
"""
check_sync.py — schematic <-> PCB consistency checker for scramble_hat.

Reads the schematic's TRUE netlist (via `kicad-cli sch export netlist`) and the
PCB's pad-net assignments, then reports every place they diverge:
  A. Component presence (refs on one side only)
  B. Value / footprint mismatches per component
  C. Net assignment mismatches per pad (the connectivity divergence)

Exit code 0 = fully in sync, 1 = drift found. Run after every schematic/PCB edit.

Usage:
    python3 tools/check_sync.py [--sch scramble_hat.kicad_sch] [--pcb scramble_hat.kicad_pcb]
    python3 tools/check_sync.py --nets-only        # just section C
"""
import argparse, os, re, subprocess, sys, tempfile

def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

# ----------------------------------------------------------------------------- netlist (schematic)
def export_netlist(sch):
    out = os.path.join(tempfile.gettempdir(), "scramble_sync_netlist.net")
    r = sh(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, sch])
    if r.returncode != 0 or not os.path.exists(out):
        sys.exit(f"netlist export failed:\n{r.stderr or r.stdout}")
    return open(out).read()

def parse_netlist(text):
    comps = {}        # ref -> {value, footprint}
    pin_net = {}      # (ref, pin) -> netname
    net_nodes = {}    # netname -> set[(ref, pin)]

    # components section
    for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)\s*\(value "([^"]*)"\)(?:\s*\(footprint "([^"]*)"\))?', text):
        ref, val, fp = m.group(1), m.group(2), m.group(3) or ""
        comps[ref] = {"value": val, "footprint": fp}

    # nets section: each (net (code ..)(name "X") (node (ref "R")(pin "1")) ...)
    for nm in re.finditer(r'\(net\s+\(code "[^"]*"\)\s*\(name "([^"]*)"\)(.*?)(?=\(net\s+\(code|\)\s*\)\s*\Z|\(libparts)', text, re.S):
        name = nm.group(1)
        body = nm.group(2)
        for node in re.finditer(r'\(node\s+\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', body):
            ref, pin = node.group(1), node.group(2)
            pin_net[(ref, pin)] = name
            net_nodes.setdefault(name, set()).add((ref, pin))
    return comps, pin_net, net_nodes

# ----------------------------------------------------------------------------- PCB
def parse_pcb(pcb_path):
    t = open(pcb_path).read()
    starts = [m.start() for m in re.finditer(r'\n\t\(footprint ', t)] + [len(t)]
    fps = {}            # ref -> {value, fpid, path, pads: {pad: net}}
    pad_net = {}        # (ref, pad) -> net
    for i in range(len(starts) - 1):
        b = t[starts[i]:starts[i+1]]
        fpid = re.search(r'\(footprint "([^"]+)"', b)
        ref = re.search(r'\(property "Reference" "([^"]+)"', b)
        val = re.search(r'\(property "Value" "([^"]*)"', b)
        path = re.search(r'\(path "([^"]+)"', b)
        if not ref:
            continue
        ref = ref.group(1)
        pads = {}
        # iterate pad blocks
        ps = [m.start() for m in re.finditer(r'\(pad "', b)] + [len(b)]
        for j in range(len(ps) - 1):
            pb = b[ps[j]:ps[j+1]]
            pn = re.search(r'\(pad "([^"]*)"', pb).group(1)
            net = re.search(r'\(net "([^"]*)"\)', pb)
            if net:                      # pads without a net are unconnected/NC
                pads[pn] = net.group(1)
                pad_net[(ref, pn)] = net.group(1)
        fps[ref] = {"value": val.group(1) if val else "",
                    "fpid": fpid.group(1) if fpid else "",
                    "path": path.group(1) if path else None,
                    "pads": pads}
    return fps, pad_net

# ----------------------------------------------------------------------------- compare
def norm_fp(s):       # ignore library prefix when comparing footprint ids
    return s.split(":")[-1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sch", default="scramble_hat.kicad_sch")
    ap.add_argument("--pcb", default="scramble_hat.kicad_pcb")
    ap.add_argument("--nets-only", action="store_true")
    a = ap.parse_args()

    comps, pin_net, net_nodes = parse_netlist(export_netlist(a.sch))
    fps, pad_net = parse_pcb(a.pcb)
    drift = 0

    sch_refs, pcb_refs = set(comps), set(fps)

    if not a.nets_only:
        print("=" * 72)
        print("A. COMPONENT PRESENCE")
        print("=" * 72)
        only_pcb = sorted(pcb_refs - sch_refs)
        only_sch = sorted(sch_refs - pcb_refs)
        print(f"  on PCB but NOT in schematic : {only_pcb or '—'}")
        print(f"  in schematic but NOT on PCB : {only_sch or '—'}")
        drift += len(only_pcb) + len(only_sch)

        print()
        print("=" * 72)
        print("B. VALUE / FOOTPRINT MISMATCH (schematic vs PCB)")
        print("=" * 72)
        bad = 0
        for ref in sorted(sch_refs & pcb_refs):
            sv, pv = comps[ref]["value"], fps[ref]["value"]
            sf, pf = comps[ref]["footprint"], fps[ref]["fpid"]
            if sv != pv:
                print(f"  {ref:5} VALUE  sch='{sv}'  pcb='{pv}'"); bad += 1
            # Compare the FULL fpid incl. library prefix: a bare 'R_0805_2012Metric'
            # vs 'Resistor_SMD:R_0805_2012Metric' makes Update-PCB-from-Schematic try
            # to swap the footprint (and fail if the lib can't load) — must catch it.
            if sf and sf != pf:
                tag = "FPRINT" if norm_fp(sf) != norm_fp(pf) else "FP-LIB"
                print(f"  {ref:5} {tag} sch='{sf}'  pcb='{pf}'"); bad += 1
        if not bad:
            print("  (none)")
        drift += bad

    print()
    print("=" * 72)
    print("C. NET ASSIGNMENT DIVERGENCE (per pad)")
    print("=" * 72)
    mism = 0
    # pads present in both -> compare net name
    both = set(pad_net) & set(pin_net)
    for ref, pad in sorted(both):
        pn, sn = pad_net[(ref, pad)], pin_net[(ref, pad)]
        if pn != sn:
            print(f"  {ref:5} pad {pad:>3}  sch-net='{sn}'   pcb-net='{pn}'"); mism += 1
    # pads with a net on PCB but no schematic node (excluding refs absent from sch)
    pcb_only = sorted((r, p) for (r, p) in pad_net if (r, p) not in pin_net and r in sch_refs)
    sch_only = sorted((r, p) for (r, p) in pin_net if (r, p) not in pad_net and r in pcb_refs)
    if pcb_only:
        print(f"  -- {len(pcb_only)} pad(s) netted on PCB but absent from schematic netlist:")
        for r, p in pcb_only[:40]:
            print(f"       {r} pad {p} = '{pad_net[(r,p)]}'")
    if sch_only:
        print(f"  -- {len(sch_only)} schematic pin(s) with a net but unnetted/absent on PCB:")
        for r, p in sch_only[:40]:
            print(f"       {r} pin {p} = '{pin_net[(r,p)]}'")
    if not (mism or pcb_only or sch_only):
        print("  (fully consistent)")
    drift += mism + len(pcb_only) + len(sch_only)

    print()
    print("=" * 72)
    print(f"RESULT: {'IN SYNC ✅' if drift == 0 else f'DRIFT — {drift} issue(s) ❌'}")
    print(f"  schematic: {len(comps)} comps, {len(net_nodes)} nets | "
          f"PCB: {len(fps)} footprints, {len(set(pad_net.values()))} nets")
    print("=" * 72)
    sys.exit(0 if drift == 0 else 1)

if __name__ == "__main__":
    main()
