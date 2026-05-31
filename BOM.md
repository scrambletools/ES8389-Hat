# scramble_hat — Bill of Materials (rev A.1)

**Sourcing strategy:** every line item has been checked for qty 1 availability. LCSC for ES8389 (not yet stocked at DigiKey/Mouser), DigiKey/Mouser for the Neutrik combo and US-stocked items, JLCPCB for assembly-only orders.

Qty 1 prices below are **typical** retail at the listed distributor as of recent search (USD, before shipping). Verify in your cart at checkout — passive prices in particular drift.

**Footprint column** uses the format `Library:Footprint`. Standard parts use the system-installed `kicad-library`; custom parts use the project-local `scramble_hat` library at `lib/scramble_hat.pretty/`.

## ICs

| Refdes | MPN | Pkg | Distributor | Distrib P/N | Qty 1 | Footprint | 3D | Notes |
|---|---|---|---|---|---|---|---|---|
| U1 | ES8389 | QFN-24 3×3 | LCSC | C5448879 *(verify)* | **~$0.88** | `Package_DFN_QFN:QFN-24-1EP_3x3mm_P0.4mm_EP1.75x1.6mm` | std | EP size 1.75×1.6 mm vs datasheet 1.7×1.7 mm — close enough; verify against datasheet pkg drawing before fab. |
| OK1 | LTV-817S | SOP-4 | LCSC C2823 / DigiKey | LTV-817S-TA1-D | **~$0.40** | `Package_SO:SO-4_4.4x4.3mm_P2.54mm` | std | SOIC-4 / DIP-4 SMD. Verify body footprint matches LTV-817S (6.65×4.4 mm). |
| Q1 | **Si2309DS-T1-GE3** | SOT-23 | DigiKey, Mouser | Si2309DSCT-ND | **~$0.60** | `Package_TO_SOT_SMD:SOT-23` | std | **CORRECTED from DMP3098L-7.** Vishay, **60 V** Vds P-channel, 1.5 A, 350 mΩ @ -10V Vgs. |

## Connectors

| Refdes | MPN | Pkg | Distributor | Distrib P/N | Qty 1 | Footprint | 3D | Notes |
|---|---|---|---|---|---|---|---|---|
| J1 | NCJ6FI-H | TH H-mount | DigiKey, Mouser | NCJ6FI-H | **~$6.50** | `Connector_Audio:Jack_XLR-6.35mm_Neutrik_NCJ6FI-H_Horizontal` | `lib/3dmodels/ncj6fi-h.stp` (Neutrik official) | **Found in std lib!** 3D from Neutrik. |
| J2 | **SJ-3524-SMT-TR** | SMD R/A 4-conductor | DigiKey | CP-43524-SMT-TR-ND | **~$1.50** | `Connector_Audio:Jack_3.5mm_CUI_SJ-3524-SMT_Horizontal` | std | **MPN updated** from SJ-43615 — std lib has SJ-3524 footprint, pin-compatible 4-conductor TRRS, similar body dimensions (~13×6 mm). |
| J3, J4 | SSQ-107-01-T-S | TH 1×7 fem | DigiKey | SAM1066-07-ND | **~$1.50 each** | `Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical` | std | Std pin-socket footprint matches Samtec geometry. |
| J5 | PRPC002SAAN-RC | TH 1×2 pin | DigiKey | S1011EC-02-ND | **~$0.30** | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | std | Sullins 0.1" header. |

## Diodes

| Refdes | MPN | Pkg | Distributor | Distrib P/N | Qty 1 | Footprint | 3D | Notes |
|---|---|---|---|---|---|---|---|---|
| D1, D2 | **PESD3V3L4UA** | SOT-353 SC-70-5 | DigiKey, Mouser | 1727-3043-1-ND | **~$0.40 each** | `Package_TO_SOT_SMD:SOT-353_SC-70-5` | std | **MPN updated** (UA = SOT-353; UF was a different pkg). 4-line ESD array, 3.5 pF. |
| D6 | SMBJ58CA | SMA | DigiKey, Mouser | SMBJ58CALFCT-ND | **~$0.55** | `Diode_SMD:D_SMA` | std | 58 V bidir TVS, 600 W. |
| D7 | MMSZ4699T1G | SOD-123 | DigiKey, Mouser | MMSZ4699T1GOSCT-ND | **~$0.30** | `Diode_SMD:D_SOD-123` | std | 12 V Zener, 0.5 W. |
| D8 | KP-2012EC | 0805 | DigiKey | 754-1124-1-ND | **~$0.20** | `LED_SMD:LED_0805_2012Metric` | std | Red SMD LED. |

## Polyfuse

| Refdes | MPN | Pkg | Distributor | Distrib P/N | Qty 1 | Footprint | 3D | Notes |
|---|---|---|---|---|---|---|---|---|
| F1 | MF-MSMF050-2 | 1812 | DigiKey | MF-MSMF050-2CT-ND | **~$0.70** | `Fuse:Fuse_1812_4532Metric` | std | 50 mA hold, 100 mA trip, 60 V max. |

## Capacitors

All ceramic X7R unless noted.

