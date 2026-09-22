# Evidence gaps — Loom experiments on 2026-09-07

Phase 2G-C recovered NAS-primary media and a durable derived inventory, but not
all retrospective observations are now quantitative claims. The authoritative
raw corpus remains:

`<archive>/FibreSeeker-KB-Archive/originals/incoming`

The repository stores provenance, manifests, derived evidence, and validated
records only. The full raw archive was not copied into normal Git.

| Gap | Current status after Phase 2G-C | Claims still blocked |
|---|---|---|
| Thermal time series | Partially represented by videos/photos showing Loom UI and ambient displays | Complete chamber, bed, nozzle, and ambient histories; rates; stability |
| Door-opening timing | Partially resolved for `IMG_3843.MOV`: about 4.1 s, 4-5 s, and 6-7 s visible open intervals | Exact recovery curves, repeatability, and full timing for all five MOV clips |
| Door-gap measurement | Partially resolved by door-gap photos and a gauge marking visible as `0.035 / 0.88 mm` | Exact measurement location, method, uncertainty, and repeatability |
| Kapton configurations | Partially resolved by a photo showing yellow tape on a vertical door seam | Complete taped/untaped run boundaries, equivalence of configurations, and leakage change |
| Taped/untaped comparisons | Still unresolved beyond owner retrospective and partial media context | Quantitative comparison, effect size, causality, or proof of benefit |
| Firmware/control state | Still missing | Whether control behavior confounded the comparisons |
| R-nozzle heat-up | Partially resolved by sparse display evidence from about 36 C to 274 C and back down | Exact 280 C target arrival, complete ramp shape, and shutoff delay |
| IR measurements | Partially resolved by IR display photos with readable example values | Emissivity, spot size, distance, exact surface identity, calibration, uncertainty |
| Power series | Partially represented by energy-monitor screenshots | Loom/Hearth attribution for unlabeled screenshots; export-grade idle, calibration, heater, peak, average, energy, and transient values |
| Instrument metadata | Still missing | Confirmed meter model/configuration, sample cadence, and measurement accuracy |
| Toolhead photos | Resolved as to presence of dedicated hotend/toolhead media | Direct plastic/CFC role labels, part identity, wiring, geometry measurements, condition conclusions |
| Shutdown record | Still missing | Exact safe shutdown sequence and UI/system behavior |
| Session chronology | Partially reconstructed from media timestamps | Complete absolute order and duration across thermal, sealing, power, inspection, and shutdown work |
| Sep 7 network state | Still missing as independent Sep 7 evidence | Independent confirmation that Loom was offline throughout Sep 7 |
| Hearth separation | Still missing for quantitative attribution | Attribution of any preserved power series to the correct appliance |

## Resolved or narrowed gaps

- Primary Sep 7 door/thermal MOV evidence is now represented in LX-003/LX-004.
- Door-gap visual evidence and one readable gauge marking are now represented.
- At least one Kapton tape placement photo is now represented.
- IR/ambient display photos are now represented.
- Sparse R-nozzle heat-up/cooldown evidence is now represented, but remains
  insufficient for exact 280 C timing.
- Energy-monitor screenshots are now represented, but unlabeled device
  attribution remains unresolved.
- Dedicated hotend/toolhead media is now represented, but role labels remain
  inferred.
- `FibreTouch_Log_2026-06-17_06-01-51.zip` is represented as June printer
  evidence and is explicitly not Sep 7 experiment evidence without direct
  linkage.

## Recovery handling

Future recovery work should preserve raw originals on the NAS or another
immutable raw-evidence store, then add only derived manifests, provenance
records, reviewed lightweight artifacts, and claim-level experiment records to
the repository. Recovered artifacts must be hashed before any record is promoted
from `USER-OBSERVED` or `UNKNOWN / EVIDENCE MISSING` to `CONFIRMED`.
