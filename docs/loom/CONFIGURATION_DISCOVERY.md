# Loom Configuration Discovery

## Scope and evidence

This Phase 2H-A record interprets three sequential read-only captures made on
2026-09-08: Klipper's loaded `configfile` object (LM-005), Moonraker's parsed
server configuration (LM-006), and Moonraker's connected extension-agent list
(LM-007). Exact response bodies, macro text, identifiers, and paths remain in
the raw capture. No macro or extension method was invoked.

Phase 2H-B adds runtime/module attribution from LM-008 through LM-010. See
`COMPONENT_ATTRIBUTION.md` for the source-location, health, command, and safety
inventory. The configuration facts below remain the Phase 2H-A baseline.

## Configuration-visible Klipper architecture

### CONFIRMED

- LM-005 returned 192 loaded Klipper configuration sections: 122
  `gcode_macro` sections, 7 `delayed_gcode` sections, and 63 other sections.
- The configured tool-role mappings are explicit in the activation bodies:
  `ACTIVATE_LEFT_F_EXTRUDER` selects `extruder2`,
  `ACTIVATE_LEFT_P_EXTRUDER` selects `extruder`, and
  `ACTIVATE_RIGHT_P_EXTRUDER` selects `extruder1`.
- `extruder` and `extruder2` declare 0.7 mm nozzles; `extruder1` declares a
  0.4 mm nozzle. All three declare 1.75 mm filament and 380 C maximum
  configured temperature. These are configuration values, not independently
  measured dimensions or validated safe operating limits.
- Temperature-control sections are `extruder`, `extruder1`, `extruder2`,
  `heater_bed`, and `heater_generic chamber`. The bed declares a 130 C maximum
  and the chamber declares an 80 C maximum. Only `extruder` has a separate
  `verify_heater` section; the chamber also has one.
- Fan-class sections are `fan`, `fan_generic fan3` through `fan_generic fan7`,
  and `heater_fan fan1` and `heater_fan fan2`. The two heater fans are bound to
  `extruder` and `extruder1`, respectively, with a configured 45 C activation
  threshold.
- Eight filament-switch sections are configured:
  `filament_sensor`, `filament_sensor_1`, `filament_sensor_3`,
  `blinds_hall_sensor1`, `blinds_hall_sensor2`, `door_hall_sensor`,
  `toolhead_hall_sensor1`, and `toolhead_hall_sensor2`. Two filament-motion
  sections are configured: `filament_sensor_2` for `extruder` with a declared
  7 mm detection length and `filament_sensor_4` for `extruder1` with a declared
  12 mm detection length. All ten declare `pause_on_runout: False`; five have
  separate runout G-code definitions.
- Additional sensing/control sections include `probe`, `adxl345`,
  `resonance_tester`, `input_shaper`, `tension_sensor`,
  `adc_temperature my_custom_resistance_adc`, `servo fibre_servo`,
  `aniso_bed_mesh`, `xyz_align`, and `ws2812b_spi`.
- Candidate custom Klipper object sections are `blinds_hall_monitor`,
  `extruder_stall_detector extruder`, `load_unload`, `tension_sensor`,
  `aniso_bed_mesh`, `xyz_align`, and `ws2812b_spi`. Names and non-upstream
  shapes identify them as extension candidates; LM-005 does not establish
  authorship.
- `blinds_hall_monitor` declares 600-second state-change and recovery timeouts,
  a 0.5-second check interval, and an 8 C tolerance.
- `extruder_stall_detector extruder` monitors `extruder`, with a 0.1-second
  sample interval, 0.5 stall threshold, 20 SG threshold, 0.3 SG drop rate,
  five-sample filter window, StallGuard disabled, and SG monitoring enabled.
- `tension_sensor` declares a 55,000 jam-deviation limit and four-sample
  trigger count. Units and physical interpretation are not exposed.

### STRONGLY INFERRED

- The macro labels and their direct selection bodies establish the configured
  logical roles with high confidence. They do not independently prove which
  hotend is physically installed, its material, or its current readiness.
- The custom-section shapes strongly indicate vendor/integrator Klipper
  extensions, but static module source is required for attribution and full
  semantics.

