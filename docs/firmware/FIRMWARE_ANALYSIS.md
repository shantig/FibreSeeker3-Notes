# FibreSeek SK3 Firmware Static Analysis

Phase 2I-A. Static, non-executing forensic analysis of two owner-supplied
official FibreSeek 3 firmware/application update packages. This phase issued
zero Loom requests, zero NAS requests, and zero external/cloud requests.
Every operation stayed rooted inside this Git repository. See
`VERSION_DIFF_2.2.30_TO_2.2.42.md` for the detailed comparative diff.

## Scope and safety statement

Nothing extracted from either package was executed, sourced, imported,
mounted, flashed, chrooted, emulated, or run as a service. `anisotouch` and
`fibreseek-installer` are native ELF binaries; they were inspected only with
`file` and `strings`. Shell scripts (`install.sh`, `enable_nm_permissions.sh`,
`fibretouch-scripts/*.sh`, `disable_system_update_prompt.sh`) were read as
text only. No discovered password was searched for, guessed, or used. No URL
found in the package was contacted.

## Step 1 — Originals, identity, and Git-tracking recommendation

| Field | `fibreseek-sk3-2.2.30.613.256.fibrepack` | `fibreseek-sk3-2.2.42.831.320.fibrepack` |
|---|---|---|
| Repository path | `sources/firmware-packages/fibreseek-sk3-2.2.30.613.256.fibrepack` | `sources/firmware-packages/fibreseek-sk3-2.2.42.831.320.fibrepack` |
| Byte size | 488,602,827 | 266,801,749 |
| SHA-256 | `09098a97186132ba6047c9ae2520dc36c7ea02fe6c0edf734e9e23772cc7389e` | `eeeabe0738fb02f11e099a82504e727b28f8e1732c66ca0302179d477a0fef26` |
| Detected type | ZIP archive, deflate, ≥v2.0 to extract | ZIP archive, deflate, ≥v2.0 to extract |
| Filename-inferred version | `fibretouch-fs3` 2.2.30.613, build 256 | `fibretouch-fs3` 2.2.42.831, build 320 |
| Git tracking before this phase | Untracked (`??`) | Untracked (`??`) |

**Recommendation: leave both binaries untracked (not committed).** This
repository's established convention (`CLAUDE.md` roles: "NAS — immutable/raw
archive and large-binary store") already treats the NAS as the destination for
large binary originals, and existing large-artifact acquisitions (e.g.
`FS-122`, a 315 MB Rocket installer; `AP-115`, a 7.2 MB firmware Git bundle)
record their `local_path` on the NAS rather than committing bytes into Git.
At 466 MB and 254 MB combined (~720 MB), these two packages are far larger
than anything currently committed to this repository and would roughly
quadruple its Git history size going forward with binary content that Git
cannot usefully diff or compress further (both are already-compressed ZIPs).
`.gitignore` now excludes `sources/firmware-packages/*.fibrepack` explicitly, with
a comment recording this rationale, so `git status` stays clean rather than
perpetually flagging them as stray untracked files. Provenance and hashes are
preserved durably in `sources/manifest.jsonl` (`FS-150`, `FS-151`) regardless
of Git-tracking status.

## Step 2 — Container format

Each `.fibrepack` is a **plain ZIP archive** (`PK\x03\x04` local-file-header
magic, `PK\x05\x06` end-of-central-directory trailer confirmed at the tail of
both files) — not a filesystem image, not a custom binary wrapper, and not
itself signed or encrypted at the outer-archive level. It is best described as
**a custom-curated bundle of ordinary formats**: 22–28 top-level members
including further nested ZIP archives, two native ELF binaries, shell scripts,
JSON metadata, an MP4 splash video, and a Python wheel.

Nested inside are the actual proprietary payloads — `moonraker.zip`,
`klipper.zip`, `anisotouch-config.zip`, `crowsnest.zip`, `fibretouch-ai.zip`,
`fibretouch-remote.zip` — and **these nested ZIPs are genuinely
password-encrypted** (traditional ZipCrypto; confirmed via each entry's
general-purpose bit-flag 0, not merely an unused `-P` option in `install.sh`).
Of moonraker.zip's 160 entries, 142 real files are encrypted (only directory
placeholders are not); klipper.zip is 1,959/2,105; fibretouch-ai.zip is
107/117; fibretouch-remote.zip is 4/5 (the one unencrypted "entry" is an empty
directory marker, not content); anisotouch-config.zip is 40/40; crowsnest.zip
is 366/420. **No password is present anywhere in either package**, and this
phase did not search for, guess, or use one — that is a deliberate,
vendor-imposed access boundary, and bypassing it would be exploitation. This
is the single most important scope-defining fact for the rest of this
analysis: **all real file content in the six proprietary nested archives is
inaccessible**; only their central-directory filenames, sizes, and CRCs are
readable, because ZIP encryption protects file data, not the directory index.

