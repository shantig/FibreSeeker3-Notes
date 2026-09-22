# Loom P2 (right-plastic) load failure — diagnosis

Opened 2026-09-12. Status: **RESOLVED per owner report (2026-09-12) — a
factory clog in both hotends was cleared, and a 20 mm calibration cube printed
on the plastic side. Root cause is `USER-OBSERVED`, not independently
confirmed; see §0.8.** T4 was not run.

Evidence labels used here: `CONFIRMED` (directly shown by a cited preserved
artifact), `USER-OBSERVED` (owner report without a preserved primary artifact),
`INFERENCE`, `OPEN QUESTION`, `UNKNOWN`. All evidence is FibreSeek/Loom
evidence; no Anisoprint legacy evidence is used. Nothing here is manufacturer
guidance.

## Revision history

- **First pass (commit `faba403`)**: from the owner's first description and
  the June 16 trace only, inferred that the flow never passed the presence
  gate, so a silent motor was "expected". That inference is **superseded**:
  LM-012 shows the gate passing repeatedly and the extruder1 feed being
  commanded (§0). Sections 5–7 are preserved below as the first-pass record.
- **Second pass (commit `e946713`)**: adds owner results for R and T1 and the
  LM-012 klippy.log capture; revises the matrix and next test (T2).
- **Third pass (commit `9dba2a0`)**: adds T2 (`T2_RESULTS.md`), §0.6, and T3.
- **Fourth pass (commit `24428d9`)**: adds T3 (`T3_RESULTS.md`), §0.7, and T4.
  The §0.6 reading that "A-grip is weakened" is superseded: the T2 "does
  nothing" observation was most likely made at the rear sensor, not at the
  toolhead drive gear (§0.7).
- **Closure (this revision)**: owner reports a factory clog in both hotends,
  now cleared, and a successful plastic calibration print (§0.8). The §0.3
  judgement that a hotend blockage (E) was "less likely" did not hold up.

## 0. Current state (second and third passes, 2026-09-12)

### 0.1 Owner results (USER-OBSERVED, 2026-09-12)

- **R:** when the filament first touches the external P2 sensor, it clicks and
  a red/blue light on the sensor blinks, but nothing grabs the filament and
  feeds it into the tube.
- **T1, filament inserted:** `filament_sensor_3` and `filament_sensor_4` both
  reported filament detected.
- **T1, filament unloaded (none on the machine):** `filament_sensor_3`
  reported no filament detected; `filament_sensor_4` still reported filament
  detected.
- Not yet recorded: FibreTouch version screen, material, inserted depth, exact
  on-screen text, how the filament was unloaded (by the machine or by hand).

`INFERENCE`: both sensors belong to the same right-plastic path (LM-005:
`filament_sensor_3` is a switch, `filament_sensor_4` is an extruder1 motion
encoder), so "both detected" with one filament is expected. In Klipper's
motion-sensor design, "detected" means the extruder has not moved more than
`detection_length` since the last encoder pulse, so it reads "detected" at idle
with no filament; it is not a presence reading. FibreSeek's modified
`filament_motion_sensor.py` content is `UNKNOWN`, so this remains an inference.

**T1 reading:** `filament_sensor_3` toggles with the physical filament
(detected → not detected). Per the T1 table this rejects a dead or stuck
presence switch (D) and an obstruction before the sensor (A-upstream).

### 0.2 New log evidence (CONFIRMED, LM-012)

Source: LM-012
`sources/loom/sessions/2026-09-12T190345Z/moonraker-api/klippy-log/response-body.log`
(SHA-256 `8918fd92…4b530`). Timestamps are Loom local time (UTC−5). Line
numbers refer to that file.

