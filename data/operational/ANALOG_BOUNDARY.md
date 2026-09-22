# Analog-to-FibreSeek Boundary

`ANISOPRINT_OFFICIAL` and `FIBRESEEK_OFFICIAL` are separate evidence classes.
Phase 2F-A creates no new FibreSeek operating value, procedure, compatibility
claim, machine limit, or confirmed equivalence.

Applicability states mean:

- `POSSIBLE_ANALOG` — a historically similar named or functional concept worth
  testing; no transfer is permitted.
- `CONCEPTUAL_ANALOG` — a general engineering or workflow concept that may help
  frame a FibreSeek question.
- `NO_KNOWN_EQUIVALENT` — no FibreSeek counterpart is presently supported.
- `CONTRADICTED` — direct evidence conflicts; none is assigned in this batch.
- `UNRESOLVED` — applicability cannot yet be assessed.
- `CONFIRMED_EQUIVALENT` — reserved for direct FibreSeek evidence and prohibited
  for the all-Anisoprint Phase 2F-A records.

Same names, UUID continuity, repository ancestry, or the absence of a
contradictory FibreSeek document do not prove physical equivalence. In
particular, relationships to Rocket `MacroLayerHeight`, `CutDistance`,
`FiberRestartLength`, and `CutCode` are lineage clues or possible analogs only.
Rocket runtime precedence remains unresolved.

Profile/database scalars keep their source-native unit uncertainty. A scalar
is not silently converted to millimetres because the field looks geometric.
Static firmware constants are model/configuration observations, never
manufacturer recommendations. Future local measurements belong in
`EXPERIMENTAL`, not in this corpus.
