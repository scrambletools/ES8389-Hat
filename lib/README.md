# scramble_hat — project libraries

This folder holds project-local component libraries. Registered via `sym-lib-table` and `fp-lib-table` at the project root under the library name `scramble_hat`.

## Layout

- `scramble_hat.pretty/` — KiCad footprint library (`.kicad_mod` files, one per part)
- `3dmodels/` — 3D models for footprints (`.step` and/or `.wrl`)
- `../scramble_hat.kicad_sym` — symbol library (lives at project root for KiCad convention)

## Naming convention

**Project-created files** (footprints/3D models we drew ourselves) use our format:
```
<refdes_class>_<MPN_or_package>.kicad_mod
<refdes_class>_<MPN_or_package>.step
```
Example: `C_Y2_DE2B_TH.kicad_mod` (custom through-hole footprint we created).

**Manufacturer-supplied files** keep their original filename for traceability. Example: `ncj6fi-h.stp` from Neutrik is left as-is; we don't rename it. This makes it easy to re-download and diff if the manufacturer updates the file.

Generic passive footprints (`R_0402`, `C_0402`, etc.) come from the standard KiCad library, not this folder.

## Sourcing

Footprints and LCSC part numbers for each component are documented in `BOM.csv` at the project root.
