# Loom retraction/wipe retest on the scraper — X0010, 2026-09-15

Physical sample **X0010**. `EXPERIMENTAL`. Plastic 2 (FFF, right, 0.4 mm),
SUNLU PLA+ 2.0. Same model and settings as X0009 except retraction; printed to
answer one question: does raising retraction speed and turning wipe on clear the
webbing that X0009 showed across the lattice?

## The one change

| | X0009 | X0010 |
| --- | --- | --- |
| Retraction length | 0.5 mm | 0.5 mm |
| Retraction speed | 15 mm/s | **35 mm/s** |
| Deretraction speed | 15 mm/s | **35 mm/s** |
| Wipe | off | **on** (`retract_before_wipe` 70 %) |

Everything else is identical: the same reconstructed model
(`derived/models/X0009/scraper_from_LM-021.stl`), 205 °C (first layer 210 °C),
flow 0.96, 0.2 mm layers, same placement.

Verified in the G-code: 1,097 E-only retracts of 0.35 mm at F2100 (35 mm/s) plus
1,472 wipe moves carrying the remaining 0.15 mm, and 1,472 deretracts of 0.5 mm
at F2100 — the same split FibreSeek's own PLA profile uses (LM-026).
`loom_scraper_pla_X0010.gcode`, sha256 `640aa59dd1809628901bbac4f0439704c02b3ff7963866468878cf4c72bc7906`; 30 layers, 8.69 g, estimated
40 m 42 s. The 3mf is on the NAS at `derived/models/X0010/` (sha256 `05a767d7a0ea81fb3bdf01755485ecf357643f546a4a151b39ceb90b47a6b1ba`).

## Print

Started 19:17:10 after the owner cleared the plate. Job variables set explicitly
(left preheat 0, right 210, bed 55, probe area 80–225 × 118–186, print mode 0,
filename set so the HMI shows the real job).

## Results

**Not printed.** The job was stopped during preheating (`standby` at 19:18:58,
about 100 s after the start; it never reached the first layer and Moonraker
recorded no job). The owner had moved on: "I thought we were moving on to the
benchy plastic 1 test. let's forget the scraper for now." No physical piece
exists for X0010; the ID stays used and is not reassigned.

The retraction question it was meant to answer is still open, and the evidence
for the change is unchanged: FibreSeek's own PLA profile retracts 0.5 mm at
30 mm/s with wipe (LM-026), and X0009 webbed badly across the lattice at
15 mm/s with no wipe. The file is built and verified if it is ever wanted.
