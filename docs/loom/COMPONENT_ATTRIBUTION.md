# Loom Component Attribution

## Scope and comparison boundary

Phase 2H-B combines the already captured configuration (LM-005 through LM-007)
with three passive captures: Moonraker's log (LM-008), Klipper's log (LM-009),
and the registered G-code help catalogue (LM-010). No registered command or
extension method was invoked.

For lineage comparison only, the official Klipper repository
(`https://github.com/Klipper3d/klipper`) at commit
`8c29c0a8e205d897f765ce867b983e009cbe32a1` and official Moonraker repository
(`https://github.com/Arksine/moonraker`) at commit
`985c1d0bbeb90bc057d34a232c9dc3b05e0c6c8d` were shallow-cloned to temporary
local storage and inspected without execution. Absence from those snapshots
means only “not present by the same module filename in this comparison.” It
does not prove original authorship, license, or the absence of an earlier or
renamed upstream implementation.

## Moonraker components

Moonraker's standard loader imports configured component `NAME` as
`moonraker.components.NAME` and calls its `load_component` entry point. The
captured launch tree and logger filenames therefore support the locations below.
The checkout root is `/home/anisoprint/moonraker`; the standard candidate path
for each component is
`/home/anisoprint/moonraker/moonraker/components/<name>.py`.

| Component | Registration and implementation evidence | Observed state | Attribution and interface boundary |
|---|---|---|---|
| `printer_setting` | Loaded through the normal Moonraker component loader; standard module location is **STRONGLY INFERRED** as `moonraker/components/printer_setting.py`. It has no explicit original config section and uses defaults. | **CONFIRMED loaded** and post-initialized during the captured startup. | Filename absent from the compared official Moonraker snapshot. Author, version, schema beyond the effective LM-006 values, routes, and dependencies are **UNKNOWN**. |
| `material_manager` | Logger identifies `material_manager.py`; normal `load_component` registration. LM-006 configures `enable: true`. | **CONFIRMED loaded**, initialized successfully, and observed handling cancelled-job metadata including separate E/U/V material usage fields. | Filename absent upstream. This is runtime integration evidence, not proof of vendor authorship. Routes and version are **UNKNOWN**. |
| `mqtt_bridge` | Logger identifies `mqtt_bridge.py`; normal component registration. LM-006 exposes a bind-timeout setting. | **CONFIRMED loaded**, initialized, and post-initialized. No publish, subscription, broker connection, or message was observed or initiated. | Filename absent upstream; distinct from upstream `mqtt.py`. Package author, version, broker relationship, route surface, and current connectivity are **UNKNOWN**. |
| `ai_detection` | Logger identifies `ai_detection.py`; normal component registration. It loads settings from Moonraker's database and is configured as a client of a host-local WebSocket service. | **CONFIRMED loaded** and post-initialized. Repeated connection refusals were followed later in the captured log by a successful local connection, so health varied during the log window. | Filename absent upstream. It depends on a local companion WebSocket service; package author/version and HTTP/remote methods are **UNKNOWN**. |
| `error_indexer` | LM-008 gives the exact module path under Moonraker's component directory and an XLSX data dependency. The component loaded 74 standard error rows, 13 AI-error rows, and 10 common terms. | **CONFIRMED loaded**, post-initialized in `en-US`, and observed consuming AI connection errors and Klipper responses to create notifications. | Filename absent upstream. Exact module version, author, route surface, and full schema are **UNKNOWN**. |

The configured `maintenance` component is **CONFIRMED failed to load** because
the module `moonraker.components.maintenance` was missing. This explains the
unparsed configuration warning; it does not establish the intended component's
origin or effect.

The application firmware reports version `2.2.30.613`. Update metadata reports
a configured repository identity that differs from the detected repository
identity and shows a newer advertised remote version. This confirms a
FibreTouch/FibreSeek integration and a repository-identity mismatch, but not
the authorship of each component. No update action or remote update URL was
called.