Version metadata is separately confirmed via `release_info_en.json` /
`release_info_cn.json` (unencrypted, top-level, outer ZIP): both declare
`"project_name": "fibretouch-fs3"`, `"project_owner": "fibreseek"`,
`"model": "Fibreseek 3"`, `"min_hw_version": 2.1`, matching the versions in
each filename exactly and matching the `repo = fibreseek/fibretouch-fs3`
value already captured live in `LM-008`.

## Step 3 — Extraction record

Both outer `.fibrepack` archives were safely extracted (ordinary `zipfile`
inflate, no code execution) into repository-local, `.gitignore`d directories:

```text
_work/firmware/2.2.30.613.256/   (from fibreseek-sk3-2.2.30.613.256.fibrepack)
_work/firmware/2.2.42.831.320/   (from fibreseek-sk3-2.2.42.831.320.fibrepack)
_work/firmware/analysis/         (filename listings only, text)
```

`_work/` is excluded from Git (`.gitignore`) as a disposable, regenerable
analysis tree; it is not committed. No path-traversal or absolute-path entries
were present in either archive (checked before extraction). Nested,
password-encrypted archives were **not** extracted further; only their
central-directory filenames were listed via `zipfile.ZipFile.infolist()`,
which does not require a password. No nested archive contents were unpacked.

## Step 4 — Structural inventory (outer package, both releases)

| Member | 2.2.30.613.256 | 2.2.42.831.320 | Kind |
|---|---:|---:|---|
| `anisotouch` | 14,852,712 B | 15,464,704 B | compiled artifact (ELF64 aarch64, Qt app) |
| `anisotouch-config.zip` | 123,375 B | 152,133 B | configuration (encrypted) |
| `anisotouch.service` | — | 391 B | metadata (systemd unit, new in 2.2.42) |
| `boot.mp4` | 237,911 B | 237,911 B | runtime data (splash video, unchanged) |
| `crowsnest.zip` | 2,184,995 B | 2,184,995 B | source (encrypted, unchanged) |
| `disable_system_update_prompt.sh` | — | 3,625 B | update payload (new in 2.2.42) |
| `enable_nm_permissions.sh` | 1,883 B | 3,437 B | update payload |
| `factory_gcodes/` | — | 17 files | runtime data (new in 2.2.42; demo prints) |
| `factory_test_gcodes/` | 8 files | 18 files | runtime data (factory calibration prints) |
| `fibreseek-installer` | 870,832 B | 918,688 B | compiled artifact (ELF64 aarch64) |
| `fibretouch-ai.zip` | 439,690,430 B | 192,794,965 B | source + models (encrypted; see below) |
| `fibretouch-remote.zip` | 21,300 B | 21,308 B | source (encrypted, unchanged filenames) |
| `fibretouch-scripts/` | 3 scripts | 3 scripts | update payload / boot scripts |
| `install.sh` | 3,599 B | 3,599 B | update payload (byte-identical, same SHA-256) |
| `klipper.config` | 3,685 B | 3,685 B | metadata (MCU Kconfig) |
| `klipper.zip` | 26,181,389 B | 26,201,672 B | source (encrypted; +1 file) |
| `moonraker.zip` | 1,018,736 B | 1,031,051 B | source (encrypted; +1 file) |
| `release_info_{en,cn}.json` | 181/176 B | 181/176 B | metadata |
| `websockets-13.1-py3-none-any.whl` | 152,134 B | 152,134 B | dependency (unchanged) |

Nested-archive **filename** inventories (paths only; content encrypted):

- **`klipper.zip`** (2,105/2,106 entries) is a full Klipper source checkout —
  `klippy/*.py` core, `klippy/extras/*.py` (139 files), `src/` MCU firmware C
  source, `scripts/` build/install tooling, and **prebuilt firmware binaries**
  at `out/bootloader_motherboard.bin`, `out/bootloader_toolhead.bin`,
  `out/bootloader_toolhead_can.bin`, `out/motherboard.bin`, `out/toolhead.bin`,
  `out/toolhead_can.bin`, plus matching `config/klipper_config_motherboard`,
  `config/klipper_config_toolhead`, `config/klipper_config_toolhead_can`
  Kconfig files. All content is ZipCrypto-encrypted, including the `.bin`
  images, so no embedded firmware version string could be extracted.
