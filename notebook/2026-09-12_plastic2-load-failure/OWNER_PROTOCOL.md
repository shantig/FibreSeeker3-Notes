# Owner protocol — Loom P2 (right-plastic) load failure

`EXPERIMENTAL` owner-performed diagnostic. Not manufacturer guidance. Prepared
2026-09-12 from `DIAGNOSIS.md`. Shant performs every physical step; Claude does
not operate Loom.

Sequence: **R** reproduce once (done), **T1** cold sensor-truth test (done),
**T2** motor-truth test (done; `T2_RESULTS.md`), **T3** step-reception test
(done; `T3_RESULTS.md`), **T4** attribution, path-reach, and grip test (not run — issue resolved by
the owner clearing a factory hotend clog; see `DIAGNOSIS.md` §0.8). Results so far are recorded at the end of this
file and interpreted in `DIAGNOSIS.md` §0.

## General stop conditions (apply throughout)

Stop, leave the machine in a safe idle state, and record what happened if:

- any error, pause, MCU/Klipper shutdown, or unexpected motion occurs;
- filament needs force to go further, bends, or buckles;
- there is a burning smell, smoke, or an unexpected temperature reading;
- a step would require disassembly, cutting, a configuration change, a
  firmware update, or a service procedure — those need the first-party SOP
  (e.g. FS-133/FS-144 plastic unclogging) and a separate decision.

Do not cold-pull, do not push filament while the nozzle is hot beyond normal
hand insertion, and do not power-cycle unless needed for safety (record it if
you do).

## R — reproduce once

**Starting state:** Loom idle, no print or load/unload flow active, doors
closed as normal. Note the FibreTouch version (About/settings screen).

**Before starting:** mark the right-plastic filament with a pen or tape exactly
where it enters the path (the first tube/fitting it goes into) so inserted
length can be measured.

**Action:**
1. Note the wall-clock time.
2. Start the normal P2 (right plastic) load in FibreTouch.
3. When the flow asks for filament, insert it the usual way, gently, to its
   normal stop. Wait up to 2 minutes at that screen.
4. Cancel/exit through FibreTouch. Note the time.
5. Pull the filament back out and measure mark-to-entry distance = inserted
   depth.

**Expected observations if the report reproduces:** heating reaches target;
the insert/detect screen never advances; the feeder motor stays silent.

**Record:**
- start/cancel times; FibreTouch version;
- material, brand, diameter if known;
- exact on-screen text (photo/screenshot of the insert screen);
- whether the target temperature was reached;
- inserted depth in mm and where it seemed to stop (felt a hard stop? reached
  the toolhead?);
- whether the filament tip came out clean, deformed, or cut.

**What it tests:** establishes the current failure precisely and puts a
fresh trace in klippy.log (state number, parameters, code-line fingerprint).

## T1 — cold sensor-truth test (single most discriminating test)

**Starting state:** R finished and cancelled; no load/unload flow active;
heaters off (no need to wait for full cool-down, but do not heat). No motion
commands in this test.

**Needs:** a G-code console on Loom (for example Mainsail/Fluidd console if
available). If no console is available, **stop and tell Claude** — do not look
for a workaround.

**Action:** in each of three physical states, send exactly these two read-only
commands and copy the full responses:

```
QUERY_FILAMENT_SENSOR SENSOR=filament_sensor_3
QUERY_FILAMENT_SENSOR SENSOR=filament_sensor_4
```

| State | Physical condition | sensor_3 response | sensor_4 response |
|---|---|---|---|
| S0 | Right-plastic filament fully removed from the path | | |
| S1 | Filament inserted by hand to its normal stop, gently, no force; measure depth: ___ mm | | |
| S2 | Filament removed again | | |

**Expected observations:** each command prints a line saying the sensor's
filament is detected or not detected.

**Hypothesis tested:** whether the controller's presence input for P2
reflects the physical filament (sensor/gating, class D), whether filament
reaches the sensor (path, class A), or whether the sensor is fine and the
load state machine is the problem (class C).

**How results support or reject hypotheses:**

| filament_sensor_3 result | Supports | Rejects | Likely next step |
|---|---|---|---|
| not detected → detected → not detected | C (sequencing/gate logic) | D, A | Edge-vs-level test: start P2 load with filament out, insert only during the insert screen, then capture log |
| detected in all three states | Stuck "present": lever, stub/debris, or short (A/D) | healthy sensor | Visual inspection of the sensor entry per first-party SOP |
| not detected in all three, filament reached its normal depth | D: switch, lever, connector, or wiring | A | Sensor/connector inspection per first-party SOP |
| not detected in all three, filament stopped early at a hard stop | A: obstruction upstream of the sensor | — | Path inspection per first-party SOP |
| sensor_3 never changes but sensor_4 does | sensor-mapping inference wrong | current mapping | Claude revises the diagnosis before any further test |