| Refdes | Value | MPN | Pkg | Qty 1 | Footprint | Notes |
|---|---|---|---|---|---|---|
| C1, C3, C4 | 100 nF 50 V | CL10B104KB8NNNC | 0402 | **~$0.04** | `Capacitor_SMD:C_0402_1005Metric` | Codec rail decoupling |
| C2, C5 | 1 µF 25 V | CL10B105KB8NNNC | 0402 | **~$0.10** | `Capacitor_SMD:C_0402_1005Metric` | Codec rail bulk |
| C6 | 10 µF 16 V | CL21A106KOQNNNE | 0805 | **~$0.13** | `Capacitor_SMD:C_0805_2012Metric` | AVDD bulk |
| C7, C8, C9 | 1 µF 25 V | CL10B105KB8NNNC | 0402 | **~$0.10** | `Capacitor_SMD:C_0402_1005Metric` | VMID/ADCVREF/DACVREF |
| C10, C11, C12, C20 | 1 µF 50 V | CL21B105KOFNNNE | 0805 | **~$0.15** | `Capacitor_SMD:C_0805_2012Metric` | Audio AC coupling |
| C13 | 1 µF 25 V | CL10B105KB8NNNC | 0402 | **~$0.10** | `Capacitor_SMD:C_0402_1005Metric` | Mic bias filter |
| C14, C15 | 22 µF 10 V | CL21A226MQQNNNE | 0805 | **~$0.20** | `Capacitor_SMD:C_0805_2012Metric` | HP output coupling |
| C16 | 10 µF 100 V | CL32B106KMJNNNE | 1210 | **~$1.40** | `Capacitor_SMD:C_1210_3225Metric` | PoE bulk |
| C17 | 100 nF 100 V | CL21B104KCFNNNE | 0805 | **~$0.15** | `Capacitor_SMD:C_0805_2012Metric` | PoE HF |
| C18 | 1 µF 100 V | CL31B105KCHNNNE | 1206 | **~$0.50** | `Capacitor_SMD:C_1206_3216Metric` | Q1 gate soft-start |
| C19 | 2.2 nF Y2 250 VAC | DE2B3KY222KA3BM02 | TH | **~$0.95** | `scramble_hat:C_Y2_DE2B_TH` | **CUSTOM** — Murata Y2 disc cap, through-hole |

Source for above: DigiKey + Samsung Electro-Mechanics (CL-prefix) for ceramics, Murata for the Y2 cap.

## Resistors (all 0402, 1% unless noted)

| Refdes | Value | MPN | Qty 1 | Footprint | Notes |
|---|---|---|---|---|---|
| R1, R2, R3, R4 | 10 kΩ | RC0402FR-0710KL | **~$0.02** | `Resistor_SMD:R_0402_1005Metric` | I²C pullups + AD0/AD1 straps |
| R5, R6 | 6.81 kΩ 1% | RC0805FR-076K81L | **~$0.10** | `Resistor_SMD:R_0805_2012Metric` | Phantom feed pair, 1/8 W |
| R7 | 2.2 kΩ | RC0402FR-072K2L | **~$0.02** | `Resistor_SMD:R_0402_1005Metric` | Mic bias |
| R9, R10 | 33 Ω | RC0402FR-0733RL | **~$0.02** | `Resistor_SMD:R_0402_1005Metric` | HP output series |
| R11, R13 | 100 kΩ | RC0402FR-07100KL | **~$0.02** | `Resistor_SMD:R_0402_1005Metric` | Q1 gate pullup, opto pulldown |
| R12, R15 | 1 kΩ | RC0402FR-071KL | **~$0.02** | `Resistor_SMD:R_0402_1005Metric` | Opto LED, status LED current limit |
| R14 | 0 Ω DNP | RC0402JR-070RL | **~$0.02** | `Resistor_SMD:R_0402_1005Metric` | Ground-lift jumper (not populated) |

## Ferrite bead

| Refdes | Value | MPN | Pkg | Qty 1 | Footprint | Notes |
|---|---|---|---|---|---|---|
| FB1 | 600 Ω @ 100 MHz | BLM18AG601SN1D | 0603 | **~$0.15** | `Inductor_SMD:L_0603_1608Metric` | Murata, 200 mA. (Ferrite beads share L footprint.) |

---

## Cost summary (qty 1, parts only, no shipping)

| Category | Approx total |
|---|---|
| ICs (U1, OK1, Q1) | ~$1.88 |
| Connectors (J1–J5) | ~$11.60 (Neutrik dominates) |
| Diodes (D1, D2, D6, D7, D8) | ~$1.85 |
| Polyfuse F1 | ~$0.70 |
| Capacitors (~20 parts) | ~$5.50 |
| Resistors (~13 parts) | ~$0.40 |
| Ferrite bead FB1 | ~$0.15 |
| **One-board parts total** | **~$22** |

Neutrik J1 is by far the most expensive single component (~$6.50 ≈ 30% of BoM). Almost everything else is sub-dollar.

Shipping is on top: DigiKey ~$5–8 to US, LCSC ~$10–20 international. Realistic prototype cost: **~$35–45 in parts + shipping** for 1 board.

## Sourcing checklist

- [ ] Verify ES8389 LCSC part number C5448879 is correct (might be different LCSC number)
- [ ] Add Neutrik NCJ6FI-H to a Mouser/DigiKey order (long-lead from European stock)
- [ ] Pull all "common passive" lines into a single DigiKey order to consolidate shipping

## Open items

These should be resolved before fab:
- C19 (Y2 cap) is through-hole only — confirm the footprint fits in our space allocation
- Q1 SOT-23 footprint is small enough to fit anywhere; placement TBD in step 12
- J3/J4 stacking socket vertical mount — must specify "top side socket, bottom enters carrier" orientation in footprint
