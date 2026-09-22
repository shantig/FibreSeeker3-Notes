# Loom capture session 2026-09-17T232853Z

- Purpose: establish the **post-calibration** state of Loom so it can be
  differenced against the accepted 2026-09-13 / 2026-09-15 / 2026-09-16
  baselines. Owner request: "check the before/after calibration states and see
  the delta of where we are", after removing the composite hotend PTFE tube,
  fitting isolation pads, and running a full calibration on 2026-09-17.
- Authorization: project owner, 2026-09-14 — full live access.
- Machine: Loom, `<printer-ip>`, Moonraker on port 7125. Printer idle, in
  `standby`, unhomed (`toolhead.homed_axes` empty) after the 18:07 local restart.
- Started `2026-09-17T23:28:53Z`, ended `2026-09-17T23:33Z`. All GETs.
  **No state-changing command was issued.** Authentication material sent or
  stored: none.

## Captures

| Provenance ID | Method and endpoint | HTTP | Body bytes | SHA-256 |
|---|---|---:|---:|---|
| LM-027 | `GET /printer/objects/query?save_variables&bed_mesh&configfile&gcode_move&toolhead` | 200 | 288,702 | `4d55322ba4c056681a9123fe4b48daac9fd8df0946f3da6b40abdba378dd5ddc` |
| LM-028 | `GET /server/files/config/printer.cfg` | 200 | 9,557 | `e42225894ec010a32e99f0280c802b798f9d70d0f19d2f7cd25b1764eee10841` |
| LM-029 | `GET /server/files/config/calibration.cfg` | 200 | 18,547 | `522c9dba9b9f5885f4529b8cda087032009c1071cff2cdbc65577ca6c0751b1c` |
| LM-030 | `GET /server/files/config/print_control.cfg` | 200 | 33,916 | `433fe2a35b0b52a2f367fbb8398bb013c586a21ae4cf53d714d92365abbcc3a7` |
| LM-031 | `GET /server/files/config/base_control.cfg` | 200 | 11,604 | `110937b176f8e214b32247b373bed6630fa047a49ff07f67eda73f078d2277bd` |
| LM-032 | `GET /server/files/config/global_variables.cfg` | 200 | 8,733 | `844a2ddca65870a15e59c6805bdc1442f7883835ab72cf2bed13e0aa2d4b821e` |
| LM-033 | `GET /server/files/config/variables.cfg` | 200 | 1,024 | `39ad9337f457d106cf3cb8c64ceed8f68e8007b6a96c88edd6970322c8058cc1` |
| LM-034 | `GET /server/files/config/xyz_offset.ini` | 200 | 157 | `3f89fa97eee9bd7b1834984d93a88cdf721fa4788c22cb5bf4b484a5578976ae` |
| LM-035 | `GET /server/files/config/spools.json` | 200 | 855 | `95aa82ce5bce1f40aae216c22e88d1549281f1d069f32044d382e6ffec8da3be` |
| LM-036 | `GET /server/files/config/materials.json` | 200 | 3,897 | `07cfd7af1aafb1f289bd5ec39d71be02bb07f4ade0557aeccfeff4fdac68e91f` |
| LM-037 | `GET /server/files/config/printer_base.cfg` | 200 | 8,604 | `e50f9a8a7d9eda0e1cd96a77deb8ed13f47ebb27493c72a5e23a54e3a5d0f126` |
| LM-038 | `GET /server/files/config/tool_switch.cfg` | 200 | 10,779 | `004a3f88cd3071cc3ebbf5f1d765bec39ae248a7f5ec2848a717c43e6f3aad0d` |
| LM-039 | `GET /server/files/config/toolhead.cfg` | 200 | 78 | `1a9821ef6edfff16e33e93046c4f1e5e888e3047489855882eca470943464df5` |

## Logs read but not preserved here

`klippy.log`, `klippy.log.1`, `moonraker.log` and
`print_logs/anisotouch_2026-09-17.log` were downloaded to a scratch path and
read for the 2026-09-17 timeline. They are **not** committed: the FibreTouch log
contains the machine's Moonraker PIN and account-binding fields. The findings
drawn from them are recorded in
`07_Troubleshooting/Loom/2026-09-17-T1/RESULTS.md` with timestamps, and the logs
themselves belong on the NAS if they are to be kept.

## Handling notes

- All thirteen bodies are FibreSeek-authored machine configuration or live
  machine state. They are `EXPERIMENTAL` first-party FibreSeek evidence from the
  owner's machine, not manufacturer guidance.
- `printer.cfg` byte size is unchanged from 2026-09-15 (9,557) but the content
  differs: the whole delta is inside the `#*#` SAVE_CONFIG autosave block.
- `calibration.cfg` and `print_control.cfg` are **byte-identical** to the
  2026-09-15T155418Z captures — no vendor macro logic changed across the
  calibration.
- No credentials, tokens, Wi-Fi configuration or cookies are present in any
  preserved body; checked before writing.