**Evidence to record:** the six console responses verbatim; S1 depth; where the
filament stopped; the time T1 started and ended.

**Stop conditions (T1-specific):** any command other than the two queries is
needed; any response is an error; any motor moves or heater turns on.

## After R and T1 (completed 2026-09-12)

The owner reported R and T1 results; Claude performed the single authorized
read-only klippy.log GET (LM-012) and updated `DIAGNOSIS.md`. Still useful to
send when convenient: FibreTouch version screen, material, inserted depth, and
whether the last unload was done by the machine or by hand.

## Results so far (USER-OBSERVED, 2026-09-12)

- **R:** at first contact the external P2 sensor clicks and its red/blue light
  blinks, but nothing grabs the filament or feeds it into the tube.
- **T1, filament inserted:** `filament_sensor_3` detected; `filament_sensor_4`
  detected.
- **T1, filament unloaded (none on the machine):** `filament_sensor_3` not
  detected; `filament_sensor_4` detected.
- The one authorized klippy.log GET was performed after R (LM-012,
  2026-09-12T19:03:45Z). It shows the load flow passing `DETECTED` and
  commanding the P2 feed, with the extruder1 encoder recording no filament
  motion during most of the commanded feed. See `DIAGNOSIS.md` §0.2.

Reading: the presence switch works. The open question is whether the P2 feeder
motor turns when commanded. Any further log capture needs a new owner
authorization.

## T2 — motor-truth test (completed 2026-09-12; results in `T2_RESULTS.md`)

`EXPERIMENTAL`. This test commands a small motor movement, so read the stop
conditions first.

**Starting state:**
- No load/unload flow active; no print.
- Heaters off (nozzle cool is fine; no heating needed).
- **No filament anywhere in the right-plastic (P2) path**, so the gear turns
  freely and nothing is pushed toward the hotend.
- The right-plastic feeder drive gear or motor is visible, or you can rest a
  fingertip lightly on the motor body. Keep fingers away from the gear teeth.
- If practical, also watch the left-plastic feeder.
- Optional but useful: phone video of the right feeder during step 2.

**Action (G-code console):**
1. `DUMP_TMC STEPPER=extruder1` — read-only; copy the full output.
2. `STEPPER_BUZZ STEPPER=extruder1` — the extruder1 motor steps back and forth
   by about 1 mm (roughly a sixth of a turn) ten times, taking several
   seconds. Watch, listen, and feel.
3. Immediately afterwards: `DUMP_TMC STEPPER=extruder1` again; copy the full
   output.

Type the stepper name exactly as `extruder1`. Do not buzz any other stepper.

**Expected observations if the motor chain works:** a quiet rhythmic buzz or
tick, and the right-plastic drive gear visibly rocking back and forth.

**Hypothesis tested:** whether commanded extruder1 steps produce motion at the
right-plastic feeder (motor/driver/cable, class B), produce motion somewhere
else (wiring/mapping, class C), or produce correct motion so the failure is
grip/path (class A).

**How results support or reject hypotheses:**

| What you see during `STEPPER_BUZZ` | Supports | Rejects | Likely next step |
|---|---|---|---|
| Right-plastic gear visibly rocks; buzz audible or felt | A: feeder not gripping, or filament not reaching the gear | B, C-mapping | Inspect feeder idler/gear engagement per first-party SOP |
| Nothing moves or sounds anywhere | B: driver output, motor cable/connector, or motor | A as sole cause | Claude reviews both `DUMP_TMC` outputs; connector/motor check per SOP |
| A different feeder or motor moves | C-mapping: wiring or connector swapped | B, A as sole cause | Stop; wiring check per SOP |
| Faint twitch or vibration, gear does not rock | B (e.g. one motor coil open) or a mechanical bind | — | Claude reviews `DUMP_TMC` open-load/short flags |

**Evidence to record:**
- Both `DUMP_TMC` outputs, verbatim.
- What moved (which feeder), whether it was audible, whether it could be felt.
- Video if taken; time of the test.
- Any console response or error text.

**Stop conditions (T2-specific):**
- The console returns an error for either command — stop and copy it.
- Anything other than a feeder gear moves (X/Y/Z, toolhead, bed) — stop.
- Grinding, burning smell, or the motor gets hot to the touch — stop.
- Do not repeat `STEPPER_BUZZ` more than twice.
- Do not open the feeder, unplug connectors, or change configuration as part
  of T2; any inspection is a separate step under the first-party SOP.

