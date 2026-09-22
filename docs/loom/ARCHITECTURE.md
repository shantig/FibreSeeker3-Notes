# Loom Architecture

This document maps Loom's software, host, MCU, CAN, device, and application
layers from preserved read-only evidence. Current live evidence is limited to
the Moonraker/Klipper, configuration, extension-agent, and host metadata
exposed in LM-001 through LM-010. Component-level attribution and interface
safety classifications are in `COMPONENT_ATTRIBUTION.md`.

## Host and service layer

### CONFIRMED

- Loom reports Ubuntu 20.04.6 LTS (`focal`) with kernel 5.10.198, 64-bit
  aarch64, four CPU cores, 3,933,096 kB of memory, and no virtualization
  (LM-004).
- The Python runtime reports 3.8.10, built with GCC 9.4.0 (LM-004).
- Moonraker obtains machine-service data through `systemd_dbus`. The available
  services are `klipper`, `klipper-mcu`, `moonraker`, and `crowsnest`; all four
  reported `active/running` at capture time (LM-004).
- The active network interface reported by this endpoint is `wlan0`. Exact
  addresses and hardware identifiers remain confined to privacy-sensitive raw
  evidence (LM-004).
- `can0` reports driver `rockchip_canfd`, transmit queue length 1024, and bitrate
  996,644 bit/s (LM-004).
- The SD-information block reports unknown manufacturer/capacity and zero total
  bytes, alongside identification fields that are retained only in raw
  evidence (LM-004).

### STRONGLY INFERRED

