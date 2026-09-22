# Loom Passive Source Recovery and Interface Map

## Scope and outcome

Phase 2H-C attempted to replace module-path inference with byte-exact source
evidence through already authorized, passive mechanisms. It reused LM-001 through
LM-010 and issued one documented read-only request, LM-011, for Moonraker's
registered file roots. No source body was recovered: the source checkouts are
outside all exposed file-manager roots, and no previously established shell or
filesystem channel exists.

This is an access-boundary result, not evidence that the files are absent. No
SSH connection, path traversal, guessed URL, external/vendor repository access,
package download, privilege escalation, extension call, G-code, or service or
machine action was attempted.

## Exact source-recovery result

LM-011 confirms these registered file roots: `config`, `logs`, `gcodes`, `usb`,
`timelapse`, `timelapse_frames`, and `config_examples`. Their returned
permissions are read-only except `gcodes`, `usb`, and `timelapse`, which the
server labels read/write. Neither requested implementation directory is
registered; `config_examples` exposes only Klipper's configuration-example
subdirectory. The recorded
official Moonraker implementation also constrains file requests to registered
roots and rejects paths escaping the selected root. Bypassing that boundary
would be exploitation and is prohibited.

### Source files recovered

None.

### Source files not accessible through the established passive channel

Moonraker:

- `/home/anisoprint/moonraker/moonraker/components/printer_setting.py`
- `/home/anisoprint/moonraker/moonraker/components/material_manager.py`
- `/home/anisoprint/moonraker/moonraker/components/mqtt_bridge.py`
- `/home/anisoprint/moonraker/moonraker/components/ai_detection.py`
- `/home/anisoprint/moonraker/moonraker/components/error_indexer.py`

Klipper:

- `/home/anisoprint/klipper/klippy/extras/blinds_hall_monitor.py`
- `/home/anisoprint/klipper/klippy/extras/extruder_stall_detector.py`
- `/home/anisoprint/klipper/klippy/extras/load_unload.py`
- `/home/anisoprint/klipper/klippy/extras/tension_sensor.py`
- `/home/anisoprint/klipper/klippy/extras/aniso_bed_mesh.py`
- `/home/anisoprint/klipper/klippy/extras/xyz_align.py`
- `/home/anisoprint/klipper/klippy/extras/ws2812b_spi.py`

All implementation-level conclusions below are therefore bounded to parsed
configuration, command descriptions, runtime logger/method names, and the
recorded official upstream loader/extension infrastructure. Imports, class
names, complete event registration, source ancestry, authentication checks,
and hidden interfaces remain unknown unless explicitly stated.

## Moonraker component map

| Component | Direct runtime/config evidence | Interfaces and data dependencies | Remaining source-level unknowns |
|---|---|---|---|
| `printer_setting` | Loaded and post-initialized; effective configuration is empty/default. | No custom route, event, file, database, subprocess, or network operation is exposed by current evidence. | Source body, imports, class, schema, version, and all callable methods. |
| `material_manager` | `material_manager.py` logger; initialized successfully; its `update_filament_used` method logs one line per field after a job ends (`Job updated with status 'cancelled': filename = ...` through `... state = standby`, LM-008). Configured `enabled` with a printer-config path. | **CONFIRMED** it runs a named update operation (`update_filament_used`) and logs per-field job/material values on job completion/cancellation. **Corrected in Phase 2H-D:** persistence is **STRONGLY INFERRED at most**, not confirmed — unlike `ai_detection` (`_load_config_from_database`) and Moonraker's own `update_manager` (`database.py _handle_data_changed_event`, both LM-008), no line in `material_manager`'s own log names a database, file, or other persistence target. Phase 2H-B's original "CONFIRMED write/update semantics" wording overstated this. | Persistence mechanism/target, exact event names, database namespace, routes, HMI notifications, imports, and version. |
| `mqtt_bridge` | `mqtt_bridge.py` logger; loaded and initialized; one bind-timeout configuration key. | MQTT bridging is implied by name only. No broker, topic, subscription, publication, socket, credential, or external destination was observed. | Entire route/topic/schema/authentication/dependency surface and current connection state. |
| `ai_detection` | `ai_detection.py` logger; database-backed configuration; host-local WebSocket client; reconnect, request-timeout, detection interval and sensitivity/enable settings; connect/refuse/read-loop/close lifecycle. | **CONFIRMED network client** to a local WebSocket service. Configuration mutation or detection requests may exist but are not exposed. Errors feed `error_indexer`. | Protocol messages, callable routes, outbound data contents, process at the peer, camera/HMI flow, external destinations, credentials, and version. |
| `error_indexer` | Exact Python path; `error_indexer.py` logger; spreadsheet path and sheet names; loads standard, AI, and common-term tables; language from database; handles G-code responses and AI errors. | **CONFIRMED local file read**, database read, G-code-response event consumption, error processing, and notification production. | Notification names/payloads, route surface, database namespace details, spreadsheet parser/imports, mutation behavior, and version. |

