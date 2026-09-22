# Loom — starting prints via Moonraker, the print_stats state machine, and error codes

Operational knowledge recovered 2026-09-14 during live PLA calibration
(`notebook/2026-09-14_pla-temperature-tower/RESULTS.md`). `CONFIRMED` from Loom's
own config/logs and the extracted vendor `print_stats.py`
(`_zipcrypto_work/ex2/klipper_2.2.42/.../print_stats.py`) unless noted.

## How to start a print on Loom from Moonraker

Do **not** call the raw `SDCARD_PRINT_FILE_BASE`, and do not expect the
touchscreen to parse a non-Rocket (e.g. OrcaSlicer) file's header. The working
sequence:

1. Upload the G-code to the `gcodes` root (`POST /server/files/upload`).
2. Set the prep variables the vendor macro reads (they persist in
   `variables.cfg`), e.g.:
   - `SAVE_VARIABLE VARIABLE=printing_info_bed_preheat_temperature VALUE=<bed>`
   - `printing_info_left_preheat_temperature` / `..._right_preheat_temperature`
     (0 turns that nozzle off for the print)
   - `printing_info_mode_x_min/y_min/x_max/y_max` = mesh/probe area
   - `printing_info_auto_leveling` = 1 (fresh full-bed probe) or 0 (load saved
     mesh via `BED_MESH_TEMP_LOAD`, ~1 min)
   - the right-nozzle offset via `SET_RIGHT_OFFSET X=.. Y=.. Z=..`
     **(always pass all three — omitted values default to 0)**
3. `SET_PRINT_STATS_INFO STATE=precheck`  ← the step the app does and the raw
   path skips.
4. `SDCARD_PRINT_FILE FILENAME=<file>` (the vendor macro; it homes, meshes/loads
   mesh, heats, brushes, then streams the file, whose own start G-code runs
   `T1 R` to select the right nozzle and apply offsets).

For a repeat at tuned settings, `auto_leveling=0` loads the saved mesh (fast);
a **fresh** probe (`=1`) is what corrects bed twist for corner accuracy.

## The print_stats state machine (custom vendor fork)

Allowed transitions (from `print_stats.py` `STATE_TRANSITIONS`):

- `standby → {precheck, paused, load_unload, calibration, maintenance, busy}`
- `precheck → {preprinting, printing, standby, cancelled, error}`
- `preprinting → {printing, paused, standby, cancelled, error}`
- `printing → {pausing, paused, complete, cancelled, error}`
- `paused → {printing, preprinting, standby, cancelled, load_unload, error}`
- `complete|cancelled|error → standby`

So the print path is **`standby → precheck → preprinting → printing`**;
`standby → preprinting` and `standby → printing` are **illegal**. After a fresh
Klipper restart the reported state is `standby` but a print must still enter via
`precheck`. Faults/shutdown force any state back to `standby`.

## Reading progress during `preprinting` (the labels mislead)

`CONFIRMED` 2026-09-15. While `print_stats.state` is `preprinting`:

- `print_stats.filename` stays **empty** and `virtual_sdcard.is_active` stays
  **false** until the file actually starts streaming. Neither is a hang signal.
- `print_stats.info.prep_stage` runs `heating_bed → heating_nozzle → cleaning →
  leveling → homing`, and **`homing` covers the bed mesh probe**, the longest
  phase by far. `CONFIRMED` from the vendor macro (LM-024, `print_control.cfg`
  l.113–132): with `auto_leveling = 1` it sets `leveling`, **cools the nozzle**
  (comment: so heater PWM does not disturb the piezo signal — expect the nozzle
  temperature to *fall*), sets `homing`, runs `G28`, then
  `BED_MESH_CALIBRATE_FAST` over `printing_info_mode_*` without setting another
  stage. Every print then aborts if the mesh range exceeds 1.0 mm
  (`BED_MESH_CHECK_RANGE MAX=1.0`, l.152).
- With `printing_info_auto_leveling = 1` the fresh probe is **81 points × 6
  samples**, roughly 9 s per point — about **20 minutes** of `preprinting`
  before the first layer (full-bed `mode` area 10–290). The 6 samples come from
  the machine's `[tension_sensor] trigger_sample_count = 6`. Narrowing
  `printing_info_mode_*` changes what `BED_MESH_CALIBRATE_FAST` does: an
  80–220 × 95–205 mm area probed 45 points (2026-09-15 flow pass 1), while a
  110–195 × 120–185 mm area loaded the temperature-predicted `default` mesh
  (`BED_MESH_TEMP_LOAD`) and corrected it from **5 points** — centre and the
  area's four corners (`[FAST_BED_MESH]` log lines, X0008). `OPEN QUESTION`:
  the area threshold between the two behaviours.
  `auto_leveling = 0` skips probing and runs `BED_MESH_TEMP_LOAD TEMP=<bed>`
  (or `BED_MESH_PROFILE LOAD=default` with the bed off) — fast, but the saved
  mesh was stale on 2026-09-14.
