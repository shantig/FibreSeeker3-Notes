# Loom PLA+ 2.0 calibration — 2026-09-14 (right nozzle / Plastic 2)

**Status: first-layer/bed-level and temperature steps COMPLETE. Retraction and
flow deferred.** Provenance class `EXPERIMENTAL` (live Loom interaction). This
session used the full live-access authorization the owner granted 2026-09-14
(`CLAUDE.md`, `docs/loom/EVIDENCE_PROTOCOL.md`); it issued Moonraker
reads **and writes** (G-code, macros, config-variable writes, prints).

## Material and toolhead

- SUNLU **PLA+ 2.0 White**, 1.75 mm, spool code `01660508E2`. Label: print
  185–205 °C @ 50–100 mm/s, 205–220 °C @ 100–300 mm/s; bed 50–60 °C; spool
  resistance < 70 °C. Loaded weight 1169 g (incl. spool). `USER-OBSERVED`.
- Printed on **Plastic 2 = right nozzle = `extruder1`** (0.4 mm), plastic-only.
  `CONFIRMED` from config: P1 is the left CFC nozzle, P2 the right FFF nozzle.
- Slicer: **OrcaSlicer 2.4.2** on the owner's Mac (no VM). A custom Klipper
  printer profile "Loom P1 0.4 nozzle" drives the right nozzle via a `T1 R`
  start-G-code call (see operational doc). `INFERENCE`: Rocket is not a stripped
  OrcaSlicer — its G-code/engine differ; unconfirmed either way.

## Results

### 1. Right extruder rotation_distance — no change
- Marked filament 120 mm above the rear inlet, extruded 100 mm at 1 mm/s
  (210 °C). Owner measured 20.25 mm remaining ⇒ **99.75 mm fed, −0.25 %**.
- Within ±1 %. `extruder1 rotation_distance` stays **5.65**. `USER-OBSERVED`.

### 2. First layer / bed leveling — dialed at Z 2.57 with a fresh mesh
- First run (right-nozzle Z offset 2.6215, saved `default` mesh loaded): five
  40×40×0.2 mm squares at C(150,150), BL(35,270), BR(270,270), FL(35,35),
  FR(270,35). Result: TL and BR solid; **TR, BL, and centre gappy/high**. A
  diagonal twist the stale `default` mesh (0.50 mm range) under-compensated.
- Second run (Z **2.57**, fresh full-bed probe `auto_leveling=1`): **all five
  squares solid, opaque, evenly fused.** Fresh mesh range 0.92 mm; the back-left
  corner (10,290) is the bed's high point at **+0.28 mm** — matches the owner's
  note that the top-left leveling screw is at end of travel and adheres most.
- Saved right-nozzle offset (persists in `variables.cfg`):
  **x −32.823188, y −0.006438, z 2.57** (was z 2.621606).
- `INFERENCE`: the `default` saved mesh is stale/under-representative vs the
  current bed; prefer a fresh probe when corner accuracy matters.

### 3. PLA+ temperature tower — recommend 205 °C (first layer 210 °C)
- OrcaSlicer temperature calibration, Custom 220→195 °C, step 5, auto-scale on
  (0.2 mm layers for the 0.4 nozzle). Bands 220/215/210/205/200/195, hottest at
  the base. File `loom_temptower.gcode`, 300 layers, ~38 min, completed.
- Reading (owner photos, NAS `originals/incoming/temp-tower`, IMG_4108–4120):
  walls and embossed text crisp and fully fused at **every** band (no
  under-extrusion even at 195); small features (ring + centre pillar) cleanest
  at **200–205**, slightly more webbing ≥ 210; overhang fins crisp through ~205,
  rougher at 215–220.
- **Stringing is present across all bands** — a retraction issue, temperature-
  independent; defer to the retraction step.
- **Recommendation: other layers 205 °C, first layer 210 °C.** Coolest band that
  still bonds well with the cleanest features; within the label's speed overlap.
  Bump to 210–215 for high speed or maximum layer strength.

## Config/state changes made on Loom this session
- `SAVE_VARIABLE zoffset 2.621606 → 2.57` (right nozzle), x/y unchanged.
- `printing_info_*` set for Moonraker-driven starts: `bed_preheat 55`,
  `left_preheat 0`, `right_preheat 210`, `mode 10,10–290,290`, `print_mode 0`,
  `auto_leveling` toggled 1/0 per run.
- No `SAVE_CONFIG` was issued. A pre-existing `save_config_pending`
  (`[tension_sensor] trigger_sample_count = 6`) was left unwritten.

## Errors encountered and resolved (see operational doc for detail)
- **10057 — Klipper unhandled exception / restart.** Cause: starting via the raw
  `SDCARD_PRINT_FILE_BASE` attempted an illegal `standby → printing` transition
  inside a reactor timer, crashing Klipper. Fix: use the vendor path with a
  `precheck` step first (`standby → precheck → preprinting → printing`).
- **"Invalid print_stats state transition standby → preprinting"** (both HMI and
  Moonraker) after a fresh restart. Cause: the vendor `SDCARD_PRINT_FILE` assumes
  state is already `precheck`; the app sets it via `applyPrintState "precheck"`
  before calling. Fix: `SET_PRINT_STATS_INFO STATE=precheck` before the macro.
- **10070 — Z-axis homing verification failed** (probe −0.30 vs −0.10 ±0.05).
  Cause: residue on the nozzle tip that does the piezo Z contact (the **left**
  nozzle is active during homing/mesh). Fix: clean the nozzle tips; passed after.
- **Print paused at ~1.8 %.** Owner paused it: the removable build plate was not
  seated (tower base started on the bare base). Cancelled and reprinted on the
  seated plate.

## Evidence artifacts
- Print files (in this folder): `loom_T1.3mf`, `loom_T1.gcode` (first-layer
  squares), `loom_temptower.gcode`.
- Owner photos on NAS `home/FibreSeeker-KB-Archive/originals/incoming/`:
  squares runs (IMG_4094–4098 first run; IMG_4102–4107 second run), temp tower
  `temp-tower/IMG_4108–4120`, spool label IMG_4073, HMI/inventory IMG_4070–4071,
  FibreSeek PET-GF/CFC-PETG boxes IMG_3557–3558.
- FibreTouch diagnostic exports (owner USB `STUDIO2`): three
  `FibreTouch_Log_2026-09-14_*.zip` capturing the 10057/10070/state errors and
  the anisotouch/klippy logs. **Not yet copied to NAS** — see next actions.
- Camera snapshots pulled to the owner's `Downloads/` (transient).

## OPEN QUESTIONS / deferred
- Retraction/stringing tuning (Orca retraction test) — flagged by the tower.
- Flow-rate calibration.
- Dual-nozzle offset — only needed for composite (CFC PETG + PETG) prints.
- Power/activity correlation: correlate smart-plug power draw against today's
  heating/mesh/print timeline. Deferred — plug data source not wired up here.
- Inventory `my-spools.json` records no empty-spool weight, so net filament mass
  from the 1169 g reading is unknown.
