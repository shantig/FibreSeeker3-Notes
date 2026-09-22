# Loom PLA+ validation Benchy X0008, and comparison with FibreSeek's PLA-Benchy — 2026-09-15

Physical sample **X0008** (`experiments/Samples/samples.jsonl`), the first
sample with a printed ID tag. `EXPERIMENTAL`. Printed on **Plastic 2** (FFF,
right, `extruder1`, `T1`, 0.4 mm). Owner requests: "print the Benchy as X0008",
then "read DemoFiles/PLA-Benchy on Loom and compare its settings with X0008".

## Purpose

One ordinary part with the owner's tuned preset — 205 °C (first layer 210 °C),
`filament_flow_ratio` 0.96, retraction 0.5 mm @ 15 mm/s — to check the settings
together, and to prove the ID-tag workflow.

## How the file was built

`experiments/Samples/make_tagged_print.py` (new): Orca's bundled 3DBenchy
(`OrcaSlicer.app/…/handy_models/3DBenchy.drc`) plus an `X0008` tag from
`make_sample_tag.py`, sliced with the Loom project settings.

```
python3 experiments/Samples/make_tagged_print.py --sample-id X0008 \
  --reference notebook/2026-09-14_pla-temperature-tower/loom_T1.3mf \
  --out notebook/2026-09-15_benchy-X0008-plastic2 --name loom_benchy_X0008 \
  --set nozzle_temperature=205 --set nozzle_temperature_initial_layer=210 \
  --set filament_flow_ratio=0.96 \
  /Applications/OrcaSlicer.app/Contents/Resources/handy_models/3DBenchy.drc
```

- **Why not the live presets directly.** OrcaSlicer's CLI refuses the owner's
  user presets ("process not compatible with printer"), because they do not
  inherit from a system preset; clearing `compatible_printers` in temporary
  copies did not help.
- **Equivalence check instead.** All 515 keys of the live machine, process and
  filament presets were compared with the 2026-09-14 resolved project settings
  in `loom_T1.3mf`. The only differences were the preset's printer-connection
  fields (`print_host`, `print_host_webui`, empty credential fields — not print
  settings) and the two tuned filament values, which the command overrides. The
  G-code confirms `nozzle_temperature = 205`, `_initial_layer = 210`,
  `filament_flow_ratio = 0.96`.
- **Tag legibility.** At the new 0.8 mm dot size the sliced text toolpaths render
  every dot of "X0008", including the X centre and the zero slashes.
- File `loom_benchy_X0008.gcode`, 2,610,508 bytes, sha256
  `487f05eae8f3f5f1059f45ab456f400d932f757aeb459f279f6ee264e25c299c`; 240
  layers, 48 mm, 10.73 g, estimated 33 m 39 s.

## Print

| Time (local) | Event |
| --- | --- |
| 15:26:03 | `SET_PRINT_STATS_INFO STATE=precheck` → `SDCARD_PRINT_FILE` (stop-on-first-error script) |
| 15:28:46–15:31:57 | Plastic 1 (CFC) nozzle cool-down before probing |
| 15:32:55 | Z home check passed (delta 0.0038 mm) |
| 15:32:56–15:33:53 | `BED_MESH_TEMP_LOAD` predicted `default` mesh at 55 °C, then `FAST_BED_MESH` probed **5 points** (centre and the four corners of the `mode` area 110–195 × 120–185) |
| 15:34:51 | mesh range check 0.5038 mm (limit 1.0) |
| 15:35:51 | printing |
| 16:13:46 | `[PRINT_COMPLETED] Print complete!`; history status `completed` at 16:14:22 |

Moonraker history: `print_duration` 2,279 s, `filament_used` 3,682 mm. No `!!`
errors. Afterwards `printing_info_mode_*` was restored to 10/10/290/290 and
`printing_info_auto_leveling` to 0 (stop-on-first-error script, all `ok`). No
`SAVE_CONFIG`.

