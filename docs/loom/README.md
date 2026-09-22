# Loom Live-System Documentation

Loom is the project owner's FibreSeeker 3. This directory contains interpreted
documentation from explicitly read-only observations of that individual
machine. Immutable response bytes and capture metadata live under
`sources/loom/`.

## Evidence labels

- **CONFIRMED:** directly present in a preserved Loom response or another cited
  first-party source. A Loom observation is time- and machine-scoped; it is not
  automatically true of every FibreSeeker 3.
- **STRONGLY INFERRED:** supported by multiple observations or a close technical
  correspondence, but not directly stated by the evidence.
- **UNKNOWN / NEEDS TESTING:** unresolved, ambiguous, unavailable, or requiring
  an additional approved observation.

Live observations are recorded as `EXPERIMENTAL` in the repository provenance
taxonomy. This identifies how the evidence was obtained; it does not imply a
state-changing physical experiment.

## Layout

- `EVIDENCE_PROTOCOL.md` — mandatory capture and safety rules.
- `ARCHITECTURE.md` — evidence-backed software/hardware architecture map.
- `CONFIGURATION_DISCOVERY.md` — Phase 2H-A configuration, extension, and
  macro inventory.
- `COMPONENT_ATTRIBUTION.md` — Phase 2H-B module/source, runtime-health,
  interface-safety, extension-agent, and MCU attribution.
- `SOURCE_RECOVERY_AND_INTERFACES.md` — Phase 2H-C source-access boundary,
  deeper interface inventory, dependency graph, and static-export next step.
- `MACRO_INVENTORY.md` — exact passive macro-name inventory and lexical groups.
- `OBSERVATIONS.md` — chronological findings and open questions.

Do not place raw responses, configs, or logs in this directory. Do not merge
Loom-specific observations into general FibreSeek guidance without separate
supporting evidence.