**Firmware changed on 2026-09-11.** MCU builds report
`v2.2.20.515-65-g1b134e70` at 10:47 (L3724) and `v2.2.38.721-32-g02b98453`
from 11:11 onward (L11512, L20566). `load_unload.py` log line numbers moved
(for example `cmd_LOAD_FILAMENT 301` in June became `313`;
`_restore_idle_timeout 801` became `813`), and a new
`filament_motion_sensor.py encoder_event` log line appears (absent from LM-009).
`INFERENCE`: host and MCU software both differ from the June 16 trace; the
installed version is neither package held in this repository (2.2.30/2.2.42).

**Six P2 load attempts, all unsuccessful:**

| Start (local) | DETECTED → MELT_EXTRUDING cycles | Confirm prompts / retries | End |
|---|---|---|---|
| 2026-09-11 12:12:26 | 1 | 2 / 1 (112 + 50 mm) | cancelled 12:28:23 |
| 2026-09-11 13:11:18 | 8 | 0 / 0 | cancelled 13:13:36 |
| 2026-09-12 12:34:57 | 5 | 0 / 0 | cancelled 12:37:00 |
| 2026-09-12 12:39:17 | 5 | 0 / 0 | cancelled 12:41:31 |
| 2026-09-12 12:42:27 | 10 | 0 / 0 | cancelled 12:45:57 |
| 2026-09-12 13:57:31 | 1 | 3 / 2 (112 + 50 + 50 mm) | cancelled 14:00:49 |

- The presence gate passes: every attempt reaches `STATE:12 DETECTED` and
  `STATE:22 MELT_EXTRUDING` (e.g. L21038–L21039). `WAIT_INSERT` is now polled
  about every 0.1 s (June: about 1 s).
- In the short-cycle attempts, the flow drops from `MELT_EXTRUDING` back to
  `STATE:11 WAIT_INSERT` after 1–24 mm of progress (e.g. L21044–L21048,
  L23961–L24000). `INFERENCE`: the presence input went "absent" during the
  feed, consistent with filament that was touched against the switch but not
  held or pulled in.
- In two attempts the feed ran to completion (112 mm, then 50 mm retries;
  L25001–L25185 on Sep 12), and each confirm prompt was answered with retry
  (`CONTINUE_LOAD` = user confirms nothing came out, LM-010).
- The extruder1 TMC2240 answers over SPI: GSTAT reads and the
  "calculate extruder1 phase offset" step complete (L11663–L11718 on Sep 11,
  L21041–L21043 on Sep 12). No TMC error, SPI failure, shutdown, or stall line
  appears anywhere in LM-012.
- `tmc2240 extruder1` and the `extruder1` pin settings are identical between
  LM-005 and the last LM-012 configuration dump (only PID values differ).
- **Encoder evidence.** `filament_sensor_4` logs every encoder pulse with the
  extruder1 distance moved since the previous pulse. Commanded extruder1
  distance with **no pulse at all**: 110.6 mm (L15512), 50.0 mm (L15612),
  171.3 mm (L16108), 44.0 mm (L16189), 47.1 mm (L16364), 61.5 mm (L16567),
  43.0 mm (L23007), 22.4 mm (L23999), 14.7 mm (L24840), 122.4 mm (L25045).
  Conversely, bursts of pulses occur while the extruder1 position is
  unchanged (`Moved since last event: 0.000`; e.g. L15513–L15528 after a
  confirm prompt, L21063–L21075).
- `INFERENCE`: during commanded feed the filament mostly did not move past the
  encoder, while pulses with a stationary extruder indicate the filament being
  moved by hand. The encoder's position relative to the drive gear is
  `OPEN QUESTION`, but either placement means the feeder did not drive the
  filament.

### 0.3 What this rules in and out

- **Rejected:** "the flow never passes the gate" (first-pass premise); dead or
  stuck presence switch (T1 + log); software never commanding the feed (log).
- **Not the cause by timing (INFERENCE):** the Sep 11 firmware change. The
  June 16 trace on older firmware already ended with ≈303 mm commanded and no
  confirmed nozzle output.
