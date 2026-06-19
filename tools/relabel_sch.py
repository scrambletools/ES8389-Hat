#!/usr/bin/env python3
"""
relabel_sch.py — regenerate the schematic's connectivity layer to match the PCB.

The schematic's pins are wired via global labels (no wires). Many existing labels
are misplaced and/or use net names that differ from the PCB. This tool:
  * keeps every symbol instance EXACTLY as-is (position/uuid/props untouched),
  * computes each pin's true connection point (validated KiCad transform),
  * removes the old (unreliable) global_label elements,
  * writes one fresh global_label per pin, carrying the PCB's net name,
    placed exactly on the pin endpoint.

Result: schematic netlist == PCB netlist -> `Update PCB from Schematic` is a no-op.

Dry-run by default (writes nothing). Use --apply to write the sheets.
Never touches the .kicad_pcb.
"""
import argparse, math, re, sys, uuid

SHEETS = ["scramble_hat.kicad_sch", "sheet_codec.kicad_sch",
          "sheet_input.kicad_sch", "sheet_output.kicad_sch"]
PCB = "scramble_hat.kicad_pcb"

# ----------------------------------------------------------------- PCB pad-nets
def pcb_padnets():
    t = open(PCB).read()
    starts = [m.start() for m in re.finditer(r'\n\t\(footprint ', t)] + [len(t)]
    out = {}
    for i in range(len(starts) - 1):
        b = t[starts[i]:starts[i+1]]
        ref = re.search(r'\(property "Reference" "([^"]+)"', b)
        if not ref:
            continue
        ref = ref.group(1)
        pads = {}
        ps = [m.start() for m in re.finditer(r'\(pad "', b)] + [len(b)]
        for j in range(len(ps) - 1):
            pb = b[ps[j]:ps[j+1]]
            pn = re.search(r'\(pad "([^"]*)"', pb).group(1)
            net = re.search(r'\(net "([^"]*)"\)', pb)
            if net:
                pads[pn] = net.group(1)
        out[ref] = pads
    return out

# ----------------------------------------------------------------- sheet parse
def balanced(txt, p):
    depth = 0
    for j in range(p, len(txt)):
        if txt[j] == '(':
            depth += 1
        elif txt[j] == ')':
            depth -= 1
            if depth == 0:
                return j + 1
    return len(txt)

def parse_libpins(t):
    lib = {}
    for lm in re.finditer(r'\n\t\t\(symbol "([^"]+)"\n', t):
        name = lm.group(1); start = lm.end()
        nxt = re.search(r'\n\t\t\(symbol "', t[start:])
        block = t[start:start + (nxt.start() if nxt else len(t) - start)]
        pins = []
        for pm in re.finditer(
            r'\(pin \w+ \w+\s*\n\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(length ([-\d.]+)\)(.*?)\(number "([^"]+)"',
            block, re.S):
            px, py, ang, length = map(float, pm.group(1, 2, 3, 4))
            pins.append((pm.group(6), px, py, ang, length))
        if pins:
            lib[name] = pins
    return lib

def parse_instances(t):
    out = []
    for m in re.finditer(r'\t\(symbol\n', t):
        p = t.index('(', m.start()); end = balanced(t, p); b = t[p:end]
        if '(property "Reference"' not in b:
            continue
        ref = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
        lib = re.search(r'\(lib_id "([^"]+)"', b).group(1)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', b)
        mir = re.search(r'\(mirror (\w+)\)', b)
        out.append(dict(ref=ref, lib=lib, x=float(at.group(1)), y=float(at.group(2)),
                        rot=int(float(at.group(3))), mir=mir.group(1) if mir else None))
    return out

def rot_pt(rot, x, y):
    # KiCad symbol TRANSFORM matrices (incl. lib Y-flip): validated against the board.
    return {0: (x, -y), 90: (-y, -x), 180: (-x, y), 270: (y, x)}[rot % 360]

def lib_lookup(libpins, lib):
    nm = lib.split(':')[-1]
    return (libpins.get(lib) or libpins.get(nm)
            or next((v for k, v in libpins.items() if k.endswith(':' + nm) or k == nm), None))

def pin_endpoint(inst, px, py):
    x, y = px, py
    if inst["mir"] == 'y': x = -x
    if inst["mir"] == 'x': y = -y
    dx, dy = rot_pt(inst["rot"], x, y)
    # full precision — a sub-0.01mm miss breaks the label↔pin connection (e.g. gate at .778)
    return round(inst["x"] + dx, 4), round(inst["y"] + dy, 4)