No source-backed custom HTTP, WebSocket, or remote-method registration was
recovered for these components. Their unknown routes must not be guessed.

## Klipper custom-module map

| Object/module | Direct configuration/runtime evidence | Registered interfaces and classification | Hardware, persistence, and safety boundary |
|---|---|---|---|
| `blinds_hall_monitor` | Configures two 600-second timeouts, 0.5-second polling, and 8 C tolerance. Logger methods include ready, heater checking, monitor-stop, door-monitor-stop, cooling-delay, and cooling-fan callback. | No uniquely attributable G-code command is exposed. Internal monitoring is observational; automatic reactions are **UNKNOWN**. | Depends on heater state, blind/door Hall sensors, and a cooling fan. Source is needed to determine whether callbacks command hardware. |
| `extruder_stall_detector extruder` | Configures extruder/TMC selection, sample/filter/stall/SG thresholds, StallGuard off and SG monitoring on. Ready and not-printing event handlers are logged. | `QUERY_EXTRUDER_STALL`: **passive/read-only**. `SET_EXTRUDER_STALL_DETECTION`: **mutating**. `TEST_STALL_DETECTION`: **ambiguous**. | Reads extruder/TMC telemetry and stops polling outside printing. Exact event registrations, state machine, false-positive handling, and any pause behavior are unknown. |
| `load_unload` | Empty section; logger exposes preparation, temperature timer, idle-timeout extension/restoration, print-state synchronization, sensor-debounce restoration, and load/preparation command handlers. Historical logs show homing checks, hotend selection, temperature waiting, tool selection, and motion-macro calls. | `LOAD_FILAMENT`, `UNLOAD_FILAMENT`, `CONTINUE_LOAD`, `PREPARE_LOAD_UNLOAD_NOZZLE`, and `FINISH_LOADUNLOAD`: **dangerous/physical**. `EXIT_LOADUNLOAD` and `SET_PRINT_LOAD_UNLOAD_STATE`: at least **mutating**. | Coordinates heaters, extrusion, motion/tool macros, filament sensors, idle timeout, and `print_stats`. Historical handler logs prove implementation capability, not Phase 2H-C execution. Error cleanup and all preconditions require source. |
| `tension_sensor` | Configures jam deviation and trigger count. Logger confirms direct host SPI open/close on `spidev0.0`, mode 0, 1 MHz. | `TENSION_SHOW_CONFIG`: **passive/read-only**. Poll/start/pause/resume and threshold/count setters: **mutating**. `TENSION_UPDATE_BASELINE`: **mutating/physical sensing**. | Host-side SPI dependency is confirmed. Sampling units, baseline persistence, jam/tangle events, automatic printer reactions, and MCU involvement are unknown. |
| `aniso_bed_mesh` | Configures a toolhead ADC pin and trigger pin. Source filename remains inferred through the standard loader. | `BED_MESH_OUTPUT`, `BED_MESH_MAP`: **passive/read-only**. `BED_MESH_CHECK_RANGE`: **likely read-only**. Clear/offset/profile: **mutating**. Verify/calibrate: **dangerous/physical**. | Toolhead ADC/trigger hardware and probing are implicated. Relationship to upstream bed mesh, persistence, error limits, and registered entry point remain unknown. |
| `xyz_align` | Configures a sensor pin, T0/T1 coordinates, motion offsets, and speed. Logger confirms loading `xyz_offset.ini`. | `XYZ_ALIGN_NEW` and related test macros: **dangerous/physical**. | Depends on motion, homing state, and alignment sensor. File loading is confirmed; whether or when it writes offsets is unknown. |
| `ws2812b_spi` | Empty section; logger exposes `cmd_M2000`, timer creation/cancellation, mode, state, and RGB values. | `M2000`: **mutating**, because it changes LED state and timers. | SPI/LED output is strongly inferred. Bus/device, persistence, startup defaults, and MCU versus host transport remain unknown. |

