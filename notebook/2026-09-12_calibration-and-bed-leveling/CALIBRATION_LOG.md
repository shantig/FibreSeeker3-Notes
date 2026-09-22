# Loom calibration and bed leveling — 2026-09-12 evening

Status: **COMPLETE per machine log.** The owner's manual heatbed leveling made
the bed worse (BM-006, 1.315 mm). It was recovered to 0.486 mm (BM-008). A full
HMI calibration and a fibre extrusion calibration then completed without errors.
A plastic-plus-fibre test print is still pending.

Evidence labels: `CONFIRMED` (shown by a cited preserved capture),
`USER-OBSERVED` (owner report or owner media), `INFERENCE`, `OPEN QUESTION`,
`UNKNOWN`. FibreSeek/Loom evidence only. `EXPERIMENTAL` owner-machine
observations; nothing here is manufacturer guidance.

Sources: LM-013 (rotated klippy.log to 21:21), LM-014 (klippy.log 21:21–22:11),
LM-015 (mesh profiles and saved variables at 22:15). Session:
`sources/loom/sessions/2026-09-13T031552Z/`. All times are Loom local
(UTC−5). Owner photo IMG_4038 (see `../PHOTOS_2026-09-12.md`).

## 1. Context

- The owner asked for the proper calibration sequence. Claude's guidance drew
  on FS-120 (User Manual R1 §3.2.2 Print Calibration; §4.3 maintenance table)
  and FS-154 (Heatbed Leveling SOP, Timing Belt Tension SOP, Fiber Extruder
  Roller SOP step 13, layer-shift and first-layer SOPs).
- Guidance sequence given: belts only if needed → manual heatbed screw
  leveling (hot bed, A4 paper, left nozzle) → HMI Print Calibration → Fiber
  Extrusion Calibration → verification print.
- **Correction, `CONFIRMED` (LM-013).** The first guidance relied on LM-012,
  which ends at 14:00. It said no nozzle-offset calibration was recorded after
  the Sep 12 hotend unclogging. LM-013 shows the owner had already run a full
  HMI calibration that afternoon:

| Local time | Step | Result |
|---|---|---|
| 15:57 | Input shaper | X zv 34.6 Hz, Y mzv 32.8 Hz |
| 16:02 | Nozzle offset | x −32.810844, y 0.012187, z 2.685436 |
| 16:07–16:41 | Bed level, 55 °C and 100 °C stages | temperature model fitted; `default` committed |
| 16:46–16:48 | Nozzle PID | left Kp 22.476 / Ki 1.314 / Kd 96.084; right 28.399 / 8.606 / 23.429 |
| 16:48–16:58 | Fibre extrusion calibration | extruder2 `rotation_distance` 37.5 → 38.25 → 37.485 |

## 2. Manual heatbed leveling and meshes

### 2.1 Timeline, `CONFIRMED` (LM-013)

- **19:18:48** — bed heating to 85 °C starts; the bed reaches 85 °C at 19:20:44.
- **19:20:25** — Z homing probe check **failed**: −0.1588 mm against an
  expected −0.100 ± 0.05 mm. Samples drifted −0.104 → −0.118 → −0.153 →
  −0.165 mm.
- **19:23:13** — probe check passed at −0.1334 mm, but samples still drifted
  from −0.126 to −0.186 mm.
- **19:36:03** — probe check −0.0977 mm, samples stable.
- **19:36:47–19:50:47** — owner-initiated `BED_MESH_CALIBRATE` saved as
  **BM-006**.
- **19:54:17–20:08:18** — **BM-007**, after the owner reports tightening all
  retaining screws under the bed (`USER-OBSERVED`).
- **20:13:56** — probe check −0.1000 mm.
- **20:32:59–20:47:26** — **BM-008**, after corner-screw adjustment
  (`USER-OBSERVED`).

`INFERENCE`: the drifting samples at 19:20 and 19:23 fit a bed still settling
thermally, since the first probe came before the bed reached 85 °C. They also
fit a plate moving on loosened retaining screws. The log cannot tell these
apart.

`UNKNOWN`:
- when the retaining screws were loosened, and the exact screw turns;
- which corners were adjusted before BM-006.

The owner's corner checks used console moves (`G28`, `BED_MESH_CLEAR`, `G90`,
`G1 Z5` before each XY move, `G1 Z0` for the paper check).

