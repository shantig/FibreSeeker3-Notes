# Loom Plastic 1 (CFC side) Benchy — X0011, 2026-09-15

Physical sample **X0011** — **built, not yet printed**. `EXPERIMENTAL`.
First print on **Plastic 1** (CFC side, left, `extruder`, `T0`, 0.7 mm nozzle)
with SUNLU PLA+ 2.0, the same filament tuned on Plastic 2.

## Purpose

A before-tuning baseline: the same Benchy as X0008, with the same filament
settings, so the two extruders can be compared directly and Plastic 1's own
tuning can start from a known point. `INFERENCE`: FS-154 pairs CFC-side nozzles
with CFC matrix filaments, so nothing here transfers to CFC PETG.

## Plastic 1 profile

`loom_P1_reference.3mf` in this folder is the Plastic 2 project (`loom_T1.3mf`)
with only the tool-specific parts changed:

- `nozzle_diameter` 0.4 → **0.7**; all line widths 0.4 → **0.75**;
- start G-code: pressure advance applied to `extruder` instead of `extruder1`,
  `M104`/`M109` target **T0**, and `T1 R` → **`T0 R`** (T0 is the reference tool,
  so no nozzle offsets are applied); end G-code turns off T0;
- `printer_settings_id` left as `Loom P1 0.4 nozzle` — the process preset's
  compatibility list checks that name, and renaming it makes the CLI refuse to
  slice. The difference is recorded in `printer_notes`.

Unchanged for the baseline: 205 °C (first layer 210 °C), flow 0.96, retraction
0.5 mm @ 15 mm/s, no wipe, 0.2 mm layers, 12 mm³/s volumetric limit.

## Sliced file

Re-sliced after the correction. `loom_benchy_P1_X0011.gcode`, sha256
`93a6f7eb04b8c5c301e778a39a00ccc5e36fd42d184190a8392584603e8c2b0c`: 240 layers,
48 mm, **12.55 g**, estimated **27 m 14 s**. Verified in the G-code: `T0 R`,
pressure advance on `extruder`, 0.7 mm nozzle, 0.75 mm lines, flow 0.96, and
walls/infill at ~88 mm/s (the 12 mm³/s limit caps the wider lines), and the
rotation-distance line at the top of the start G-code. The Plastic 1 project
`loom_P1_reference.3mf` (sha256 `57a674fee1a4c813a3d6269085285e77b3d666a578513e444c89b9dd94a54346`) stays in this folder; the sliced 3mf is on
the NAS at `derived/models/X0011/` (sha256 `7fbc78fda80d3040bc22c90528c20c377a7f04ebb7a1ab6fbbd30c34be7ff93e`).

## Before printing

- [done] Extrusion check complete; 5.49 is baked into the start G-code.
- [done] Job variables set before the start: `left_preheat = 210`,
  `right_preheat = 0` (the reverse of a Plastic 2 print), `bed = 55`,
  `chamber = 0`, `auto_leveling = 1`, `print_mode = 0`, mode area
  X 115–190 / Y 125–180, `filename = 'loom_benchy_P1_X0011.gcode'`.
- The Fibre is still loaded in the CFC head; PLA has been purged through it.

### Klipper shutdown during the start sequence — 2026-09-15 20:29

Setting `printing_info_filename` needs **two** levels of quoting
(`VALUE="'name.gcode'"`); a probe of mine with a leading space
(`VALUE=" abc "`) raised an uncaught `IndentationError` inside
`save_variables` and **shut Klipper down**. Recovery:
`POST /printer/firmware_restart`, then `G28` (the restart clears homing *and*
every runtime setting, including the 5.49 rotation distance — the start G-code
re-applies it). The owner had to dismiss the HMI modal. Full write-up in
`docs/loom/PRINT_START_AND_STATE_MACHINE.md`.

## Extrusion check on Plastic 1 — `USER-OBSERVED`, 2026-09-15