None of these commands was invoked. Descriptions and historical logs do not
establish that a command is safe to run on the current machine.

`TENSION_UPDATE_BASELINE`'s classification of **mutating/physical sensing** in
the table above is canonical. `COMPONENT_ATTRIBUTION.md`'s interface-safety
table references this classification rather than independently redefining it
(Phase 2H-D reconciliation).

## Standard Moonraker extension infrastructure and `remote`

The recorded official Moonraker snapshot provides a comparison model that is
consistent with Loom's observed agent registration:

| Standard interface | Transport/method | Classification | Evidence boundary |
|---|---|---|---|
| `/server/extensions/list` | HTTP/JSON-RPC GET | passive/read-only | Invoked in LM-007; returns connected agents' self-identification, not methods. |
| `/server/connection/identify` | WebSocket POST-equivalent | mutating registration | Used by clients to identify and become an agent. Observed indirectly in the log; not invoked by this work. |
| `/connection/register_remote_method` | agent WebSocket POST-equivalent | mutating registration | Dynamically registers a method with the Klipper connection in the recorded upstream implementation. No `remote` method names were recovered. |
| `/connection/send_event` | agent WebSocket POST-equivalent | mutating/event-producing | Restricted by the recorded implementation to agent connections; not invoked. |
| `/server/extensions/request` | HTTP/JSON-RPC POST | ambiguous proxy to agent | Calls an agent-supplied method. Side effects depend on the unknown method; prohibited. |

Loom evidence confirms only that `remote` identified over a host-local
WebSocket as an agent, version `1.0.0`, with a FibreSeek application URL. No
process name, command line, service definition, executable, package path,
startup script, configuration file, Unix socket use, registered method name, or
permission set is exposed. Its relationship to FibreTouch/HMI and remote/cloud
functionality remains **STRONGLY INFERRED**, not confirmed.

## Evidence-backed dependency graph

Legend: solid arrows are **CONFIRMED** data/control relationships in the
captures; dashed arrows are **STRONGLY INFERRED** integration relationships;
question-mark labels are **UNKNOWN**.

```text
FibreTouch / HMI ............................... [CONFIRMED versioned app]
        :
        : vendor integration [STRONGLY INFERRED]
        v
remote agent --local WebSocket identification--> Moonraker
        |                                          |
        | external/cloud destination? [UNKNOWN]    +--> material_manager
        |                                          |      `-- job/material metadata
        |                                          +--> error_indexer
        |                                          |      +-- XLSX error tables
        |                                          |      `-- notifications
        |                                          +--> ai_detection
        |                                          |      `-- local WebSocket AI service
        |                                          +--> mqtt_bridge
        |                                          |      `-- broker/topics? [UNKNOWN]
        |                                          `--> printer_setting
        |                                                 `-- behavior? [UNKNOWN]
        v
external/cloud boundary [UNKNOWN; not contacted]

Moonraker --Klippy connection--> Klipper
                                  +--> load_unload --> motion/heaters/extruders/sensors
                                  +--> tension_sensor --> host SPI
                                  +--> extruder_stall_detector --> extruder/TMC telemetry
                                  +--> blinds_hall_monitor --> Hall/heater/fan state
                                  +--> aniso_bed_mesh --> toolhead ADC/trigger
                                  +--> xyz_align --> motion/alignment sensor/offset file
                                  `--> ws2812b_spi --> LED state

Klipper --> main MCU [serial device]
        `-> toolhead MCU [serial device]

host can0 --> consumer? [UNKNOWN; no mapping to either MCU]
```

The graph does not assert that every application layer is a strict serial call
chain. Several components are peers inside Moonraker or Klipper, and the
FibreTouch-to-`remote` relationship remains inferred.

## Security-relevant observations

- From the trusted local client context, Moonraker exposes configuration, logs,
  registered commands, extension identity, and file-root metadata without an
  authentication credential. This is a LAN/trusted-client observation, not an
  internet-exposure test.
- Raw logs contain local paths, hardware/network identifiers, historical
  printer actions, and update metadata. They contain no nonempty credential
  found by the Phase 2H-B/2H-C review and remain confined to raw evidence.
- The file manager exposes three read/write roots, but Phase 2H-C used only the
  root-list GET and performed no file operation.