## `remote` extension agent

### CONFIRMED

- LM-007 reports one connected Moonraker extension agent named `remote`, version
  `1.0.0`, type `agent`, with a self-advertised FibreSeek application URL.
- LM-008 records an inbound host-local WebSocket identifying itself with those
  same values. The connection appears about two seconds after `ai_detection`
  successfully connects to its separate host-local WebSocket service.
- No extension method was invoked. Neither capture exposes a method catalogue,
  registration file, process name, package path, or permission list.

### STRONGLY INFERRED

The local connection, vendor URL, name, and adjacent remote-print/update
vocabulary make `remote` a vendor/integrator companion associated with the HMI,
remote, or cloud-facing application layer. The timing alone does not prove it
is the AI service or that it contacts the cloud.

### UNKNOWN

Its implementation location, startup unit/process, code origin, dependencies,
advertised methods, authorization model, and present health beyond the logged
connection remain unknown. Calling or probing it is outside this phase.

## Custom Klipper modules

Klipper's standard loader maps a configuration section's first word to an
`extras/<name>.py` module, which normally provides `load_config` or
`load_config_prefix`. Runtime logger filenames directly confirm six module
filenames; `aniso_bed_mesh.py` is **INFERRED** from the standard loader because
no corresponding logger line was found. All seven filenames are absent from
the compared official Klipper snapshot. The captured checkout root is
`/home/anisoprint/klipper`, so standard module paths are
`/home/anisoprint/klipper/klippy/extras/<name>.py`.

| Config object | Source/registration evidence | Parameters and hardware dependencies | Registered commands and safety |
|---|---|---|---|
| `blinds_hall_monitor` | **CONFIRMED** logger `blinds_hall_monitor.py`; standard module registration. Ready logs report sensor initialization and repeated heater/Hall monitoring. | Timeouts, polling interval, and temperature tolerance; depends on configured blind Hall sensors and heater state. | No uniquely attributable command was recovered. Monitoring is observational; its reactions remain **UNKNOWN**. |
| `extruder_stall_detector extruder` | **CONFIRMED** logger `extruder_stall_detector.py`; prefix-style object registration. Ready log associates it with an extruder and TMC driver. | Extruder name, sampling/filter thresholds, StallGuard and SG-monitor flags; depends on extruder/TMC telemetry. | `QUERY_EXTRUDER_STALL` is **passive/read-only**. `SET_EXTRUDER_STALL_DETECTION` is **mutating**. `TEST_STALL_DETECTION` is **ambiguous** despite saying it simulates a stall; none was invoked. |
| `load_unload` | **CONFIRMED** logger `load_unload.py`; standard module registration and historical command-handler logs. | Empty config section; runtime logs show print-state coordination and E/U/V material accounting. | Load/unload, continue, prepare, finish, exit, and print-state commands are **dangerous/physical** or **mutating**. |
| `tension_sensor` | **CONFIRMED** logger `tension_sensor.py`; standard module registration. | Jam-deviation and consecutive-sample settings; opens host SPI device `spidev0.0` at 1 MHz. | `TENSION_SHOW_CONFIG` is **passive/read-only**. Poll/start/pause/resume, threshold/consecutive setters, and baseline update are **mutating**; baseline capture may sample hardware. |
| `aniso_bed_mesh` | Source filename **INFERRED** as `aniso_bed_mesh.py` from the standard loader; no direct logger line. | Toolhead ADC and trigger pins. | Output/map are **passive/read-only**; clear/offset/profile are **mutating**; range check is **likely read-only** but unverified; verify and calibrate are **dangerous/physical**. |
| `xyz_align` | **CONFIRMED** logger `xyz_align.py`; standard module registration. Logs show offset-file loading and ready initialization. | Sensor pin, T0/T1 offsets, motion offsets, and speed; depends on motion and alignment sensor hardware. | `XYZ_ALIGN_NEW` and test macros are **dangerous/physical**. Its generic help text does not document preconditions. |
| `ws2812b_spi` | **CONFIRMED** logger `ws2812b_spi.py`; standard module registration. | Empty config section; runtime logs identify LED color/mode handling. | `M2000` changes LED state and is **mutating**. |