- **`moonraker.zip`** (160/161 entries) is a full Moonraker source checkout —
  every standard upstream component alongside the five known custom ones,
  `pdm_build.py`, `pyproject.toml`, `CLAUDE.md`, `verify.key`, and bundled
  wheel dependencies (`et_xmlfile`, `websockets`, `openpyxl`). All content is
  encrypted.
- **`anisotouch-config.zip`** (40/43 entries) is the Klipper/Moonraker/Mainsail
  configuration library that `install.sh` symlinks into
  `~/printer_data/config`: `printer.cfg`, `variables.cfg`, `spools.json`
  (the three files `install.sh` never overwrites), `moonraker.conf`,
  `mainsail.cfg`, `crowsnest.conf`, `timelapse.cfg`, `xyz_align.cfg`,
  `toolhead.cfg`, `toolhead_can.cfg`, `printer_bed_mesh.cfg`, `eddy.cfg`,
  `tool_switch.cfg`, `calibration.cfg`, `heavy_duty_brush.cfg`,
  `error_info.xlsx`, `verify.key`, and **seven hardware-revision-specific base
  configs** (`printer_base_v1.1.cfg` through `printer_base_v2.2.cfg`, plus a
  `v1.3_4248` variant) with matching per-revision `fans_*.cfg`,
  `filament_switch_sensor*.cfg`, and `piezoelectric_ceramic*.cfg` overrides.
  All content is encrypted.
- **`fibretouch-ai.zip`** (117/61 entries — see version diff) is the local AI
  service: `ai_server.py`, `libs/`, `utils/` (including `onnx2rknn.py`,
  `py_utils/yolo11.py`, `py_utils/yolo11_v2.py`, `info_rag.py`,
  `status_analysis.py`, `anisoprint_machine.xlsx`), `vis/show.py`,
  `requirements.txt`, `verify.key`, and a `models/` directory containing
  several dated `.rknn` (Rockchip NPU) object/defect-detection models,
  `labels.txt`, and a **separate semantic error-search subsystem**
  (`models/error_search-v1.5/` — a sentence-transformer model with tokenizer,
  config, and pooling files — plus `models/error_db2_0225.faiss` and
  `models/error_db2_ox_0225.sqlite`). All content is encrypted.
- **`fibretouch-remote.zip`** (5 entries, identical between releases) contains
  exactly `my_logger.py`, `moonraker_broker_bridge.py` (108,274 B),
  `configs/factory_config.json`, and `configs/user_default_config.json`. All
  content is encrypted.
- **`crowsnest.zip`** (420 entries, byte-identical filenames both releases) is
  a standard `crowsnest` webcam-streaming checkout (`tools/`, install/build
  scripts). Content is encrypted; this is very likely the unmodified
  upstream/community `crowsnest` project rather than FibreSeek-proprietary
  code, based on its filename shape (`tools/libs/messages.sh`,
  `tools/build_apps.sh`, `tools/test_install.sh` match the public project's
  layout), though its exact commit/fork point cannot be confirmed without
  decrypting it.

## Step 5 — The twelve previously unresolved implementations

**Path-level result: all twelve are now directly confirmed present at exact
paths from the ZIP central directory. Source-level content (imports, classes,
registered routes, event names) remains inaccessible behind ZipCrypto
encryption and stays `UNKNOWN`.**

