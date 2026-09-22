# Loom capture session 2026-09-15T155418Z

- Purpose: preserve the vendor macros that explain two behaviours recorded in
  the 2026-09-15 sessions (`07_Troubleshooting/Loom/2026-09-15-T1/RESULTS.md`,
  `07_Troubleshooting/Loom/2026-09-15-T2/RESULTS.md`): what the print-prep
  stages and `printing_info_auto_leveling` actually do, and why a fresh mesh
  rewrites `printer.cfg` without a Klipper restart.
- Authorization: project owner, 2026-09-14 — full live access.
- Machine: Loom, `<printer-ip>`, Moonraker on port 7125.
- Started and ended: `2026-09-15T15:54:18Z` (capture-client clock). Two
  sequential GETs, issued while the flow-rate calibration print was in its
  preprint phase. Reads only; no state change from this capture session.
  Authentication material sent or stored: none.

## Captures

| Provenance ID | Method and endpoint | HTTP status | Body bytes | SHA-256 |
|---|---|---:|---:|---|
| LM-024 | `GET /server/files/config/print_control.cfg` | 200 | 33,916 | `433fe2a35b0b52a2f367fbb8398bb013c586a21ae4cf53d714d92365abbcc3a7` |
| LM-025 | `GET /server/files/config/calibration.cfg` | 200 | 18,547 | `522c9dba9b9f5885f4529b8cda087032009c1071cff2cdbc65577ca6c0751b1c` |

Both files report `Last-Modified` 2026-08-31 (vendor-installed; not changed by
the owner or by these sessions).

## What they establish (line numbers refer to the captured bodies)

- **Prep stages** (LM-024, `SDCARD_PRINT_FILE` prep): `heating_bed` (l.74) →
  `heating_nozzle` (l.101) → `cleaning` (l.107) → `leveling` (l.113). With
  `printing_info_auto_leveling == 1` (l.114) the macro first **cools the nozzle**
  — the Chinese comment reads "lower the nozzle temperature (to prevent
  temperature PWM interfering with the piezoelectric ceramic signal)" — then sets
  `homing` (l.122), runs `G28`, and runs
  `BED_MESH_CALIBRATE_FAST PRINT_MIN=mode_min PRINT_MAX=mode_max` (l.132)
  **without setting a new stage**. That is why the whole mesh probe reports
  `prep_stage: homing`. With `auto_leveling == 0` it runs
  `BED_MESH_TEMP_LOAD TEMP=<bed target>` (l.145), or
  `BED_MESH_PROFILE LOAD=default` if the bed target is 0 (l.147).
- Every print then checks `BED_MESH_CHECK_RANGE MAX=1.0` (l.152): a mesh range
  over 1.0 mm aborts the print.
- **Mesh persistence** (LM-025, l.115–117): the vendor comment reads
  "`LOAD=default` internally does `save_runtime_mesh_snapshot` →
  `SAVE_CONFIG R=0`, which also flushes the pending `default` /
  `runtime_active`; do not follow it with another `SAVE_CONFIG` (it races the
  asynchronous disk write and raises 10012)". `SAVE_CONFIG R=0` also appears at
  l.50 and elsewhere. `INFERENCE` still: `R=0` is a vendor no-restart variant of
  `SAVE_CONFIG` (not in upstream Klipper); the extension source itself was not
  inspected here.