- **Remaining:** the commanded extruder1 steps are not producing filament
  motion. Candidates:
  - **B** — motor or driver output: motor not turning (power stage, motor
    cable/connector, motor), consistent with "silent".
  - **A-grip** — motor turns but the drive gear/idler does not grip the
    filament (idler open or worn, filament not reaching the gear, wrong entry).
  - **C-mapping** — steps sent to a different physical motor than the right
    plastic feeder (wiring or connector swap). Config pins for extruder1 are
    unchanged between LM-005 and the LM-012 config dump.
  - **E** — hotend blockage stalling the gear. `INFERENCE`: less likely when the
    motor is silent and nothing grabs, because a blocked but driven gear
    usually clicks or grinds; it cannot be excluded until the motor is seen
    turning.

### 0.4 Revised diagnostic matrix

| Class | Observed | Historical | Inference | Unknown | Test needed |
|---|---|---|---|---|---|
| D sensor / gating | Switch toggles (T1); gate passes (LM-012) | Jun 16 gate passed | Rejected as primary cause | Encoder position | — |
| C sequencing | Feed commanded, 112/50 mm stages run (LM-012) | Same stages Jun 16 | Rejected as "never commands"; mapping swap still open | Physical motor wired to extruder1; STEP line | T3 (MSCNT, watch both feeders) |
| B motor / driver | T3: driver receives exact step counts both directions, no faults; USER-OBSERVED toolhead pulley moves as if feeding | No TMC errors ever logged | B-signal rejected; B-output rejected if the moving pulley is the right one | Which pulley moved | T4 step 1 |
| A path / grip | USER-OBSERVED nothing moves at the rear sensor (INFERENCE: no motor there); encoder silent during commanded feed | Jun 16 no output after ≈303 mm | **Leading candidate** (§0.7) | Where filament stops between rear sensor and toolhead; gear grip | **T4** steps 2–3 |
| E hotend / backpressure | Not observable yet | Jun 16 no output | Less likely with a silent motor | Nozzle condition | After T2 |
| F material | Material UNKNOWN | S=250 both periods | Unlikely to stop a gear from turning | Material | Record |
| G combination | Problem spans Jun 16 → Sep 12 across firmware | — | One long-standing mechanical/electrical fault fits | — | T2 |

### 0.5 Second-pass next test — T2 (completed; result in §0.6)