| Target | Exact path (CONFIRMED) | Prior Phase 2H status | New status |
|---|---|---|---|
| `printer_setting` | `moonraker/components/printer_setting.py` | path STRONGLY INFERRED | path **CONFIRMED**; content still UNKNOWN |
| `material_manager` | `moonraker/components/material_manager/__init__.py` + `moonraker/components/material_manager/material_manager.py` | path STRONGLY INFERRED as a flat module | **CONFIRMED it is a package, not a flat module** — a structural correction; content still UNKNOWN |
| `mqtt_bridge` | `moonraker/components/mqtt_bridge.py` | path STRONGLY INFERRED | path **CONFIRMED**; content still UNKNOWN |
| `ai_detection` | `moonraker/components/ai_detection.py` | path STRONGLY INFERRED | path **CONFIRMED**; content still UNKNOWN |
| `error_indexer` | `moonraker/components/error_indexer.py` | path CONFIRMED (from LM-008 logger) | reconfirmed; **new bonus file** `error_indexer_plugin_debug_tool.py` at the checkout root |
| `blinds_hall_monitor` | `klippy/extras/blinds_hall_monitor.py` | path CONFIRMED (from LM-009 logger) | reconfirmed |
| `extruder_stall_detector` | `klippy/extras/extruder_stall_detector.py` | path CONFIRMED | reconfirmed |
| `load_unload` | `klippy/extras/load_unload.py` | path CONFIRMED | reconfirmed |
| `tension_sensor` | `klippy/extras/tension_sensor.py` | path CONFIRMED | reconfirmed |
| `aniso_bed_mesh` | `klippy/extras/aniso_bed_mesh.py` (plus MCU-side `src/aniso_bed_mesh.c`, `src/aniso_bed_mesh.h`) | path INFERRED (no direct logger line) | path **upgraded to CONFIRMED**; **new finding**: has MCU-firmware-side C source, not just a Klipper host-side Python module |
| `xyz_align` | `klippy/extras/xyz_align.py` (plus MCU-side `src/stm32/xyz_align.c`) | path CONFIRMED | reconfirmed; **new finding**: also has MCU-side C source |
| `ws2812b_spi` | `klippy/extras/ws2812b_spi.py` | path CONFIRMED | reconfirmed |

**Two more custom modules not in the original twelve were discovered by
filename alone:**

- `klippy/extras/aniso_temp_compensation.py` — a previously undocumented
  custom Klipper extra. Name suggests temperature-compensation logic (thermal
  drift correction for the fiber/nozzle system or ambient/chamber
  compensation); purpose is `UNKNOWN` beyond the name, content is encrypted.
- `error_indexer_plugin_debug_tool.py` — a companion debug/CLI tool for
  `error_indexer`, sitting at the Moonraker checkout root rather than inside
  `moonraker/components/`. Suggests `error_indexer` has a plugin-style
  internal architecture. Content is encrypted.

No custom Moonraker component named `remote` exists anywhere in
`moonraker.zip`'s 160-entry listing — this **confirms** (by exhaustive
absence in a now-directly-inspected checkout, not just prior live API
evidence) that `remote` is not a Moonraker-side component at all, consistent
with the `fibretouch-remote.zip` finding below.

## Step 6 — `remote` agent attribution

**STRONGLY INFERRED implementation identity:** `fibretouch-remote.zip`'s
`moonraker_broker_bridge.py` (108,274 bytes) is the leading candidate
implementation of the `remote` Moonraker extension agent (self-identified in
`LM-007`/`LM-008` as name `remote`, version `1.0.0`, connecting over a
host-local WebSocket). This inference rests on: (a) `remote` is confirmed
absent from `moonraker.zip`'s component list, so its implementation must live
elsewhere; (b) `fibretouch-remote.zip` is the only other package member whose
name and contents plausibly match an external Moonraker-connecting agent;
(c) the filename `moonraker_broker_bridge.py` directly names both "moonraker"
and "broker" (message-broker bridging vocabulary), matching `remote`'s
observed role bridging Moonraker to something else; (d) `my_logger.py`
alongside it matches the pattern of every other custom component (each has
its own logger module observed in `LM-008`/`LM-009`); (e) `configs/
factory_config.json` and `configs/user_default_config.json` match a
factory-versus-user-configuration split consistent with a
vendor-provisioned, field-configurable bridge. **This is not proven**: the
file's actual content, its registration call, and its exact relationship to
the observed WebSocket connection remain encrypted and `UNKNOWN`. No exact
byte-level confirmation is possible without the password.

`fibretouch-remote.zip`'s file list is byte-identical between 2.2.30.613 and
2.2.42.831 (same five filenames, same directory shape), so whatever `remote`
does, it did not structurally change between these two releases.

Supporting UI evidence (from `anisotouch`'s embedded QML resource paths,
read via `strings`, Step 7): a `qrc:/qml/.../AccountBindTabPage.qml` page
exists, suggesting a cloud-account-binding feature in the touchscreen UI.
This is consistent with, but does not prove, a cloud/remote-monitoring
relationship for the `remote` agent — recorded as `STRONGLY INFERRED`
circumstantial support, not confirmation.

## Step 7 — FibreTouch / AnisoTouch architecture

**CONFIRMED** (via `file`, `strings`, and the 2.2.42 `anisotouch.service`
unit, all read as static text/metadata, never executed):

- `anisotouch` is a native **ELF 64-bit ARM aarch64** executable, matching
  Loom's confirmed host architecture. It is a **Qt/QML application**: embedded
  QML resource paths (`qrc:/qml/mainpages/...`) and Qt Quick import
  statements (`import QtQuick 2.11` / `2.15`) are present in the binary, and
  its own systemd unit (2.2.42) literally describes it as `"Anisotouch Qt
  Application"`.