- The reported CAN bitrate is the controller's realized value for a nominal
  1 Mbit/s configuration. **Phase 2I-A confirms** the nominal configuration
  is exactly 1,000,000 bit/s with `txqueuelen` 1024, from the official
  firmware package's `klipper.config` (`CONFIG_CANBUS_FREQUENCY=1000000`) and
  a boot script's literal `ip link set can0 ... bitrate 1000000 ...
  txqueuelen 1024` — previously only inferred from Loom's live realized rate.
- The SD-information block is incomplete or incorrectly decoded; zero reported
  bytes does not establish that Loom lacks persistent storage.
- `can0`'s `rockchip_canfd` driver name (public Linux kernel information, not
  vendor-specific) indicates a Rockchip SoC family host board (Phase 2H-D).
  **Phase 2I-A** adds independent, stronger support: the official firmware's
  `fibretouch-ai.zip` bundles `rknn_toolkit2` (Rockchip's own NPU inference
  SDK) and ships `.rknn`-format vision models, confirming on-device inference
  is compiled for a Rockchip NPU target. No specific board model is claimed
  from either source.

### UNKNOWN / NEEDS TESTING

- Host board and storage-device models;
- systemd unit definitions, launch arguments, environment, and dependencies;
- CAN node identifiers, attached device count, bus health, and MCU mapping.

## Moonraker and Klipper application layer

### CONFIRMED

- `/server/info` reports Moonraker API 1.5.0, Klippy connected and ready, 32
  loaded components, one failed component (`maintenance`), five warnings, and
  three websocket connections at capture time (LM-002).
- The reported Moonraker version is `?`. `/printer/info` likewise reports
  Klipper software version `?` and CPU summary `4 core ?` (LM-002, LM-003).
- `/printer/info` reports hostname `anisoprint`, machine name `FibreSeeker 3`,
  process UID/GID 1000, and the owner-supplied Klipper executable, Python,
  configuration, and log paths (LM-003).
- Registered Moonraker directories are `config`, `logs`, `gcodes`, `usb`,
  `timelapse`, `timelapse_frames`, and `config_examples` (LM-002).
- The five active warnings concern three unparsed log-rotation options, the
  unparsed `[maintenance]` section, and invalid Klipper docs path
  `/home/anisoprint/klipper/docs` (LM-002).
- HTTP response headers for LM-001 through LM-007 identify
  `TornadoServer/6.4.2`.
- `/server/config` confirms effective configuration for `printer_setting`,
  `material_manager`, `mqtt_bridge`, `ai_detection`, and `error_indexer`.
  The latter four are explicit in the source configuration;
  `printer_setting` is loaded with defaults (LM-006).
- `/server/extensions/list` reports one connected agent named `remote`, version
  `1.0.0`. Its purpose and callable methods are not exposed (LM-007).

### STRONGLY INFERRED

- `printer_setting`, `material_manager`, `mqtt_bridge`, `ai_detection`, and
  `error_indexer` are vendor- or integrator-added component candidates because
  they are not explained by upstream interfaces visible in the current
  evidence. Names alone do not establish authorship.
- The failed `maintenance` component likely accounts for the unparsed
  `[maintenance]` section. The response does not expose the actual import or
  initialization error.

### UNKNOWN / NEEDS TESTING

- Exact Moonraker and Klipper source revisions and why both versions are `?`;
- component source paths, authorship, code differences, registered APIs, and
  runtime health;
- purpose, source, permissions, and methods of the connected `remote` agent;
- root cause and practical effect of the failed `maintenance` component;
- configuration content behind the registered directory names and warnings.

## Current object-level map

### CONFIRMED

- Moonraker returned 178 Klipper object names from
  `GET /printer/objects/list` (LM-001).
- Two MCU status namespaces are present: `mcu` and `mcu toolhead`. LM-005 shows
  both configured with serial device paths and no `canbus_uuid` or
  `canbus_interface`; board models and physical wiring remain unknown.
- Three extruder status namespaces are present: `extruder`, `extruder1`, and
  `extruder2`.
- Six TMC2240 driver namespaces are present for X, Y, Z, and the three
  extruders.
- Ten filament-sensor namespaces are present: eight switch sensors and two
  motion sensors. Their configured names include generic filament sensors,
  blind Hall sensors, toolhead Hall sensors, and a door Hall sensor.
- The namespace includes a generic chamber heater, heated bed, eight fan-class
  objects, a probe, bed mesh, motion reporting, endstop querying, a servo, and
  three output pins.
- Two object types stand out as nonstandard candidates:
  `blinds_hall_monitor` and `extruder_stall_detector`. Their implementations and
  provenance are not established by the name list.
- There are 122 G-code macro objects. Names expose fiber feed/restart, cutter,
  tool switching, nozzle cleaning, calibration, Hall/filament sensing,
  timelapse, and test-oriented surfaces. Enumeration did not execute any macro.
- LM-005 preserves all 122 bodies. The three role-activation bodies explicitly
  map left fiber to `extruder2`, left plastic to `extruder`, and right plastic
  to `extruder1`.
- `M2800` configures a 0, 1, 0 `M280` sequence with 100, 300, and 100 ms
  dwells, then updates the tension baseline. `M280` maps those states to the
  configured fiber servo. No macro was invoked.

### STRONGLY INFERRED

- The `mcu toolhead` name indicates a toolhead-local control role, but its
  board identity and physical wiring remain unresolved. LM-005 confirms that
  the `toolhead:` namespace supplies many configured toolhead devices.
- `M2800` is likely Loom's fiber-cut macro because its body operates the fiber
  servo, it is called from fiber-context macros, and prior Rocket static
  evidence identifies M2800 as the cut-command candidate. Its own body does
  not state a cutting result. **Phase 2I-B** adds circumstantial (not
  independent) support: AnisoTouch's `LoadUnloadModel::cutFilament()` exists
  as its own dedicated touchscreen action, confirming a "cut" operation is a
  first-class UI feature — but the disassembly does not show which G-code it
  actually issues, so this remains `STRONGLY INFERRED`, not `CONFIRMED`.

### UNKNOWN / NEEDS TESTING

- MCU board models, firmware builds, physical buses, and topology;
- what uses host `can0`; LM-005 does not link it to either configured MCU;
- definitions and upstream/vendor lineage of `blinds_hall_monitor` and
  `extruder_stall_detector`;
- macro include-file ownership, physical effects, safety preconditions, and
  complete call graph;
- whether every configured object corresponds to installed, enabled, and
  currently healthy hardware.

See `OBSERVATIONS.md` for the chronological record and evidence limitations.

## Phase 2H-B implementation attribution

### CONFIRMED

- LM-008 shows Moonraker running from a source checkout and virtual environment,
  with the five configured vendor/integrator components loaded through the
  standard `moonraker.components` mechanism. `error_indexer` exposes its exact
  component-module location and spreadsheet dependency; logger filenames
  identify `material_manager.py`, `mqtt_bridge.py`, and `ai_detection.py`.
- The FibreTouch application reports version `2.2.30.613`. Update-manager logs
  expose a configured/detected repository-identity mismatch. This confirms an
  integrated vendor application layer, not per-module authorship.
- LM-009 shows Klipper running from a source checkout and virtual environment.
  Six custom module filenames are directly present in logger output; the
  seventh, `aniso_bed_mesh.py`, follows from Klipper's standard section loader
  but lacks a direct logger line.
- Both MCU firmware strings share vendor build base
  `v2.2.20.515-34-g2093130b`; the main and toolhead MCUs expose 126 and 135
  commands respectively. Klipper's Git version still reports `?`.
- LM-008 places the `remote` agent on an inbound host-local WebSocket. Its
  self-advertised FibreSeek URL and version match LM-007.

### STRONGLY INFERRED

- A local companion-service layer mediates at least AI detection and the
  Moonraker extension connection. `remote` is associated with the vendor HMI,
  remote, or cloud-facing application, but its process identity and external
  traffic are not proven.
- The seven custom Klipper candidates and five Moonraker components are
  integrator additions: none exists by the same filename in the recorded
  current official upstream comparison. This does not prove their author.

### UNKNOWN / NEEDS TESTING

- Exact component source contents, package versions, authors, licenses, and
  custom Moonraker routes;
- `remote` methods, implementation path, startup source, and permissions;
- MQTT broker/connectivity and any cloud data flow;
- which process, if any, uses host `can0`.

## Phase 2H-C access and extension boundary

### CONFIRMED

- LM-011 exposes only the registered `config`, `logs`, `gcodes`, `usb`,
  `timelapse`, `timelapse_frames`, and `config_examples` roots. Neither requested
  implementation directory is registered, so no custom source body was recovered.
- The recorded official Moonraker extension manager defines a read-only agent
  list, agent identification/event/method-registration interfaces, and a POST
  proxy that calls agent-supplied methods. LM-007 exposes no method list for
  `remote`; the proxy was not called.
- Existing logger evidence adds concrete internal relationships: AI detection
  reads database configuration and connects to a local WebSocket service;
  error indexing reads spreadsheet tables and consumes AI/Klipper errors;
  tension sensing opens host SPI; load/unload coordinates printer state,
  temperature, sensors, tool selection, and motion-capable macros.

### UNKNOWN / NEEDS TESTING

- Actual vendor source bodies and every implementation fact that requires them;
- the names and safety semantics of any methods dynamically registered by
  `remote`;
- process/service ownership of the local AI endpoint and remote agent.

See `SOURCE_RECOVERY_AND_INTERFACES.md` for the full graph and safety table.

## Phase 2H-D evidence synthesis and confidence reconciliation

Phase 2H-D is analysis-only: it issued zero new Loom, NAS, or external
requests and re-read only already-captured evidence. Full detail, exact log
citations, and confidence tiers are canonical in
`SOURCE_RECOVERY_AND_INTERFACES.md`; this section records the architectural
conclusions.

- **Corrected:** `material_manager`'s persistence behavior was previously
  overstated as `CONFIRMED write/update semantics`. It is confirmed only to
  run a named update operation and log per-field values; whether or where
  that persists is unresolved.
- **New relationship, CONFIRMED:** the two configured `update_manager`
  sections (`fibreseek-updater`, `fibreseek-updater-factory`) and the logged
  repository-identity mismatch are the same subsystem observed from
  configuration and from the log. The tracked local update-manager version
  (`2.2.30.613`) matches the FibreTouch application version, and the OTA
  package naming convention (`fibreseek-sk3-<version>.<build>.fibrepack`) is
  now directly evidenced in the log.
- **New relationship, tiered CONFIRMED/STRONGLY INFERRED/INFERRED/UNKNOWN:**
  the Sep 7 physical door/warning-dialog observations and `blinds_hall_monitor`
  share the same functional domain (door sensing plus chamber-heater
  interlock, including a `PRINTED_DOOR_DETECTION` macro reading "Close hatch
  to enable heater!"), but the captured `klippy.log` contains no entries for
  2026-09-07 at all, so no timestamp-level correlation is possible with
  current evidence. This relationship is not promoted past `INFERRED` for the
  parts that would require that missing window.
- **Evaluated and not elevated:** a proposed `crowsnest`/`ai_detection` shared-
  camera-feed relationship. Neither logs nor configuration name `crowsnest` in
  relation to `ai_detection`, and the transport (`ai_detection` uses a
  WebSocket; `crowsnest` conventionally serves HTTP/MJPEG) does not match
  cleanly. This remains `UNKNOWN`, not `STRONGLY INFERRED`.
- **Reconciled:** `TENSION_UPDATE_BASELINE` now has one canonical
  classification (`mutating/physical sensing`, in
  `SOURCE_RECOVERY_AND_INTERFACES.md`); `COMPONENT_ATTRIBUTION.md` references
  it instead of independently redefining it.
- **Retained, provenance stated exactly:** the MKA-firmware negative
  comparison (Phase 2H-B-style shallow-clone method, no execution) is
  confirmed architecturally unrelated to Loom's Klipper/Moonraker stack. That
  comparison read the archived bundle from its NAS-mounted path; see
  `SOURCE_RECOVERY_AND_INTERFACES.md` for the exact provenance statement.
- **New, conservative:** `can0`'s `rockchip_canfd` driver indicates a Rockchip
  SoC family host board; no specific model is inferred.
- **Local-workspace check only:** the owner-named
  `fibreseek-sk3-2.2.30.613.256.fibrepack` artifact is not present anywhere in
  this repository's Git working tree. Its exact naming convention and version
  number are independently confirmed in LM-008's already-captured log,
  materially raising its priority as a future ingestion/static-analysis target
  over the legacy MKA-firmware bundle. See `project/NEXT_HANDOFF.md`.

## Phase 2I-B offline password-recovery attempt and disassembly synthesis

The owner subsequently authorized offline password recovery against the six
ZipCrypto-encrypted nested archives. **Recovery did not succeed** —
full detail (what was attempted, in what order, and why further brute force
is not treated as reasonable) is in
`docs/firmware/FIRMWARE_ANALYSIS.md`. No password value is recorded
anywhere in this repository. Static disassembly of the two unencrypted,
un-stripped ELF binaries in each package (`anisotouch`, `fibreseek-installer`)
nonetheless resolved substantial architecture from the consumer side:

- **`mqtt_bridge`, previously totally unknown, is `STRONGLY INFERRED`** to
  report MQTT-broker connectivity status into AnisoTouch's cloud
  account-binding UI (`AccountBindingModel::onMqttBridgeStatusUpdate`,
  fed by a dedicated `MessageHandleTask` signal).
- **`remote`'s candidate purpose is now `STRONGLY INFERRED`** as remote/cloud
  print-job file transfer with progress reporting: a Moonraker agent-event
  signal is consumed by `RemoteTransferModel` (`startTransfer`,
  `onFileUploadProgress`, `finishTransfer`, `showTransferPopup`). Still not
  `CONFIRMED` — the actual `remote` source remains encrypted.
- **`ai_detection`'s configuration schema is `CONFIRMED`** field-for-field
  against `AIDetectorModel`'s sensitivity/enable setters.
- **The Sep 7 door/warning-dialog question (Phase 2H-D) is upgraded from
  `INFERRED (weak)` to `STRONGLY INFERRED`**: a dedicated, named
  `DoorDetectionWarning` signal runs from Moonraker message routing to a
  system-level UI warning in AnisoTouch, and `blinds_hall_monitor`'s
  configured `blinds_hall_sensor1`/`blinds_hall_sensor2` names match
  `SensorsModel::setBlindsSensor1`/`setBlindsSensor2` exactly. Still not
  `CONFIRMED`: the Moonraker-side trigger source is encrypted, and the
  `klippy.log` gap for 2026-09-07 still prevents timestamp correlation with
  the physical footage.
- **MCU firmware flashing is `CONFIRMED`**: `fibreseek-installer` runs
  Klipper's own `scripts/flashtool.py` against `~/klipper/out/{motherboard,
  toolhead,toolhead_can}.bin`, independently per board, with an explicit
  hardware-version-mismatch warning path. Hardware-revision selection
  (`printer_base_v1.1.cfg`–`v2.2.cfg`) is `CONFIRMED` driven by an ADC-based
  board-voltage read (`board_voltage::readBoardVoltage`), not a manual flag.
- **2.2.42's installer replaces process-killing with proper systemd service
  lifecycle management** (`stopAnisotouchForUpdate`, `setupAnisotouchService`,
  a transient-scope re-exec to avoid self-termination) — a `CONFIRMED`
  (symbol-table diff of unencrypted binaries), genuinely meaningful
  robustness improvement between releases.

## Phase 2I-A firmware static-analysis synthesis

The owner subsequently supplied both firmware/application packages named
above. Phase 2I-A analyzed them statically (never executed) — full detail in
`docs/firmware/FIRMWARE_ANALYSIS.md` and
`docs/firmware/VERSION_DIFF_2.2.30_TO_2.2.42.md`; per-component
attribution updates are in `SOURCE_RECOVERY_AND_INTERFACES.md` and
`COMPONENT_ATTRIBUTION.md`. Architectural conclusions:

- The `.fibrepack` is an ordinary ZIP wrapping six further, genuinely
  ZipCrypto-encrypted nested archives (Moonraker, Klipper, printer config,
  crowsnest, the AI service, and the `remote` agent's package). No password
  is present in either release; none was searched for or used. This resolves
  every one of the twelve previously unattributed modules' **exact file
  path** (plus two more discovered by filename alone:
  `aniso_temp_compensation.py`, `error_indexer_plugin_debug_tool.py`), while
  leaving all source **content** exactly as unresolved as Phase 2H-C left it.
- **FibreTouch/AnisoTouch is a native Qt/QML application** (not Electron, not
  a web app), holding its own direct WebSocket JSON-RPC connection to
  Moonraker, separate from the `remote` agent. It reads `ai_detection`'s
  configuration back from Moonraker via a QML `AIDetectorModel`.
- **`remote` is confirmed absent from Moonraker's component list**, and its
  leading candidate implementation (`fibretouch-remote.zip`'s
  `moonraker_broker_bridge.py`) is a standalone package, not a Moonraker
  plugin — consistent with its live self-identification as an external
  WebSocket agent.
- **A new AI architecture layer was discovered**: `fibretouch-ai.zip` ships a
  YOLOv11-based, Rockchip-NPU-accelerated object/defect-detection pipeline
  (`ai_server.py`, the most likely peer of `ai_detection`'s confirmed
  `ws://127.0.0.1:8765` connection), plus a previously undocumented
  sentence-transformer/FAISS semantic error-search subsystem, architecturally
  distinct from the Moonraker `error_indexer` component's XLSX lookup.
