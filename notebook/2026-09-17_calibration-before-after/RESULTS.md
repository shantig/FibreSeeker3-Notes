# Loom calibration state before vs after the 2026-09-17 full calibration

`EXPERIMENTAL`. Owner question: after removing the composite hotend PTFE tube,
fitting isolation pads and running a full calibration, what actually changed?

Evidence: capture session `sources/loom/sessions/2026-09-17T232853Z`
(LM-027 … LM-039), differenced against the accepted baselines
`2026-09-13T031552Z` (save_variables), `2026-09-15T151115Z` (printer.cfg) and
`2026-09-15T155418Z` (macros), plus the 2026-09-16 offsets recorded in
`notebook/2026-09-16_composite-hotend-heater-check/RESULTS.md`.

Timeline read from Loom's `moonraker.log` and `print_logs/anisotouch_2026-09-17.log`.
Those logs are **not** committed — the FibreTouch log carries the machine's
Moonraker PIN. Times below are machine-local (UTC−5).

## What the owner ran

| Local time | Command | Source |
| --- | --- | --- |
| 15:52, 16:04 | `START_CALIBRATION` (bed levelling / mesh), twice | HMI |
| 16:11 | `START_SHAPER_CALIBRATE` | HMI |
| 16:15 | `START_CALIBRATE_NOZZLE_OFFSET` | HMI |
| 16:59 | `START_PID_CALIBRATION` | HMI |
| 17:37 | `UNLOAD_FILAMENT T=0 S=220 I=0` | HMI |

Klipper restarted at **17:36:28** and again at **18:07:23**. The printer is now
in `standby` and **unhomed** (`toolhead.homed_axes` is empty).

**No extrusion (`rotation_distance`) calibration was run.** The vendor has one —
`E_ROTATION_DISTANCE_ALIGN` / `ALIGN_FIBRE_LENGTH` — and it was not invoked. It
also only ever touches `extruder2` (fibre), never the plastic extruders.

## The delta

### Nozzle offsets — today's run undoes the 2026-09-16 outlier

| | 2026-09-13 | 2026-09-16 (new hotend) | 2026-09-17 (now) | 09-16 → 09-17 |
| --- | ---: | ---: | ---: | ---: |
| `xoffset` | −32.823 | **−35.043** | **−33.073** | **+1.970** |
| `yoffset` | −0.006 | −0.355 | +0.047 | +0.402 |
| `zoffset` | 2.622 | 2.652 | 2.654 | +0.002 |

The 2026-09-16 X offset was an **outlier of about 2 mm**. Today's value lands
within **0.25 mm** of the pre-failure 2026-09-13 baseline.

`INFERENCE`: the 09-16 nozzle-offset calibration ran on a hotend that had just
leaked PLA over the block (`IMG_4497`, `IMG_4500`). A blob on the nozzle or
skirt displaces the touch-off point, so −35.043 measured the contamination, not
the tool. Today's number, taken on a cleaned assembly, agrees with the
uncontaminated baseline. **Treat −35.043 as bad data and do not use it as a
reference point.**

Cross-check: `xyz_offset.ini` (LM-034) holds the raw per-tool switch positions,
`t0.x = 151.6456875`, `t1.x = 118.57221875`, `t0.y = 326.81753125`,
`t1.y = 326.864875`. Their differences reproduce `xoffset` and `yoffset` to the
last digit, so today's offsets are internally consistent.

Z moved **+0.002 mm**. Removing the PTFE tube and adding the isolation pads did
not change the nozzle's Z datum.

### Plastic 1 PID — the largest real change

| Term | 2026-09-15 | 2026-09-17 | Change |
| --- | ---: | ---: | ---: |
| `pid_Kp` | 25.451 | 19.944 | **−21.6 %** |
| `pid_Ki` | 1.749 | 1.031 | **−41.1 %** |
| `pid_Kd` | 92.574 | 96.476 | +4.2 % |

Lower proportional and much lower integral gain with slightly more derivative is
the signature of a **slower, better-insulated thermal path** — the loop no
longer needs to push as hard, and it has to anticipate more. This is the
expected, and desirable, consequence of the isolation pads. It is direct
physical confirmation that the pads changed the heater's behaviour.

For contrast, Plastic 2 — which the owner did not touch — barely moved:

| Term | 2026-09-15 | 2026-09-17 | Change |
| --- | ---: | ---: | ---: |
| `pid_Kp` | 27.566 | 28.181 | +2.2 % |
| `pid_Ki` | 8.751 | 8.947 | +2.2 % |
| `pid_Kd` | 21.708 | 22.192 | +2.2 % |

That is run-to-run repeatability. It is a useful control: it shows the Plastic 1
shift is real and not calibration noise.

### Input shaper — noise

`shaper_freq_x` 34.4 → 34.6, `shaper_freq_y` 33.2 → 32.8. Sub-1.5 % on both
axes, shaper types unchanged (`zv` / `mzv`). Nothing to read into this.

### Bed mesh — a small coherent tilt, not noise

| | 2026-09-15 | 2026-09-17 |
| --- | ---: | ---: |
| min | −0.1548 | −0.1213 |
| max | +0.3489 | +0.4307 |
| range | 0.5037 | 0.5519 |
| mean | 0.1011 | 0.1139 |

The per-point delta is not random. The **front edge dropped** 0.03–0.05 mm and
the **back edge rose** 0.03–0.08 mm, smoothly, across all nine columns — a
rotation about X of roughly 0.10 mm over the 280 mm probed span. Total range
grew from 0.504 to 0.552 mm.