- Standard extension infrastructure can proxy arbitrary agent methods and can
  dynamically register remote methods. Because `remote` publishes no passive
  method catalogue in LM-007, its callable surface is an explicit **UNKNOWN**.
- The custom load/unload and alignment surfaces can coordinate motion, heating,
  extrusion, sensor state, or persistent offsets. Their presence is not
  authorization to invoke them.

## Phase 2H-D evidence synthesis and confidence reconciliation

Phase 2H-D issued zero new Loom requests, zero NAS requests, zero external/
cloud requests, and no G-code, extension call, or printer/machine action. It
re-read LM-005 through LM-011 (already captured) and the Sep 7 physical-
experiment record set (already captured) to correct one overstated claim,
resolve two proposed cross-document relationships, and reconcile one
classification drift.

### Update-manager identity reconciliation — CONFIRMED

LM-008's raw text directly ties `CONFIGURATION_DISCOVERY.md`'s two configured
sections to `COMPONENT_ATTRIBUTION.md`'s "repository identity mismatch" claim;
they are the same subsystem observed from configuration and from the log:

- Configured: `[update_manager fibreseek-updater]` with
  `repo = fibreseek/fibretouch-fs3` and
  `ota_manifest_url = https://ota.fibreseek3d.com/firmware/release_update.json`,
  plus a parallel `[update_manager fibreseek-updater-factory]` section.
- Logged: `Value at option 'repo: fibreseek/fibretouch-fs3' does not match
  detected repo 'shanghai-aneso/fibretouch-fs3', falling back to detected
  version.` This is the exact, directly quoted repository-identity mismatch;
  it is **CONFIRMED**, not inferred.
- Logged: a `database.py _handle_data_changed_event` record for namespace
  `update_manager`, record `fibreseek-updater`, with `version: 2.2.30.613`,
  `remote_version: 2.2.38.721`, and
  `dl_info: ['https://ota.fibreseek3d.com/firmware/fibreseek-sk3-2.2.38.721.295.fibrepack', ...]`.
- **CONFIRMED**: the tracked local `version` (`2.2.30.613`) is the same value
  LM-008 separately reports as the FibreTouch application version. The update
  package naming convention is directly evidenced as
  `fibreseek-sk3-<version>.<build>.fibrepack` over `https://ota.fibreseek3d.com/firmware/`.

### Door experiment / `blinds_hall_monitor` cross-evidence — primary 2H-D task

Evidence consulted: `blinds_hall_monitor` configuration (LM-005: 600.0 s
`state_change_timeout`/`recovery_timeout`, 0.5 s `check_interval`, 60.0 s
`cooling_fan_delay`, 8.0 C `temperature_tolerance`, 5.0 s `door_check_interval`);
LM-009 runtime logger lines; the `printed_door_detection` macro body (LM-005);
and the Sep 7 physical-experiment record (LX-004,
`experiments/Loom/2026-09-07/`).

**CONFIRMED:**
- `gcode_macro printed_door_detection` exists with body
  `M118 [PRINTED_DOOR_DETECTION] Close hatch to enable heater!` (LM-005).
