# Loom fibre channel shown as not loaded — diagnosis

Opened 2026-09-12. Status: **RESOLVED per owner report (2026-09-12) — the
Fibre spool length was 0 km by default; after the owner set the correct length
in Edit Filament, the Fibre ring shows "X-CCF 100%".** Hypothesis H4 (missing
spool data) is supported; see §7. F1 steps 1, 3 and 4 were not run.

Evidence labels: `CONFIRMED` (directly shown by a cited preserved artifact),
`USER-OBSERVED` (owner report or owner photo without machine capture),
`INFERENCE`, `OPEN QUESTION`, `UNKNOWN`. FibreSeek/Loom evidence only; no
Anisoprint legacy evidence. Nothing here is manufacturer guidance.

## 1. Report (USER-OBSERVED, 2026-09-12)

Owner, verbatim excerpt:

> now the HMI is showing that the fibre isn't loaded, even though it is and
> fibre extrusion has been calibrated. There was a clog from the factory in
> both of the hotends but now i'm experiencing a new issue with the fibre side.

Context:
- The preceding right-plastic (P2) load failure is closed on the owner's
  report of a cleared factory hotend clog
  (`../2026-09-12_P2_load_wait_insert/DIAGNOSIS.md` §0.8).

Photo IMG_4028.jpg (created 2026-09-12 23:13:17 UTC ≈ 18:13 local; HMI clock
shows 18:05; SHA-256 in `../PHOTOS_2026-09-12.md`) shows the FibreTouch
filament screen:

| Channel group | Ring label | Material | Remaining indicator | Ring appearance |
|---|---|---|---|---|
| CFC | Plastic 1 | PETG | 99% | light |
| CFC | Fibre | X-CCF | **null** | dark |
| FFF | Plastic 2 | PETG | 99% | light |

Side buttons: Load, Unload, Edit.

`UNKNOWN`:
- how the fibre was loaded (HMI Load flow to completion, manual feed, or
  calibration flow);
- which screen or popup says "not loaded" beyond this ring;
- whether printing is blocked;
- whether the ring was dark or "null" before the fibre was loaded;
- the installed FibreTouch version.

## 2. Relevant evidence already in the repository

- **Fibre presence switch, `CONFIRMED` (LM-012, last config dump,
  2026-09-11 14:35).** `filament_switch_sensor filament_sensor`:
  `switch_pin ^PG4`, `debounce_delay 5`.
  - While printing it pauses with "extruder fiber filament ran out!".
  - Otherwise it logs `M118 [filament_sensor] Fiber filament ran out in the
    extruder: …`. That makes fibre-sensor dropouts visible in klippy.log.
  - The load flow restores this sensor's debounce to 5 s after each P2 load
    (`_restore_f_filament_sensor_debounce`, LM-009/LM-012).
- **Other fibre-path sensing, `CONFIRMED` (LM-005/LM-012).**
  - `tension_sensor`: SPI, `jam_deviation_limit 55000`,
    `trigger_sample_count 6` since 2026-09-11.
  - Fibre extruder `extruder2`: `rotation_distance 37.5`, adjusted through
    `SET_EXTRUDER_MODE`, `RESTORE_EXTRUDER2`, `ALIGN_FIBRE_LENGTH`.
  - Fibre load/unload variables: `f_long_distance 1100`,
    `f_melt_distance 250`, `f_step_length 30`, `f_melt_step_length 5`,
    `f_p1_unload_speed 1800`.
- **HMI spool/channel state, `CONFIRMED` (FS-152/FS-153 symbol tables).**
  - Both HMI releases have `FilamentModel::onSpoolsDetailUpdate`,
    `onSpoolMaterialInfoUpdate`, `sigRequestSpoolsDetail`,
    `Settings::spoolUiState`/`setSpoolUiState`,
    `Settings::writeFibretouchNullFieldsFromCache`,
    `ResetPageModel::getLoadedFilamentChannels`, plus a `FibreKeyModel`
    (`checkUsbForFibrekey`, `updateFromDatabase`) and `FibreKeyDecryptor`.
  - 2.2.42.831 adds `FilamentModel::isChannelLoaded(int)`,
    `applyChannelLoaded(int)`, `reconcileChannelsWithSpools()`,
    `channelSpoolData(int)`, `readSpoolUiState()`,
    `sigUpdateSpoolMaterial(QString,QString,QString,float,float,bool)`,
    and `indexFromSpoolId`/`spoolIdFromIndex`. 2.2.30.613 has none of these.
  - Symbol names only; the code behind them is not recovered.
- **Firmware version.** Loom's MCU build is `v2.2.38.721-32-g02b98453`
  (LM-012). Which HMI build is installed, and whether it contains the
  2.2.42-style channel-loaded logic, is `UNKNOWN`.
- **No fibre load trace is preserved.** LM-012 ends 2026-09-12 14:00:49
  local, before the fibre work described in the report.