“Loaded,” “registered,” “observed in a historical handler log,” and “healthy”
are deliberately separate. None of the commands above was called in Phase
2H-B, and their physical outcomes are not confirmed by names or descriptions.

## Interface safety inventory

LM-010 contains 241 registered command descriptions. The following subset is
attributable to the custom candidates or material to the safety boundary:

| Interface group | Classification | Basis |
|---|---|---|
| `QUERY_EXTRUDER_STALL`, `TENSION_SHOW_CONFIG`, `BED_MESH_OUTPUT`, `BED_MESH_MAP`, `QUERY_FILAMENT_SENSOR` | passive/read-only | Descriptions explicitly query, show, retrieve, serialize, or report existing state. |
| `BED_MESH_CHECK_RANGE` | likely read-only | Description says it checks the stored/probed range and may raise an error; source was not recovered. Not invoked. |
| `TEST_STALL_DETECTION` | ambiguous | Description says it simulates conditions, but runtime side effects are not established. |
| Tension polling/detection/settings; sensor enable/debounce/detection length; mesh clear/offset/profile; `M2000` | mutating | Descriptions change runtime state, thresholds, mesh state, or LEDs. |
| `TENSION_UPDATE_BASELINE` | mutating/physical sensing — canonical classification in `SOURCE_RECOVERY_AND_INTERFACES.md`, referenced here rather than redefined | Samples SPI hardware directly and updates a stored baseline value; this is more specific than a bare "mutating" bucket. |
| Load/unload workflow, `BED_MESH_VERIFY`, `BED_MESH_CALIBRATE`, `XYZ_ALIGN_NEW` and alignment tests | dangerous/physical | Descriptions or known macro bodies involve heating, extrusion, probing, or motion. |

No custom Moonraker HTTP route or extension remote method was revealed by the
three captures. Their route semantics remain **UNKNOWN**, so none was guessed or
tested.

## MCU, CAN, and application map

- LM-009 confirms two loaded MCU firmware builds with the same vendor build
  base `v2.2.20.515-34-g2093130b`; the main MCU exposes 126 commands and the
  toolhead MCU 135. Their build timestamps differ by 14 seconds. Klipper's Git
  version remains `?`.
- Both MCU configuration entries still use serial-device paths, not Klipper
  CAN UUIDs. No evidence links host `can0` to either MCU.
- **STRONGLY INFERRED architecture:** Moonraker loads vendor components in its
  Python component namespace; Klipper loads custom hardware/workflow modules in
   its `extras` namespace; a host-local companion connects through WebSockets;
  HMI/remote/cloud-facing functions sit above this local layer. The exact
  process/service boundaries and MQTT/cloud flows remain unknown.
- No CAN query, shell access, process inspection, service-unit inspection,
  MQTT publication, external infrastructure probe, or physical action occurred.

## Next safe evidence step

Acquire the exact vendor source trees or packaged source files through an
owner-approved, read-only static export, then compare module contents and route
registrations offline. Until source is available, do not guess component routes,
invoke `remote`, or treat configured/loaded components as fully healthy.

## Phase 2H-C source-access result

LM-011 directly confirms that Moonraker exposes seven registered file roots,
none of which is the Moonraker component directory or Klipper extras directory.
No target source file was therefore recoverable through the
established passive file API. `SOURCE_RECOVERY_AND_INTERFACES.md` records the
complete access-boundary result, deeper logger-method inventory, standard
extension interfaces, dependency graph, and next safe static-export protocol.

This does not change the Phase 2H-B path classifications: `error_indexer.py`
remains directly located by its own log; the other component/module paths remain
strongly inferred or inferred from loader and checkout evidence until their
bytes are recovered.

