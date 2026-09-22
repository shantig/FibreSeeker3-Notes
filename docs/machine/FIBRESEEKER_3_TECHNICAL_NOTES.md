# FibreSeeker 3 Technical Notes

This is a FibreSeek-only evidence summary. Source IDs resolve through
`sources/manifest.jsonl`. Values from Rocket are versioned software definitions,
not automatically physical operating instructions.

## Architecture

- **FACT (FS-120):** build volume is 305 × 305 × 245 mm; the heated chamber is
  rated to 65°C and the bed to 120°C.
- **FACT (FS-120):** the machine uses separate FFF and CFC all-metal hotends with
  hardened-steel nozzles, both rated to 350°C. Listed nozzle diameters are 0.4
  mm FFF and 0.7 mm CFC.
- **FACT (FS-120):** the CFC hotend has a built-in cutter. Manual controls expose
  cutting, fiber feed, and retraction actions.
- **FACT (FS-120):** sensors cover plastic breakage/clogging and fiber
  breakage/clogging; the machine also includes a camera.
- **FACT (FS-120):** listed maxima are 500 mm/s FFF speed and 20 cc/h CFC
  throughput. The latter is not a linear fiber feed speed.
- **FACT (FS-125):** the current machine store agrees on build volume and 0.4/0.7
  mm nozzle diameters and contains explicit cut/restart parameters.

## Material paths and storage

- **FACT (FS-120):** FFF plastic spools mount on rear hangers; CFC fiber is placed
  in an embedded chamber.
- **FACT (FS-120):** for long storage, materials should be removed and placed in
  a sealed container.
- **FACT (FS-120):** the manual tells users to dry highly hygroscopic materials,
  naming PETG, PC, and PACF as examples, before each print.
- **OPEN QUESTION:** no X-CCF-specific temperature, humidity, or drying cycle is
  provided. See `X_CCF_DRYING_STATUS.md`.

## Loading and Rocket workflow

- **FACT (FS-120):** documented composite loading order is composite plastic,
  then fiber, then plastic.
- **FACT (FS-120):** listed calibration functions include vibration, nozzle
  offset, bed leveling, and nozzle temperature.
- **FACT (FS-121, FS-122):** Rocket 1.3.2 imports/associates `.auprojx`, contains
  printer/material/profile stores, and supports mask and reinforced-path settings.
- **FACT (FS-125):** current preset v15 provides 48 profiles across 16
  material/nozzle groups.

## Machine and profile limits

- **FACT (FS-120):** the marketing/manual machine minimum layer height is 50 µm.
- **FACT (FS-125):** current composite profiles use macrolayer heights from 0.10
  through 0.30 mm and fiber-layer thickness values of 0.15 or 0.20 mm.
- **OPEN QUESTION:** the 50 µm machine minimum must not be interpreted as a
  supported CFC layer height; the applicable composite range is profile-specific.
- **FACT (FS-125):** `FiberMinRadius` is 10 or 12 mm in current profiles, but the
  UI defines it as the radius corresponding to minimum speed.
- **OPEN QUESTION:** no absolute FibreSeeker minimum physical turning radius was found.

## Unresolved machine questions

- Internal CFC nozzle and cutter geometry.
- Absolute linear fiber feed speed and its units.
- Runtime precedence of 58 mm structured cut distance versus 54.8 mm code comment.
- Public user procedure for cutter calibration.
- FibreSeek design rules for holes, bending, torsion, and laminate sequences.
