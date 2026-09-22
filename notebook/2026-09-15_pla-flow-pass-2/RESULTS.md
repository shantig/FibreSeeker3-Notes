# Loom PLA+ 2.0 flow-rate calibration, pass 2 — 2026-09-15 (right nozzle)

Physical sample **X0007** (formerly SMP-0007) (`experiments/Samples/samples.jsonl`). Printed
before the ID tag existed: label the bag or pieces by hand.

**Result: recommend `filament_flow_ratio` 0.96 (0.95 equally smooth, but next
to the under-extrusion step at 0.94).** Revised after controlled re-photography;
supersedes the first reading of 0.93 below.

`EXPERIMENTAL`. Follows pass 1 (`../2026-09-15-T2/RESULTS.md`), which put the
best patch at −5 (flow 0.95), with over-extrusion visible at +5 and bead relief
at 0, and line gaps from −10. Pass 2 resolves that bracket in 1 % steps.
Owner request: "run pass 2".

## Why the sweep is 0.91–1.00, not Orca's default

Orca's pass 2 takes the pass-1 result as its new base and sweeps modifiers
0 … −9 below it; with a 0.95 base that is 0.86–0.95, which would miss the
0.96–0.99 half of the bracket. This build keeps the base at the current
`filament_flow_ratio` **1.00** and applies Orca's own pass-2 modifiers, so the
ten patches cover **0.91–1.00**, spanning the whole bracket from pass 1.

## Method

Same generator as pass 1, now with an output-name option:

```
python3 notebook/2026-09-15_pla-flow-pass-1/make_flow_patches.py \
  --calib /Applications/OrcaSlicer.app/Contents/Resources/calib/filament_flow/flowrate-test-pass2.3mf \
  --reference notebook/2026-09-14_pla-temperature-tower/loom_T1.3mf \
  --out notebook/2026-09-15_pla-flow-pass-2 --name loom_flow_pass2
```

Orca's bundled pass-2 model (ten patches `flowrate_0`, `flowrate_m1` …
`flowrate_m9`), the Loom project settings with 205/210 °C, Orca's per-patch
calibration overrides, no brim, layout recentred on (150, 150), 10 layers.
Built-in G-code check: every patch's top-surface extrusion matched its
intended ratio within **0.07 %**.

| Patch | `print_flow_ratio` |
| --- | --- |
| 0 | 1.00 |
| −1 | 0.99 |
| −2 | 0.98 |
| −3 | 0.97 |
| −4 | 0.96 |
| −5 | 0.95 |
| −6 | 0.94 |
| −7 | 0.93 |
| −8 | 0.92 |
| −9 | 0.91 |

File: `loom_flow_pass2.gcode`, 698,093 bytes, sha256
`8d4e01f834ee7935cccc62f8895f9ebb08e58541f2d602079c5b856f893e25ec`; 10 layers,
15.45 g, estimated 33 m 45 s. Patches span X 88.2–211.8, Y 87.2–212.8.

## Machine setup

- Plate checked by camera before start: pass-1 patches removed; only a faint
  gloss outline of their footprint visible on the PEI.
- Commands sent by a script that stops at the first non-`ok` response (after
  the pass-1 pop-up incident): upload → `SAVE_VARIABLE`
  `printing_info_auto_leveling = 1`, `printing_info_mode_*` = 80/80/220/220 →
  state check `standby` → `SET_PRINT_STATS_INFO STATE=precheck` →
  12:16:11 `SDCARD_PRINT_FILE FILENAME=loom_flow_pass2.gcode`.

## Timeline and machine state

| Time (local) | Event |
| --- | --- |
| 12:16:11 | `SDCARD_PRINT_FILE` (preprint: bed heat, nozzle cool-down, adaptive mesh) |
| 12:25:03 | mesh range check `min=-0.1547 max=0.3491 range=0.5038 (limit=1.0000)` |
| 12:26:13 | `printing` |
| 13:03:10 | `complete`, 10/10 layers; heaters off |

Nozzle 205–207 °C through the print. No `!!` errors in the G-code store after
12:15. Moonraker `print_stats`: `total_duration` 2,201 s, `filament_used`
5,302 mm. After completion `printing_info_mode_*` was restored to 10/10/290/290
and `printing_info_auto_leveling` to 0 by the stop-on-first-error script (all
five `ok`, verified in `variables.cfg`). No `SAVE_CONFIG`.

## Results

### Final reading (controlled photos) — recommend 0.96

The owner re-photographed the patches with a fixed camera, locked exposure, a
single light and all compared patches in one frame. Texture was measured on the
top surface of each patch: standard deviation of (greyscale − Gaussian blur),
the fine line-to-groove relief, normalised by focus sharpness of the mat grid
(single-patch set) or by patch brightness (group shots). `USER-OBSERVED`
photos, measurement by Claude.

