# Findings

The practical findings for a FibreSeeker 3 owner, each labelled and linked to
its evidence. Loom findings are scoped to one machine at a date; treat them as a
strong starting point, not a spec. Shorthand is in [glossary.md](glossary.md).

## Firmware and slicer bugs (corroborate 3ric's reports)

- **`M1001` / `M1002` are unknown to the firmware.** Rocket emits them, the
  firmware rejects them. *CONFIRMED* on Loom and by
  [3ricj/FibreSeeker3 #9](https://github.com/3ricj/FibreSeeker3).
- **`CASE_FAN` is undefined.** Print-start and resume call `CASE_FAN S=255`,
  which the firmware doesn't define; valid fan control is `M106 P0`/`M106 P4`.
  *CONFIRMED* (Loom + 3ric #11).
- **Error 10077 "Chamber temperature too high" reads the toolhead sensor.** The
  10077 trip matches the *toolhead* temperature, not the chamber (~34.8 °C when
  it fired at "63.8 °C"). *CONFIRMED* by 3ric #10; *OPEN QUESTION* whether
  Loom's check reads `toolhead_temp` (to be verified on-machine).
- **Error 10047 "Z axis homing false trigger" is a mistranslation.** The vendor
  table defines it as *no trigger after full movement*. *CONFIRMED* from the
  firmware error table.
- **The machine clock resets on reboot.** klippy.log timestamps go out of order
  across boots — read logs in file order. *CONFIRMED* (Loom; 3ric #21).

Detail: [firmware/FIRMWARE_ANALYSIS.md](firmware/FIRMWARE_ANALYSIS.md),
[firmware/VERSION_DIFF_2.2.30_TO_2.2.42.md](firmware/VERSION_DIFF_2.2.30_TO_2.2.42.md),
[community/Forums/2026-09-21-facebook-fibreseeker3-group.md](community/Forums/2026-09-21-facebook-fibreseeker3-group.md).

## Starting prints and reading state

- **Print start / `print_stats` state machine.** How prints start via Moonraker,
  what the `print_stats` states mean, and why the on-screen "preprinting"
  progress labels are misleading (the "homing" preprint step is actually the bed
  mesh). *CONFIRMED*. See
  [loom/PRINT_START_AND_STATE_MACHINE.md](loom/PRINT_START_AND_STATE_MACHINE.md).

## Calibration and safety

- **A dead Z probe drives the nozzle into the bed.** Loom's probe is the vendor
  toolhead piezoelectric-ceramic scheme (signal on main-MCU `PF5`). If it
  doesn't trigger, the vendor `G28` retries 4 × 375 mm into the bed — cut power,
  don't let it repeat. *CONFIRMED*.
- **A hotend refit can kill homing via the wrong fan socket.** After a hotend
  clean, Z homing failed because the toolhead front-cover fan cable had been
  refitted into the wrong toolhead-board socket. Re-plugging fixed it.
  *CONFIRMED* — the [../notebook/](../notebook/) 2026-09-21 session.
- **Full-calibration delta after removing the PTFE tube + fitting isolation
  pads.** PID retuned on Plastic 1; X offset corrected; Z datum essentially
  unchanged. *CONFIRMED*. See
  [../notebook/2026-09-17_calibration-before-after/](../notebook/2026-09-17_calibration-before-after/).

## PLA+ on the FFF side (Plastic 2)

Validated settings for SUNLU PLA+ 2.0 on the right/0.4 mm nozzle:

- 205 °C (first layer 210 °C), from a temperature tower. *EXPERIMENTAL*.
- Flow 0.96, from two flow-calibration passes. *EXPERIMENTAL*.
- `rotation_distance` 5.65 (−0.25 %) confirmed. Benchy **X0008** printed cleanly.

Sessions: [../notebook/](../notebook/) 09-14 through 09-15.

## Composite / Plastic 1 (CFC side)

- **Repeated clogs and a first-extrusion leak on the new composite hotend.** The
  cause looked systemic, not a single bad part; the PTFE tube was removed and
  isolation pads fitted. Not yet cleared for fibre. *EXPERIMENTAL / OPEN*. See
  the 09-15/09-16 [../notebook/](../notebook/) sessions.

## Materials

- **X-CCF drying status** and material compatibility notes:
  [machine/X_CCF_DRYING_STATUS.md](machine/X_CCF_DRYING_STATUS.md),
  [machine/MATERIALS_AND_COMPATIBILITY.md](machine/MATERIALS_AND_COMPATIBILITY.md).

---

New findings should be added here with a label and a link to the notebook
session, firmware doc, or manifest record that backs them.