### UNKNOWN / NEEDS TESTING

- Runtime health and actual installed state of each configured device;
- units and algorithms behind custom numeric fields;
- Python source paths, authorship, versions, and status fields for custom
  objects;
- why no separate `verify_heater` section is visible for `extruder1` or
  `extruder2`, and whether defaults or custom handling apply.

## Macro inventory

### CONFIRMED

- All 122 macro names and bodies are preserved verbatim inside LM-005. Reading
  the `configfile` object did not execute them. The exact name-only inventory
  is in `MACRO_INVENTORY.md`.
- Lexical, non-exclusive name clusters provide a navigation inventory only:
  22 names contain fiber/extruder/load/unload/filament terms; 3 contain
  M280/servo/cut terms; 26 contain cleaning/brush/waste/cooling/preload terms;
  28 contain calibration/alignment/offset/homing/mesh/probe/shaper/PID terms;
  10 contain fan/temperature/standby/idle terms; 21 contain print/pause/resume/
  cancel/timelapse/SD-card/hyperlapse terms; and 7 are explicitly test-named.
  Clusters overlap and names alone do not establish behavior.
- `M280` maps its parameter to `fibre_servo` positions of 0 or 45 configured
  degrees. `M2800` calls `M280` in a 0, 1, 0 sequence with configured dwell
  intervals of 100 ms, 300 ms, and 100 ms, then calls
  `TENSION_UPDATE_BASELINE`.
- `EXTRUDE_FIBRE_LINE` selects the left-fiber role, commands a 100-unit
  U-axis relative extrusion at a configured feed value of 300, then calls
  `M2800`. `PAUSE` and `CANCEL_PRINT` also conditionally call `M2800` in fiber
  contexts.
- `T0` selects `extruder`; `T1` selects `extruder1`. Their bodies contain
  tool-switch motion and offset handling. Neither was invoked.
- The inspected cleaning bodies select T0/T1, move to a brush station, control
  cooling fans, brush the active plastic nozzle, and leave the station.
- Calibration bodies include homing, motion, heating, extrusion, probing,
  offset mutation, and persistent-configuration commands. In particular,
  `ALIGN_FIBRE_LENGTH` contains a `SAVE_CONFIG` call. Their presence is not
  authorization to run them.

### STRONGLY INFERRED

- The direct servo sequence, fiber-context call sites, and prior Rocket static
  evidence make `M2800` a strong fiber-cut operation candidate. The Loom macro
  text itself does not use a cut verb, so physical cutter behavior is not
  promoted to `CONFIRMED`.

### UNKNOWN / NEEDS TESTING

- Physical results, timing, safety preconditions, and error paths for every
  macro;
- whether referenced custom G-code commands come from FibreSeek, Klipper
  forks, or another integration layer;
- include-file ownership and a complete static call graph.

## Moonraker vendor-component and extension visibility

### CONFIRMED

- LM-006 confirms effective Moonraker configuration objects for
  `printer_setting`, `material_manager`, `mqtt_bridge`, `ai_detection`, and
  `error_indexer`. The latter four also have explicit sections in the original
  main Moonraker configuration; `printer_setting` is loaded with defaults but
  has no original configuration section.
- `material_manager` is configured as enabled. `ai_detection` is configured as
  enabled and auto-connecting, with defect, floor, and object detection
  enabled. Host, port, paths, and network allow-list details stay in raw
  evidence.
- `mqtt_bridge` has a configured bind-timeout field. `error_indexer` has
  configured spreadsheet/CSV/path fields. Configuration presence does not
  prove successful operation.
- Two named update-manager sections, `fibreseek-updater` and
  `fibreseek-updater-factory`, expose configured vendor update integration.
  No update endpoint or action was invoked.
- LM-007 lists one connected extension agent named `remote`, self-reporting
  version `1.0.0` and type `agent`. No extension method was requested.
- `blinds_hall_monitor` and `extruder_stall_detector` are Klipper-side custom
  object candidates, not entries in Moonraker's component list.

### STRONGLY INFERRED