## Phase 2I-A firmware static-analysis update

Two owner-supplied official `.fibrepack` packages were statically analyzed
(full detail in `docs/firmware/FIRMWARE_ANALYSIS.md`). This upgrades
several path-level attributions in the table above from `STRONGLY INFERRED`
to `CONFIRMED` and corrects one structural assumption, all via ZIP
central-directory filenames only (the file content itself remains ZipCrypto-
encrypted and unread):

- `printer_setting.py`, `mqtt_bridge.py`, `ai_detection.py`,
  `error_indexer.py` module paths: **CONFIRMED**.
- `material_manager`: **corrected** — it is
  `moonraker/components/material_manager/material_manager.py` inside a
  package with its own `__init__.py`, not a flat `material_manager.py`
  module as previously inferred.
- `aniso_bed_mesh.py`: path **upgraded to CONFIRMED** (previously inferred
  only from the standard section loader, no direct logger line); it also has
  MCU-side C source (`src/aniso_bed_mesh.c/.h`), as does `xyz_align`
  (`src/stm32/xyz_align.c`) — both previously host-Python-only in this
  document.
- `remote`: **confirmed absent** from the full Moonraker component list (160
  entries), closing that question definitively. The leading candidate
  implementation is `fibretouch-remote.zip`'s `moonraker_broker_bridge.py`
  (STRONGLY INFERRED, not confirmed; content encrypted).
- `can0` nominal bitrate (1,000,000 bit/s) and `txqueuelen` (1024): both
  **CONFIRMED** by source (`klipper.config`'s `CONFIG_CANBUS_FREQUENCY` and
  a boot script's literal `ip link` commands), previously only
  `STRONGLY INFERRED`/live-observed.
- Two additional custom modules discovered by filename, not in this
  document's original scope: `klippy/extras/aniso_temp_compensation.py` and
  `error_indexer_plugin_debug_tool.py`.

None of the "Attribution and interface boundary" / "Remaining source-level
unknowns" cells above change substantively: exact routes, imports, classes,
schemas, and versions remain `UNKNOWN` because the actual file bytes are
encrypted and no password was searched for or used.

## Phase 2I-B update

An owner-authorized offline password-recovery attempt against the six
ZipCrypto-encrypted archives did not succeed (full detail in
`docs/firmware/FIRMWARE_ANALYSIS.md` and
`docs/loom/SOURCE_RECOVERY_AND_INTERFACES.md`'s Phase 2I-B section);
no password value is recorded anywhere in this repository. Static
disassembly of the unencrypted `anisotouch`/`fibreseek-installer` binaries
nonetheless upgraded three rows in this document's tables from the
consumer side:

- `mqtt_bridge`: purpose upgraded `UNKNOWN` → `STRONGLY INFERRED` (wired to
  AnisoTouch's cloud account-binding status display).
- `ai_detection`: configuration schema upgraded to `CONFIRMED` field-for-
  field against `AIDetectorModel`'s setters.
- `remote`: candidate purpose upgraded to `STRONGLY INFERRED` (remote/cloud
  print-job file transfer with progress reporting, via a Moonraker
  agent-event signal consumed by `RemoteTransferModel`).

Exact routes, imports, classes, and full schemas for all five components
remain `UNKNOWN` — this update is entirely from the consumer (AnisoTouch)
side, not from decrypting the component source itself.

## Phase 2H-D reconciliation note

Phase 2H-D re-read LM-008 and corrected one overstated claim: `material_manager`
is confirmed to run a named update operation (`update_filament_used`) that logs
per-field job/material values, but no line in its own log names a database,
file, or other persistence target — unlike `ai_detection` and Moonraker's own
`update_manager`, both of which do. The exact evidence and corrected wording
are canonical in `SOURCE_RECOVERY_AND_INTERFACES.md`'s Moonraker component map;
this file's own `material_manager` row above was already scoped to "handling
cancelled-job metadata" and did not itself require correction.