**Outcome: Plastic 1 under-fed by ~3.9 %; `rotation_distance` 5.719 → 5.49
applied in the Plastic 1 start G-code. Verified: less than 1 mm short over
100 mm.**

Method as on 2026-09-14 for Plastic 2: mark the filament 120 mm above the inlet,
extrude 100 mm at 1 mm/s at 210 °C, owner measures what is left.

All runs at 210 °C, 1 mm/s, marks measured by the owner. From run 3 the mark was
set at 100 mm so the gap reads directly as the error; earlier runs used 120 mm.

| Run | Path | Commanded | Conditions | Gap | Error |
| --- | --- | --- | --- | --- | --- |
| 1 (19:27) | `E` | 100 mm | parked at the waste station, clog present | 24.75 mm from a 120 mm mark | −4.75 % |
| 2 (19:42) | `E` | 100 mm | clog cleared, free air at (150, 150, Z60) | 25 mm from 120 mm | −5.0 % |
| 3 (19:55) | `E` | 100 mm | free air | 3.5 mm | −3.5 % |
| 4 (19:50) | `V` | 50 mm | free air; "a tiny piece came out" | 5 mm | −10 % (**outlier, discarded**) |
| 5 (20:06) | `V` | 100 mm | free air (`IMG_4439`) | 2.5 mm | −2.5 % |
| 6 (20:19) | `E` | 100 mm | **after applying 5.49** (`IMG_4440`) | **< 1 mm, too small to measure** | **≈ 0 %** |

`E` and `V` agree within the scatter, which supports the vendor comment that they
drive the same Plastic 1 motor; run 4 is discarded because 50 mm magnifies both
marking error and the first-stroke lag, and the owner reported almost nothing
emerged. Runs 1–3 and 5 average **−3.9 %** (spread −2.5 % to −5.0 %, consistent
with ±0.5 mm hand marking plus some grip variation).

Correction: 5.719 × 0.961 ≈ **5.49**. Run 6 confirms it: less than 1 mm short
over 100 mm, i.e. within ±1 %. Owner reports flow as "a steady even strand"
throughout; the photos show a clean, gravity-stretched strand, so the shortfall
was never a restriction.

The owner reports run 2 ran as "a steady even strand", so the shortfall is not a
restriction: **Plastic 1 under-feeds by 5 %**, reproducibly. Plastic 2 measured
−0.25 % by the same method, so this is specific to the CFC-side extruder.

Two clogs appeared in Plastic 1 earlier the same evening (the vendor load
routine flagged one at 16:53, and the owner cleared another before run 2).
`OPEN QUESTION`: whether PLA through the CFC nozzle clogs repeatedly.

Lesson recorded: extrude in free air, not at the waste/brush station — a parked
nozzle adds back-pressure and the first reading could not be trusted until it was
repeated in the air. (Run 1 agreeing with run 2 shows the station was not the
cause here, but the ambiguity is avoidable.)

Photos: `extrusion_V_100mm_IMG_4439.jpg` (run 5) and
`extrusion_verify_IMG_4440.jpg` (run 6), originals on the NAS at
`originals/incoming/20260915/`.

## How the correction is applied

`printer.cfg` is read-only over Moonraker (it still reads 5.719), so the Plastic 1
start G-code now issues
`SET_EXTRUDER_ROTATION_DISTANCE EXTRUDER=extruder DISTANCE=5.49` — the same
command the vendor macros use for the fibre motor. It applies for the session and
is re-applied by every Plastic 1 print. When shell access exists it belongs in
`printer.cfg`; until then, **any print started from the touchscreen rather than
from this profile will use the uncorrected 5.719**.

## Results — abandoned at layer 3, Plastic 1 clogged

**Outcome: no baseline. Plastic 1 stopped extruding at layer 3 of 240 and the
print was cancelled. X0011 is `discarded`; no physical piece exists.**

Timeline (`USER-OBSERVED` + machine log):

