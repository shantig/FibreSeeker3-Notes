# FibreSeeker 3 Facebook group — posts on 3ric's findings (screenshots 2026-09-21)

Provenance `COMMUNITY` (CM-007). Five screenshots the owner took on 2026-09-21
in the "FibreSeeker 3 / Fibre 3D Printer Community" Facebook group. Everything
the posts say is the posters' claim. The Loom cross-checks below are
`EXPERIMENTAL` evidence from this repository and are cited where they are used.

## What the posts say

| Post (age at capture) | Author | Content |
|---|---|---|
| ~6 days | 3ric Johanson | Ran Rocket Slicer on Benchy with ten G-code profiles and filed eight slicer-output issues ([3ricj/FibreSeeker3](https://github.com/3ricj/FibreSeeker3) #1–#8: unretracted travel, aligned seams, perimeter gaps, volumetric flow, layer time, bridging, fan schedule, motion contract). In the replies he says FS's official Facebook group has held his posts about problems in "pending approval" for weeks. |
| ~4 days | 3ric Johanson | Sent three firmware issues to FS: slicer-emitted `M1001`/`M1002` are unknown to the firmware (#9, 181 rejections across his hybrid jobs); error 10077 "Chamber temperature too high: 63.8C" matches the **toolhead** sensor, while the chamber read about 34.8 °C (#10); print-start and resume call an undefined `CASE_FAN S=255` (#11). |
| ~2 days | 3ric Johanson | FS's reply: all three are forwarded to the development team for verification. No fix or date. |
| ~2 days | another owner | On firmware 2.2.42.831, error 10077 pauses his PETG prints. He asks whether there is a fix. 3ric: none yet. He suggests opening the door and lid, and notes the case fan doesn't work, so the machine can't hold temperature. |

## Cross-check against Loom evidence

- **`CASE_FAN` — corroborated.** `print_control.cfg` captured on 2026-09-17
  (`sources/loom/sessions/2026-09-17T232853Z/configs/print-control/`) calls
  `CASE_FAN S=255` at line 191 in `SDCARD_PRINT_FILE` and at line 433 in
  `RESUME`. No macro defines it. The 2026-09-12 klippy log records
  `Unknown command:"CASE_FAN"` three times. The same macros turn fans on with
  valid `M106 P0` and `M106 P4` calls, which matches 3ric's report that the
  individual fans work.
- **`M1001`/`M1002` — corroborated.** The 2026-09-12 klippy logs contain 17
  unique `Unknown command:"M1001"` lines and 17 for `M1002`. They pair up about
  30 s apart. The PETG scraper demo G-code
  (`2026-09-13T054125Z/.../gcode-demo-petg-scraper`) contains 34 of these
  commands. The plastic-only PLA Benchy demo contains none, consistent with
  their marking fibre sections (`INFERENCE`).
- **10077 — partly corroborated.** `printer.cfg` defines the chamber as
  `[heater_generic chamber]` (sensor `PB0`, max 80 °C) and a separate
  `[temperature_sensor toolhead_temp]` (the toolhead board thermistor
  `toolhead:PC3`, max 100 °C). Two distinct sensors therefore exist, and a check
  that reads `toolhead_temp` would report the toolhead board as "chamber". The
  10077 check itself appears in **no** configuration or log captured here.
  `OPEN QUESTION`: it most likely lives in the HMI or a Klipper extras module
  (`INFERENCE`). Locating it on Loom is live reverse-engineering work (authorized)
  and has not been done.
- **Related, not in 3ric's list:** Loom's `extruder2` (Fibre zone) reads a
  constant ~200.9 °C at idle on two hotend assemblies (2026-09-16-T1). On GitHub
  #13, another owner reports the same symptom and 3ric sees 200.7 °C on his own
  machine.

## Relevance to this KB

- The 10077 mislabel puts a ceiling on hot-chamber or long PETG runs on Loom
  until FS fixes it. The door-open workaround is 3ric's claim and has not been
  tested here.
- `OPEN QUESTION` (FS): do `M1001`/`M1002` do anything in the fibre path?
  Unknown commands are ignored, so any intended fibre-section behaviour is not
  happening today.