- `blinds_hall_monitor` is a real, running module that reacts to the chamber
  heater being commanded off: LM-009 shows `M141/M191 S0` followed immediately
  by `_stop_monitoring`, `_stop_monitoring_loop`, `_stop_door_monitoring`, then
  `_start_cooling_fan_delay` ("Cooling fan timer started, will run for 60.0
  seconds") and `cooling_fan_timer_callback` ("Cooling fan stopped after 60.0
  seconds delay"). The logged 60.0 s duration matches the configured
  `cooling_fan_delay` exactly, which also confirms that field's unit is
  seconds.
- The captured `klippy.log` contains **no entries for 2026-09-07 at all**: its
  timestamps run 2026-06-16 through 2026-06-17, then jump to 2026-09-08/09.
  The five Sep 7 door/thermal videos are independently timestamped
  2026-09-07 16:06–17:36 (container creation times, LX-004). This means no
  currently captured log covers the exact window the physical experiment
  occurred in.

**STRONGLY INFERRED:**
- `blinds_hall_monitor` polls a door-related Hall sensor as part of its
  monitoring loop (its own logged method is literally
  `_stop_door_monitoring`), and the configured `filament_switch_sensor
  door_hall_sensor` (pin `!PE3`, `pause_on_runout: false`) is the most likely
  physical input, given naming and the module's declared dependency on
  "configured blind Hall sensors." No source text confirms this wiring.

**INFERRED (weak — functional/thematic match only, not call-site or
timestamp evidenced):**
- `printed_door_detection`'s text ("Close hatch to enable heater!") is a
  plausible functional match for the "door/top-cover warning dialogs" the
  owner observed on video after door-open events (LX-004). However, the only
  four occurrences of that macro's text in the captured log are Klipper's own
  startup config-dump echoes, not a runtime invocation line — there is no
  logged call to `PRINTED_DOOR_DETECTION`, and no configuration field (e.g. a
  `runout_gcode` on `door_hall_sensor`) names it as an automatic callback.
  Whether `blinds_hall_monitor` (or anything else) actually calls this macro
  is unresolved.

**UNKNOWN / EVIDENCE MISSING — the loop does not close:**
- Whether the physical warning dialogs the owner filmed on 2026-09-07 are this
  `M118` message, a separate FibreTouch-native UI warning, or something else
  entirely. This cannot be resolved from currently captured evidence at any
  confidence level above thematic plausibility, because the relevant log
  window (2026-09-07) does not exist in LM-009. `LX-004` and
  `experiments/Loom/2026-09-07/EVIDENCE_GAPS.md` already and correctly list
  "exact thermal recovery curves after door openings" and exact UI text as
  open gaps; this synthesis does not close them and does not upgrade any Sep 7
  physical observation to `CONFIRMED` or `STRONGLY INFERRED`.
- `blinds_hall_monitor`'s automatic reactions to a door-open event during
  active heating (does it cut the heater, only warn, or both?) remain
  unresolved; the recovered log excerpt shows behavior following a heater-off
  command, not behavior triggered by the door sensor itself.

If the owner has an archived Moonraker/Klipper log rotation that actually
covers 2026-09-07, supplying it would let this correlation be resolved without
any new Loom or NAS access; this is noted as a possible input to a future
phase, not a request to search for one now.

### `crowsnest` / `ai_detection` — evaluated conservatively, not elevated

`ai_detection` connects to `ws://127.0.0.1:8765` (LM-008, `AI Detection Client
configured: 127.0.0.1:8765`) and is loaded from Moonraker's database
(`_load_config_from_database`). No log line or configuration key names
`crowsnest` in relation to `ai_detection`, and `crowsnest` itself never appears
in `moonraker.log` except in the systemd service-name list — never with a port,
URL, or process reference. A raw WebSocket AI-inference port is also not
`crowsnest`'s typical transport (`crowsnest` conventionally serves an HTTP/MJPEG
stream, not a WebSocket). The two facts that a single-camera printer likely has
one physical camera, and that both components are camera-adjacent, do not by
themselves establish a shared feed. **Conclusion: this relationship remains
UNKNOWN, not `STRONGLY INFERRED` as an earlier draft proposed.** Resolving it
would require a passive metadata endpoint (e.g. a webcam-configuration query)
that has not yet been made, which is a future-phase decision, not a Phase 2H-D
action.

### MKA-firmware boundary — retained, provenance stated exactly

The MKA-firmware comparison referenced in the Phase 2H analysis preceding this
document **read the archived `AP-115` GPLv3 bundle from its NAS-mounted path**
(`<archive>/FibreSeeker-KB-Archive/originals/ANISOPRINT_OFFICIAL/AP-115/`),
via a read-only `git clone --bare` and text/log search — no execution, no
network fetch, no write back to the archive. This mirrors the no-execution
shallow-clone comparison method already used in Phase 2H-B against official
Klipper/Moonraker, and the artifact itself was already acquired, hashed, and
license-reviewed in Phase 2F-A; it was not a repo-local copy and not derived
solely from previously captured evidence. No further NAS access occurred in
Phase 2H-D itself. The result is retained because its provenance is a
precedented, read-only archival-analysis access, not a new live-system or
external contact:

- **CONFIRMED negative**: none of the twelve target filenames
  (`printer_setting.py`, `material_manager.py`, `mqtt_bridge.py`,
  `ai_detection.py`, `error_indexer.py`, `blinds_hall_monitor.py`,
  `extruder_stall_detector.py`, `load_unload.py`, `tension_sensor.py`,
  `aniso_bed_mesh.py`, `xyz_align.py`, `ws2812b_spi.py`) and no commit matching
  the MCU build fragment `2093130b` exist anywhere across all branches/tags of
  the bundle.
