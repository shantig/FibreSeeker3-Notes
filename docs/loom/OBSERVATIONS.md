# Loom Observations

## Baseline supplied by owner

The following is investigation context supplied by the project owner. It has
now been independently matched by LM-002 through LM-004. The list is retained
as the pre-capture baseline; the cited live observations below are the
authoritative repository evidence:

- hostname `anisoprint`; machine name `FibreSeeker 3`;
- aarch64, four CPU cores, approximately 4 GB RAM;
- Ubuntu 20.04.6 LTS, kernel 5.10.198, Python 3.8.10;
- `can0` using `rockchip_canfd` at approximately 1 Mbit/s;
- running services `klipper`, `klipper-mcu`, `moonraker`, and `crowsnest`;
- Klipper and Moonraker `software_version` reported as `?`;
- listed Moonraker components, failed `maintenance` component, configuration
  warnings, and known filesystem paths from the owner's initial fingerprint.

These details guided endpoint selection and were not treated as captured facts
before LM-002 through LM-004.

## Live observations

### 2026-09-09 — Phase 2I-B offline password-recovery attempt and disassembly reconstruction

Evidence: the same two owner-supplied `.fibrepack` packages (`FS-150`,
`FS-151`), analyzed further via static disassembly (`nm`, `c++filt`,
`objdump`, `strings` — all already-installed local tools). Zero Loom, NAS, or
external requests. Full detail: `docs/firmware/FIRMWARE_ANALYSIS.md`.
Derived symbol/string extracts preserved as `FS-152`/`FS-153`.

#### CONFIRMED

- Password recovery against the six ZipCrypto-encrypted nested archives did
  **not** succeed: a 1,785-entry targeted dictionary and the full 6-digit
  numeric keyspace (1,000,000 candidates) were tested against all six
  archives with no match. No password value is recorded anywhere in this
  repository.
- Disassembly of `fibreseek-installer` (both releases, ELF64 aarch64,
  un-stripped) confirms the password is a caller-supplied `argv` value
  passed through to a persisted object field, not a value embedded or
  derived inside either package.
- MCU firmware flashing runs Klipper's own `scripts/flashtool.py`
  independently per board; hardware-revision config selection is driven by
  an ADC board-voltage read.
- 2.2.42's installer replaces 2.2.30's process-kill shutdown of `anisotouch`
  with proper systemd service lifecycle management and a transient-scope
  re-exec.

#### STRONGLY INFERRED

- `mqtt_bridge` reports MQTT-broker status into AnisoTouch's cloud
  account-binding UI.
- `remote`'s candidate purpose is remote/cloud print-job file transfer with
  progress reporting, via a Moonraker agent-event signal.
- The Sep 7 door/warning-dialog question (Phase 2H-D) is upgraded from
  `INFERRED (weak)`: a dedicated, named `DoorDetectionWarning` signal exists
  end-to-end from Moonraker to a system-level AnisoTouch warning, and
  `blinds_hall_sensor1`/`2` naming matches exactly. Not `CONFIRMED`: no
  Moonraker-side trigger source or Sep-7 timestamp correlation exists.
- `ai_detection`'s configuration schema is `CONFIRMED` field-for-field; its
  exact WebSocket peer remains `STRONGLY INFERRED`, unchanged from Phase 2I-A.

#### UNKNOWN / EVIDENCE MISSING

- All source content behind the ZipCrypto boundary remains unresolved.
- Whether the same password (if one exists) is shared across all six
  archives and both releases — no password was recovered for any of them.