| Time | Event |
| --- | --- |
| 20:42:20 | Job started, `printing_info_*` correct for the first time (HMI showed the right job) |
| 20:42:26–34 | Brush station, `CLEAN_NOZZLE`, first extrusion at 20:42:35 |
| 20:42:25–20:44 | Layers 1–3 printed; 146 mm of filament, all on the **V** path (`e_filament_used` 0) |
| 20:44:11 | Owner pressed Pause on the HMI — "nothing was coming out" |
| 20:44:13 | `PAUSE` ran with `FIBRE_IMMEDIATE=1`, parked at X50 Y100, LEDs flashing red |
| ~21:0x | Cancelled at the owner's request; heaters off |

Owner video `IMG_4441.MOV` (NAS `originals/incoming/20260915/`), 4K60, 17.8 s of
the CFC head at the pause position. The part-cooling duct hides the nozzle tip,
so the video shows the absence of extrusion rather than the blockage itself.

### What the machine says about the failure mode

- `pause_error_message` was **null** and all five filament sensors read
  `filament_detected: true` — so this was **not** a runout, door or vendor clog
  trigger. The owner initiated the pause.
- `filament_motion_sensor filament_sensor_2` (detection length 7 mm) never
  fired, so **filament kept moving through the extruder** while nothing left the
  nozzle. That places the blockage **at or near the nozzle**, not at the drive
  gear.

### Flow demanded by X0011 vs X0008

Measured from the two G-code files with `2026-09-15-T4/gcode_profile.py`:

| Feature | X0008 (Plastic 2, 0.4 mm) | X0011 (Plastic 1, 0.7 mm) |
| --- | --- | --- |
| Outer wall | 175 mm/s, 0.40 mm → **12.00 mm³/s** | 88 mm/s, 0.75 mm → **11.93 mm³/s** |
| Sparse infill | 175 mm/s → **12.00 mm³/s** | 88 mm/s → **11.95 mm³/s** |
| Gap infill | 141 mm/s → 11.59 mm³/s | 125 mm/s → **13.56 mm³/s** |
| Internal bridge | 75 mm/s → 9.04 mm³/s | 32 mm/s → 11.82 mm³/s |

Both files sit on Orca's 12 mm³/s volumetric cap almost everywhere, so **raw
volumetric demand does not by itself explain why Plastic 1 failed and Plastic 2
did not** — X0008 printed the same model at the same mm³/s and the same 205 °C
without trouble. Gap infill at 13.6 mm³/s is the only place X0011 exceeds it.

### Ranked hypotheses — `INFERENCE`

1. **Residue from the previous CFC material in the composite hotend.** The CFC
   nozzle last ran fibre-reinforced composite whose matrix needs ~270 °C. PLA at
   205–210 °C cannot melt or flush that residue. Supporting evidence: the vendor
   load routine already flagged a clog at 16:53 *before* any of our prints, the
   owner had to clean the nozzle during loading, and clogs then recurred at
   ~19:40 and 20:44 — three in one evening on Plastic 1 and none on Plastic 2
   with the same spool.
2. **A fibre stub in the shared channel.** The CFC nozzle merges the fibre and
   the plastic; a cut fibre end left in the channel never melts and PLA has to
   flow around it. FibreSeek ships a separate SOP for exactly this (FS-139),
   which implies it is a known failure.
3. **Under-melt at print flow in the CFC melt zone.** Weakest: the free-air
   extrusion checks at 1 mm/s all passed, and Plastic 2 sustained the same
   12 mm³/s. It would only explain the failure if the composite hotend has less
   plastic-melting capacity than the FFF hotend despite the larger nozzle.

`OPEN QUESTION`: which of these it is. Hypothesis 1 predicts that a high-temp
purge clears it; hypothesis 2 predicts a solid fibre core in whatever is pulled
out of the nozzle.

### Clog cleared — what came out supports hypothesis 1