- **CONFIRMED architecturally unrelated**: the bundle's own `README.md` states
  it is "Firmware for Anisoprint Composer 3D printers, based on MK4duo 3D
  Printer Firmware" — a C++/Marlin-family firmware (511 `.h`, 111 `.cpp`, zero
  Python files) for the legacy Composer A3/A4 line, with no mention of
  "klipper" anywhere in its tree.
- **Not evidence of authorship** for Loom's Klipper/Moonraker layer, in either
  direction. `docs/firmware/` is currently an empty directory; no
  FibreSeek-specific firmware package has been archived there.

### Host SoC inference — kept conservative

`can0`'s reported driver, `rockchip_canfd` (LM-004), is public Linux kernel
information naming the onboard CAN-FD peripheral of a Rockchip SoC (the RK35xx
family uses this driver name). This is **STRONGLY INFERRED** evidence that
Loom's host board uses a Rockchip SoC family part. It does **not** identify a
specific board model, vendor, or revision — no DTS, `/proc/cpuinfo`, or board
label evidence has been captured, and none should be inferred from the driver
name alone. Host board and storage-device models remain `UNKNOWN / NEEDS
TESTING` as before.

### Official `.fibrepack` artifact — status and recommendation

The project owner named an official firmware artifact,
`fibreseek-sk3-2.2.30.613.256.fibrepack`. Checked against the repository/
current local Git working tree only (`docs/firmware/` is empty; no
filename match anywhere under this repository): **it is not present in the
repository.** No NAS or internet search was performed to locate it, per
instruction.

Independently, LM-008's already-captured log (see the update-manager
reconciliation above) shows the exact naming convention
`fibreseek-sk3-<version>.<build>.fibrepack` and the exact currently-installed
version number `2.2.30.613` that matches the artifact's filename precisely —
this is a **CONFIRMED** naming/version correspondence found in evidence already
in the repository, not a claim about the file's current location. This
materially raises the priority of ingesting this artifact over the legacy
MKA-firmware bundle: if it is FibreSeek's own SK3 application/firmware package
at the exact version Loom is running, static extraction could plausibly recover
byte-exact Moonraker component and Klipper extras sources that the file-manager
API boundary (Phase 2H-C) could not reach. Ingestion and static analysis of
this artifact is recommended as the leading candidate for a future phase; see
`project/NEXT_HANDOFF.md`.

## Phase 2I-A firmware static-analysis result

Phase 2I-A statically analyzed two owner-supplied official
`fibreseek-sk3-*.fibrepack` packages already placed in
`docs/firmware/`. This did not reopen Loom, the NAS, or any external
service; it is a separate, offline evidence channel from the live Moonraker
API boundary above. Full detail is in
`docs/firmware/FIRMWARE_ANALYSIS.md` and
`docs/firmware/VERSION_DIFF_2.2.30_TO_2.2.42.md`.

**The `.fibrepack` container itself is an ordinary ZIP** (not encrypted, not
signed at the outer level), so its central directory is fully readable. The
six proprietary payloads nested inside it — `moonraker.zip`, `klipper.zip`,
`anisotouch-config.zip`, `crowsnest.zip`, `fibretouch-ai.zip`,
`fibretouch-remote.zip` — are **genuinely ZipCrypto password-encrypted**, and
no password is present in either package. This phase did not search for,
guess, or use one. **A ZIP's central directory lists filenames even for
encrypted entries**, so exact file paths are readable without a password even
though file content is not.

### Exact-path result for all twelve targets

All twelve previously unresolved implementations exist at the exact expected
paths, confirmed by direct inspection of the ZIP central directory:

- `moonraker/components/printer_setting.py`, `mqtt_bridge.py`,
  `ai_detection.py`, `error_indexer.py` — path now **CONFIRMED** (previously
  `STRONGLY INFERRED` from the loader mechanism alone).
- `moonraker/components/material_manager/` — **corrected**: it is a package
  (`__init__.py` + `material_manager.py`), not the flat single-file module
  previously assumed.
- `klippy/extras/blinds_hall_monitor.py`, `extruder_stall_detector.py`,
  `load_unload.py`, `tension_sensor.py`, `xyz_align.py`, `ws2812b_spi.py` —
  reconfirmed at the exact paths already established from `LM-009` logger
  evidence.
- `klippy/extras/aniso_bed_mesh.py` — path **upgraded from `INFERRED` to
  `CONFIRMED`** (it had no direct logger line in `LM-009`); also has
  MCU-firmware-side C source (`src/aniso_bed_mesh.c/.h`), a new finding.
  `xyz_align` likewise has MCU-side C source (`src/stm32/xyz_align.c`).