After T2, send Claude the results. A new klippy.log capture is optional and
needs a separate authorization; the console text is sufficient for T2.

## T2 result (USER-OBSERVED, 2026-09-12)

`STEPPER_BUZZ STEPPER=extruder1` "does nothing". Both `DUMP_TMC` outputs are
preserved verbatim in `T2_RESULTS.md`: driver alive on SPI, 24.1 V supply, no
fault flags, enabled, DIR input changed during the buzz, microstep counter
(`MSCNT`) 648 before and after — which the back-and-forth buzz cannot
distinguish from "no steps received".

## T3 — step-reception test (completed 2026-09-12; results in `T3_RESULTS.md`)

`EXPERIMENTAL`. Commands two 1 mm one-direction moves per motor; read the stop
conditions first.

**Question:** do STEP pulses reach the extruder1 driver? A one-direction move
must change the driver's microstep counter `MSCNT`; T2's back-and-forth buzz
could not.

**Starting state:** same as T2 — no load/unload flow, no print, heaters off,
**no filament in either plastic path**, right-plastic feeder gear visible (and
the left one if practical), fingers away from gears. Phone video of the right
feeder during step 2 is useful.

**Action, part 1 — right plastic (`extruder1`), G-code console:**
1. `DUMP_TMC STEPPER=extruder1` — note `MSCNT`, `IOIN`, `DRV_STATUS`.
2. `FORCE_MOVE STEPPER=extruder1 DISTANCE=1 VELOCITY=1` — one second; a
   working motor turns the gear about one sixth of a turn. Watch and listen.
3. `DUMP_TMC STEPPER=extruder1` — note `MSCNT`, `IOIN`, `DRV_STATUS`.
4. `FORCE_MOVE STEPPER=extruder1 DISTANCE=-1 VELOCITY=1` — returns it.
5. `DUMP_TMC STEPPER=extruder1` — note `MSCNT`.

**Action, part 2 — control on left plastic (`extruder`):**
6. `DUMP_TMC STEPPER=extruder` — note `MSCNT`.
7. `FORCE_MOVE STEPPER=extruder DISTANCE=1 VELOCITY=1` — watch the left gear.
8. `DUMP_TMC STEPPER=extruder` — note `MSCNT`.

Copy the `MSCNT`, `IOIN`, and `DRV_STATUS` lines from every dump (or paste the
whole output, as for T2).

**Expected if extruder1 receives steps:** after step 2, `MSCNT` is no longer
648 — about 488–504 or 792–808 depending on direction (Klipper step count for
1 mm at `rotation_distance 5.65`, 16 microsteps, 200 full steps); after step 4
it returns to 648. Any change from 648 counts as "steps received".

**Expected for the control:** the left gear visibly turns and its `MSCNT`
changes between steps 6 and 8.

**How results support or reject hypotheses:**

| extruder1 `MSCNT` after step 2 | Right gear moved? | Control (left) | Supports | Rejects | Likely next step |
|---|---|---|---|---|---|
| Changed | No | Moves, `MSCNT` changes | Driver receives steps; fault in driver output stage, motor cable/connector, or motor (B-output) | B-signal, A as sole cause | Connector/cable/motor check per first-party SOP or vendor support |
| Unchanged (648) | No | Moves, `MSCNT` changes | STEP pulses not reaching the extruder1 driver: board/MCU step line or pin mapping (B-signal / C) | B-output as sole cause, A | Vendor support; do not open electronics without SOP |
| Any | Yes, right gear turns | Moves | Motor chain works; T2 motion was too small to notice | B, C | Feeder idler/gear inspection per SOP (A-grip) |
| Any | Another feeder moves instead | — | C-mapping (wiring/connector swap) | — | Stop; wiring check per SOP |
| — | — | Left does not move either, or its `MSCNT` does not change | Method or shared fault | this table's other rows | Stop; Claude reassesses before anything else |

**Evidence to record:** all dump lines listed above; what moved; video if
taken; times; any console response or error text.

**Stop conditions (T3-specific):**
- Any console error — stop and copy it.
- Anything other than a feeder gear moves (X/Y/Z, toolhead, bed, fiber
  mechanism) — stop.
- Grinding, burning smell, or a hot motor — stop.
- Use only `STEPPER=extruder1` and `STEPPER=extruder`, only `DISTANCE=1` or
  `DISTANCE=-1`, only `VELOCITY=1`. Do not repeat a move more than twice.