Observed at the machine (owner photo `IMG_4416`, 15:55, in the owner's Downloads —
not yet on the NAS): FFF 206 °C, CFC 40 °C (idle), 14 min left, status bar
"High Strength Mode". `INFERENCE`: the label is the HMI's name for
`printing_info_print_mode = 0`, which the vendor macro uses only to pick the light
pattern.

Operational findings:
- With `auto_leveling = 1` and a small `mode` area, the vendor path did **not**
  probe a full grid: it loaded the temperature-predicted `default` mesh and
  corrected it from 5 probe points (`FAST_BED_MESH`). This morning's full-area
  probe did 81 points, and flow pass 1 (area 80–220 × 95–205) did 45.
- The macro logged `Printing file: DemoFiles/PETG-Scraper.gcode`: it reports the
  stale `printing_info_filename` variable, which Moonraker-started prints never
  update. `OPEN QUESTION`: set it before each start (string `SAVE_VARIABLE`
  values need Python-literal quoting) so the HMI and logs show the real file.

## Comparison with FibreSeek's `DemoFiles/PLA-Benchy.gcode`

Source: LM-026 (capture session `sources/loom/sessions/2026-09-15T211520Z`), Rocket 1.3.1.480, generated 2026-07-15, `PRINTING_MODE: Plastic
Only`, also on **Plastic 2** (`T1`). Both files were measured the same way with
`gcode_profile.py` (this folder): what the G-code actually does, per `;TYPE:`
feature. Flow is extruded volume per mm relative to Orca's nominal cross-section;
the method returns exactly 0.96 on X0008's fixed-width features, which validates
it. Speeds are the value covering most of each feature's extrusion length.