**Two more custom modules were discovered by filename that were not in the
original twelve**: `klippy/extras/aniso_temp_compensation.py` (new custom
Klipper extra, purpose unknown beyond its name) and
`error_indexer_plugin_debug_tool.py` (a companion debug tool for
`error_indexer`, at the Moonraker checkout root).

**This does not recover any source content.** Imports, classes, registered
routes, event names, and all other implementation-level facts remain
`UNKNOWN` behind the ZipCrypto boundary — the "Source files recovered: None"
result for the *live Moonraker file-manager API* (Phase 2H-C) is unchanged;
this is a separate, offline static-package channel that resolves file
*existence and exact path* but not *content*.

### `remote` agent — new attribution

`remote` is **exhaustively confirmed absent** from `moonraker.zip`'s full
160-entry component listing, closing the "is `remote` a Moonraker component"
question definitively (previously only inferred from live API absence).
`fibretouch-remote.zip` — a 5-entry, encrypted, standalone package containing
`my_logger.py`, `moonraker_broker_bridge.py` (108,274 bytes),
`configs/factory_config.json`, and `configs/user_default_config.json` — is
the leading candidate implementation, based on naming and structural
correspondence to every other custom component's pattern (own logger module).
This is `STRONGLY INFERRED`, not confirmed; content is encrypted.

### `can0` and CAN bitrate — upgraded

`klipper.config`'s `CONFIG_CANBUS_FREQUENCY=1000000` and
`fibretouch-scripts/set_USB3.0_OTG_to_host_mode.sh`'s boot-time
`config_can0()` function (`ip link set can0 type can bitrate 1000000
restart-ms 100`, `txqueuelen 1024`) **CONFIRM** (source evidence) the exact
values `LM-004` observed live, previously only `STRONGLY INFERRED`.
`klipper.zip` ships a third MCU target, `toolhead_can` (firmware binary and
Kconfig), and `anisotouch-config.zip` ships a matching `toolhead_can.cfg`
alongside the `toolhead.cfg` Loom actually uses (serial, confirmed live).
`can0`'s architectural purpose is now `STRONGLY INFERRED` as support for this
alternate, not-selected-on-Loom CAN-based toolhead connection mode; its
consumer (if any) on Loom specifically remains `UNKNOWN`.

## Phase 2I-B — offline password-recovery attempt and disassembly-based reconstruction

Phase 2I-B was explicitly owner-authorized to attempt offline password
recovery against the six ZipCrypto-encrypted nested archives, using only
already-local material and already-installed tools. **Recovery did not
succeed.** Full detail, including exactly what was attempted (static
string/disassembly analysis, a 1,785-candidate targeted dictionary, and a
full 6-digit numeric brute force against all six archives) and why an
unbounded further brute force is not treated as reasonable here, is in
`docs/firmware/FIRMWARE_ANALYSIS.md`'s Phase 2I-B section. No
password value is recorded anywhere in this repository.

Despite that, static disassembly of the **unencrypted, un-stripped**
`anisotouch` and `fibreseek-installer` ELF binaries recovered substantial new
architecture evidence with no decryption required, because these binaries'
compiled C++ symbol tables reveal what each program *consumes from* or
*sends to* the still-encrypted components:

- **`mqtt_bridge`**'s purpose, previously entirely unknown, is now
  `STRONGLY INFERRED`: it is wired to AnisoTouch's cloud account-binding
  feature (`MessageHandleTask::sigNotifyMqttBridgeStatusUpdate` →
  `AccountBindingModel::onMqttBridgeStatusUpdate`).