- Deployment: `ExecStart=/home/anisoprint/anisotouch`, a graphical session
  (`DISPLAY=:0`, `.Xauthority`) launched via `graphical-session.target`, with
  `Restart=on-failure`. `install.sh` also independently confirms deployment:
  it copies the executable to `~/`, killing any running instance first
  (`killall anisotouch`) — consistent with a desktop-resident native app, not
  a container or web service.
- **Moonraker communication mechanism**: `WebSocketBase`/`WebSocketThread`
  C++ classes are compiled into the binary; embedded strings include
  `"WebSocket connected successfully to"`, `"Moonraker RPC Error:"`,
  `"Unable to connect to Moonraker. Please check the service status."`, and
  `"Failed to create Moonraker user. Please configure it manually."`. This
  **confirms** AnisoTouch holds its own direct WebSocket JSON-RPC connection
  to Moonraker (the standard Moonraker-frontend pattern, the same mechanism
  Mainsail/Fluidd use), separate from whatever `remote` does.
- **AI integration**: the string `"[AIDetectorModel] Config updated from
  Moonraker:"` confirms a QML/C++ `AIDetectorModel` component that reads
  `ai_detection`'s configuration back from Moonraker — i.e. AnisoTouch is the
  UI-side configurator/consumer of the `ai_detection` Moonraker component.
- Observed QML page names include `FibreCalibrationPage.qml`,
  `PrinterCalibrationPage.qml`, `NozzlePositionSwitch.qml`,
  `SensorListPage.qml`, `MachineExtruder.qml`, `MachineFilament.qml`, and
  `AccountBindTabPage.qml`.
- Version correlation: Loom's live-observed FibreTouch application version
  (`2.2.30.613`, from `LM-008`) matches `fibreseek-sk3-2.2.30.613.256
  .fibrepack`'s own declared version exactly, in both the filename and
  `release_info_en.json`. **This package is, at the version level, the exact
  build Loom is currently running** (build number `256` is not independently
  visible in Loom's live capture, only the three-part `2.2.30.613`, so this
  is `CONFIRMED` at the version string Loom reports and `STRONGLY INFERRED`
  at the exact build).
- MQTT integration for AnisoTouch itself was not found in the strings sampled;
  the confirmed MQTT-adjacent surface remains the separate Moonraker
  `mqtt_bridge` component (path confirmed, content encrypted).

## Step 8 — Update architecture

Fully reconstructed from directly read, unencrypted, non-executed source
(`install.sh`, full text; `fibreseek-installer`, `strings` output only):

- **What updates what.** `install.sh` explicitly extracts (password-protected)
  `anisotouch-config.zip` → `~/anisotouch-config` (then symlinked into
  `~/printer_data/config`, preserving `printer.cfg`/`variables.cfg`/
  `spools.json` if they already exist), `klipper.zip` → `~/klipper`,
  `moonraker.zip` → `~/moonraker`, `crowsnest.zip` → `~/crowsnest`, and
  (referenced but not present in either package we have) `moonraker-
  timelapse.zip` → `~/moonraker-timelapse`. It then copies the `anisotouch`
  executable to `~/`. **This package updates the HMI, Moonraker, Klipper
  (host-side checkout and prebuilt MCU firmware images), and the webcam
  streaming stack together, in one release.** MCU firmware flashing itself
  (writing `out/*.bin` to the MCUs) is not shown in `install.sh` — Klipper's
  own `flash-sdcard.sh`/`flash_usb.py` tooling is present inside the encrypted
  `klipper.zip`, so the flashing step is presumed to live there or in the
  (also encrypted) `fibreseek-installer` binary logic; this is `UNKNOWN` in
  detail. `fibretouch-ai.zip` and `fibretouch-remote.zip` are not touched by
  `install.sh` at all — they must be deployed by a separate mechanism (most
  plausibly `fibreseek-installer` itself, or a first-boot/factory step), which
  remains `UNKNOWN`.