| Patch (flow) | 0 (1.00) | −1 | −2 | −3 | −4 (0.96) | −5 (0.95) | −6 (0.94) | −7 | −8 | −9 (0.91) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Single patch, fixed camera (`IMG_4304`…`4394`) | 0.68 | 0.68 | 0.55 | 0.52 | **0.42** | **0.36** | 0.91 | 0.98 | 1.03 | 1.08 |
| Group, neutral light (`IMG_4399`) | 1.30 | 1.03 | 1.12 | 0.89 | **0.83** | 1.04 | 1.77 | 1.39 | 2.94 | 1.61 |
| Group, rotated light (`IMG_4410`) | 2.15 | 2.70 | 1.42 | 1.61 | **1.19** | **1.27** | 2.44 | 1.60 | 2.94 | 1.98 |

- **Every controlled set has its minimum at −4/−5.** Relief rises gradually
  toward 0/−1 (over-extrusion: raised beads, the edge ridge) and **steps up
  abruptly at −6**: below 0.95 the top lines stop merging and grooves open
  between rounded beads — the onset of under-extrusion, without holes yet.
- **The −6 step is not lighting.** In the single-patch set it fell between two
  frames 24 s apart; the group shots put −5 and −6 side by side under identical
  light, and −6 measured higher in all three colour temperatures
  (`IMG_4398`/`4399`/`4400`: 1.55/1.77/1.52 vs 1.04/1.04/1.01) and with the
  light rotated (`IMG_4410`: 2.44 vs 1.27). Crops:
  `analysis_controlled_single_m9_m7_m6_m5_m4_0.jpg` (−9, −7, −6, −5, −4, 0 at
  1:1; raw above, contrast-normalised below) and
  `analysis_group_rotated_m5_vs_m6.jpg` (−5 left, −6 right; `IMG_4410` above,
  `IMG_4411` below).
- `IMG_4411` (flatter light, strong top-to-bottom brightness gradient) is the
  least discriminating shot; its minimum is −2…−5, consistent with the others.
- The group shots resolve each top line with only ~6–12 px, so they separate
  the under side clearly but the over side weakly; the single-patch set carries
  the 0/−1 vs −4/−5 comparison.

**Recommendation: `filament_flow_ratio` 0.96.** −4 (0.96) and −5 (0.95) are the
flattest in every set. The under-extrusion side has a cliff at −6 while the
over side rises gently, so the patch one step further from the cliff is the
safer setting.

**Why the touch picks disagree.** The owner's sister picked −6/−7 and the owner
−8/−9 — exactly the patches whose lines stay separate and rounded. `INFERENCE`:
rounded, unmerged beads with shallow grooves can feel smoother under a fingertip
than a flat top with slight bead crowns, so touch does not detect the onset of
under-extrusion here. A blind, tab-covered ranking was suggested but not done.

**Applied (2026-09-15, owner request).** Claude added
`"filament_flow_ratio": ["0.96"]` to the owner's OrcaSlicer user preset
`~/Library/Application Support/OrcaSlicer/user/<user-id>/filament/SUNLU PLA+ 2.0
@System - Loom T1.json` with Orca closed, and bumped `updated_time` in the
matching `.info` file. Nothing else in the preset changed; the value previously
came from the inherited `SUNLU PLA+ 2.0 @base` (1.0), which confirms 1.0 was the
calibration baseline. Check: a CLI slice of `../2026-09-14-T1/loom_T1.3mf` with
a copy of the edited preset (plus the `type` key the CLI requires) wrote
`filament_flow_ratio = 0.96`, `nozzle_temperature = 205`,
`nozzle_temperature_initial_layer = 210`. To revert, delete that key.

**Superseded readings:** 0.93 (first reading below, which leaned on the touch
picks because the handheld photos could not rank 1 % steps) and pass 1's 0.95
(photo-only, 5 % steps).

### First reading (handheld photos) — superseded

**Recommendation at the time: `filament_flow_ratio` 0.93** (patch −7), window
0.92–0.94.

### Owner and helper touch test — `USER-OBSERVED`

- Owner's sister: **−6 / −7** feel smoothest.
- Owner: leaning **−8 / −9**.

Both picks fall in −6 … −9 (0.94–0.91); neither picked 0 … −5.

### Photos — `USER-OBSERVED`, read by Claude

26 owner photos on NAS `originals/incoming/20260915/` (13:18–14:02). Patch
identity for the oblique shots was read from the embossed tab of each (−1 and −7
separated on enlarged crops). Derived comparison sheets in this folder:
`analysis_raking_0_to_m9.jpg` (oblique raking shots, ordered 0 … −4 top row,
−5 … −9 bottom row) and `analysis_topdown_0_to_m9_contrast.jpg` (top-down
shots, same order, greyscale with local contrast equalisation).

