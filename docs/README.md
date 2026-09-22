# Documentation index

Human-readable findings. For the shorthand used throughout (Loom, Plastic 1/2,
sample IDs, evidence labels), see [glossary.md](glossary.md).

## Findings

- **[findings.md](findings.md)** — the top practical findings for an FS3 owner,
  each labelled and linked to its evidence.
- **[how-this-kb-works.md](how-this-kb-works.md)** — the evidence model,
  provenance ledger, and the query/data layer.

## The machine

`loom/` documents the owner's FibreSeeker 3, from read-only observation and
authorized live work. Loom observations are time- and machine-scoped.

- [loom/README.md](loom/README.md) — evidence labels and layout for this set.
- [loom/ARCHITECTURE.md](loom/ARCHITECTURE.md) — software/hardware map.
- [loom/PRINT_START_AND_STATE_MACHINE.md](loom/PRINT_START_AND_STATE_MACHINE.md)
  — starting prints via Moonraker, `print_stats` states, progress labels.
- [loom/MACRO_INVENTORY.md](loom/MACRO_INVENTORY.md) — the vendor macros.
- [loom/CONFIGURATION_DISCOVERY.md](loom/CONFIGURATION_DISCOVERY.md),
  [loom/COMPONENT_ATTRIBUTION.md](loom/COMPONENT_ATTRIBUTION.md),
  [loom/SOURCE_RECOVERY_AND_INTERFACES.md](loom/SOURCE_RECOVERY_AND_INTERFACES.md)
  — configuration, module attribution, and the source/interface boundary.
- [loom/OBSERVATIONS.md](loom/OBSERVATIONS.md) — raw observation log.
- [loom/EVIDENCE_PROTOCOL.md](loom/EVIDENCE_PROTOCOL.md) — capture and safety
  rules for live work.

`machine/` holds general FibreSeeker 3 notes not specific to Loom:

- [machine/FIBRESEEKER_3_TECHNICAL_NOTES.md](machine/FIBRESEEKER_3_TECHNICAL_NOTES.md)
- [machine/MATERIALS_AND_COMPATIBILITY.md](machine/MATERIALS_AND_COMPATIBILITY.md)
- [machine/CALIBRATION_MAINTENANCE_TROUBLESHOOTING.md](machine/CALIBRATION_MAINTENANCE_TROUBLESHOOTING.md)
- [machine/X_CCF_DRYING_STATUS.md](machine/X_CCF_DRYING_STATUS.md)

## Firmware

- [firmware/FIRMWARE_ANALYSIS.md](firmware/FIRMWARE_ANALYSIS.md) — static
  analysis of the two official `.fibrepack` releases.
- [firmware/VERSION_DIFF_2.2.30_TO_2.2.42.md](firmware/VERSION_DIFF_2.2.30_TO_2.2.42.md)
  — what changed between releases.

## Slicer (Rocket, and its Aura lineage)

- [slicer/ROCKET_STATIC_ANALYSIS.md](slicer/ROCKET_STATIC_ANALYSIS.md)
- [slicer/aura/](slicer/aura/) — Rocket↔Aura lineage, field map, project
  formats, and bounded static findings.

## Community

- [community/Forums/2026-09-21-facebook-fibreseeker3-group.md](community/Forums/2026-09-21-facebook-fibreseeker3-group.md)
  — cross-checks of bugs reported by other owners (see also
  [3ricj/FibreSeeker3](https://github.com/3ricj/FibreSeeker3)).
- [community/Tools/vilos-gcode-modifier.md](community/Tools/vilos-gcode-modifier.md)

## Notebook

Dated calibration and troubleshooting sessions are in
[../notebook/](../notebook/), indexed by [../notebook/README.md](../notebook/README.md).