- **Verification/signature logic.** A file named `verify.key` appears in
  three places (`moonraker.zip` root, `anisotouch-config.zip`,
  `fibretouch-ai.zip`), and `fibreseek-installer`'s own strings include
  `/verify.key`, `"(verify.key was empty)..."` and reference `pip install
  --upgrade`. This confirms a package-wide file-presence/integrity convention
  named `verify.key`, but the one message fragment recovered ("verify.key was
  empty") suggests the check may be a simple non-empty/presence test rather
  than genuine cryptographic signature verification — **this is `INFERRED`
  from a single string fragment, not confirmed**, because the surrounding
  control flow is compiled/encrypted and unavailable. No actual key material
  could be read (the files themselves are ZipCrypto-encrypted).
- **Password handling.** `fibreseek-installer`'s own usage text is
  `<password> <install_directory> [lang]` (example `mypassword
  /path/to/install/dir`); its strings also include `"Testing ZIP file
  integrity and password for"` and `"Error: Password incorrect or ZIP file
  corrupted for"`. **No actual password value is embedded in either package**
  — it is supplied externally at install/update time (by an operator or by a
  higher-level provisioning step), which this analysis does not have and did
  not search for.
- **Rollback/version comparison.** Not directly observed in unencrypted
  content; `LM-008`'s live log already confirmed Moonraker's own
  `update_manager` tracks `version`/`remote_version`/`rollback_version`/
  `rollback_repo` fields per app, and `fibreseek-installer`'s strings show
  `curl -L --fail --retry 3 --connect-timeout 15 --max-time 1800 -o
  update.fibrepack` and a `HEAD`-style `curl -sI -L` check — confirming the
  installer downloads to a fixed local name (`update.fibrepack`) regardless
  of the release-specific filename on the OTA server.
- **`fibreseek-updater` / `fibreseek-updater-factory`.** These remain
  Moonraker `update_manager` client sections (confirmed in
  `CONFIGURATION_DISCOVERY.md`/`LM-006`); this phase found no direct
  implementation code for them (both are Moonraker's own generic
  `update_manager/net_deploy.py`/`app_deploy.py` machinery, present in
  `moonraker.zip` but encrypted), only their `.fibrepack` payload target.
- **Component boundaries.** MCU firmware is a distinct payload
  (`klipper.zip`'s `out/*.bin`, prebuilt, three targets — see Step 4) from the
  host-side Klipper/Moonraker/HMI software; both are shipped in the same
  `.fibrepack`, but nothing in `install.sh` shows them being applied
  atomically together, so their update boundary is `UNKNOWN` in detail.

## MCU / host findings

- `klipper.config` (unencrypted, top-level) is a **Kconfig build
  configuration for an STM32H723xx MCU** (`CONFIG_MCU="stm32h723xx"`,
  `CONFIG_MACH_STM32H7=y`), with `CONFIG_USB_VENDOR_ID=0x1d50` /
  `CONFIG_USB_DEVICE_ID=0x614e` — the exact USB VID:PID pair registered to
  the Klipper project itself (via pid.codes/OpenMoko's shared range), and
  `CONFIG_USB_SERIAL_NUMBER="aniso"`. This **directly confirms** (source
  evidence, not inference) that Loom's MCU firmware is built from vanilla
  Klipper's own build system for a standard STM32H723 target, not a
  from-scratch proprietary firmware — the customization is in Klipper's
  Python `extras/` layer and the C-level `aniso_bed_mesh`/`xyz_align`
  additions, not a MCU-firmware fork of Klipper's core.
- `CONFIG_CANBUS_FREQUENCY=1000000` **directly confirms** the CAN nominal
  bitrate as exactly 1,000,000 bit/s — previously only `STRONGLY INFERRED`
  from LM-004's realized rate of 996,644 bit/s.
- **The `can0` mystery is substantially resolved.**
  `fibretouch-scripts/set_USB3.0_OTG_to_host_mode.sh` (read as plain text,
  never executed) contains a `config_can0()` function that runs at boot:
  waits for `can0` to appear, then executes `ip link set can0 type can
  bitrate 1000000 restart-ms 100`, `ip link set can0 txqueuelen 1024`, and
  `ip link set up can0`, verifying `ERROR-ACTIVE` state. This **confirms**
  (source evidence) the exact bitrate (1,000,000) and `txqueuelen` (1024)
  values LM-004 observed live, and confirms `can0` bring-up is a FibreSeek
  vendor boot-time action, not an OS default. Separately, `klipper.zip`
  ships **three** MCU firmware/config target sets — `motherboard`,
  `toolhead` (serial), and `toolhead_can` — and `anisotouch-config.zip` ships
  both `toolhead.cfg` and a distinct `toolhead_can.cfg`. **STRONGLY
  INFERRED**: `can0`'s architectural purpose is to support an *alternate*
  CAN-based toolhead-MCU connection mode that this specific machine (Loom)
  is not using — Loom's live capture confirms both MCU sections configured
  via serial device paths, not `canbus_uuid`, meaning it is running the
  `toolhead.cfg`/serial variant, not `toolhead_can.cfg`. What (if anything)
  else uses `can0` on Loom specifically remains `UNKNOWN`; the co-location of
  the USB3-OTG-host-mode switch and the CAN bring-up in the same script file
  does not by itself prove they are causally related, and is not claimed as
  such.
- `rknn_toolkit2` (a Rockchip NPU inference SDK) is bundled in
  `fibretouch-ai.zip`'s `pkg/` wheel cache (2.2.30 release only), and
  `utils/onnx2rknn.py` plus `.rknn` model files confirm on-device inference
  is compiled for a Rockchip NPU target. This **upgrades** Phase 2H-D's
  conservative `rockchip_canfd`-driver-only inference (Rockchip SoC family,
  no model claimed) to a stronger, still-conservative conclusion: Loom's SoC
  is confirmed to be a member of the Rockchip family with an NPU used for
  on-device AI inference (consistent with the RK35xx line's NPU-equipped
  parts). No specific model number is claimed; none is evidenced.
- A physical status LED exists: `fibretouch-scripts/turn_on_user_led.sh`
  writes to `/sys/class/leds/led_user/brightness` (previously undocumented).
- USB drives auto-mount under `/media/anisoprint/`, cleaned up by
  `fibretouch-scripts/poll_and_cleanup_invalid_mountpoint.sh` — consistent
  with Moonraker's confirmed `usb` read/write file-manager root (Phase 2H-C).

## AI / MQTT findings

- **`ai_detection`'s WebSocket peer is very likely `ai_server.py`** inside
  `fibretouch-ai.zip` (STRONGLY INFERRED: `ai_detection.py` is a confirmed
  WebSocket client of `ws://127.0.0.1:8765`, per `LM-008`; `fibretouch-ai.zip`
  ships a file literally named `ai_server.py` alongside every dependency and
  model needed for the object/floor/defect-detection features `ai_detection`
  exposes). Content is encrypted; the exact port binding in `ai_server.py`
  could not be independently confirmed.
- The vision pipeline is **YOLOv11-based** (`utils/py_utils/yolo11.py`,
  `yolo11_v2.py`, `coco_utils.py`, `onnx_executor.py`, `rknn_executor.py`),
  with several dated `.rknn` model files for both "object" and "defect"
  detection, run on the Rockchip NPU.
- **New, previously undocumented capability**: a semantic error-search
  subsystem — `models/error_search-v1.5/` (a sentence-transformer embedding
  model with tokenizer/config/pooling files), `models/error_db2_0225.faiss`
  (a FAISS vector index), and `models/error_db2_ox_0225.sqlite` — plus
  `utils/info_rag.py` (retrieval-augmented lookup). This is architecturally
  distinct from the Moonraker `error_indexer` component's confirmed
  XLSX-table lookup (`error_info.xlsx`, present in `anisotouch-config.zip`
  and separately as `utils/anisoprint_machine.xlsx` in `fibretouch-ai.zip`,
  purpose of the latter `UNKNOWN`): `error_indexer` appears to be a simpler
  Moonraker-side catalog/notification component, while this FAISS/
  sentence-transformer stack is a separate, more sophisticated semantic
  search layer, most plausibly surfaced through `ai_server.py` or the
  AnisoTouch UI as a "search similar past errors" feature. No large-language
  generation model was found alongside it, so a full conversational
  assistant is not evidenced — only retrieval.
- `mqtt_bridge`'s path is confirmed (`moonraker/components/mqtt_bridge.py`)
  but its content is encrypted; no MQTT broker address, topic, or credential
  was found anywhere in the unencrypted content of either package.

## Security-relevant static findings (Step 10)

- **No plaintext credential, API key, token, or private key was found** in
  any unencrypted file or binary string table inspected in this phase.
- The nested archives' **ZipCrypto passwords constitute credential-like
  material**: their existence is confirmed, their type is a ZIP archive
  password (not a network credential), their location is six specific
  members of the outer `.fibrepack`, and they are **not device-specific** in
  any way this analysis could determine — no per-device or per-serial
  password derivation was observed in any unencrypted string. No password
  value was searched for, guessed, or used, per the phase's access boundary.
- `verify.key` (three copies, one per major sub-package) is a public/shared
  integrity-check artifact by naming convention; its actual bytes are
  encrypted and were not read. One binary string suggests the check may be a
  simple non-empty-file test rather than real signature verification —
  recorded as `INFERRED`, not confirmed, and not exploited.
- `enable_nm_permissions.sh` grants the running user passwordless polkit
  control over NetworkManager (WiFi) and system time/timezone. This is a
  kiosk-mode convenience, not a discovered secret, but is worth recording as
  an operational security-relevant fact: the AnisoTouch account can silently
  reconfigure networking/time without a sudo prompt.
- `fibreseek-installer`'s own `curl` invocations show plausible OTA endpoints
  (`ota.fibreseek3d.com`) matching the domain already confirmed live in
  `LM-008`; no URL was contacted by this analysis.

## Correlation with prior live (LM-*) evidence

| Prior claim | Prior confidence | New evidence | New confidence |
|---|---|---|---|
| `printer_setting`/`mqtt_bridge`/`ai_detection`/`error_indexer` module paths | STRONGLY INFERRED (loader mechanism) | exact path in ZIP central directory | **CONFIRMED** (path only; content still unknown) |
| `material_manager.py` is a flat module | STRONGLY INFERRED | it is `material_manager/__init__.py` + `material_manager/material_manager.py` | **CORRECTED**: it is a package |
| `aniso_bed_mesh.py` filename | INFERRED (no direct logger line) | exact path confirmed; MCU-side `.c`/`.h` also found | **CONFIRMED** (path); scope expanded |
| CAN nominal bitrate 1 Mbit/s | STRONGLY INFERRED | `CONFIG_CANBUS_FREQUENCY=1000000` and boot script's literal `bitrate 1000000` | **CONFIRMED** |
| `can0` `txqueuelen` 1024 | CONFIRMED (live observation only) | boot script explicitly sets `txqueuelen 1024` | **CONFIRMED** (now also source-evidenced) |
| `can0` consumer/purpose | UNKNOWN | alternate CAN-toolhead firmware/config variant found, not selected on Loom | **STRONGLY INFERRED** purpose; consumer on Loom still UNKNOWN |
| Rockchip SoC family (from `rockchip_canfd` alone) | STRONGLY INFERRED, no model claimed | `rknn_toolkit2` + `.rknn` models confirm NPU-targeted inference | **upgraded confidence**; still no specific model claimed |
| `remote` implementation location | UNKNOWN | `fibretouch-remote.zip`'s `moonraker_broker_bridge.py` is the leading candidate | **STRONGLY INFERRED**; content still UNKNOWN |
| `remote` is not a Moonraker component | STRONGLY INFERRED (absence from `/server/extensions/list` semantics) | exhaustively absent from the full 160-entry `moonraker.zip` component list | **CONFIRMED** |
| FibreTouch framework | UNKNOWN | Qt/QML native application, direct Moonraker WebSocket client | **CONFIRMED** |
| `ai_detection`'s WebSocket peer | UNKNOWN | `fibretouch-ai.zip` ships `ai_server.py` with the exact detection stack `ai_detection` exposes | **STRONGLY INFERRED** |
| `update_manager` `fibreseek-updater`/`-factory` config vs. log identity mismatch (Phase 2H-D) | CONFIRMED as one subsystem | `release_info_*.json` independently confirms `project_name: fibretouch-fs3` | reaffirmed, additional independent source |

## Remaining unknowns

- All source-level content behind the six ZipCrypto-encrypted nested
  archives: exact imports, classes, HTTP/WebSocket routes, event names,
  subprocess/database/file access, MQTT topics, and any external destination
  encoded in source.
- `remote`'s exact registration mechanism and callable methods.
- Whether `ai_server.py` truly is the process behind `127.0.0.1:8765`, and
  its exact protocol.
- How `fibretouch-ai.zip` and `fibretouch-remote.zip` are actually deployed
  (not referenced by `install.sh`).
- The exact MCU-flashing step and whether it runs automatically on update.
- Whether `verify.key`'s check is a real signature verification or a
  presence/non-empty check only.
- Purpose of `aniso_temp_compensation.py`, `piezoelectric_ceramic*.cfg`,
  `eddy.cfg`, and `utils/anisoprint_machine.xlsx`.
- Whether this exact package (build 256) is byte-identical to what Loom is
  currently running, or merely version-string-identical.


## Package access (private)

The `.fibrepack` nested archives are ZipCrypto-encrypted. The record of the offline package-access work — what was and was not attempted, and the boundary that stopped it — is kept separately in `package-access.md`, which is **private-only** and excluded from the public export (`tools/public_export.json`). It records that no archive was opened and no password value exists in the repository or its history.