- **`remote`**'s purpose gains its strongest evidence yet, `STRONGLY
  INFERRED` (not `CONFIRMED`): a Moonraker agent-event signal
  (`MessageHandleTask::sigAgentEvent`) is consumed by
  `RemoteTransferModel`, whose methods (`startTransfer`,
  `onFileUploadProgress`, `finishTransfer`, `cancelTransfer`,
  `showTransferPopup`) point to remote/cloud print-job file transfer with
  progress reporting as its most plausible primary function.
- **`ai_detection`**'s configuration schema is now `CONFIRMED` field-for-field
  against `AIDetectorModel`'s setters (`setFloorSensitivity`,
  `setDefectSensitivity`, `setObjectSensitivity`, and the three
  `setEnable*Detect` toggles) — an exact match to the Moonraker config keys
  already confirmed in `LM-006`.
- **`blinds_hall_monitor`'s door/warning-dialog question from Phase 2H-D is
  substantially strengthened**: `MessageHandleTask::sigDoorDetectionWarning()`
  and `SystemModel::onDoorDetectionWarning()`/`sigDoorDetectionWarning()` are
  a dedicated, named "door detection warning" signal flowing from Moonraker
  message routing to a system-level UI warning — not a generic notification.
  `SensorsModel::setBlindsSensor1(bool)`/`setBlindsSensor2(bool)` match
  `blinds_hall_monitor`'s configured `blinds_hall_sensor1`/
  `blinds_hall_sensor2` sensor names exactly.
  `SensorsModel::setChamberTemper`/`setChamberFanSpeed`/
  `setChamberCoolingFanSpeed` confirm a full chamber-heater/fan UI control
  surface consistent with `blinds_hall_monitor`'s domain. This is upgraded
  from Phase 2H-D's `INFERRED (weak — thematic only)` to `STRONGLY INFERRED`
  — see the reconciliation table below. It is **not** upgraded to
  `CONFIRMED`: the Moonraker-side trigger source for
  `DoorDetectionWarning` is still encrypted/unread, and the `klippy.log`
  gap for 2026-09-07 (Phase 2H-D) still prevents any timestamp-level
  correlation with the Sep 7 physical footage.
- **Continuous-fiber UI surface, `CONFIRMED`**: `LoadUnloadModel::
  cutFilament()`/`loadFilament()`/`unloadFilament()`/`moveFilamentByStep()`
  and `SensorsModel::onTensionSensorUpdate`/`setTensionSensorValue` (64-bit
  integer type) confirm dedicated touchscreen actions and live tension
  polling exist as first-class UI features, consistent with — but not
  independent proof of — the M2800/tension-sensor interpretations below.

MCU firmware flashing (previously `UNKNOWN` in detail) is now `CONFIRMED`
from `fibreseek-installer`'s own strings: it runs Klipper's standard
`scripts/flashtool.py` against `~/klipper/out/{motherboard,toolhead,
toolhead_can}.bin`, independently per board. See
`FIRMWARE_ANALYSIS.md` for the complete reconstructed install/decrypt/deploy
call chain.

## Remaining unknowns and next safe experiment

Actual source imports, classes, schemas, event registration, custom Moonraker
routes, MQTT topics, credentials/authentication assumptions, subprocess use,
complete network destinations, source commits, licenses, vendor authorship,
and remote-agent implementation remain unresolved. Phase 2H-D additionally
leaves open: `material_manager`'s persistence target; the call site (if any)
of `PRINTED_DOOR_DETECTION`; whether `blinds_hall_monitor` reacts to a
door-open event during active heating; and any relationship between
`crowsnest` and `ai_detection`.

Phase 2I-A completed (b): both official `.fibrepack` packages were statically
analyzed (see above and `docs/firmware/FIRMWARE_ANALYSIS.md`), which
resolved every target's exact path but not its content, because the six
proprietary payloads inside each package are ZipCrypto-encrypted and no
password is present.

Phase 2I-B attempted owner-authorized offline password recovery against
those six archives (static analysis, a 1,785-entry dictionary, and a full
6-digit numeric brute force) and did not succeed; disassembly evidence
indicates the password is a caller-supplied runtime argument, not embedded
or derivable from either package (see `FIRMWARE_ANALYSIS.md`). It also
recovered substantial new architecture evidence from `anisotouch`'s and
`fibreseek-installer`'s own unencrypted symbol tables without needing any
decryption (`mqtt_bridge`, `remote`, `ai_detection`, and
`blinds_hall_monitor`'s consumer-side wiring; MCU flashing mechanics).

**Meaningful further source-content recovery now requires an owner-supplied
password for these specific packages**, an owner-supplied already-decrypted
export of the same trees, or a ZipCrypto known-plaintext attack via a
purpose-built tool (e.g. `bkcrack`) against a predictable file such as
`moonraker.zip`'s `LICENSE` — used offline against these already-possessed
local files only, never against Loom, never guessed beyond what was already
attempted, and never sourced from a network or cloud search. Do not use
traversal, SSH discovery, guessed credentials, extension invocation, OTA
downloads, or external/cloud probing as substitutes.
