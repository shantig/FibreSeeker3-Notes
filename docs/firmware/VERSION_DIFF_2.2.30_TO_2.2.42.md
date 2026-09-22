# FibreSeek SK3 Firmware Version Diff: 2.2.30.613.256 → 2.2.42.831.320

Phase 2I-A. Semantic diff between the two owner-supplied official packages.
Because the six proprietary nested archives (`moonraker.zip`, `klipper.zip`,
`anisotouch-config.zip`, `crowsnest.zip`, `fibretouch-ai.zip`,
`fibretouch-remote.zip`) are ZipCrypto-encrypted in both releases and no
password is available, this diff is a **filename/size-level diff of ZIP
central directories**, not a content diff. Where a filename or size change
strongly implies a behavioral change, that inference is stated explicitly and
labeled; source-level confirmation is not possible without decryption. See
`FIRMWARE_ANALYSIS.md` for the full per-package structural inventory.

## Outer package (top-level members)

| Change | Detail |
|---|---|
| Added | `anisotouch.service` (systemd unit) |
| Added | `disable_system_update_prompt.sh` |
| Added | `factory_gcodes/` (17 demo print files, distinct from `factory_test_gcodes/`) |
| Unchanged (byte-identical SHA-256) | `install.sh` |
| Unchanged | `boot.mp4`, `websockets-13.1-py3-none-any.whl`, `klipper.config` |
| Grown | `factory_test_gcodes/` (8 → 18 files); `enable_nm_permissions.sh` (1,883 → 3,437 B, content not diffed, both read in full — see below) |

### `anisotouch.service` (new)

**Meaningful, confirmed behavioral change.** 2.2.30.613 has no systemd unit
for the HMI app in the package; 2.2.42.831 ships one, running `anisotouch` as
`Type=simple` with `Restart=on-failure`/`RestartSec=5s` under a graphical
session. This formalizes what `install.sh`'s manual `killall anisotouch` /
`cp` dance in 2.2.30 handled ad hoc — the app now has proper supervised
restart-on-crash behavior starting in 2.2.42. Whether Loom (still on
2.2.30.613) has an equivalent unit installed some other way is `UNKNOWN`.

### `disable_system_update_prompt.sh` (new)

**Meaningful, confirmed behavioral change**, read in full as plain text. Its
own comment states the motivation directly: *"the device is an all-in-one
product; background APT auto-updates could hog bandwidth/CPU and could break
the Klipper environment."* It: sets `Prompt=never` in
`/etc/update-manager/release-upgrades`; zeroes all `APT::Periodic::*`
settings in `/etc/apt/apt.conf.d/20auto-upgrades` (and patches
`10periodic` if present); disables and masks `apt-daily.timer`,
`apt-daily-upgrade.timer`, and `unattended-upgrades.service`; overrides
`update-notifier`/`update-manager`/`gnome-software-service` desktop autostart
entries to `Hidden=true`; disables related `gsettings` notification keys; and
kills any currently-running `update-manager`/`update-notifier`/
`check-new-release` processes. **This is a robustness fix added between
these two releases**, consistent with a real-world incident class where an
Ubuntu OS-level unattended upgrade interfered with the Klipper environment —
directly relevant to "may explain known Loom behavior or bugs" if Loom (still
on the pre-fix 2.2.30.613) has ever experienced an unexplained
service/environment disruption not attributable to FibreSeek's own
components.

### `factory_gcodes/` (new)

17 new demo/showcase print files (e.g. `PLA-Benchy.gcode`,
`PETG-Molle Organiser.gcode`, `PLA-S Hook.gcode`) plus
`factory_gcodes/demoLocalizations.json`, distinct from the pre-existing
`factory_test_gcodes/` (calibration/test prints, which also grew from 8 to 18
files with additional PLA/PETG variants). Marketing/demo content, not an
architectural change.

## `klipper.zip`

| Change | Detail |
|---|---|
| Added | `klippy/extras/bed_temp_linearity.py` |
| Unchanged | all other 2,105 entries (paths only checked; content encrypted both releases) |

**One new custom Klipper extra.** Name strongly suggests bed-thermistor
linearity/compensation logic (a common fix for thermistor non-linearity at
temperature extremes). Not present in Loom's live captures (no such object or
macro was ever observed on Loom, which runs 2.2.30.613) — **CONFIRMED absent
from Loom's currently-running configuration**, consistent with Loom not yet
having this firmware version.

## `moonraker.zip`

| Change | Detail |
|---|---|
| Added | `moonraker/components/enclosure_temp_monitor.py` |
| Unchanged | all other 160 entries |