- No connector, cable, or configuration changes as part of T3.

## T3 result (USER-OBSERVED, 2026-09-12)

Full transcript in `T3_RESULTS.md`.

- **Right plastic (`extruder1`):** its driver's `MSCNT` moved exactly as
  predicted, 648 → 328 after two +1 mm moves and → 488 after −1 mm. DIR
  followed direction; no fault flags.
- **Left-plastic control (`extruder`):** after first enable it matched its
  prediction too (8 → 776).
- **Owner:** "the pulley on top of the extruder/toolhead" moves as if feeding.
  Nothing moves or sounds at the rear filament runout sensor when loading.
- **Not recorded:** which pulley moved during which command.

## T4 — attribution, path-reach, and grip test (not run; superseded by resolution)

`EXPERIMENTAL`. Cold test; commands only 1–3 mm moves of `extruder1`. Read the
stop conditions first.

**Question:** does the right-plastic toolhead pulley turn for `extruder1`,
does filament pushed in at the rear runout sensor reach that pulley, and does
the pulley grip it?

**Starting state:**
- No load/unload flow, no print; heaters off and nozzle cool (no heating in T4).
- Top of the toolhead visible so both the right and left pulleys can be
  watched. Phone video of the toolhead top during steps 1 and 3 is useful.
- Right-plastic filament ready, tip cut clean and straight.

**Action:**

1. **Attribution** (no filament in the P2 path yet). Watch both toolhead
   pulleys:
   - `FORCE_MOVE STEPPER=extruder1 DISTANCE=1 VELOCITY=1` — which pulley moves:
     right, left, or none?
   - `FORCE_MOVE STEPPER=extruder1 DISTANCE=-1 VELOCITY=1`
2. **Path reach** (no commands):
   - Mark the filament with a pen or tape where it enters the rear runout
     sensor.
   - Push it in by hand, gently, until it stops. Do not force it.
   - Measure how far it went in (mark to entry, in mm).
   - Note where the tip ended up: inside the tube partway, at the toolhead
     inlet, or felt against the right pulley. If you can, also measure the tube
     run from the rear sensor to the toolhead inlet.
3. **Grip** — only if step 1 showed the right pulley moving **and** step 2
   put the tip at that pulley:
   - Keep light hand pressure on the filament at the rear.
   - Put a fresh mark at the rear entry.
   - `FORCE_MOVE STEPPER=extruder1 DISTANCE=3 VELOCITY=1` — did the filament get
     pulled in? Measure how far the mark moved.
   - `FORCE_MOVE STEPPER=extruder1 DISTANCE=-3 VELOCITY=1` — did it come back out?

**Expected if path and extruder work:** right pulley moves in step 1; in step 2
the tip reaches the right pulley; in step 3 the mark moves in about 3 mm and
back out about 3 mm.

**How results support or reject hypotheses:**

| Step 1 (pulley for extruder1) | Step 2 (where the tip stops) | Step 3 (grip) | Supports | Next |
|---|---|---|---|---|
| Right moves | Hard stop well short of the toolhead | not run | A-path: obstruction or disconnection between rear sensor and toolhead | Tube/connector inspection per first-party SOP |
| Right moves | At the toolhead inlet, but will not enter the pulley/extruder | not run | Blockage at the extruder entry (leftover filament piece or debris) | Extruder/plastic-hotend inspection per first-party SOP (FS-133/FS-144) |
| Right moves | At the pulley | Pulled in ≈3 mm and back | Path and grip work → loading procedure or hotend (E) | Heated load with filament pushed to the pulley, watching the nozzle |
| Right moves | At the pulley | Pulley turns but filament does not move | A-grip: idler pressure or worn gear | Extruder roller/idler inspection per first-party SOP |
| Left moves, or none | — | not run | C-mapping (wiring swap) or B-output | Stop; Claude reassesses |

**Evidence to record:** step 1 answer; step 2 depth (mm), where it stopped, and
tube length if measured; step 3 mark movement (mm); any sounds; video; any
console text.

**Stop conditions (T4-specific):**
- Any console error — stop and copy it.
- Anything other than the right or left toolhead pulley moves — stop.
- Filament needs force, bends, or buckles — stop pushing.
- Grinding, clicking under load, burning smell, hot motor — stop.
- No heating; only `STEPPER=extruder1`, only `DISTANCE` ±1 or ±3,
  only `VELOCITY=1`; do not repeat a move more than twice.
- No disassembly, tube removal, connector, or configuration changes as part of
  T4 — any inspection is a separate step under the first-party SOP.