- **0 and −1 are over.** Each top line stands as a raised bead, and 0 has a row
  of small nubs where the top lines meet the wall (the same edge ridge pass 1
  showed at 0).
- **No patch shows under-extrusion gaps**, down to −9; the grooves between lines
  are even and closed. Pass 1's −10 (0.90) was the first patch with visible
  gaps, so the gap threshold sits just below 0.91.
- **The photos cannot rank adjacent 1 % steps.** The oblique shots are handheld
  with varying angle and focus, and exposure changes between the −5 and −6
  top-down shots (−6 … −9 read crisper, but that coincides with the lighting
  change). Treat any photo ordering inside −4 … −9 as not established.

### Reading

Over at 0/−1 (photos), first gaps at 0.90 (pass 1), and both touch picks in
−6 … −9. The consensus window is **0.92–0.94**; its centre, **0.93**, is the
recommendation. It sits 3 % above the first under-extruded patch. Pass 1's
photo-only pick of −5 is superseded: its bracket was coarse, and 0.95 is the
edge of what both testers passed over.

### Photo index

| File | Content | SHA-256 |
| --- | --- | --- |
| `IMG_4156.heic` | all ten patches / group, top-down | `f8b6febc87653b1629ba3718125613d594ea408d10f859fc078e47d99ff1eb1a` |
| `IMG_4162.heic` | all ten patches / group, top-down | `bfa0515b99c79208603f0592caae2dc3453ca96489647a86d4ce58c9cb715317` |
| `IMG_4163.heic` | all ten patches / group, top-down | `d9f6fe20910841fa2cd59dcb2f92cecd9734f1cc513f147fd87b6b0ef5de7e57` |
| `IMG_4164.heic` | all ten patches / group, top-down | `ed297fbfcf9d02779792122b5f82f34af5f1a7f95adb80f20342bea55b323426` |
| `IMG_4166.heic` | all ten patches / group, top-down | `58f0e6f68c4b0385d5c10e77c2fc962dd4bfd54cb0865c0bafa2a11feff8dea5` |
| `IMG_4167.heic` | all ten patches / group, top-down | `04412b168814536479324c4d9915ca5f391595bafe6f9de81d1ee08f8a60d1b5` |
| `IMG_4171.jpg` | patch 0, top-down diffuse light on cutting mat | `d8ab79381ea5598977e57ab6c2d07ec2035fed40cf98313caeca8d4b19c06f3a` |
| `IMG_4183.jpg` | patch -1, top-down diffuse light on cutting mat | `1beb674a6b3bf533bdd5ab1a12260e60572e700e07174f4809cdb2db8d265ec0` |
| `IMG_4193.jpg` | patch -2, top-down diffuse light on cutting mat | `db4981e4c9a86f656c46ce92ccbe45687d2a45c1ea1df5aeed137075d2f2dd91` |
| `IMG_4205.jpg` | patch -3, top-down diffuse light on cutting mat | `91ea03b009962f6f5e4bc2256dfa38e66d26de76d8a5b24b3e819c202c49067a` |
| `IMG_4214.jpg` | patch -4, top-down diffuse light on cutting mat | `234a37e791731c22d530e4bc56705837f92f18e6db7c779f7235bb6fc1a66655` |
| `IMG_4224.jpg` | patch -5, top-down diffuse light on cutting mat | `4511f34ac088ac39aa55a02a8fb5bac3068adf6e543c8310e1e5b57d6d817955` |
| `IMG_4230.jpg` | patch -6, top-down diffuse light on cutting mat | `62df7aca45f855b9c942428563ab77b383d9999ac285aae27ccb887daf227c88` |
| `IMG_4243.jpg` | patch -7, top-down diffuse light on cutting mat | `470cb59bba560d8a64b47ce4a99852ff56273275bd5f32db58b4a4b97a45da3f` |
| `IMG_4251.jpg` | patch -8, top-down diffuse light on cutting mat | `c36cf089f9a718ff96325f5a58f8494e91fa8b628efdf719038c0a02b8d963eb` |
| `IMG_4264.jpg` | patch -9, top-down diffuse light on cutting mat | `f0f249d2ef00b66b737051fa4dec470686681aa98f0ec29829eae6e41880b6cb` |
| `IMG_4268.heic` | patch -7, low oblique raking light | `3edf2a2cbe9b229ea66861d87d06cfc75e4bba2b5720772fb57bed6f0ea7c750` |
| `IMG_4269.heic` | patch -9, low oblique raking light | `318e0eef33170b63d735bfdcf3bcab444edd84512d34029189fce1510a34a5b8` |
| `IMG_4270.heic` | patch -6, low oblique raking light | `b8517dcfc92a70bafc8e1d705f3f0ca204364097247a1a1276239368039ab84c` |
| `IMG_4271.heic` | patch -8, low oblique raking light | `09779b0faaaa7bc23698c31a48e39ee5bd75129eba0c9efe9e90b5ea8eb4cddc` |
| `IMG_4272.heic` | patch -4, low oblique raking light | `bbf15f8f480ac5cdd3c0d6fff20a89586e5a97318fd7686e59abcce69dc01e3c` |
| `IMG_4273.heic` | patch -3, low oblique raking light | `4a254dfdce18715d4307270c3440c28b9ef6f717fa4d75c45a244ee9e5497fe7` |
| `IMG_4274.heic` | patch -5, low oblique raking light | `b93d4db3c9da9eac3374be43c9f46244e1adfbb35e512d05968636091feb2df6` |
| `IMG_4275.heic` | patch -1, low oblique raking light | `2d6a3e41fd144ecb6297d180f427d3543137f52392bddafde4af06dbde20a12c` |
| `IMG_4276.heic` | patch -2, low oblique raking light | `552ab61e945e5884be094d1776dc857f56011ee38f92186105d4d8869de978dc` |
| `IMG_4277.heic` | patch 0, low oblique raking light | `4394c4f4be11d688fa09daee5cc17f4f7e6a49f90f03ef1473bac200728df535` |