| Setting | FibreSeek PLA-Benchy (Rocket) | X0008 (owner's Orca preset) |
| --- | --- | --- |
| Filament | FibreSeek "PLA" ("CLEAR PLA", embedded profile) | SUNLU PLA+ 2.0 White |
| Layers | 240 × 0.2 mm (0.4 on internal bridges) | same |
| Nozzle temperature | **220 °C** all layers | 210 °C first layer, **205 °C** after |
| Bed | 55 °C | 55 °C |
| Flow (measured) | **0.97** | **0.96** |
| Line width | outer 0.42, inner and sparse 0.45, solid and top 0.42, first-layer bottom 0.5 mm | 0.40 mm everywhere |
| Outer wall speed | **50 mm/s** (96 % of outer-wall length) | **~175 mm/s** (200 set, capped by 12 mm³/s) |
| Inner wall, sparse infill | 152 mm/s | 175 mm/s |
| Solid infill, top surface | 164 / 163 mm/s | 175 / 174 mm/s |
| Volumetric limit (implied) | ≈12 mm³/s (0.079 mm³/mm × 152 mm/s) | 12 mm³/s |
| First layer | walls 50, solid 105 mm/s; accel 2,000 | walls 50, solid 105 mm/s; accel 500 |
| Travel | 1,000 mm/s | 500 mm/s |
| Retraction | **0.5 mm @ 30 mm/s with wipe** (0.21 mm before the wipe, 0.29 mm during a 105 mm/s wipe) | **0.5 mm @ 15 mm/s, no wipe** |
| Lift | spiral lift, +0.4 mm | 0.2 mm straight lift |
| Pressure advance | 0.035 (filament override of the start's 0.04) | 0.03 |
| Square-corner velocity | start sets 10; the `T1` macro then applies the saved 5 (`INFERENCE` from macro order) | 5 (`T1` macro) |
| Part cooling | `M106 P1` (plastic cooling fan): off on layer 1, then 100 % | plain `M106` (plastic *and* fibre cooling fans): off on layer 1, then 100 % |
| Chamber fans | from layer 50: cross-flow (`P3`) and exhaust (`P5`) at 100 % | none |
| Skirt / brim | 1 skirt loop | auto brim, only 35 mm extruded (a small first-layer feature near X149 Y160) |
| Arc fitting | off | on |
| Layers containing top surface | 25 | 37 (`INFERENCE`: fewer top shells in Rocket) |
| Estimated time | 43 min | 34 min (actual print 38 min) |

Fan mapping is `CONFIRMED` from Loom's `fans.cfg` `M106` macro: no `P` → plastic
and fibre cooling fans; `P0` filter, `P1` plastic cooling, `P2` fibre cooling,
`P3` cross-flow circulation (also turns the chamber heater target to 0), `P4`
mainboard, `P5` exhaust.

### What it means

- **Flow agrees.** FibreSeek's own PLA profile prints at 0.97; the calibrated 0.96
  for SUNLU PLA+ is consistent with it.
- **Retraction.** FibreSeek retracts the same 0.5 mm but at **30 mm/s with wipe
  on** — the direction recommended from the retraction test (raise the speed,
  enable wipe for the stray hairs).
- **Outer wall speed is the largest difference.** FibreSeek prints outer walls at
  50 mm/s for finish; the owner's preset runs them at ~175 mm/s. If the Benchy's
  hull shows ringing or roughness, outer wall speed is the first thing to lower.
- **Temperature differs by filament.** 220 °C for FibreSeek's PLA is within the
  manual's 210–230 °C PLA-Basic range; 205 °C came from a tower on SUNLU PLA+.
- **Chamber airflow.** FibreSeek switches on the cross-flow and exhaust fans from
  layer 50 on PLA, presumably to keep an enclosed chamber cool; the Orca profile
  never does. Worth adding for long PLA prints.
- `INFERENCE`: Rocket's plastic-only output is OrcaSlicer/Bambu-family G-code
  (`;TYPE:`, `;WIDTH:`, `;WIPE_START`, `;_SET_FAN_SPEED_CHANGING_LAYER`), unlike
  its composite files (LM-021).
- **The embedded `; SESSION:` profile is not what printed.** It lists retraction
  15 mm/s, extrusion multiplier 1.0, travel 500 mm/s, accelerations 5,000 and 3
  skirt loops, while the emitted moves use 30 mm/s with wipe, flow 0.97, travel
  1,000 mm/s, accelerations up to 10,000 and 1 skirt loop. Its temperatures
  (220 / 55 °C) do match. `OPEN QUESTION`: which profile Rocket uses for
  plastic-only slicing, and whether it can be exported.

## Results

**Pass: the tuned Plastic 2 PLA+ profile prints a clean Benchy.** Owner: "it
looks pretty good to me". `USER-OBSERVED` photos read by Claude (NAS
`originals/incoming/20260915/`, `IMG_4417`–`IMG_4437`):

- **Geometry and details clean:** arches, portholes, chimney bore, deck and cabin
  roof, the underside and the bow flare all printed without sagging, gaps or
  layer shifts.
- **Tag X0008 printed and reads correctly** (`IMG_4432`–`IMG_4434`).
- **Minor stringing:** a few fine hairs at the chimney top and inside the cabin
  windows — the same residual hairs as the retraction test.
- **Two small vertical seam scars on the bow side** (`IMG_4434`), a few layers
  tall; `INFERENCE`: seam start/stop marks (aligned seam, 0.5 mm @ 15 mm/s
  retraction, PA 0.03).
- **Hull:** fine, even layer lines; slightly more visible banding on the lower
  stern overhang, as usual for a Benchy.

Remaining polish, all optional: retraction 30 mm/s with wipe (as FibreSeek's
PLA-Benchy uses) for the hairs; seam position or pressure advance for the bow
scars; slower outer walls only if a smoother hull is wanted.

Photo files: `IMG_4417`, `IMG_4420`–`IMG_4427`, `IMG_4430`–`IMG_4437` (HEIC). Each
of `IMG_4417`–`IMG_4430` was also uploaded as a byte-identical `… (1).heic` copy
(SHA-256 matched); only the originals are listed.

## Evidence

- In this folder: `loom_benchy_X0008.3mf`, `loom_benchy_X0008.gcode`,
  `gcode_profile.py` (the measurement used for the table).
- LM-026: FibreSeek `DemoFiles/PLA-Benchy.gcode`, session
  `sources/loom/sessions/2026-09-15T211520Z`.
- Moonraker calls that drove the print were not preserved as byte-for-byte
  captures; this record is their account.
