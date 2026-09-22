# Loom PLA+ 2.0 flow-rate calibration, pass 1 — 2026-09-15 (right nozzle)

**Result: best patch −5 → recommend `filament_flow_ratio` 0.95 (from 1.00).**
**Superseded by pass 2** (`../2026-09-15-T3/RESULTS.md`): recommend 0.96.

Physical sample **X0006** (formerly SMP-0006) (`experiments/Samples/samples.jsonl`; no tag).

`EXPERIMENTAL`. Follows the retraction session
(`../2026-09-15-T1/RESULTS.md`). Provenance: live Moonraker session under the
owner's 2026-09-14 full-access authorization.

## Baseline

Everything held at the accepted baseline: SUNLU PLA+ 2.0, right nozzle T1,
205 °C (first layer 210 °C), bed 55 °C, 0.2 mm layers, right-nozzle offset
`x −32.823188, y −0.006438, z 2.57`. Retraction unchanged (0.5 mm @ 15 mm/s).
Current `filament_flow_ratio` = **1.0**. Machine start G-code sets
`extruder1` pressure advance 0.03.

Settings source: the GUI-resolved project settings embedded in
`../2026-09-14-T1/loom_T1.3mf`, with only the nozzle temperatures overridden.
`OPEN QUESTION`: any change the owner made to the Orca presets after 2026-09-14
other than the 205/210 °C temperatures is not reflected.

## Method — OrcaSlicer flow pass 1, reproduced from the CLI

Orca's Calibration → Flow rate is GUI-only, so `make_flow_patches.py` (this
folder) rebuilds it:

1. Takes Orca's own bundled model
   `OrcaSlicer.app/Contents/Resources/calib/filament_flow/flowrate-test-pass1.3mf`:
   nine patches named `flowrate_m20 … flowrate_20`, each with its modifier
   embossed on top.
2. Exports it to a project with `OrcaSlicer --export-3mf`, swaps in the Loom
   project settings, and gives every patch the per-object overrides Orca's
   calibration applies (3 walls, one top wall, 5 top / 1 bottom shells, 35 %
   infill, monotonic top at 0.48 mm line width, top/solid speeds capped by the
   12 mm³/s volumetric limit → 137 mm/s, ironing off) plus
   `print_flow_ratio = (100 + modifier) / 100`.
3. Two deliberate deviations: **no brim** on the patches (the Loom project
   default is `auto_brim`, which collides on the calibration grid — Orca's own
   path-conflict check refused the first build), and the layout is **recentred
   on (150, 150)** with `--arrange 0` rather than auto-arranged, so patches keep
   their grid and orientation.
4. Slices with `OrcaSlicer --arrange 0 --slice 0`.
5. **Verifies the G-code**: per patch, top-surface extrusion per mm relative to
   `flowrate_0`. All nine matched their intended ratio within **0.06 %**
   (5-decimal E rounding). The script exits non-zero above 0.5 %.

Known difference from the GUI: the patches slice at **10 layers (2.0 mm)**.
`INFERENCE`: Orca's GUI rescales Z for its own layer target; this build does
not. The read surface — a monotonic top over five solid layers — is the same.

| Patch | `print_flow_ratio` |
| --- | --- |
| −20 | 0.80 |
| −15 | 0.85 |
| −10 | 0.90 |
| −5 | 0.95 |
| 0 | 1.00 (current) |
| +5 | 1.05 |
| +10 | 1.10 |
| +15 | 1.15 |
| +20 | 1.20 |

File: `loom_flow_pass1.gcode`, 640,450 bytes, sha256
`db9ec85de06bbb92bd06d8f68a35e6526740ad0cdf41dad01c57108058f03028`; 10 layers,
14.55 g, estimated 30 m 57 s. Patches span X 88.2–211.8, Y 103.2–196.8.

## Machine setup and timeline

- `SAVE_VARIABLE`: `printing_info_auto_leveling = 1`,
  `printing_info_mode_x_min/y_min/x_max/y_max = 80/95/220/205` (fresh probe
  limited to the patch footprint plus margin). Preheat and offsets already
  correct; unchanged.
- Plate checked clear by camera snapshot before start (the T1 pillars had been
  removed).

| Time (local) | Event |
| --- | --- |
| 10:53:36 | `SET_PRINT_STATS_INFO STATE=precheck` → `SDCARD_PRINT_FILE FILENAME=loom_flow_pass1.gcode` |
| 10:54–10:56 | `heating_bed`, `heating_nozzle` |
| 10:56–10:59 | `leveling`: nozzle cooled (macro guards the piezo probe) |
| 11:01:42–11:09:47 | adaptive mesh over the patch area: **45 points** (vs 81 full-bed), ~8 min |
| 11:09–11:11 | nozzle heat, homing, brush |
| 11:11:49 | `printing` |
| 11:45:21 | `complete`, 10/10 layers; heaters off |

Mesh check: `min=-0.1204 max=0.2149 range=0.3353 (limit=1.0000)`. Nozzle held
205–206 °C (210–212 °C on the first layer). No errors in the G-code store.
Moonraker `print_stats`: `total_duration` 2,021 s, `filament_used` 4,994 mm.
Camera snapshot at completion shows the patches on the plate (too coarse to read).

## Results

