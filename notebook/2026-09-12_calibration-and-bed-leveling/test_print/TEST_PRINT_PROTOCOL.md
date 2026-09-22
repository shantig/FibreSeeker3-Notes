# Loom plastic-plus-fibre test print — protocol

Status: **Stage 1 complete — PASS with notes (`STAGE1_RESULTS.md`). Stage 2
READY; not yet run.** This is the follow-up to `../CALIBRATION_LOG.md` §6. Everything here is `EXPERIMENTAL` owner-machine test design, not
manufacturer guidance.

## 1. Why this test

`CONFIRMED` (Loom `/server/history`; job G-code headers, read-only
2026-09-12):
- Loom's retained job history holds one job, `Calibration Cube Clean
  20mm.gcode`. It was sliced by Rocket 1.3.1.480 as `PRINTING_MODE: Plastic
  Only` and uses T1 (the right FFF nozzle) only.
- The history totals count 17 jobs, so earlier entries (plausibly factory
  testing, `INFERENCE`) were removed from the list.
- **No retained job on Loom has used the CFC (fibre) nozzle.**

What the test must show:
1. Fibre feed, lay-down, cut (`M2800`) and restart work in a real print.
2. The first layer is good across the bed, especially at the high back-left
   corner (X10 Y290, +0.35 mm in `default`) and the dip at X220–255/Y185–220
   (−0.15 mm).
3. Plastic/fibre XY alignment after the 21:05 nozzle offset (x −32.823188,
   y −0.006438). FS-154's layer-shift SOP gives the correction rule.

## 2. Stage 1 — known-good composite job (recommended first)

Print `DemoFiles/PETG-Scraper.gcode`, which is already on Loom.

`CONFIRMED` (file header):
- Rocket 1.3.1.480, 2026-08-25; `PRINTING_MODE: Plastic and Composite`.
- 49 layers; header time estimate 3,195 s (≈53 min); 17 `M2800` cuts.
- CFC nozzle 270 °C, bed 75 °C.
- XY move extents X 83.0–222.6, Y 124.2–178.8 (central bed only).

Loom's loaded materials match: CFC PETG, X-CCF and PETG (IMG_4028/IMG_4036).

`INFERENCE`: FibreSeek sliced this file, so a failure points to hardware,
material or calibration rather than to slicer settings. It does not test the
bed corners or measure alignment.

Pass criteria:
- the first-layer priming line lays fibre;
- no pause messages (fibre ran out, clogging, tangling, door open);
- fibre is visible and continuous in the part;
- all cuts complete.

## 3. Stage 2 — alignment and bed-coverage coupons

### 3.1 Model

`loom_coupon_40x40x2_chamfer.stl`:
- 40 × 40 × 2.0 mm plate with a 6 mm chamfer at one corner;
- ASCII STL, 20 triangles, closed manifold, volume 3,164 mm³;
- SHA-256 `0fcfc05ce6b15eb562d1f43f62e50604439dab083a5103712ef34cbe92808d1b`.

The chamfer marks orientation. Keep it at the **back-left (X−/Y+)** on every
copy: do not rotate the copies, and do not use Auto-layout or Auto orient.

### 3.2 Placement (bed coordinates, coupon centre)

| ID | Centre X, Y | Why |
|---|---|---|
| C | 150, 150 | Mesh zero reference |
| BL | 35, 270 | High corner (top-left screw at end of travel) |
| BR | 270, 270 | Corner |
| FL | 35, 35 | Corner |
| FR | 270, 35 | Corner |
| D | 237, 202 | Mesh dip |

`INFERENCE`: Rocket plate coordinates map 1:1 to Loom coordinates, because the
Rocket-sliced cube centred on X/Y 152.5 in its G-code. Check in Rocket whether
**Move** positions the object's centre or its corner.

### 3.3 Slicing in Rocket (FS-154 Rocket Quick Start §4, §5, §6)

1. Import the STL (Add models), then **Clone** until there are six copies.
   Place each copy with **Move** using the table above.
2. Materials: plastic PETG; composite CFC PETG + X-CCF.
3. Print Mode: **Reinforced** (CFC + FFF), using the built-in template.
4. **Preview** before printing and confirm:
   - fibre (reinforced perimeters) appears on every coupon;
   - the reinforced-perimeter paths are at least 55 mm. Rocket's
     ReinForced/Fortified profiles skip shorter perimeters (Rocket static
     analysis). A 40 mm coupon perimeter is about 150 mm.
   - fibre is visible from the top. If top solid layers cover it, copy the
     built-in template (built-ins are not editable) and set top solid layers
     to 0 for this test only. Record the change.
5. If no fibre appears, set the coupon Z to 3.0 mm with Resize (absolute)
   before changing any template setting.

### 3.4 Before printing

- Bed clean. Apply glue as FS-154 suggests for PETG ("Glue when needed").
- Chamber door closed. Correction from Stage 1: door-open pause is
  **disabled** on Loom (LM-017 pre-check), so an open door will not pause the
  print.
- Leave the auto-leveling toggle on. `printing_info_auto_leveling` is 1 on
  Loom.
- Stay nearby for the first layers. If fibre drags, tangles or does not lay
  down, stop from the touchscreen.
- From Stage 1: clean the CFC nozzle tip first. Watch the first fibre section,
  which follows a long standby: if an orange clump forms, pause, hold about
  1 min, then resume.

## 4. Measurements

Mark each coupon's ID in place before removing it.

### 4.1 First layer and thickness

- Photograph the underside of every coupon.
- Measure total thickness with calipers at the four edge midpoints (nominal
  2.00 mm).

| ID | Front | Back | Left | Right | Underside notes |
|---|---:|---:|---:|---:|---|
| C | | | | | |
| BL | | | | | |
| BR | | | | | |
| FL | | | | | |
| FR | | | | | |
| D | | | | | |

### 4.2 Plastic/fibre alignment

On the top face of each coupon, measure the gap from the outer plastic edge to
the fibre ring at each side's midpoint, with calipers or a macro photo against
a ruler.

| ID | gap Left | gap Right | gap Front | gap Back |
|---|---:|---:|---:|---:|
| C | | | | |
| BL | | | | |
| BR | | | | |
| FL | | | | |
| FR | | | | |
| D | | | | |

Reading (`INFERENCE`, geometric):
- The FFF nozzle prints the outer plastic and the CFC nozzle lays the fibre.
- A fibre ring off-centre by *d* shortens one gap and lengthens the opposite
  gap by *d* each, so the plastic shift relative to fibre is:
  - X: `dx = (gap Right − gap Left) / 2` (positive = plastic toward X+);
  - Y: `dy = (gap Back − gap Front) / 2` (positive = plastic toward Y+).

## 5. Decision rules

| Observation | Meaning (`INFERENCE`) | Action |
|---|---|---|
| dx, dy about the same on all coupons, and \|d\| ≥ 0.2 mm | Nozzle offset error | FS-154 layer-shift rule: plastic right (dx > 0) → decrease X offset by dx; plastic up (dy > 0) → decrease Y offset by dy |
| \|d\| < 0.2 mm on all coupons | Within the measurement repeatability assumed here | No change |
| d differs by location | Mechanical (belt, skew), not offset | FS-154 belt-tension SOP; do not change offsets |
| BL thinner/over-squished, or others thin/gappy, beyond ~0.1 mm from C | Mesh not fully compensating | Loosen the top-left screw slightly → Calibration with only Bed Level → repeat Stage 2 |
| Pause, fibre tangle, missed cut, fibre not laid | Fibre path problem | Stop; capture klippy.log; FS-154 fibre SOPs |

The 0.2 mm and 0.1 mm thresholds are assumed working limits for this test.
`OPEN QUESTION`: FibreSeek publishes no numeric XY alignment tolerance
(`../../../docs/machine/CALIBRATION_MAINTENANCE_TROUBLESHOOTING.md`).

For FS-154's word "upward", `INFERENCE`: it is taken as Y+ (toward the back).
Confirm the sign on a first correction by re-measuring.

## 6. Evidence to capture

- Owner photos: the first layer in progress, coupon undersides, and top faces
  with a ruler.
- Read-only after the print: `klippy.log`, `/server/history`, and the job
  G-code header, preserved per `docs/loom/EVIDENCE_PROTOCOL.md`.