`USER-OBSERVED` 2026-09-15 ~21:15. Owner cleared the blockage and reports
getting all of it. Photos in this folder (originals on the NAS at
`originals/incoming/20260915/`):

- `clog_purge_blob_IMG_4449.jpg` — the purged mass on the plate. It is **not
  uniform white PLA**: opaque white PLA+ is mixed with large **glassy
  translucent** regions and **amber/orange streaks**, and the whole mass is full
  of trapped gas bubbles. SUNLU PLA+ White is opaque; a translucent glassy phase
  is what the previous CFC matrix looks like, and amber is thermally degraded
  polymer. One small dark speck is visible; no continuous fibre strand is.
- `clog_nozzle_crust_IMG_4453.jpg` — before cleaning: a thick tan/cream baked
  crust ringing the nozzle seat and more of it up around the heater and
  thermistor leads.
- `clog_nozzle_cleaned_IMG_4456.jpg` — after cleaning: bare metal on the block,
  nozzle protruding clear.

**Reading (`INFERENCE`):** mixed-polymer residue, consistent with hypothesis 1 —
old CFC matrix that PLA at 205–210 °C could not flush, degraded in place and
finally pushed out as one plug. Hypothesis 2 (fibre stub) is **not supported**:
nothing fibre-like came out.

> **Corrected 2026-09-16.** That reasoning was wrong. FS's reply gives the
> mechanism as *the fibre failing to carry molten plastic through the nozzle*,
> under which the absence of fibre in the purge is consistent with, not evidence
> against, a fibre-path cause. See `notebook/2026-09-16_composite-hotend-heater-check/`. Hypothesis 3 (under-melt at flow) remains
unsupported and is now redundant — a physical plug explains the failure.

This also explains the whole evening: the vendor load routine flagged a clog at
16:53 before any of our prints, the owner cleaned the tip during loading, and
clogs recurred at ~19:40 and 20:44. The plug was there from the start and was
being pushed around rather than removed.

The blob is worth keeping in a labelled bag as the physical evidence for this
diagnosis; it is not a print, so it gets no `XNNNN` ID.

### NOT cleared — melt is packing the block around the fibre guide tube

`USER-OBSERVED` 2026-09-15 ~22:00. **The clog was not cleared.** After the
purge, a needle through the orifice and an attempted cold pull at 250 °C, a
50 mm hand push still bunched at the nozzle. Owner's own description: *filament
is filling the aluminium block, and poking it with the needle made the level
**rise**; it appears to be clogging right where the **guide tube** sits over the
nozzle.*

Photos: `clog_block_before_poke_IMG_4465.jpg` and
`clog_block_filled_IMG_4466.jpg`. In the second, pale material is visible packed
around the joint where the tube enters the top face of the heater block, and as
a pale ring at the block's underside around the nozzle. The material level
moving **up** in response to pressure from below is the diagnostic detail.

**`INFERENCE` — this is not a simple orifice blockage.** Melt is taking the
annulus around the fibre guide tube as its path of least resistance instead of
the 0.7 mm orifice. That is what a guide tube that is not seated tightly against
the nozzle produces: every gram of plastic pushed in packs the gap above rather
than exiting below, and once it freezes it locks the assembly. It would explain
the whole pattern — why the CFC side clogged three times with PLA while Plastic 2
never did with the same spool, why cleaning "worked" briefly each time, and why
neither a high-temp purge nor a needle nor a cold pull fixed it.

`OPEN QUESTION`: whether the guide tube has receded, is damaged, or was never
seated. Disassembly will show it — check the seating face and the tube end
before cleaning anything off them, and photograph the annulus before clearing.

**Status: owner is disassembling the hotend assembly tomorrow (2026-09-16),
per FS-133 Step 4. Printer powered off 2026-09-15 ~22:00.**

### Upgraded diagnosis: melt is leaking out of the top joint