- The five named Moonraker components and custom Klipper objects are
  vendor/integrator extensions because they are not explained by the upstream
  interfaces visible in this evidence. Names do not establish FibreSeek
  authorship.

### UNKNOWN / NEEDS TESTING

- The registered HTTP/JSON-RPC routes, request methods, schemas, and mutation
  behavior for all five named Moonraker components;
- source code, authorship, version, and runtime health for each component;
- the purpose, software origin, permissions, and callable methods of the
  `remote` agent;
- whether the AI and MQTT components were connected or processing data at
  capture time.

No guessed vendor route was probed because route semantics were not available
through the documented passive metadata endpoints.

Phase 2H-B resolves part of the preceding unknowns: all five components loaded
in the captured startup; AI connectivity changed from refused to connected
during the log window; module filenames are established for most targets; and
the missing `maintenance` module explains its load failure. Custom HTTP routes,
package versions, authorship, MQTT connectivity, and complete dependency
schemas remain unresolved.

Phase 2H-C confirms through LM-011 that the requested implementation directories
are not among Moonraker's registered file roots. Consequently, configuration keys and
runtime logger methods can be inventoried, but source-defined schemas, custom
routes, imports, and hidden defaults remain unresolved without a separately
approved static export.

Phase 2I-A's static analysis of the official firmware packages (see
`docs/firmware/FIRMWARE_ANALYSIS.md`) exposed the underlying
config-file/include structure behind this merged, effective configuration for
the first time: per-hardware-revision base configs (`printer_base_v1.1.cfg`
through `printer_base_v2.2.cfg`), matching per-revision fan/filament-sensor/
piezoelectric-ceramic overrides, a distinct `toolhead_can.cfg` alongside the
`toolhead.cfg` Loom actually loads, an `eddy.cfg` (eddy-current probe option),
and the exact `error_info.xlsx` spreadsheet `error_indexer` reads. These are
new structural facts, not corrections to the live-observed values above; the
firmware package's config files are ZipCrypto-encrypted, so only their
filenames (not contents) are confirmed.

## Unexpectedly exposed metadata

### CONFIRMED

- All three Phase 2H-A endpoints accepted unauthenticated requests from the
  capture client. LM-006 reports logins are not forced and includes an
  extremely broad trusted-client IPv4 range. The exact network value remains
  confined to raw evidence. This is a configuration observation, not a remote
  exposure test; no host outside the owner's LAN was tested.
- LM-006 exposes effective/original Moonraker configuration, including local
  service locations, network allow-list data, update integration, and AI
  detection settings. Its password/secret fields are empty/default; no
  nonempty credential was found.
- LM-005 exposes the complete loaded Klipper configuration and macro bodies,
  including macros capable of motion, heating, calibration, and persistent
  configuration changes. None was invoked.

### UNKNOWN / NEEDS TESTING

- Whether any network outside the owner's intended trusted boundary can reach
  Moonraker. Phase 2H-A did not perform exposure scanning or networking tests.

## MCU and CAN visibility

### CONFIRMED

- LM-005 confirms two configured MCU sections, `mcu` and `mcu toolhead`. Both
  use serial device paths; neither section exposes `canbus_uuid` or
  `canbus_interface`.
- The `toolhead:` pin namespace is used by the `extruder` and `extruder1`
  heater/sensor pairs, both heater fans, two generic nozzle fans, both toolhead
  Hall sensors, the fiber servo and its switch, ADXL345 chip select, and the
  custom bed-mesh ADC/trigger pair.
- LM-004 independently confirms a live host `can0` interface at capture time.
  LM-005 provides no configuration link between that interface and either
  Klipper MCU section.

### STRONGLY INFERRED

- `mcu toolhead` is a toolhead-local I/O controller because many toolhead
  devices use its pin namespace. Board model and physical topology remain
  unknown.

### UNKNOWN / NEEDS TESTING

- What uses `can0`, if anything, in the printer application stack;
- MCU board models, firmware builds, physical buses, and device topology;
- whether another process or concealed configuration maps CAN nodes outside
  Klipper's loaded configuration.

No CAN command, bus scan, restart, or shell access occurred.