- **`can0` is architecturally explained** as boot-time infrastructure for an
  alternate, CAN-based toolhead-MCU connection mode (`toolhead_can.cfg` +
  a third MCU firmware/build target) that Loom's specific unit does not use
  (Loom's live capture confirms serial-only MCU sections). Its consumer, if
  any, on Loom specifically remains `UNKNOWN`.
- **Multiple hardware revisions are supported from one release**:
  `anisotouch-config.zip` ships per-revision base configs (`v1.1` through
  `v2.2`) with matching fan/servo/piezo/filament-sensor overrides — previously
  invisible from Loom's live API, which only exposes the merged, effective
  configuration, not the underlying file/include structure.
- **New, previously undocumented hardware/software elements**: a
  piezoelectric-ceramic subsystem (`piezoelectric_ceramic*.cfg`, purpose
  unknown), an eddy-current probe option (`eddy.cfg`), a physical status LED
  (`led_user`), and (2.2.42 only) an `enclosure_temp_monitor.py` Moonraker
  component plausibly related to `blinds_hall_monitor`'s domain, and a
  `bed_temp_linearity` Klipper extra.
- **A real, documented robustness fix exists between releases**: 2.2.42 adds
  `disable_system_update_prompt.sh`, explicitly written (per its own comment)
  to stop Ubuntu's unattended OS upgrades from disrupting the Klipper
  environment — Loom, still on 2.2.30.613, does not have this fix.