- Per-point progress is visible in the G-code store as
  `// [BED_LEVELING] point=n/81, zpos=[…], zev=…`
  (`GET /server/gcode_store?count=…`). That, not `prep_stage`, is how to tell a
  probing machine from a stuck one.
- `SDCARD_PRINT_FILE` runs the whole preprint sequence synchronously, so the
  HTTP call returns **`504` from nginx** long before the macro finishes. The
  504 is not a failure; poll `print_stats` instead.
- A fresh probe **rewrites `printer.cfg`** when it finishes: the
  `[bed_mesh runtime_active]` block is replaced in the file even though no
  `SAVE_CONFIG` was issued and `save_config_pending` stays `true` (LM-022).
  The vendor comment in `calibration.cfg` (LM-025, l.115–117) explains it:
  loading a mesh profile runs `save_runtime_mesh_snapshot` → `SAVE_CONFIG R=0`,
  and a second `SAVE_CONFIG` straight after races that async write (error
  10012). `INFERENCE`: `R=0` is a vendor no-restart `SAVE_CONFIG`. Re-read
  `printer.cfg` immediately before editing it, and never chain a `SAVE_CONFIG`
  after a mesh load.

## Fans (`M106` on Loom)

`CONFIRMED` from the vendor `M106` macro in `fans.cfg`: **no `P`** sets the
plastic *and* fibre cooling fans (so OrcaSlicer's plain `M106 S…` does cool
Plastic 2); `P0` filter fan, `P1` plastic cooling, `P2` fibre cooling, `P3`
cross-flow circulation (also sets the chamber heater target to 0 and starts the
blinds monitor), `P4` mainboard, `P5` exhaust. `M107` turns off the plastic and
fibre cooling fans. FibreSeek's own PLA-Benchy uses `P1` for part cooling and
turns on `P3` and `P5` from layer 50 (LM-026).

## `calibration` state and the nozzle-offset routine

`CONFIRMED` 2026-09-16 by observation. `calibration` already appears in the
`STATE_TRANSITIONS` table above as a legal target from `standby`; what is new is
what the state looks like in practice. `idle_timeout` reads `Printing`
throughout, so an idle check alone will not tell a calibrating machine from a
printing one. The
nozzle-offset routine heats **Plastic 1 to 220 °C then holds 170 °C**, keeps
**Plastic 2 at 120 °C**, emits `echo: [PRECALIBRATION] nozzle is heating, please
wait...`, runs with no bed mesh loaded (`// No mesh loaded to offset`) and
toggles `min_extrude_temp` between 0 and 180 around the heat-up. Do not inject
temperature or motion commands while this state is active.

## Filament sensors — which is which

`CONFIRMED` 2026-09-16 from the vendor `RESUME` macro, which names each sensor in
its runout errors:

| Object | Meaning |
| --- | --- |
| `filament_switch_sensor filament_sensor` | **Left fibre** present (`"Left fiber missing"`) |
| `filament_switch_sensor filament_sensor_1` | **Left plastic — Plastic 1** present (`"Left plastic missing"`) |
| `filament_switch_sensor filament_sensor_3` | **Right plastic — Plastic 2** present (`"Right plastic missing"`) |
| `filament_motion_sensor filament_sensor_2`, `_4` | Motion sensors, 7 mm detection length |

A switch sensor only proves filament is present **at the sensor**, upstream — not
that its tip is in the nozzle.

**Before any manual extrusion, check two things and fail closed:** the presence
sensor for the intended path, and `toolhead.extruder`. An HMI purge leaves
whichever extruder it used last selected — on 2026-09-16 a purge ending with
`ACTIVATE_RIGHT_P_EXTRUDER` left `extruder1` active, and a following `G1 E…`
intended for Plastic 1 went out of Plastic 2. Issue `ACTIVATE_LEFT_P_EXTRUDER`
(or `ACTIVATE_RIGHT_P_EXTRUDER`) and assert the result before extruding.

## Stale job variables

The start macro logs `Printing file: …` from `printing_info_filename`, which
Moonraker-started prints do not update — on 2026-09-15 it still read
`DemoFiles/PETG-Scraper.gcode`. The HMI status bar showed "High Strength Mode"
during an Orca plastic-only print; `printing_info_print_mode` (0) is used by the
macro only to choose the light pattern (`INFERENCE`: 0 is what the HMI labels
"High Strength Mode"). Setting the variables before `SDCARD_PRINT_FILE` does
make the HMI and the log agree with the job (`CONFIRMED` 2026-09-15, X0011).

### Quoting a string `SAVE_VARIABLE` value

`CONFIRMED` 2026-09-15. Klipper parses extended-command arguments with
`shlex.split`, which **removes one level of quoting**, and `save_variables` then
runs `ast.literal_eval` on what is left. A value that must stay a string
therefore needs **two** levels — the vendor's own macros use double outside,
single inside:

```
SAVE_VARIABLE VARIABLE=printing_info_filename VALUE="'loom_benchy_P1_X0011.gcode'"
```

`VALUE="name.gcode"` and `VALUE='name.gcode'` both arrive as bare
`name.gcode` and fail with `Unable to parse 'name.gcode' as a literal`.

**A malformed value can take the printer down.** `literal_eval` raises
`IndentationError` for a value with leading whitespace (`VALUE=" abc "`), and
that is not caught: Klipper logs `Internal error on command:"SAVE_VARIABLE"`,
calls `invoke_shutdown`, and the MCU stays shut down until a
`POST /printer/firmware_restart` (a plain restart fails with "Can not update MCU
'mcu' config as it is shutdown"). `CONFIRMED` 2026-09-15 20:29 — a probe command
of mine shut Klipper down; recovery was one firmware restart plus `G28`, and the
runtime-only settings (`SET_EXTRUDER_ROTATION_DISTANCE`, pressure advance) were
lost with it. Never probe `SAVE_VARIABLE` with speculative values on a machine
that is holding state.

## Writing configuration

`CONFIRMED` 2026-09-15. Moonraker's `config` root is **read-only**
(`GET /server/files/roots` → `config: "r"`; an upload fails with
`Invalid root request: config`), and `gcodes`, `usb` and `timelapse` are the
writable roots. Changing `printer.cfg` therefore needs shell access, and SSH to
`anisoprint@<printer-ip>` refuses public-key auth as shipped. Uploading a
G-code file: `POST /server/files/upload` with `root=gcodes` and **no `path`
field** — passing `path=<name>.gcode` creates a *directory* of that name.

## Error codes seen (HMI shows these; they are Klipper errors surfaced by the app)

- **10057 — "Unhandled exception during run."** A Klipper unhandled exception.
  On 2026-09-14 it was caused by the raw `SDCARD_PRINT_FILE_BASE` doing an
  illegal `standby → printing` inside `virtual_sdcard.work_handler →
  print_stats.note_start`; the raise happened in a reactor timer, so Klipper
  shut down and auto-restarted. `INFERENCE`: raising inside the timer instead of
  failing the command gracefully is a robustness bug in the vendor fork.
- **10070 — "Z-axis homing verification failed."** The piezo Z probe (nozzle-tip
  contact) read outside `z_offset ±0.05 mm`. Caused by residue on the tip of the
  **active nozzle during homing** — homing/meshing run with the **left nozzle
  (T0)** active, so the **left** tip cleanliness gates the Z check even for a
  right-nozzle-only print. Fix: clean the nozzle tips (vendor prompt says so).
- A **plain-text** state-transition error ("Invalid print_stats state transition
  …") appears with `Error Code: UNKNOWN`.
- More generally, **any `!!` error from a command sent through Moonraker pops a
  modal on the touchscreen** ("Error — Error Code: UNKNOWN" plus the Klipper
  message; `CONFIRMED` 2026-09-15 with five malformed `SAVE_VARIABLE` commands,
  owner photo `IMG_4147`). The command itself had no effect, but someone at the
  machine has to dismiss each pop-up. Scripts that send several commands should
  stop at the first error.

## Camera

`fibreseek_camera` (crowsnest/mjpegstreamer) serves a JPEG snapshot at
**`http://<printer-ip>/webcam/?action=snapshot`** and an MJPEG stream at
`?action=stream`. **Keep the trailing slash after `webcam`**: without it nginx
answers `301` and a client that does not follow redirects (plain `curl`, no
`-L`) saves the redirect HTML instead of a JPEG. It reports `enabled:false`
when idle and `true` during a job, but snapshots were served fine while idle on
2026-09-15. Wide-angle, mounted low at the front looking back
across the bed: good for live monitoring (print present, gross failures,
detachment/spaghetti) but too shallow/distorted for fine first-layer squish or
to read the HMI. Use owner top-down photos for squish-level calibration.

**Framing** (`CONFIRMED` 2026-09-15): the toolhead blocks the bed from most
positions, and at high Z the bed falls out of frame. Park at **X320 Y335** and
set **Z ≈ 20–35** for a clear view of the plate; Z 60 and above shows little of
it. After a cancel the axes are unhomed, and Z homing probes at (150, 150) —
directly over a part still on the plate — so declare the current height with
`SET_KINEMATIC_POSITION Z=<reported z>` (force_move is enabled) and move Z from
there rather than homing. Even at the best framing the camera cannot resolve
surface quality; it shows presence, adhesion and gross failure only.

## Related
- Right-nozzle Z offset and mesh handling, first-layer result: [[RESULTS.md]] in
  `notebook/2026-09-14_pla-temperature-tower/`.
- Retraction sweep method and the `[firmware_retraction]` blocker:
  `notebook/2026-09-15_pla-retraction-stringing/RESULTS.md`.
- Component/architecture attribution: `docs/loom/ARCHITECTURE.md`,
  `COMPONENT_ATTRIBUTION.md`.