`INFERENCE`: consistent with the toolhead being removed and refitted, which
changes the probe's geometry relative to the nozzle. It is not evidence that the
bed itself moved.

`OPEN QUESTION`: 0.5 mm of mesh range on a 300 mm bed is large in absolute
terms, and it was large before today too. Worth a separate look; it is not a
regression introduced by this calibration.

### What did not change

- **`rotation_distance` on every axis**: `extruder` 5.719, `extruder1` 5.65,
  `extruder2` 37.485. Unchanged in `printer.cfg`, and no runtime override
  survives — Klipper restarted twice today.
- **`calibration.cfg` and `print_control.cfg` are byte-identical** to the
  2026-09-15 captures. No vendor macro logic changed.
- `extrude_factor` 1.0, `speed_factor` 1.0, `homing_origin` all zero.
- The Plastic 1 start-G-code workaround
  (`SET_EXTRUDER_ROTATION_DISTANCE EXTRUDER=extruder DISTANCE=5.49`) is
  untouched and still applies only to prints started with that start G-code.

### One pending config write

`configfile.save_config_pending` is **true**. The only pending item is
`[tension_sensor] trigger_sample_count = 6`, written by the HMI's fibre-jam
sensitivity sync at startup, not by the calibration. Harmless, but it means a
`SAVE_CONFIG` from any source will also commit that value and restart Klipper.

## The Plastic 2 over-extrusion report

The owner reports that purging 10 mm or 50 mm on Plastic 2 put out roughly five
times the expected material. The log shows exactly what was commanded.

The HMI's Plastic 2 control sends, per press:

```gcode
M83
RESTORE_EXTRUDER2
ACTIVATE_RIGHT_P_EXTRUDER
G0 F300
G1 E<n> F300
M400
M118 EXTRUDER_COMPLETE_PLASTIC
```

Reading the macros (LM-038): `ACTIVATE_RIGHT_P_EXTRUDER` selects `extruder1` and
applies the saved gcode offsets. `RESTORE_EXTRUDER2` unsyncs and restores
**only** `extruder2`; it never alters `extruder` or `extruder1`. There is **no
flow multiplier, no motion sync, and no rotation-distance override anywhere in
this path.** With `rotation_distance = 5.65`, `G1 E50` feeds 50 mm of 1.75 mm
filament. The firmware did what the button said.

Twenty-one presses were logged between 17:26 and 17:44, totalling
**418 mm of filament = 1,005 mm³ ≈ 1.25 g of PLA**:

| Step | Presses | Total |
| ---: | ---: | ---: |
| 1 mm | 8 | 8 mm |
| 10 mm | 6 | 60 mm |
| 50 mm | 7 | 350 mm |

**Leading `INFERENCE` — the number is a unit mismatch, not a fault.** 10 mm of
1.75 mm filament is 24.1 mm³. Pushed through the 0.4 mm Plastic 2 nozzle into
free air it emerges as a strand roughly 12–19 cm long, depending on die swell.
A "50 mm" purge yields 120 mm³, or on the order of 0.6–1.0 m of strand. Judged
against the number on the button, that reads as many times too much — but it is
the correct volume. The same purge on Plastic 1's 0.7 mm nozzle gives about a
third the strand length for the same commanded feed, which is why the two sides
feel so different.

This is a hypothesis about what was measured, not a dismissal. It is settled by
one measurement, below.

### Confirmed defect: the touchscreen double-fired once

At 17:28:21.203 and 17:28:21.374 — **171 ms apart** — the HMI sent the 50 mm
purge script **twice** from what the log records as two separate press events.
Every other gap in the session is 5 s or longer. One press in twenty-one
delivered 100 mm instead of 50 mm.

This is real and reproducible enough to matter for any hand-fed calibration: a
feed measurement taken across a double-fire reads 2× high with nothing visible
on screen. It is **not** a 5× effect and does not by itself explain the report.

### `OPEN QUESTION`: the HMI's E / U / V labels do not match the axes they drive

From the QML handlers:

| HMI control | Handler | G-code sent | Klipper extruder | Physical |
| --- | --- | --- | --- | --- |
| `E` | `onRequestMoveCarbonFiberByStep` | `G0 U<n>` | `extruder2` | **fibre** |
| `U` | `onRequestMoveCoextrudedFilamentByStep` | `G0 V<n>` | `extruder` | **Plastic 1** |
| `V` | P2 extrude script | `G1 E<n>` | `extruder1` | **Plastic 2** |

Each label drives the axis named by a *different* label — a consistent rotation
E→U, U→V, V→E. The names above are the internal QML identifiers; whether the
**on-screen** labels match them has not been confirmed and needs the owner to
look at the panel. If they do match, every manual extrusion in the KB's history
needs re-reading against this table, and pressing "E" to purge plastic on the
left side actually drives the fibre motor.

## Where this leaves the machine

- The calibration itself is clean and internally consistent. The one
  substantive change is the Plastic 1 PID, and it moved in the direction the
  isolation pads predict.
- The 2026-09-16 X offset of −35.043 is withdrawn as contaminated.
- The machine is unhomed with one trivial config write pending.
- Nothing in today's calibration touched extrusion rate on either plastic side.

## Next action

One measurement settles the Plastic 2 question. With P2 at temperature and the
filament marked at the extruder inlet:

1. Mark the filament, measure to a fixed reference.
2. Press the 50 mm purge **once**, and confirm in the log that exactly one
   script was sent.
3. Measure the mark again. **Consumed length**, not extrudate length, is the
   number that matters.

If it consumed ~50 mm, the feed is correct and the report was extrudate volume.
If it consumed ~250 mm, there is a real 5× fault and it is upstream of anything
in the config captured here.