Controlled re-photography (same folder):

| File | Content | SHA-256 |
| --- | --- | --- |
| `IMG_4295.jpg` | patch −9, single patch, fixed camera (first framing) | `0fa60d196e050e6a63de2a642f17a5bc3c2b43ed095434761233d8c7c549d5d5` |
| `IMG_4304.jpg` | patch −9, single patch, fixed camera | `291ad3b62ebcedf4828b3b9ceafb43a30d58b02c9951c85b59f4ddd80b37709c` |
| `IMG_4314.jpg` | patch −8, single patch, fixed camera | `855d07058bb6f09e769740559c66db803668d6ae46f3fc570b567852f093e880` |
| `IMG_4324.jpg` | patch −7, single patch, fixed camera | `9e91cbe94d74c76f46d152cf039494bf9ab129820703ad6ba8b8769043fd1e10` |
| `IMG_4335.jpg` | patch −6, single patch, fixed camera | `4393dd81599623920c5ddf106bdc9e059391aebc38329de5a7d28dd7f4d393a4` |
| `IMG_4341.jpg` | patch −5, single patch, fixed camera | `750909ea729631a9b473f35b069806b7f6129a18ad73f84aebfecaea4d3661d9` |
| `IMG_4355.jpg` | patch −4, single patch, fixed camera | `571fc223ec73291d70feea01659315cd116e20dae68ba87b1445478aa613c26c` |
| `IMG_4363.jpg` | patch −3, single patch, fixed camera | `57b9c809f8eaa09bbaff614ee5aab9b21228e06a0f03312b189a495447018221` |
| `IMG_4372.jpg` | patch −2, single patch, fixed camera | `b88d47d132279ce17eb1437ea5fc99c90212929685c5ca3c6e33baddbbd7a6d3` |
| `IMG_4380.jpg` | patch −1, single patch, fixed camera | `d4bc8816ba848d58814250b975c9bc1557a69b3f24a03f4c9bf1462c1f9531df` |
| `IMG_4394.jpg` | patch 0, single patch, fixed camera | `1e798a3b213088329613d40efe289010dc92fa6d29028885558857f0145ea3ba` |
| `IMG_4398.heic` | all ten, one frame, warm white balance | `d900ad520e9b1655b57d0db96f616e41cfadffaa67a1b56c07db94d82dde57fb` |
| `IMG_4399.heic` | all ten, one frame, neutral white balance | `9dc6f86c59d86490c35456fcafd01c37185c255a29680b86d91496bd359b54e3` |
| `IMG_4400.heic` | all ten, one frame, cool white balance | `2805545eeed7232d1834847ef0191162dfe258b9f8710476c3a1f3866a8d9bb0` |
| `IMG_4410.heic` | all ten, one frame, patches rotated 90° (light rotated relative to lines) | `950c00d21b4328331d711f104524457e01472e220acd7db6c99684330ac8c4d5` |
| `IMG_4411.heic` | as `IMG_4410`, flatter light | `ba2f5f401cbb30d0bad32056db83dd174b1c09c51c8c40ed7650dbd446d35de3` |

Single-patch set: 1/60 s, ISO 250, same lens and framing in every frame (EXIF).
Group shots: 1/97 s ISO 250 (`4398`–`4400`), 1/121 s ISO 80 (`4410`–`4411`).
Patch identity read from the embossed tabs. Originals stay where the owner saved
them.