### 2.2 Mesh comparison, `CONFIRMED` (LM-015)

All values are in mm, relative to the mesh zero reference at (150, 150).
Tilt is the least-squares plane slope across the 280 mm probed span. Residual
is the range left after removing that plane (bend).

| Profile | Spread | Min | Max | Tilt X | Tilt Y | Residual | X10 Y10 | X290 Y10 | X10 Y290 | X290 Y290 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BM-004 | 0.485 | −0.088 | +0.397 | −0.240 | −0.131 | 0.386 | +0.379 | +0.268 | +0.186 | +0.192 |
| BM-005 | 0.498 | −0.119 | +0.379 | −0.245 | −0.126 | 0.304 | +0.299 | +0.175 | +0.071 | +0.097 |
| BM-006 | 1.315 | −0.035 | +1.280 | −0.301 | +0.147 | 1.062 | +0.715 | +0.733 | +1.280 | +0.802 |
| BM-007 | 0.662 | −0.317 | +0.345 | −0.400 | +0.075 | 0.484 | −0.188 | −0.317 | +0.345 | −0.315 |
| BM-008 | 0.486 | −0.148 | +0.338 | −0.294 | +0.026 | 0.349 | +0.054 | +0.075 | +0.286 | +0.136 |
| `default` (21:49) | 0.504 | −0.155 | +0.349 | −0.294 | −0.032 | 0.395 | +0.135 | +0.180 | +0.349 | +0.159 |

Additional measurements:
- The pre-leveling `default` (committed 16:41) had a spread of 0.487 mm. It was
  read during the session from an **unpreserved** object query at
  2026-09-13T00:57Z and has since been overwritten.
- The new `default` differs from BM-008 by −0.039 to +0.105 mm per point.

Interpretation:
- `INFERENCE`: BM-006 is a bowl, with every corner 0.7–1.3 mm above the
  centre. That fits a plate left free on loosened retaining screws. Tightening
  them (BM-007) removed the bowl but left a 0.40 mm X tilt with both X=290
  corners low. Corner adjustment (BM-008) brought the X=290 corners up and
  matched the best earlier spread.
- `INFERENCE`: the remaining X10 edge rise (about +0.3 mm) and the local dip
  around X220–255, Y185–220 (about −0.15 mm) are bend in the plate, not tilt.
  Further corner-screw work was judged to have diminishing returns.

### 2.3 Top-left leveling screw

- **`USER-OBSERVED`:** the top-left corner screw (owner-confirmed as X10 Y290)
  is tightened all the way and cannot be tightened further.
- **`CONFIRMED`** (BM-008, `default`): X10 Y290 is the highest corner (+0.286 /
  +0.349 mm).
- Per FS-154, tightening raises the bed. `INFERENCE`: this corner has no
  upward adjustment left and sits high. Loosening it would both lower it and
  restore adjustment range. It was not changed, because auto-leveling
  compensates.
- Owner-facing note, `EXPERIMENTAL`: if first layers at the back-left come out
  over-squished, loosen this screw slightly. Then rerun HMI Calibration with
  only Bed Level enabled.

## 3. Print-time mesh use

`CONFIRMED` (Loom configuration in LM-013; LM-013 17:23–17:26):
- The HMI Bed Level stage macro `_RUN_MESH_STAGE` runs `BED_MESH_CALIBRATE`
  without a profile name. It then runs `BED_MESH_TEMP P=1` and, at stage 0,
  `BED_MESH_PROFILE SAVE=default`.
- At print start, Loom logged `[BED_MESH_TEMP_LOAD] predicted mesh loaded:
  profile=default`. It then ran `FAST_BED_MESH`: five probe points within the
  print area, `max_abs_threshold=0.06`, `range_threshold=0.06`.
- Named profiles BM-006 to BM-008 came from `BED_MESH_CALIBRATE PROFILE=…`
  outside the HMI flow. The Mainsail Heightmap page shown by the owner lists
  them.

`INFERENCE`: prints use `default` plus its temperature model, not named test
profiles. After mechanical leveling, `default` must be regenerated through the
HMI Bed Level calibration.

## 4. HMI calibration, 20:50–21:54

### 4.1 Selection UI