The rest of the owner's photos from the same session (added 2026-09-16) show
more than a blocked orifice:

- `clog_leak_over_block_IMG_4448.jpg` — **the top face of the heater block is
  buried under a mound of solidified plastic** that has welled up around the
  heat-break/guide-tube joint and spread across the block, over the
  heater/thermistor area. The needle is in frame; a thin strand hangs from the
  nozzle.
- `clog_orifice_plugged_IMG_4460.jpg` — looking up into the nozzle-plate
  recess: the black nozzle tip with a **white plug visible in the orifice**,
  ringed by baked tan crust.
- `clog_seat_crust_IMG_4452.jpg` — the same seat from another angle, the crust
  ring around it clearly thick and layered, i.e. built up over many cycles.

**`INFERENCE`, revised: this is a hot-end leak at the nozzle / heat-break joint,
not only a clog.** Melt under pressure is escaping upward through the joint and
pooling on top of the block. That is the classic signature of a nozzle that is
not sealing against the heat-break — on this head, with the fibre guide tube
also landing in that joint. The orifice plug and the repeated "clogs" are then
**downstream symptoms**: pressure that should open the orifice is venting into
the gap instead, so flow stalls, material stagnates and cooks, and the crust
grows. It also explains the layered crust — this has been developing over many
prints, not since last night.

**Consequence for the repair: cleaning alone will not fix it.** The joint has to
be taken apart, the leaked plastic removed from the block, heater and thermistor,
and the nozzle re-seated and tightened correctly — on most hot ends that means
tightening **at temperature** against the heat-break, though FS-133 does not
state a procedure or a torque.

> **Corrected 2026-09-16 by FS:** *"There is no special hot-tightening procedure
> or specific torque requirement for this connection. Please follow the existing
> procedure in the SOP."* The hot-tightening advice above does not apply to this
> hotend. `OPEN QUESTION`: FibreSeek's specified seating
and tightening procedure for the composite hotend, and whether the guide tube is
separately serviceable. Asked in `docs/vendor/VENDOR_CORRESPONDENCE.md`.

**Safety note for reassembly:** plastic has flowed over the heater cartridge and
thermistor area. Both need to be clean and correctly seated before the block is
powered again; a thermistor sitting in a plastic shell reads low and the heater
runs away.

### Vendor procedure to follow

- **FS-133 "Composite Plastic Hotend Unclogging"** (`sources/vendor-docs/Composite
  Plastic Hotend Unclogging.pdf`): heat the **left** nozzle to the material's
  printing temperature first — the SOP warns that lower temperatures block
  extrusion; disconnect the PTFE tube and hand-push filament as the decisive
  test (if it exits, the path is clear and the **extruder** is at fault, which
  the SOP says announces itself with loud abnormal noise); otherwise power off,
  pull the toolhead front cover (bottom clips both sides, unplug FAN-R), H2.5 to
  remove the two fixing screws, free the composite hotend and force a slender
  hex key through the nozzle, then extrude several times to flush debris.
  Replace the assembly if it will not clear.
- **FS-139 "Fiber Unclogging in Composite Hotend"** covers the fibre side of the
  same nozzle and is worth a pass if hypothesis 2 holds.
- **Required afterwards**: `Calibration > Print Calibration > Nozzle offset`,
  **"Nozzle offset" only**, after removing or replacing the composite hotend
  (FSD-0007, `MANUFACTURER_GUIDANCE`, HIGH confidence).

### Before Plastic 1 PLA is attempted again

1. Clear the clog per FS-133 and recalibrate the nozzle offset.
2. Purge at the **CFC material's** temperature, not PLA's, to get old matrix out
   before PLA goes back in.
3. Re-slice with the volumetric limit dropped from 12 to about 8 mm³/s so the
   first attempt is not simultaneously testing the hotend and its flow ceiling.
4. Print something small first — the tag alone, or a single-wall cube — rather
   than committing 27 minutes to a Benchy.