**One new custom Moonraker component.** This is the most architecturally
significant single change in this diff: it very plausibly relates to, extends,
or partially supersedes `blinds_hall_monitor`'s confirmed chamber-heater/
door-interlock role (Phase 2H-D's tiered analysis of the Sep 7 door
experiment). A dedicated Moonraker-level "enclosure temperature monitor"
component is a natural place to centralize the chamber-heater-off →
cooling-fan-delay behavior currently implemented in the Klipper-side
`blinds_hall_monitor` extra, or to add finer monitoring/alerting on top of it.
**This is `STRONGLY INFERRED` from naming and domain overlap only** — its
actual relationship to `blinds_hall_monitor` (replaces it, extends it, or is
unrelated) cannot be determined without decrypting either file. Not present
on Loom (2.2.30.613).

## `anisotouch-config.zip`

| Change | Detail |
|---|---|
| Added | `bed_temp_linearity.cfg` |
| Added | `fans_v2.1_new.cfg` |
| Added | `fans_v2.2_new.cfg` |
| Unchanged | all other 40 entries |

`bed_temp_linearity.cfg` is the configuration counterpart to the new Klipper
extra above. `fans_v2.1_new.cfg`/`fans_v2.2_new.cfg` are revised fan-control
configs specifically for hardware revisions v2.1 and v2.2 (the existing
`fans_v2.0.cfg`/`fans_v2.2.cfg`/`fans.cfg` are retained, not replaced) —
**STRONGLY INFERRED** to be a fan-behavior fix or tuning change scoped to
those two hardware revisions specifically, content not confirmable.

## `fibretouch-remote.zip` and `crowsnest.zip`

**No filename or count changes at all** between releases (same 5 entries for
`fibretouch-remote.zip`; same 420 entries for `crowsnest.zip`). Combined with
`install.sh` being byte-identical, this is reasonably strong circumstantial
evidence that the `remote` agent and the webcam-streaming stack did not
change between these two releases — though content-level changes within
unchanged filenames cannot be ruled out without decryption.

## `fibretouch-ai.zip` — the largest change in this diff

Package size dropped from **439,690,430 bytes to 192,794,965 bytes**
(≈247 MB smaller, a 56% reduction), fully explained by filename evidence:

**Removed entirely: the whole `pkg/` third-party wheel cache** (~55 packages,
including `torch-2.2.0`, `torchvision-0.17.0`, `transformers-4.46.3`,
`sentence_transformers-3.2.1`, `tokenizers-0.20.3`, `faiss_cpu-1.8.0.post1`,
`onnxruntime-1.16.3`, `onnx-1.16.1`, `scikit_learn-1.3.2`, `scipy-1.10.1`,
`pandas-2.0.3`, `opencv_python-4.12.0.88`, `rknn_toolkit2-2.3.2`,
`numpy-1.24.4`, and about 40 more supporting wheels).

**STRONGLY INFERRED explanation**: the heavy Python ML dependency stack
(several hundred MB of PyTorch/Transformers/ONNX/RKNN wheels) was very likely
already installed into a persistent environment during the first (2.2.30 or
earlier) install, and later releases stopped re-shipping unchanged
dependencies on every OTA update — shipping only the changed application code
and models. This is a reasonable, evidence-consistent explanation but **is
not confirmed**: the actual install/update logic that would decide whether to
reinstall dependencies is inside the encrypted `fibretouch-ai.zip` content
(or `fibreseek-installer`, whose relevant logic is compiled) and was not
recoverable.

**Model files changed** (iterative retraining, not architecture change):

| Removed (2.2.30) | Added (2.2.42) |
|---|---|
| `models/defect_20260610.rknn` | `models/defect_20260716s.rknn` |
| | `models/defect_20260728s.rknn` |
| `models/object_detect_0611_i8.rknn` | `models/object_20260616s.rknn` |
| | `models/object_20260824.rknn` |
| | `models/.rknn` (anomalous empty-basename entry; recorded as observed, purpose unknown) |

The defect-detection model was updated twice (2026-07-16, 2026-07-28) and the
object-detection model twice (2026-06-16, 2026-08-24) between these two
firmware releases — confirming active, ongoing model iteration on the vendor
side. `models/error_search-v1.5/`, `error_db2_0225.faiss`, and
`error_db2_ox_0225.sqlite` (the semantic error-search subsystem) are
**unchanged** between releases (not listed as added/removed), meaning that
subsystem is stable across this version span.

## Summary: what actually changed vs. what stayed the same

**Changed (7 concrete deltas, all filename/size-level, all consistent with a
coherent story):**

1. `anisotouch.service` added — HMI now has proper systemd supervision.
2. `disable_system_update_prompt.sh` added — OS-level auto-update suppressed,
   explicitly to protect the Klipper environment.
3. `klippy/extras/bed_temp_linearity.py` + `bed_temp_linearity.cfg` added —
   new bed-thermistor linearity feature.
4. `moonraker/components/enclosure_temp_monitor.py` added — new chamber/
   enclosure monitoring component, likely related to `blinds_hall_monitor`'s
   domain.