`STEPPER_BUZZ STEPPER=extruder1` (registered, LM-010: "Oscillate a given
stepper to help id it") with no filament in the P2 path and heaters off, while
watching **both** plastic feeders, followed by the read-only
`DUMP_TMC STEPPER=extruder1`. It bypasses the load state machine, needs no
heat, and moves only the feeder gear by small back-and-forth steps. Full
protocol in `OWNER_PROTOCOL.md`.

| T2 result | Supports | Rejects | Next |
|---|---|---|---|
| Right-plastic feeder gear visibly/audibly oscillates | A-grip (motor chain works) | B, C-mapping | Inspect feeder idler/gear engagement per first-party SOP |
| Nothing moves anywhere; silent | B (driver output, cable, connector, motor) | A as sole cause | Review `DUMP_TMC` flags; connector/motor check per SOP |
| A different feeder moves | C-mapping (wiring/connector swap) | B, A as sole cause | Stop; wiring check per SOP |
| Weak twitch or vibration without rotation | B (one coil open, low current) or mechanical bind | — | Review `DUMP_TMC` open-load/short flags |

### 0.6 T2 result and next test T3 (2026-09-12)

`USER-OBSERVED` (owner console transcript, preserved verbatim in
`T2_RESULTS.md`): `STEPPER_BUZZ STEPPER=extruder1` with no filament "does
nothing". `DUMP_TMC STEPPER=extruder1` before and after shows:

- SPI communication working; motor supply 24.08–24.10 V.
- `GSTAT = 0`; no short, overtemperature, or warning bits in `DRV_STATUS`.
- Driver enabled (`drv_enn` clear), holding at `ihold` in standstill.
- `IOIN dir` changed 0 → 1 across the buzz.
- `MSCNT` = 648 in both dumps.

Reading:

- `INFERENCE`: the host scheduled extruder1 motion and the DIR line reached
  the driver. Software never commanding the motor is rejected again, now below
  the load flow.
- `MSCNT` unchanged is **not discriminating**: the buzz is symmetric (+1 mm /
  −1 mm × 10), so a driver that received every step ends where it started.
- Open-load flags are only evaluated in motion and commanded-current fields do
  not show a connected motor, so the dumps cannot distinguish "no STEP pulses"
  from "driver output, cable, connector, or motor not turning the shaft".
- A motor that does not move with **no filament load** weakens A-grip as the
  sole explanation.

Remaining split:

| Candidate | What it means |
|---|---|
| B-signal / C | STEP pulses not reaching the extruder1 driver (MCU pin, board trace, pin mapping) |
| B-output | Driver receives steps but the output stage, motor cable/connector, or motor does not turn the shaft |
| C-mapping | A different physical motor is wired to extruder1 (not observed; not excluded) |

**Next test — T3 (step reception).** One-direction
`FORCE_MOVE STEPPER=extruder1 DISTANCE=1 VELOCITY=1` bracketed by `DUMP_TMC`,
then `DISTANCE=-1`, then the same on left plastic `extruder` as a control. A
1 mm move is 566 microsteps at `rotation_distance 5.65` (Klipper default 200
full steps, 16 microsteps), so a driver that receives the steps must show
`MSCNT` ≈ 488–504 or ≈ 792–808 instead of 648.

- `MSCNT` changes but the gear does not turn → **B-output** (driver output
  stage, motor cable/connector, motor).
- `MSCNT` stays 648 while the control moves → **B-signal / C** (STEP line or
  pin mapping).
- Gear turns → T2 motion was too small to notice; back to A-grip.

Full protocol and stop conditions in `OWNER_PROTOCOL.md`.

### 0.7 T3 result and next test T4 (2026-09-12)

`USER-OBSERVED` (owner console transcript, verbatim in `T3_RESULTS.md`).

**Step counts matched exactly.**
- extruder1 `MSCNT` 648 → 328 after two +1 mm moves → 488 after −1 mm.
- Predicted from 566 steps/mm × 16 counts: 328 and 488.
- Left-plastic control `extruder` 8 → 776 after +1 mm (predicted 776).
- DIR followed direction, and no driver fault flags appeared.

Owner observation: "the pulley on top of the extruder/toolhead" moves "as if
it's attempting to feed", while nothing moves or sounds at "the filament
runout sensor on the back" when loading.

**Reading:**

- **Rejected:** STEP pulses not reaching the extruder1 driver (B-signal).
- **B-output rejected, conditionally:** only if the moving pulley is the right
  one during the extruder1 moves. Not yet recorded, so it stays open until
  T4 step 1.
- **Physical layout (INFERENCE):**
  - The plastic drive gear sits on top of the toolhead.
  - The rear runout sensor module (switch plus red/blue light) has no drive
    motor of its own; plastic spools hang at the rear (FS-120).
  - The earlier "motor silent, nothing grabs" and T2 "does nothing"
    observations were then made at the rear sensor, where no motion is
    expected. That reconciles them with LM-012 and T3.
- **Leading class, A (INFERENCE):** filament inserted at the rear does not
  reach, or is not gripped by, the toolhead drive gear. Candidate causes:
  - an obstruction or disconnection in the tube between the rear sensor and
    the toolhead;
  - a leftover filament piece or debris at the extruder entry — plausibly
    related to the June 16 no-output episode, not established;
  - loss of idler grip.
  This fits the LM-012 encoder recording no filament motion during commanded
  feed.
- **E (hotend) returns as a later candidate:** it becomes relevant if filament
  is shown to reach and be gripped by the gear but still not extrude.

**Next test — T4 (cold):**
1. Watch the toolhead top during a 1 mm `extruder1` move to see which pulley
   turns.
2. Hand-push filament from the rear sensor and measure where it stops.
3. Only if it reaches the right pulley: a 3 mm move to check grip.

Full protocol in `OWNER_PROTOCOL.md`.

### 0.8 Resolution (USER-OBSERVED, 2026-09-12)

Owner report, verbatim excerpt: "Progress! I was able to get a 20mm
calibration printed using the plastic side … There was a clog from the factory
in both of the hotends".

**Photos** (owner-supplied; originals kept outside Git per source policy;
full SHA-256 and sizes in `../PHOTOS_2026-09-12.md`). Local time is UTC−5.

| File | Created (UTC) | Content | SHA-256 |
|---|---|---|---|
| IMG_4022.jpg | 22:50:33 | Caliper on cube, face label "T": 19.94 mm | `21b8408e…09f0827` |
| IMG_4023.jpg | 22:51:00 | Caliper, face "F": 19.91 mm | `2b63a990…117b077` |
| IMG_4024.jpg | 22:51:23 | Caliper, face label "B" (handwriting partly legible): 19.95 mm | `aa6bcc27…c3b4b01` |
| IMG_4025.jpg | 22:51:50 | Caliper, face label "B+"/"Bk" (legibility uncertain): 19.93 mm | `bea274da…202002a7a` |
| IMG_4026.jpg | 22:52:37 | Caliper, face "R": 19.96 mm | `b868d58c…d99c78` |
| IMG_4027.jpg | 22:53:37 | Caliper, face "L": 19.95 mm | `abf5175c…d2d1ad4a8` |
| IMG_4029–4034.heic | 23:19:41–23:22:29 | The same cube photographed face by face on the bed | see `../PHOTOS_2026-09-12.md` |
| IMG_4019.jpg | 23:33:33 | Cube on the bed | `a3bcf32a…6289c3b9d` |

**Reading:**
- Caliper readings span 19.91–19.96 mm. Which axis each reading spans is not
  recorded, and measurement technique and uncertainty are `UNKNOWN`.
- `UNKNOWN`: which plastic channel (P1 or P2) printed the cube; how the clogs
  were identified and cleared; whether a first-party SOP (FS-133/FS-144) was
  used; material (the HMI shows PETG on both plastic channels, IMG_4028).
- `INFERENCE`: a clogged hotend fits the preserved evidence:
  - feed commanded with no filament motion at the encoder (LM-012);
  - the June 16 no-output episode (LM-009);
  - the driver receiving all steps (T3).
  How a clog squares with the earlier "silent motor" reports is not
  established.
- The P2 issue is closed on the owner's report. Nothing here is manufacturer
  guidance.

## 1. Current failure — first owner report (USER-OBSERVED, 2026-09-12)

Reported by the owner in the Claude Code session of 2026-09-12, before LM-012
was captured.

| Item | Owner report |
|---|---|
| Channel | Right plastic, P2 (`extruder1`, HMI index `I=2`) |
| Feeder motor | Silent, no motion |
| FibreTouch load flow | Stuck at the insert/detect step (never gets past waiting for filament insertion) |

`UNKNOWN`: material, time of occurrence, exact HMI text, whether heating reached
target, how far filament was inserted, current FibreTouch/firmware version,
whether anything changed on Loom (update, service, filament path work) since
2026-09-09.

## 2. Historical software sequence (CONFIRMED, LM-009, 2026-06-16)

Source: LM-009 `sources/loom/sessions/2026-09-09T012636Z/moonraker-api/klippy-log/response-body.log`
(SHA-256 `c3e85f77…5329a`). Line numbers below refer to that file. This is
historical comparative evidence only; it does not describe today's failure.

| Log line | Time (2026-06-16) | Event |
|---|---|---|
| 14997 | 18:56:37.828 | `LOAD_FILAMENT` parameters `I=2, T=1, S=250, L=0`; extruder lookup `extruder1` |
| 15008 | 18:56:37.837 | `[P2 LOAD] STATE:9 PREPARING` (homing check, `T1`, `MOVE_TO_BRUSH_STATION`, `MOVE_RIGHT_PRELOAD_POSITION`, `PREPARE_LOAD_UNLOAD_NOZZLE`) |
| 15058 | 18:57:30.342 | `STATE:10 PREHEATING T:250`; `_temp_timer_handler` polls about once per second |
| 15184 | 18:57:55.370 | `STATE:11 WAIT_INSERT` (heater reported within range at the same second) |
| 15186–15187 | 18:57:56.378–.383 | second `WAIT_INSERT` poll, then `STATE:12 DETECTED` |
| 15188 | 18:57:56.385 | `STATE:22 MELT_EXTRUDING` |
| 15190–15192 | 18:57:56.691–.705 | **first** `extruder1` TMC GSTAT read and "Pausing toolhead to calculate extruder1 phase offset" — the extruder1 motor is enabled only now |
| 15370–15373 | 18:58:41 | `PROGRESS 112/112mm`, `STATE:30 CONFIRM_EXTRUSION`, `ACTION:PROMPT_CONFIRM P2_EXTRUDED` |
| 15374–15623 | 18:59:51–19:02:58 | four `STATE:31 RETRYING` cycles (3 × 50 mm complete, 4th stopped at 41/50 mm) |
| 15699 | 19:03:14.943 | `STATE:91 CANCELLED` |
| 15724–15757 | 19:03:25–19:04:11 | `P2 UNLOAD`: preheat 250, `UNLOADING`, `PROGRESS 500mm`, `SENSOR_DETECTED: Filament removed`, `STATE:90 FINISHED` |
| 15772–15851 | 19:05:33–19:05:48 | new P2 load reaches `STATE:10 PREHEATING`, then `STATE:91 CANCELLED` |

Supporting facts:

- `CONFIRMED` (LM-010 `printer/gcode/help`): `CONTINUE_LOAD` is described as
  "继续补料（用户确认未出料）" — continue feeding, user confirms no filament came
  out. `STATE:31 RETRYING` after each confirm prompt is consistent with that
  command. So the June 16 episode was itself an unsuccessful load: about
  112 + 50 + 50 + 50 + 41 = 303 mm commanded with no confirmed nozzle output,
  then cancel and a successful 500 mm unload.
- `CONFIRMED` (LM-009): no TMC error, SPI failure, MCU shutdown, or stall line
  appears anywhere in the preserved log window. The only `Must home axis first`
  warning is on 2026-09-09 (line 19291) and is unrelated to loading.
- `INFERENCE`: every stepper (`stepper_x/y/z`, `extruder1`) reports
  `GSTAT 0000001d reset=1 uv_cp=1` once on its first enable and `00000000`
  immediately after. This pattern is the usual power-on driver flag, not
  evidence of an undervoltage fault.
- `INFERENCE`: `PROGRESS` lines follow commanded, not measured, motion. 112 mm
  took 44.7 s (≈2.5 mm/s) although labelled `0.6mm/s`; 50 mm retries took
  ≈19.8 s (2.5 mm/s); unload advanced 400 mm in 24.1 s (≈16.6 mm/s), matching
  `variable_p2_unload_speed = 1000` (mm/min). Therefore these logs cannot show
  whether filament actually moved.
- `INFERENCE`: the June 16 `WAIT_INSERT`→`DETECTED` transition took one poll
  (≈1 s), so filament was either already present at the gate or inserted
  immediately. This does not establish whether the gate is level- or
  edge-triggered.

## 3. Configuration relevant to P2 (CONFIRMED, LM-005, 2026-09-08)

- Role mapping (from prior phases): `extruder2` left fiber, `extruder` left
  plastic, `extruder1` right plastic.
- `extruder1`: `rotation_distance 5.65`, `microsteps 16`, nozzle 0.4 mm,
  `max_extrude_only_distance 1000`, heater `toolhead:PB0`, sensor `Generic 3950`.
- `tmc2240 extruder1`: `run_current 0.7`, `hold_current 0.2`, `rref 12000`.
- `filament_switch_sensor filament_sensor_3`: `switch_pin ^PF2`; its runout
  G-code names "extruder1 plastic filament ran out".
- `filament_motion_sensor filament_sensor_4`: `switch_pin ^PF1`,
  `extruder: extruder1`, `detection_length 12` (set to 7.000 mm at runtime,
  LM-009 lines 14981, 19288).
- `extruder_stall_detector extruder` is bound to `extruder` (left plastic) only,
  with `enable_stallguard = False`. It has no configured role on P2.
- `_LOAD_UNLOAD_VARIABLES`: `load_unload_temperature 200` default,
  `p2_long_distance 300`, `p2_step_length 5`, `retry_distance 50`,
  `p2_unload_speed 1000`, `right_nozzle_temperature_offset 100`.
- Custom module `load_unload.py` implements `LOAD_FILAMENT`, `UNLOAD_FILAMENT`,
  `CONTINUE_LOAD`, `EXIT_LOADUNLOAD`, `FINISH_LOADUNLOAD`,
  `PREPARE_LOAD_UNLOAD_NOZZLE` (LM-010). Its source is inside the
  ZipCrypto-encrypted `klipper.zip` and remains `UNKNOWN`.

`OPEN QUESTION`: which sensor gates `WAIT_INSERT` → `DETECTED` for P2.
`INFERENCE`: the switch sensor `filament_sensor_3` is the presence candidate;
a motion sensor cannot report presence before any extruder movement.

`OPEN QUESTION`: whether the gate uses the sensor level or requires an
absent→present transition, and whether a disabled runout sensor
(`SET_FILAMENT_SENSOR ENABLE=0` via the `SWITCH_FILAMENT_SENSOR` macro; the
FibreTouch symbol `onRequestSyncFilamentRunoutPauseSensors` suggests an HMI
setting, `INFERENCE`) is treated as "not detected".

`OPEN QUESTION`: the physical position of `filament_sensor_3` and
`filament_sensor_4` along the right-plastic path.

## 4. Firmware version context

- `CONFIRMED` (prior phases): Loom's FibreTouch version was `2.2.30.613` on
  2026-09-08/09. Its current version is `UNKNOWN`.
- `CONFIRMED` (FS-150/FS-151 inner-ZIP central directories, member size/CRC):
  between 2.2.30.613 and 2.2.42.831 the members `klippy/extras/load_unload.py`
  (109,069 → 111,097 B), `klippy/extras/filament_switch_sensor.py`
  (7,617 → 8,289 B), `klippy/extras/filament_motion_sensor.py`
  (4,838 → 7,374 B), `klippy/kinematics/extruder.py` (15,926 → 18,723 B), and
  `filament_switch_sensor_v2.0.cfg` in `anisotouch-config.zip`
  (6,725 → 8,096 B) changed. `klippy/extras/tmc.py`, `tmc2240.py`,
  `extruder_stall_detector.py`, and `force_move.py` have identical size and
  CRC. Content of every one of these files is `UNKNOWN` (encrypted). See the
  correction section in `docs/firmware/VERSION_DIFF_2.2.30_TO_2.2.42.md`.
- `INFERENCE`: if Loom has been updated since 2026-09-09, the load/sensor code
  path is different code from the one that produced the June 16 trace. The
  Python line numbers embedded in `load_unload.py` log lines (for example
  `cmd_LOAD_FILAMENT 301`, `_prepare_load 1861`) are a practical fingerprint:
  identical numbers in a new log support an unchanged file; different numbers
  support a changed file.

## 5. Key inference (first pass — SUPERSEDED by §0)

> Superseded 2026-09-12: LM-012 shows the gate passing and the feed being
> commanded, so the premise below does not describe the current failure.

In the preserved sequence the `extruder1` motor is not enabled until after
`STATE:12 DETECTED`. A silent feeder motor while the flow waits at the insert
step is therefore the **expected** behavior of that sequence (`INFERENCE`,
assuming the current firmware follows the same order). The reported symptom does
not by itself implicate the motor, driver, hotend, or material. The failure is
located at the **presence gate**: the controller does not accept that filament
has been inserted.

## 6. Diagnostic matrix (first pass — SUPERSEDED by §0.4)

| Class | Observed (2026-09-12) | Historical | Inference | Unknown | Test needed |
|---|---|---|---|---|---|
| **D** sensor / state gating | USER-OBSERVED: stuck at insert/detect | Jun 16 gate passed in ≈1 s; sensor reported removal on unload | Leading candidate | Gating sensor identity; level vs edge; current sensor readings | **T1** cold sensor-truth test |
| **A** filament path / mechanical | Not reported | Jun 16 load gave no confirmed nozzle output after ≈303 mm | Filament may not physically reach the sensor (stub, debris, PTFE/path obstruction), or a stub may hold the sensor "present" | Sensor location; insertion depth reached | T1 insertion-depth measurement |
| **C** macro / firmware sequencing | USER-OBSERVED: stuck state | Full state trace under 2.2.30 | Plausible only if the sensor reads correctly; firmware may have changed since Sep 9 | Current version; gate logic (source encrypted) | R log (state, line-number fingerprint); T1 "sensor OK" branch |
| **B** feeder motor / driver / torque | USER-OBSERVED: silent motor | No TMC errors; motor first enabled after DETECTED | Not supported by this symptom: silence is expected at WAIT_INSERT | Motor behavior once commanded | Deferred until the gate passes |
| **E** hotend / nozzle / backpressure | Not reached | Jun 16 no-output episode is a separate, unresolved E/A candidate | Cannot hold the flow at WAIT_INSERT | Nozzle condition | Deferred |
| **F** material-specific | Material UNKNOWN | Jun 16 used S=250 | Relevant only if the filament cannot actuate the sensor | Material, diameter, stiffness | Record material during R |
| **G** combination | — | Jun 16 no-output and today's gate stall could share one path obstruction | Possible (A + D) | — | T1 separates A from D |

## 7. First-pass next test (T1 — completed; result in §0.1)

**T1 — cold sensor-truth test** (full owner protocol in `OWNER_PROTOCOL.md`):
query `filament_sensor_3` and `filament_sensor_4` with no load flow active,
heaters off and no motion, with the filament removed, inserted to its normal
stop, and removed again, while measuring insertion depth. It separates:

- a correctly toggling sensor → C (state machine) — rejects D and A;
- a sensor stuck "present" → stuck lever / stub / debris (A/D);
- a sensor stuck "absent" with filament at normal depth → D;
- a sensor stuck "absent" with filament stopping early → A;
- the other sensor toggling instead → the sensor-mapping inference is wrong.

It needs no heat, no extrusion, and no configuration change, and its console
responses are also written to klippy.log (FibreSeek's `gcode.py` logs
`respond_info` lines, LM-009), so one later authorized GET preserves them.

## 8. Remaining uncertainty

- `OPEN QUESTION`: which toolhead pulley turns for `extruder1` (T4 step 1).
- `OPEN QUESTION`: where filament inserted at the rear runout sensor stops, and
  whether the toolhead drive gear grips it (T4 steps 2–3).
- `OPEN QUESTION`: physical layout of the right-plastic path (rear sensor
  module, encoder position, tube run, drive gear); layout above is INFERENCE.
- `OPEN QUESTION`: FibreSeek's documented plastic loading procedure (whether
  the user must push filament from the rear to the drive gear before or during
  `LOAD_FILAMENT`). FS-120 is referenced in the ledger but its loading steps
  are not extracted in this repository.
- `OPEN QUESTION`: hotend condition (E), relevant only if the gear grips but
  nothing extrudes.
- `UNKNOWN`: installed host/FibreTouch version (MCU build
  `v2.2.38.721-32-g02b98453` is CONFIRMED).
- `OPEN QUESTION`: whether P2 has loaded successfully at any time since the
  June 16 no-output episode.
- `UNKNOWN`: material and FibreTouch version screen.