## 3. Inference

- `INFERENCE`: "null" is shown where the plastic rings show a percentage,
  which reads like a null data field rendered as text. It points to missing
  remaining-quantity data in the fibre spool record, not to a sensor reading.
- `INFERENCE`: the symbol set suggests the HMI keeps a per-channel "loaded"
  state and reconciles it with spool records held by Moonraker
  (`material_manager`), so the ring can disagree with the physical state. It
  may equally depend on the fibre presence switch; the code is not available
  to decide.

## 4. Hypotheses

| ID | Hypothesis | What would support it |
|---|---|---|
| H1 | HMI channel or spool bookkeeping: the fibre channel is not marked loaded, or its spool record has null fields | `filament_sensor` reads detected while the ring stays dark or "null"; Edit page shows empty/null spool fields |
| H2 | Fibre presence switch (`filament_sensor`, PG4) reads not detected although fibre is loaded | `QUERY_FILAMENT_SENSOR SENSOR=filament_sensor` → not detected; klippy.log "Fiber filament ran out" messages |
| H3 | The fibre load flow did not finish (cancelled or exited), so the channel was never marked loaded | klippy.log fibre load trace ends in a cancelled or exited state rather than finished |
| H4 | Fibre spool/material data missing (e.g. no remaining length, or no FibreKey-provided data) | Edit page shows X-CCF with null length/weight; loaded state independent of it |

These can combine: for example H3 or H4 could cause H1.

## 5. Most discriminating next test — F1 (read-only)

With the fibre loaded as it is now:
1. `QUERY_FILAMENT_SENSOR SENSOR=filament_sensor`.
2. A photo of the HMI Edit page for the Fibre channel.

No motion, no heating, no settings saved.

| F1 result | Supports | Rejects | Next |
|---|---|---|---|
| Sensor detected; Edit page shows null/empty spool fields | H1/H4 (bookkeeping or spool data) | H2 | Decide with the owner whether to complete spool data or rerun the HMI fibre Load flow; a log capture would test H3 |
| Sensor detected; Edit page shows complete spool data | H1/H3 (channel state, not data) | H2, H4 as sole cause | Log capture to check how the fibre load flow ended |
| Sensor not detected | H2 (sensor or fibre not reaching the switch) | H1 as sole cause | Fibre sensor toggle test (like T1) |

## 6. Remaining uncertainty

- `OPEN QUESTION`: what drives the HMI "loaded" ring and the "null" value.
  HMI and `material_manager` code is not recovered.
- `OPEN QUESTION`: how the fibre was loaded and calibrated, and how that flow
  ended.
- `OPEN QUESTION`: where `filament_sensor` (PG4) sits on the fibre path.
- `OPEN QUESTION`: role of `FibreKeyModel` (USB fibre key) in spool data.
- `UNKNOWN`: installed FibreTouch/HMI version.

## 7. Resolution (USER-OBSERVED, 2026-09-12)

Owner, verbatim excerpt: "That was it! Looks like it set it to 0km by default,
i changed it to the correct lenght."

Photos (SHA-256 in `../PHOTOS_2026-09-12.md`):
- **IMG_4035.jpg (00:00:10 UTC 2026-09-13; HMI clock 19:00):** *Edit
  Filament* dialog.
  - Filament Brand: FibreSeek; Filament Type: X-CCF; Color swatches.
  - Length options: 0.5km / 1.0km / 1.5km / Custom (Custom highlighted).
  - Buttons: Clean, Save.
  - The background ring still shows "X-CCF null".
- **IMG_4036.heic (00:02:20 UTC; HMI clock 19:02):** filament screen after the
  change. CFC: Plastic 1 PETG 99%, **Fibre X-CCF 100%**; FFF: Plastic 2 PETG
  99%.

Reading:
- The HMI "null" for the Fibre channel coincided with a spool length of 0 km.
  Setting a non-zero length through Edit Filament → Save changed it to 100%,
  and the owner reports the not-loaded indication resolved.
- `INFERENCE`: the remaining percentage is computed against the configured
  spool length, so a 0 km length yields no value ("null"). The loaded-state
  indication depends on that spool record, not only on the fibre presence
  switch.
- `UNKNOWN`:
  - the length value the owner entered (Custom value not visible);
  - whether the 0 km default came from a fresh install, the 2026-09-11 firmware
    change, or a spool reset;
  - whether `filament_sensor` would have read detected (F1 step 1 not run).
- `OPEN QUESTION` (unchanged): the unit and encoding of fibre spool length in
  Rocket/printer data (`FiberSpoolLength`) remain unresolved elsewhere in this
  repository. This HMI shows lengths in km.
- Owner-facing note, `EXPERIMENTAL`, not manufacturer guidance: if the Fibre
  ring shows "null" again, check the Fibre spool length in Edit Filament
  before investigating sensors.