5. `fans_v2.1_new.cfg` / `fans_v2.2_new.cfg` added — fan-behavior revision for
   two specific hardware revisions.
6. `fibretouch-ai.zip`'s bundled ML dependency wheelhouse removed (~247 MB);
   object/defect detection models refreshed twice each.
7. `factory_gcodes/` demo-print set added; `factory_test_gcodes/` expanded.

**Did not change:** `install.sh` (byte-identical), `fibretouch-remote.zip`
(`remote`/`moonraker_broker_bridge.py`, identical filenames), `crowsnest.zip`
(identical filenames), the semantic error-search model/index files, the core
Klipper/Moonraker checkouts apart from the two additions above, `boot.mp4`,
and the bundled `websockets` wheel. **Corrected 2026-09-12:** the claim about
the core Klipper/Moonraker checkouts (and the config package) is wrong at
member size/CRC level — see "Correction — member-level size/CRC deltas" below.

**Most likely to explain observed Loom behavior or bugs**, in priority order:
`disable_system_update_prompt.sh` (if Loom has ever shown unexplained
service/environment disruption, an unattended OS upgrade on the still-running
2.2.30.613 build is now a concrete, named candidate cause this fix directly
addresses) and `enclosure_temp_monitor.py` (if Loom's chamber-heater/door
behavior — the subject of Phase 2H-D's Sep 7 analysis — has open questions,
this new component may be the vendor's own fix or refinement for exactly that
area, though its precise relationship to `blinds_hall_monitor` is unconfirmed).

## Correction — member-level size/CRC deltas (2026-09-12)

Found during the Loom P2 load diagnosis
(`notebook/2026-09-12_plastic2-load-failure/DIAGNOSIS.md`).
Method: read each inner archive's ZIP central directory in both `.fibrepack`
files and compare `(uncompressed size, CRC-32)` for members present in both.
No decryption; central-directory metadata is readable for encrypted entries.
A changed CRC shows the file bytes differ; it does not show what changed or
whether behavior changed. Content remains `UNKNOWN`.

| Inner archive | Members 2.2.30 → 2.2.42 | Added | Removed | Changed size/CRC |
|---|---|---|---|---|
| `klipper.zip` | 1,959 → 1,960 | 1 | 0 | 31 |
| `moonraker.zip` | 142 → 143 | 1 | 0 | 11 |
| `anisotouch-config.zip` | 40 → 43 | 3 | 0 | 20 |
| `fibretouch-remote.zip` | 4 → 4 | 0 | 0 | 2 |
| `fibretouch-ai.zip` | 107 → 52 | 5 | 60 | 3 |
| `crowsnest.zip` | 366 → 366 | 0 | 0 | 0 |

`klipper.zip` changed `klippy/` members (bytes, 2.2.30 → 2.2.42):
`configfile.py` 25,446→26,375; `extras/aniso_temp_compensation.py`
11,065→16,819; `extras/bed_mesh.py` 91,734→127,807; `extras/bed_tilt.py`
4,540→4,575; `extras/exclude_object.py` 11,766→12,172;
`extras/filament_motion_sensor.py` 4,838→7,374;
`extras/filament_switch_sensor.py` 7,617→8,289; `extras/gcode_move.py`
25,469→28,366; `extras/homing.py` 18,302→24,409; `extras/load_unload.py`
109,069→111,097; `extras/powerloss_progress.py` 27,728→33,351;
`extras/print_stats.py` 19,803→20,013; `extras/probe.py` 41,656→42,415;
`extras/skew_correction.py` 7,606→7,641; `extras/statistics.py` 2,981→3,458;
`extras/tension_sensor.py` 49,921→51,949; `extras/tuning_tower.py`
4,668→4,871; `extras/virtual_sdcard.py` 62,497→54,381; `extras/xyz_align.py`
30,528→35,342; `extras/z_thermal_adjust.py` 7,633→7,683;
`kinematics/extruder.py` 15,926→18,723; `queuelogger.py` 2,943→3,343;
`toolhead.py` 33,486→36,438; `__pycache__/msgproto.cpython-38.pyc` (same size,
CRC changed). Non-`klippy/` changes: `out/motherboard.bin`, `out/toolhead.bin`,
`out/toolhead_can.bin` (same sizes, CRC changed), the three
`out/bootloader_*.bin` files (each +48 B), and one `kconfiglib` `.pyc`.

Unchanged size and CRC, relevant to extruder/loading: `klippy/extras/tmc.py`,
`klippy/extras/tmc2240.py`, `klippy/extras/extruder_stall_detector.py`,
`klippy/extras/force_move.py`.