- **`USER-OBSERVED`** (IMG_4038, HMI clock 20:50): the Calibration screen shows
  four orange-checked items: Vibration Compensation, Nozzle Offset, Bed Level,
  Nozzle Temperature.
- The owner first believed they could not be deselected, then confirmed they
  are toggles that look like static glyphs. So the FS-137/FS-154 instruction
  to "select only Nozzle offset" is achievable on this HMI.
- `OPEN QUESTION` (UX): no visual affordance distinguishes the toggles from
  icons.

### 4.2 Results, `CONFIRMED` (LM-013/LM-014)

| Local time | Step | Result | Prior value |
|---|---|---|---|
| 20:50:33 | Start (state `calibration`) | — | — |
| 20:56–21:00:25 | Input shaper | X zv 34.4 Hz, Y mzv 33.2 Hz; saved | X zv 34.6, Y mzv 32.8 (15:57) |
| 21:00:57–21:05:12 | Nozzle offset (`XYZ_ALIGN_NEW`) | x −32.823188, y −0.006438, z 2.621606; z surround compensation 0.0292 < 0.03, skipped | x −32.810844, y 0.012187, z 2.685436 (16:02) |
| 21:14:53 | Z homing probe check | −0.1008 mm (delta −0.0008) | — |
| 21:15–21:29:26 | Bed level stage 0 (≈55 °C) | 81 points; zero reference Z −0.025170 | — |
| 21:35–21:49:13 | Bed level stage 1 (≈100 °C) | 81 points; zero reference Z +0.106661 | — |
| 21:49:13 | Temperature model | samples 2/2 at 55.10 °C and 100.05 °C; `temp_comp.npz` saved; baseline committed to `default` | `default` from 16:41 |
| 21:49:27–21:53:41 | Left nozzle PID at 300 °C | Kp 25.451, Ki 1.749, Kd 92.574 | 22.476 / 1.314 / 96.084 |
| 21:53:49–21:54:53 | Right nozzle PID at 300 °C | Kp 27.566, Ki 8.751, Kd 21.708 | 28.399 / 8.606 / 23.429 |
| 21:54:59 | State `standby` | — | — |

Nozzle-offset changes against 16:02: x −0.012 mm, y −0.019 mm, **z −0.064 mm**.
No `!!` shutdown or calibration error appears in LM-013 after BM-008 or in
LM-014. The only error-shaped strings are macro definitions in config dumps.

Interpretation:
- `INFERENCE`: the Z offset shift is the only material change. It fits a
  hotend reseated differently, but the afternoon calibration (16:02) came after
  the reported unclogging, so the cause is `UNKNOWN`.
- `INFERENCE`: the left-nozzle Ki change (1.314 → 1.749) is within ordinary
  relay-autotune scatter. The right-nozzle autotune had one noisy first cycle,
  and its final values match the afternoon run.

## 5. Fibre extrusion calibration, 22:02–22:11

`CONFIRMED` (LM-014):
- 22:02:14: state `calibration`; left heater to 250 °C; `extruder2` activated
  at 22:03:33 and 22:08:58 (two extrusion segments).
- 22:11:53: `save_config: set [extruder2] rotation_distance = 37.485`;
  `SAVE_CONFIG`; state `standby`.
- `ALIGN_FIBRE_LENGTH` computes `new = current × L / 100`, and the same value
  37.485 was saved.

`INFERENCE`: the entered length was 100 mm, which is within the FS-154 target
of 100 ± 0.5 mm, so the distance was unchanged. This assumes the macro's
`current_u_rotation_dis` still held 37.485, since no Klipper restart appears
after 17:59.

`UNKNOWN`: the owner's measured segment lengths; whether the FS-154 two-repeat
check was performed.

## 6. Open items

- [ ] Plastic-plus-fibre test print spread across the bed. Check the first
  layer near X10/back-left and around the X220–255, Y185–220 dip, and check
  plastic/fibre XY alignment. Apply the FS-154 manual offset rule only if
  misaligned.
- [ ] Optional: loosen the top-left (X10 Y290) screw to restore range, then
  Bed Level only.
- [ ] Optional cleanup: delete the test profiles BM-006/BM-007.
- `OPEN QUESTION`: retaining-screw tightening order and torque. FS-154 says
  only "firmly tighten".
- `OPEN QUESTION`: Loom's leveling-screw pitch, so paper-feel corrections
  could be converted to turns.
