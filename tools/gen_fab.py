#!/usr/bin/env python3
"""gen_fab.py — regenerate the JLCPCB production files for scramble_hat.

Writes into fab/:
  - gerbers (F/B/In1/In2 copper, masks, paste, silk, edge) + PTH/NPTH drills
  - scramble_hat-gerbers.zip                (upload this for PCB fab)
  - scramble_hat-BOM.csv / .xlsx            (from BOM.csv, DNP rows dropped, has LCSC#)
  - scramble_hat-CPL.csv                    (placement, JLCPCB rotation corrections applied)

CPL rotations reproduce the KiCad "Fabrication Toolkit" plugin output (cross-
validated) PLUS the U1/QFN correction the plugin misses because of the custom
footprint name. Parts flagged `dnp` or `exclude_from_pos_files` in the PCB
(R14 unpopulated; J1/J2/J5 hand-soldered) are left out of BOM + CPL.

    ALWAYS verify rotations in JLCPCB's assembly preview before ordering —
    especially U1 (QFN), the one part whose correction couldn't be auto-verified.

Usage:   python3 tools/gen_fab.py
Needs:   kicad-cli (KiCad 9/10) on PATH; openpyxl for the .xlsx BOM (optional).
"""
import csv, os, re, subprocess, sys, zipfile

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = "scramble_hat"
PCB   = os.path.join(ROOT, f"{BOARD}.kicad_pcb")
BOM   = os.path.join(ROOT, "BOM.csv")
FAB   = os.path.join(ROOT, "fab")

GERBER_LAYERS = ("F.Cu,B.Cu,In1.Cu,In2.Cu,F.Mask,B.Mask,F.Paste,B.Paste,"
                 "F.Silkscreen,B.Silkscreen,Edge.Cuts")

# --- JLCPCB rotation corrections -------------------------------------------
# Degrees ADDED after the bottom-side (180 - theta) transform. These reproduce
# the Fabrication Toolkit plugin's positions.csv for this board (validated by
# diffing). Add/adjust entries as parts change; always confirm in JLCPCB preview.
ROTATION_PATTERNS = [
    (r"^SOT-23",  180),   # SOT-23 / SOT-23-5   (Q1, U2)
    (r"^SOT-353", 180),   # SC-70-5 ESD arrays  (D1, D2)
    (r"^SOP-4_",  -90),   # SOP-4 optocoupler   (OK1)
]
# The ES8389 uses a CUSTOM QFN footprint whose name the patterns (and the
# plugin's auto-DB) miss. Correct it by refdes. *** VERIFY U1 IN PREVIEW ***
# — a wrong QFN rotation = dead board, and this value is a best estimate.
QFN_BY_REF = {"U1": 270}


def sh(*args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FAILED: {' '.join(args)}\n{r.stderr or r.stdout}")


def gen_gerbers():
    sh("kicad-cli", "pcb", "export", "gerbers", "--no-protel-ext", "--no-x2",
       "--subtract-soldermask", "-l", GERBER_LAYERS, "-o", FAB + os.sep, PCB)
    sh("kicad-cli", "pcb", "export", "drill", "--format", "excellon",
       "--excellon-separate-th", "--excellon-units", "mm",
       "--drill-origin", "absolute", "-o", FAB + os.sep, PCB)
    zp = os.path.join(FAB, f"{BOARD}-gerbers.zip")
    if os.path.exists(zp):
        os.remove(zp)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(FAB)):
            if f.endswith(".gbr") or f in (f"{BOARD}-NPTH.drl", f"{BOARD}-PTH.drl"):
                z.write(os.path.join(FAB, f), f)
    print(f"  gerbers + drills + {BOARD}-gerbers.zip")


def gen_bom():
    rows = list(csv.reader(open(BOM)))
    out = [["Comment", "Designator", "Footprint", "JLCPCB Part #（optional）"]]
    for r in rows[1:]:
        if len(r) < 10 or r[9].strip().upper() == "DNP":
            continue
        out.append([r[0], r[1], r[5], r[6]])
    with open(os.path.join(FAB, f"{BOARD}-BOM.csv"), "w", newline="") as f:
        csv.writer(f, lineterminator="\r\n").writerows(out)
    try:
        import openpyxl
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Sheet"
        for r in out:
            ws.append([c if c != "" else None for c in r])
        wb.save(os.path.join(FAB, f"{BOARD}-BOM.xlsx"))
        print(f"  {BOARD}-BOM.csv/.xlsx  ({len(out)-1} assembled parts)")
    except ImportError:
        print(f"  {BOARD}-BOM.csv  ({len(out)-1} parts)  [no openpyxl -> skipped .xlsx]")


def footprints():
    t = open(PCB).read()
    for m in re.finditer(r'\n\t\(footprint "([^"]+)"', t):
        s = m.start() + 1; d = 0; i = s
        while i < len(t):
            c = t[i]
            if c == "(":
                d += 1
            elif c == ")":
                d -= 1
                if d == 0:
                    break
            i += 1
        b = t[s:i + 1]
        ref = re.search(r'\(property "Reference" "([^"]+)"', b)
        if not ref or ref.group(1).startswith("#"):
            continue
        at = re.search(r'\n\t\t\(at ([\-0-9.]+) ([\-0-9.]+)(?: ([\-0-9.]+))?\)', b)
        attr = re.search(r'\n\t\t\(attr ([^\)]*)\)', b)
        yield {
            "ref": ref.group(1),
            "name": m.group(1).split(":")[-1],
            "top": re.search(r'\n\t\t\(layer "([^"]+)"\)', b).group(1) == "F.Cu",
            "x": float(at.group(1)), "y": float(at.group(2)),
            "rot": float(at.group(3) or 0),
            "attr": attr.group(1) if attr else "",
        }


def correction(ref, name):
    if ref in QFN_BY_REF:
        return QFN_BY_REF[ref]
    for pat, deg in ROTATION_PATTERNS:
        if re.search(pat, name):
            return deg
    return 0


def sort_key(f):
    return (f["ref"][0], int(re.sub(r"\D", "", f["ref"]) or 0))


def gen_cpl():
    out = [["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]]
    corrected, excluded = [], []
    for fp in sorted(footprints(), key=sort_key):
        if "dnp" in fp["attr"] or "exclude_from_pos_files" in fp["attr"]:
            excluded.append(fp["ref"]); continue
        base = fp["rot"] if fp["top"] else (180 - fp["rot"]) % 360
        corr = correction(fp["ref"], fp["name"])
        rot = int(round((base + corr) % 360))
        out.append([fp["ref"], f"{fp['x']:.4f}mm", f"{-fp['y']:.4f}mm",
                    "Top" if fp["top"] else "Bottom", rot])
        if corr:
            corrected.append((fp["ref"], fp["name"], rot, corr))
    with open(os.path.join(FAB, f"{BOARD}-CPL.csv"), "w", newline="") as f:
        csv.writer(f, lineterminator="\r\n").writerows(out)
    print(f"  {BOARD}-CPL.csv  ({len(out)-1} placed; excluded {sorted(excluded)})")
    print("  rotation-corrected parts (verify in JLCPCB preview):")
    for ref, name, rot, corr in corrected:
        flag = "   <-- QFN, VERIFY FIRST" if ref in QFN_BY_REF else ""
        print(f"     {ref:4} {name:26} rot={rot:3} (corr {corr:+d}){flag}")


if __name__ == "__main__":
    print("Regenerating fab/ ...")
    gen_gerbers()
    gen_bom()
    gen_cpl()
    print("Done. Upload gerbers.zip + BOM + CPL to JLCPCB; verify rotations in "
          "the preview (U1 first).")
