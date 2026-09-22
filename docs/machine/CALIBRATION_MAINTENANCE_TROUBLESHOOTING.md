# Calibration, Maintenance, and Troubleshooting

## Calibration

- **FACT (FS-120):** built-in calibration categories include vibration, nozzle
  offset, bed leveling, and nozzle temperature.
- **FACT (FS-139):** the fiber-extrusion service check commands 100 mm and treats
  ±0.5 mm as the comparison tolerance; the nozzle is heated above 180°C during
  that check.
- **FACT (FS-147):** the layer-shift SOP includes manual nozzle-offset adjustment
  direction and an example in millimetres.
- **FACT (FS-120, FS-147):** FibreSeek exposes automatic Nozzle Offset under
  Print Calibration. If residual plastic/fiber XY deviation remains, the SOP
  directs correction by the measured millimetres: plastic right/up requires
  decreasing X/Y respectively.
- **OPEN QUESTION:** no public numeric XY acceptance tolerance or calibration
  target specification was recovered.
- **FACT (FS-132, FS-133, FS-136–FS-144):** hotend, sensor, heater, and unclogging
  procedures require nozzle-offset recalibration after relevant service.
- **FACT (FS-137):** the CFC nozzle replacement SOP specifically requires
  selecting only Nozzle offset after replacement and warns that skipping it may
  cause printing issues.
- **OPEN QUESTION:** no FibreSeek equivalent of `NozzleOffsetTest.gcode` was
  located in the bounded preserved manual/Rocket package search. This search
  miss does not establish that an equivalent does not exist.
- **OPEN QUESTION:** the support corpus does not establish a complete public
  cutter-distance calibration procedure.

## Maintenance

- **FACT (FS-120):** the manual organizes maintenance by every-use, 50-hour,
  300-hour, and 600-hour intervals.
- **FACT (FS-120):** 300- and 600-hour work includes recalibration.
- **FACT (FS-134–FS-146):** the official support page directly exposes component
  replacement SOPs for air guides, extruder roller, heaters, nozzles,
  temperature sensors, piezoelectric ceramic, and toolhead fans.

## Failure and recovery evidence

- **FACT (FS-133, FS-139, FS-144):** FibreSeek publishes separate plastic-hotend,
  composite-hotend, and fiber-path unclogging procedures.
- **FACT (FS-139):** FibreSeek's fiber no-feed chain distinguishes spool
  movement/breakage, extruder debris and roller pressure, tension-sensor debris,
  guide-tube/cutter obstruction, and composite-hotend clogging, followed by
  extrusion/cut verification.
- **OPEN QUESTION:** the public chain is not an explicit failed cut/restart
  state-machine diagnosis, and it does not distinguish high versus low CFC
  nozzle compression symptoms.
- **FACT (FS-144):** the plastic-clog example uses PETG at 250°C; this is a
  procedure-specific example, not a universal temperature.
- **FACT (FS-147):** official troubleshooting covers layer shifting in
  plastic-only and fiber-only printing.
- **FACT (FS-149):** the first-layer SOP covers bed adhesive, bed temperature,
  automatic leveling, and piezoelectric-ceramic checks.
- **OPEN QUESTION:** the English first-layer PDF URL embedded in the support page
  is malformed and returns homepage HTML (FS-148); the Chinese parallel PDF was
  preserved instead (FS-149).

## Safety boundary

These notes index manufacturer procedures; they do not replace the source PDFs.
Service actions involving heated components, wiring, cutters, or calibration
must follow the exact first-party procedure and hardware state described there.