`moonraker.zip` changed: `ai_detection.py`, `error_indexer.py`,
`file_manager/metadata.py`, `klippy_apis.py`, `klippy_connection.py`,
`material_manager/material_manager.py`, `printer_setting.py`,
`simplyprint.py`, `timelapse.py`, `update_manager/net_deploy.py`,
`zeroconf.py`.

`anisotouch-config.zip` changed: `base_control.cfg`, `calibration.cfg`,
`crowsnest.conf` (same size), `error_info.xlsx`, `fans_v2.0.cfg`,
`fans_v2.2.cfg`, `filament_switch_sensor_v2.0.cfg` (6,725→8,096),
`gcode_test.cfg`, `heavy_duty_brush.cfg`, `materials.json`, `moonraker.conf`,
`nozzle_cleaning_station.cfg`, `piezoelectric_ceramic_v2.0.cfg`,
`print_control.cfg`, `printer.cfg`, `printer_base_v2.1.cfg`,
`printer_base_v2.2.cfg`, `printer_bed_mesh.cfg`, `tool_switch.cfg`,
`variables.cfg`.

The MCU firmware binaries (`out/motherboard.bin`, `out/toolhead.bin`,
`out/toolhead_can.bin`) have different CRCs, so they are not byte-identical.
Whether flashing them changes MCU behavior is `UNKNOWN`.

## `fibreseek-installer` binary — behavioral diff (Phase 2I-B, from unencrypted symbol tables)

Both `fibreseek-installer` binaries are **not stripped**, so a full exported
symbol-table diff (153 text symbols in 2.2.30 vs. 183 in 2.2.42; see
`docs/firmware/FIRMWARE_ANALYSIS.md`'s Phase 2I-B section and
`sources/firmware/*/anisotouch-fibreseek-installer-symbols-and-strings.txt`)
is **CONFIRMED source-level evidence**, not inference, for the following
installer behavior changes:

| Change | Detail |
|---|---|
| Removed | `killProcess(string, Logger&)` — crude process-kill shutdown of `anisotouch` before update |
| Added | `stopAnisotouchForUpdate`, `stopUserService`/`stopSystemService`, `stopPrinterServices`, `setupAnisotouchService`, `ensureGuiEnvironment` — proper systemd service lifecycle management replacing the kill-based approach |
| Added | `reexecInTransientScopeIfNeeded`, `detachInstallerFromParentCgroup` — installer now re-execs into a transient systemd scope and detaches from its parent's cgroup, plausibly to avoid self-termination when stopping `anisotouch.service` |
| Added | `disableSystemUpdatePrompt(string, Logger&)` — installer itself now runs this step |
| Added | `loadDemoLocalizationConfig`/`DemoLocalizationConfig`; `copyFactoryGcodesIfNeeded` gained an extra path parameter | matches the new `factory_gcodes/`/`demoLocalizations.json` |
| Added | `file_utils::getHomeDirectory()`; `execCommand` gained an output exit-status parameter |
| Changed | `FibreseekInstaller` constructor: 2 string parameters → 3; `shouldLinkVersionedConfig` gained a trailing `bool` parameter |

This is the single clearest, most directly source-confirmed behavioral
change set in this entire diff: 2.2.42's installer treats `anisotouch` as a
properly supervised systemd service throughout install/update, where
2.2.30's installer manipulated the raw process directly.

## Confidence summary

| Finding | Confidence |
|---|---|
| The 7 filename-level deltas listed above exist | CONFIRMED (ZIP central directory, both packages, cross-checked by diff) |
| `fibretouch-ai.zip`'s size drop is due to wheel removal | CONFIRMED (exact filename accounting matches the size delta) |
| Dependency-reshipping-avoidance explains the wheel removal | STRONGLY INFERRED |
| `enclosure_temp_monitor.py` relates to `blinds_hall_monitor` | STRONGLY INFERRED (domain/naming only) |
| `fans_v2.1_new.cfg`/`fans_v2.2_new.cfg` are a fan behavior fix | INFERRED (naming only, content unknown) |
| `remote` and `crowsnest` are unchanged in behavior | STRONGLY INFERRED (filenames + sizes identical; content not diffable) |
| Any content-level change inside unchanged-filename encrypted files | UNKNOWN — cannot be ruled out |
| 67 shared members inside the inner archives changed bytes (size and/or CRC-32), including `load_unload.py`, both filament sensor modules, `kinematics/extruder.py`, and the MCU firmware binaries (2026-09-12 correction) | CONFIRMED (central-directory size/CRC comparison); what changed is UNKNOWN |
| `fibreseek-installer`'s systemd-based service lifecycle replaces process-killing in 2.2.42 | CONFIRMED (symbol-table diff of unencrypted, un-stripped binaries) |
| MCU firmware flashing uses Klipper's own `scripts/flashtool.py`, independently per board | CONFIRMED (strings in unencrypted `fibreseek-installer`, both releases) |