`USER-OBSERVED` from owner photos on NAS `originals/incoming/20260915/`
(4032×2268 HEIC): `IMG_4142`, `IMG_4143` (all nine, 11:45), `IMG_4144` (top
and middle rows, close), `IMG_4145` (middle and bottom rows, close), `IMG_4149`
(all nine under low raking light from the left, 11:50). Crops
of the middle and bottom rows with local contrast equalisation are in this folder
(`analysis_patches_p5_0_m5_IMG_4144.jpg`,
`analysis_patches_m20_m15_m10_IMG_4145.jpg`).

| Patch | Flow | Top surface |
| --- | --- | --- |
| +20 | 1.20 | rough, pebbly, ridged; embossed digits blurred — clearly over |
| +15 | 1.15 | rough and ridged — over |
| +10 | 1.10 | ridged, chevron texture — over |
| +5 | 1.05 | fine raised crosshatch texture across the whole top — slightly over |
| **0** | **1.00** | smooth; faint diagonal texture near one edge and a few specks |
| **−5** | **0.95** | **smoothest and most uniform; no line texture visible even contrast-enhanced** |
| −10 | 0.90 | faint but visible diagonal line gaps — slightly under |
| −15 | 0.85 | clear line gaps — under |
| −20 | 0.80 | distinct gaps between every line — under |

Raking light (`IMG_4149`, crop `analysis_patches_0_m5_raking_IMG_4149.jpg`)
separates the two best: on **0** every top line stands as a bright raised bead
and excess material forms a ridge where the top lines meet the wall; on **−5**
the lines are lower-relief and continuous, with no edge ridge and no dark gaps.
Under the same light +5 shows a raised frame around the patch and +10…+20 show
ridges and chevrons.

**Reading: best patch −5, bracketed by visible over-extrusion at +5 (and mild
bead relief at 0) and under-extrusion at −10.** The optimum lies between about 0.91 and 1.00, most
likely near 0.95. Not touch-tested; a finger check of 0 vs −5 by the owner
would be a useful tie-break.

**Recommendation.** Set `filament_flow_ratio` for `SUNLU PLA+ 2.0 @System -
Loom T1` to **0.95** (from 1.00). Optional pass 2 for a 1 % answer: sweep
**0.91–1.00** — i.e. base 1.00 with Orca's pass-2 modifiers 0 … −9 — which
spans exactly the bracket above. (Orca's own pass 2 would take 0.95 as its base
and sweep 0.86–0.95, missing 0.96–0.99.)

## Error caused by this session: HMI "Malformed command" pop-ups

`CONFIRMED` (G-code store; owner photo `IMG_4147`, HMI clock 11:49). While
restoring the prep variables at 11:47:42, a shell word-splitting mistake sent
five malformed commands through Moonraker, e.g.
`SAVE_VARIABLE VARIABLE=printing_info_mode_x_min 10 VALUE=`. Klipper rejected
each (`!! Malformed command …`), so **nothing was changed by them**, and the
correct commands followed at 11:47:49 (values verified in `variables.cfg`).
But the touchscreen raised an **"Error — Error Code: UNKNOWN"** modal for
them, which the owner had to dismiss. Lesson recorded in the operational doc:
any `!!` error from a Moonraker-issued command surfaces on the HMI, so batch
commands must stop at the first failure rather than run on.

## Config/state changes made on Loom this session

- For the print: `printing_info_auto_leveling = 1`, `printing_info_mode_*` =
  80/95/220/205.
- After the print (11:47): **restored** `printing_info_mode_*` to 10/10/290/290
  and `printing_info_auto_leveling` to 0 — the values found at the start of the
  day — so a later print does not inherit a small mesh area.
- No `SAVE_CONFIG` issued. The vendor mesh routine will have rewritten
  `[bed_mesh runtime_active]` in `printer.cfg` again (see LM-025); not re-captured.
- `loom_flow_pass1.gcode` remains in the Loom `gcodes` root.

## Evidence

- In this folder: `make_flow_patches.py` (generator + G-code verification),
  `loom_flow_pass1.3mf` (the sliced project), `loom_flow_pass1.gcode` (the file
  printed), and three `analysis_patches_*.jpg` crops of the owner photos
  (greyscale, local contrast equalised; derived, originals untouched).
- Vendor macros explaining the prep sequence and mesh persistence: LM-024
  (`print_control.cfg`) and LM-025 (`calibration.cfg`), capture session
  `sources/loom/sessions/2026-09-15T155418Z`.
- Moonraker calls that drove the print were not preserved as byte-for-byte
  captures; this record is their account.
- Owner photographs: NAS `originals/incoming/20260915/` —
  `IMG_4142` sha256 `bcbc9734625b3541c5ea36e0a68b976054e0f8bb5eb684b476011338925d3ed2`,
  `IMG_4143` `97bcbfabf59136fa4371d1887d1438f1f527617606813b6d2dd09379c4218990`,
  `IMG_4144` `09efe12fbd5cfe801ad688c145263c590b8f70deea552289b498a35a3c5766fb`,
  `IMG_4145` `e875ea52b772f754dba85cef7a08d039d74201c86342118ee8a17458ace54b4e`,
  `IMG_4147` (HMI error) `13e0d8d881ce5eeb7d53cc79e6a6f18cc9c6d900010f1df4ae9ef5e8d5fb6766`,
  `IMG_4149` `92f72210732fdc985c47a84bc788183f34ba65f981c675c596e48a8576e32e87`.