- The theoretically stronger known-plaintext ZipCrypto attack (using
  `moonraker.zip`'s `LICENSE` as a crib) was assessed but not attempted, for
  lack of a purpose-built tool within this phase's tooling boundary.

### 2026-09-09 — Phase 2I-A official firmware static analysis (offline, no Loom/NAS/external access)

Evidence: two owner-supplied `fibreseek-sk3-*.fibrepack` packages placed
directly in `docs/firmware/` (manifest `FS-150`, `FS-151`), analyzed
statically and correlated against LM-005 through LM-011. Full detail is in
`docs/firmware/FIRMWARE_ANALYSIS.md` and
`docs/firmware/VERSION_DIFF_2.2.30_TO_2.2.42.md`.

#### CONFIRMED

- Both packages are plain ZIP containers; their six nested proprietary
  archives (Moonraker, Klipper, printer config, crowsnest, AI service,
  `remote`'s package) are ZipCrypto-encrypted with no password present in
  either package. No password was searched for, guessed, or used.
- All twelve previously unresolved Moonraker/Klipper implementations exist at
  exact confirmed paths (ZIP central directory, readable without a password);
  `material_manager` is corrected from a flat module to a package.
  `remote` is confirmed absent from the full Moonraker component list.
- `can0`'s nominal 1,000,000 bit/s bitrate and 1024 `txqueuelen` are confirmed
  by source (`klipper.config`, a boot script), previously only inferred from
  Loom's live realized rate.
- FibreTouch/AnisoTouch is a native Qt/QML application with its own direct
  Moonraker WebSocket connection, confirmed via the binary's own strings and
  (2.2.42 only) its systemd unit description.

#### STRONGLY INFERRED / INFERRED

- `remote`'s implementation is most likely `fibretouch-remote.zip`'s
  `moonraker_broker_bridge.py`; `ai_detection`'s WebSocket peer is most likely
  `fibretouch-ai.zip`'s `ai_server.py`. Neither is confirmed; both packages'
  content is encrypted.
- `can0` architecturally supports an alternate, not-selected-on-Loom
  CAN-based toolhead connection mode.

#### UNKNOWN / EVIDENCE MISSING

- All source content behind the ZipCrypto boundary: imports, classes, routes,
  event names, and exact runtime behavior for every one of the twelve
  modules, `remote`, and the AI service.
- Whether the analyzed 2.2.30.613.256 package is byte-identical to what Loom
  is currently running, or only version-string-identical.

### 2026-09-09 — Phase 2H-D evidence synthesis (analysis-only, no new capture)

Evidence: re-read of LM-005 through LM-011 and
`experiments/Loom/2026-09-07/` only. Zero new Loom, NAS, or external
requests were issued; no G-code, extension call, or printer/machine action
occurred. Full detail and exact citations are canonical in
`SOURCE_RECOVERY_AND_INTERFACES.md`.

#### CONFIRMED

- `material_manager`'s prior "CONFIRMED write/update semantics" claim
  overstated the evidence; it is corrected to: confirmed to run a named
  update operation and log per-field values, with persistence target
  unresolved.
- The two configured `update_manager` sections and the logged
  repository-identity mismatch are the same subsystem; the tracked local
  version matches the FibreTouch application version, and the OTA package
  naming convention is directly evidenced in the log.
- `blinds_hall_monitor` reacts to a chamber-heater-off command by stopping its
  monitoring loop and running a cooling-fan delay matching its configured
  duration exactly, confirmed from log lines dated 2026-06-17 and 2026-09-09.
- The captured `klippy.log` contains no entries for 2026-09-07.

#### STRONGLY INFERRED / INFERRED

- `blinds_hall_monitor` polls the configured `door_hall_sensor` as part of its
  door-monitoring loop (STRONGLY INFERRED; wiring not source-confirmed).
- `printed_door_detection`'s message is a plausible functional match for the
  Sep 7 owner-observed warning dialogs (INFERRED; no call-site or timestamp
  evidence).

#### UNKNOWN / EVIDENCE MISSING

- Whether the Sep 7 physical warning dialogs are this `M118` message or a
  separate FibreTouch-native warning; this cannot be resolved without a log
  window covering 2026-09-07, which does not currently exist in the repository.
- Any relationship between `crowsnest` and `ai_detection`; evaluated and kept
  at `UNKNOWN` rather than elevated, per conservative review.
- Whether `fibreseek-sk3-2.2.30.613.256.fibrepack` is present anywhere outside
  this repository's Git working tree was not checked (out of scope); it is
  confirmed absent from the repository itself.

### 2026-09-09 — Passive source-access boundary check

Evidence: LM-011, preserved under
`sources/loom/sessions/2026-09-09T020242Z/`.

#### CONFIRMED

- One unauthenticated `GET /server/files/roots` returned HTTP 200, 569 bytes,
  and seven registered roots with server-reported permissions.
- Neither Loom's Moonraker component directory nor Klipper extras directory is
  registered. No implementation source file was recovered.
- No follow-up file request, traversal, shell/SSH access, external download,
  extension call, printer command, or mutation occurred.

#### UNKNOWN / NEEDS TESTING

- Whether an owner-approved administrative export channel can read the source
  paths without changing atime or machine/application state;
- all implementation details that cannot be established from configuration,
  command descriptions, and logs alone.

The source-recovery attempt stopped at the confirmed API boundary. See
`SOURCE_RECOVERY_AND_INTERFACES.md`.

### 2026-09-09 — Passive architecture attribution

Evidence: LM-008 through LM-010, preserved under
`sources/loom/sessions/2026-09-09T012636Z/`.

#### CONFIRMED

- Three sequential unauthenticated passive GETs retrieved Moonraker's log,
  Klipper's log, and 241 registered G-code descriptions. No listed command or
  extension method was invoked.
- The five target Moonraker components loaded during captured startup;
  `maintenance` failed specifically because its Python component module was
  missing. AI detection later connected to its host-local WebSocket after
  earlier refusals.
- Runtime logger evidence identifies six of seven custom Klipper module
  filenames and shows sensor, SPI, LED, alignment, load/unload, and extruder-
  stall integration. Registration does not establish safe operation.
- Two MCU firmware builds share the same vendor build base. Their serial
  configuration still provides no mapping to host `can0`.
- The `remote` agent connected from the host itself and reported the same name,
  version, type, and vendor URL preserved in LM-007.

#### STRONGLY INFERRED

- The vendor/integrator additions occupy both Moonraker's component layer and
  Klipper's extras layer, with a local companion-service layer above them.
- `remote` is associated with vendor HMI/remote/cloud functionality, but the
  captured evidence does not establish its process or external connections.

#### UNKNOWN / NEEDS TESTING

- Component source bodies, author/license metadata, package versions, and
  custom Moonraker route registration;
- `remote` methods and permissions;
- MQTT/cloud flow and the user of `can0`.

Historical printer actions present in the downloaded logs were not initiated
or repeated. No shell, SSH, service, CAN, MQTT, external infrastructure, NAS,
or physical-machine access occurred.

### 2026-09-08 — Initial Moonraker object enumeration

Evidence: LM-001, preserved under
`sources/loom/sessions/2026-09-08T152800Z/moonraker-api/printer-objects-list/`.

#### CONFIRMED

- One unauthenticated `GET /printer/objects/list` returned HTTP 200 with a
  5,333-byte JSON body and 178 object names.
- The response includes 122 G-code macros, 2 MCU objects, 6 TMC2240 driver
  objects, 8 filament switch sensors, 2 filament motion sensors, 8 fan-class
  objects, 2 non-extruder heater objects, 3 output pins, and 3 extruders.
- `gcode_macro M2800` is present. This connects the earlier Rocket static
  cut-command candidate to an available Loom macro name, but not to its macro
  body or runtime effect.
- Potential vendor-extension objects `blinds_hall_monitor` and
  `extruder_stall_detector extruder` are present.
- No macro, G-code, motion, heater, service, update, maintenance, or other
  state-changing action was invoked.

#### STRONGLY INFERRED

- Loom's configured tool model is consistent with one fiber and two plastic
  extruder roles. Exact object and physical-side mappings are unresolved.
- The object namespace shows substantial vendor workflow customization around
  tool switching, calibration, fiber handling, sensing, nozzle cleaning, and
  cutter control.

#### UNKNOWN / NEEDS TESTING

- Which macros and Python modules are FibreSeek-authored versus upstream,
  third-party, or integrator-modified;
- macro bodies and their static call graph;
- current object health and sensor state;
- CAN interface settings and MCU/device topology;
- whether Moonraker exposes safe read-only config/log copies after privacy and
  credential screening.

### 2026-09-08 — Bounded host and application metadata

Evidence: LM-002 through LM-004, preserved under
`sources/loom/sessions/2026-09-08T154557Z/moonraker-api/`.

#### CONFIRMED

- Three sequential unauthenticated GETs returned HTTP 200: `/server/info`
  (1,803 bytes), `/printer/info` (462 bytes), and `/machine/system_info`
  (1,723 bytes). No other Loom endpoint was requested in this session.
- Klippy and the printer reported ready. Moonraker reports API 1.5.0, while
  Moonraker and Klipper software versions both report `?`.
- The host reports Ubuntu 20.04.6 LTS, kernel 5.10.198, Python 3.8.10, 64-bit
  aarch64, four CPU cores, 3,933,096 kB memory, and no virtualization.
- `klipper`, `klipper-mcu`, `moonraker`, and `crowsnest` all reported
  active/running through the `systemd_dbus` provider at capture time.
- `can0` reports `rockchip_canfd`, transmit queue length 1024, and bitrate
  996,644 bit/s.
- Moonraker reports 32 loaded components and one failed component,
  `maintenance`. The response repeats the three unparsed log-rotation options,
  unparsed `[maintenance]` section, and invalid docs-path warning supplied by
  the owner.
- Seven registered directory names expose likely diagnostic/configuration
  surfaces without exposing their contents.
- No service action, shell command, config access or change, file operation,
  macro, G-code, motion, heater, update, or network change was invoked.

#### STRONGLY INFERRED

- The reported 996,644 bit/s CAN rate represents a nominal 1 Mbit/s setup.
- `printer_setting`, `material_manager`, `mqtt_bridge`, and `ai_detection` are
  vendor/integrator extension candidates. Static source evidence is required
  before attributing them to FibreSeek.
- The failed `maintenance` load likely caused its configuration section to
  remain unparsed, but the response does not provide the root exception.
- The SD-information fields are incomplete or misdecoded; they must not be
  treated as a valid capacity inventory.

#### UNKNOWN / NEEDS TESTING

- Exact Klipper/Moonraker revisions and cause of the `?` version values;
- component code origins, source paths, API routes, and modifications;
- maintenance-component failure cause and effect;
- systemd service definitions and launch arguments;
- CAN nodes, device identifiers, topology, error state, and MCU mapping;
- contents of registered directories, configs, and logs.

LM-003 and LM-004 contain privacy-sensitive identifiers in their exact raw
responses. Those identifiers are intentionally omitted from this interpretation.

### 2026-09-08 — Phase 2H-A configuration and extension discovery

Evidence: LM-005 through LM-007, preserved under
`sources/loom/sessions/2026-09-08T230535Z/moonraker-api/`.

#### CONFIRMED

- Three sequential unauthenticated GETs returned HTTP 200:
  `/printer/objects/query?configfile` (226,337 bytes), `/server/config` (7,436
  bytes), and `/server/extensions/list` (110 bytes).
- The loaded Klipper configuration contains 192 sections, including 122 macro
  bodies and seven delayed G-code sections. Configuration-visible tool roles
  map left fiber to `extruder2`, left plastic to `extruder`, and right plastic
  to `extruder1`.
- Relevant heater, fan, filament/Hall, custom-sensor, probe, accelerometer,
  servo, bed-mesh, and alignment sections are inventoried in
  `CONFIGURATION_DISCOVERY.md`.
- The `M2800` body operates the configured fiber servo in a timed sequence and
  updates the tension baseline. It was not invoked.
- The server configuration confirms the five named vendor/integrator component
  candidates and one connected extension agent named `remote`. No custom
  action or extension method was called.
- The unauthenticated server configuration reports that logins are not forced
  and includes an extremely broad trusted-client IPv4 range. Exact network
  values remain in raw evidence; no external exposure test was performed.
- Both MCU objects use serial device paths and expose no CAN UUID or CAN
  interface option. No relationship between host `can0` and the two MCU
  sections is visible.
- No shell-command endpoint, macro, G-code, vendor action, file operation,
  service action, CAN command, or guessed endpoint was used.

#### STRONGLY INFERRED

- Direct role-selection bodies establish configured tool roles, but not the
  physical installation or present health of any hotend.
- `M2800` is a fiber-cut candidate based on its body, fiber-context call sites,
  and prior Rocket evidence; the macro text does not state the physical result.
- The named non-upstream components and custom Klipper object shapes are
  vendor/integrator extensions, but the captures do not establish authorship.

#### UNKNOWN / NEEDS TESTING

- Vendor component routes, request methods, schemas, source, versions, and
  runtime health;
- purpose and callable surface of the `remote` extension agent;
- custom Klipper implementation semantics and authorship;
- MCU board identities, physical topology, and what uses `can0`;
- macro physical effects and safe execution preconditions.

LM-005 through LM-007 contain privacy-sensitive identifiers or locations in
their exact raw responses. No nonempty credential was detected; identifiers
remain intentionally omitted from interpretation.