def label_angle(inst, ang):
    # outward direction = (ang+180) in lib coords, transformed; snapped to 0/90/180/270
    a = math.radians(ang + 180.0)
    dx, dy = math.cos(a), math.sin(a)
    if inst["mir"] == 'y': dx = -dx
    if inst["mir"] == 'x': dy = -dy
    dx, dy = rot_pt(inst["rot"], dx, dy)
    deg = round(math.degrees(math.atan2(-dy, dx)) / 90.0) * 90 % 360  # -dy: schematic Y-down
    return int(deg)

# ----------------------------------------------------------------- label s-expr
def make_label(net, x, y, ang):
    u = str(uuid.uuid4())
    return (
f'\t(global_label "{net}"\n'
f'\t\t(shape passive)\n'
f'\t\t(at {x} {y} {ang})\n'
f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left)\n\t\t)\n'
f'\t\t(uuid "{u}")\n'
f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n'
f'\t\t\t(at {x} {y} {ang})\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
f'\t)\n')

def strip_global_labels(t):
    out = []; i = 0
    for m in re.finditer(r'\n\t\(global_label ', t):
        out.append(t[i:m.start()+1])           # keep up to and incl the newline
        i = balanced(t, m.start()+1)
        while i < len(t) and t[i] == '\n':       # swallow trailing newline
            i += 1; break
    out.append(t[i:])
    return ''.join(out)

# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    padnets = pcb_padnets()
    pcb_refs = set(padnets)
    sheet_refs = set()
    total_labels = 0
    conflicts_nopad = []      # (ref,pin) symbol pin with no PCB pad
    conflicts_nopin = []      # (ref,pad) PCB pad with no symbol pin
    per_sheet_new = {}

    for sh in SHEETS:
        t = open(sh).read()
        libpins = parse_libpins(t)
        insts = parse_instances(t)
        newlabels = []
        seen_pins = {}
        for inst in insts:
            ref = inst["ref"]; sheet_refs.add(ref)
            pins = lib_lookup(libpins, inst["lib"])
            if not pins:
                print(f"  ! no lib pins for {ref} ({inst['lib']})"); continue
            pcbpads = padnets.get(ref, {})
            seen_pins[ref] = set()
            for num, px, py, ang, length in pins:
                seen_pins[ref].add(num)
                net = pcbpads.get(num)
                if net is None:
                    conflicts_nopad.append((ref, num)); continue
                x, y = pin_endpoint(inst, px, py)
                la = label_angle(inst, ang)
                newlabels.append(make_label(net, x, y, la))
        # PCB pads with no symbol pin (only for refs on this sheet)
        for inst in insts:
            ref = inst["ref"]
            for pad in padnets.get(ref, {}):
                if pad not in seen_pins.get(ref, set()):
                    conflicts_nopin.append((ref, pad))
        per_sheet_new[sh] = newlabels
        total_labels += len(newlabels)

    print("=" * 70)
    print(f"PLAN: place {total_labels} global labels across {len(SHEETS)} sheets")
    for sh in SHEETS:
        print(f"   {sh:28} +{len(per_sheet_new[sh])} labels")
    print(f"\nRefs on PCB but absent from schematic : {sorted(pcb_refs - sheet_refs)}")
    if conflicts_nopad:
        print(f"\nSymbol pins with NO matching PCB pad ({len(conflicts_nopad)}):")
        for r, p in conflicts_nopad: print(f"   {r} pin {p}")
    if conflicts_nopin:
        print(f"\nPCB pads with NO matching symbol pin ({len(conflicts_nopin)}):")
        for r, p in conflicts_nopin: print(f"   {r} pad {p} = '{padnets[r][p]}'")
    print("=" * 70)

    if not a.apply:
        print("DRY-RUN — nothing written. Re-run with --apply to write the sheets.")
        return

    for sh in SHEETS:
        t = open(sh).read()
        t2 = strip_global_labels(t)
        block = "".join(per_sheet_new[sh])
        if not block:
            open(sh, "w").write(t2); continue
        anchor = re.search(r'\t\(text "claude-insert-below[^\n]*\n(?:[^\n]*\n)*?\t\)\n', t2)
        if anchor:
            t2 = t2[:anchor.end()] + block + t2[anchor.end():]
        else:                                  # fallback: before sheet_instances / final close
            si = t2.rfind('\t(sheet_instances')
            if si == -1: si = t2.rstrip().rfind(')')
            t2 = t2[:si] + block + t2[si:]
        open(sh, "w").write(t2)
        print(f"  wrote {sh}")
    print("APPLIED. Now run: python3 tools/check_sync.py")

if __name__ == "__main__":
    main()
