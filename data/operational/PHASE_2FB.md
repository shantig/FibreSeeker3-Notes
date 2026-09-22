# Phase 2F-B — Direct FibreSeek/Rocket Validation

## Scope and baseline

Phase 2F-B started from and preserves immutable Phase 2F-A publication commit
`d49899368227979c9ea743ed09fff9b4bba06c88`. The historical analog records,
analog-generated question file, fixtures, and Phase 2A canonical generated
summary are byte-guarded by the Phase 2F-B validator.

The phase exhausted the preserved static FibreSeek corpus before considering
runtime work: FibreSeeker manuals and service SOPs, public Rocket preset v15,
the read-only Rocket 1.3.2 macOS distribution, its integrity-checked ASAR
contents, UI strings/enums, G-code parser contract, and static .NET metadata.
Every finding is linked to one or more of `FSQ-001` through `FSQ-022`.

## Evidence classes

- `FIBRESEEK_FIRST_PARTY` is a direct manual or support claim.
- `ROCKET_STATIC_OBSERVATION` is a package/profile/UI/code observation. It is
  not automatically manufacturer operating guidance.
- `ROCKET_OFFLINE_RUNTIME` is reserved for a captured no-hardware execution.
  No record of this class was created in Phase 2F-B.
- `OWNER_EXPERIMENT` and `VENDOR_CONFIRMATION` remain future evidence classes.
- The Phase 2F-A `ANISOPRINT_OFFICIAL` analog corpus remains separate and
  unchanged. It cannot resolve a Phase 2F-B question by itself.

Bounded search misses are explicitly `BOUNDED_SEARCH_ABSENCE`. They preserve an
open question and never assert nonexistence.

## Outputs

- `fibreseek/records/direct_evidence.jsonl`: 20 direct evidence records.
- `fibreseek/questions/fsq_status.jsonl`: additive status overlay for all 22
  Phase 2F-A questions.
- `fibreseek/static/rocket_static_index.json`: Rocket version, artifact hashes,
  inspection method, and explicit non-execution list.
- `fibreseek/fixtures/regression_cases.json`: 12 question/status boundary cases.
- `fibreseek/runtime/OFFLINE_TEST_PLAN.md`: bounded future runtime experiments.
- `schemas/direct-evidence.schema.json` and `schemas/fsq-status.schema.json`:
  contracts for the new layer.

## Status result

| Status | Count | Questions |
|---|---:|---|
| Resolved | 3 | FSQ-008, FSQ-009, FSQ-011 |
| Partially resolved | 15 | FSQ-001–005, FSQ-007, FSQ-010, FSQ-012–013, FSQ-015, FSQ-017–019, FSQ-021–022 |
| Open | 4 | FSQ-006, FSQ-014, FSQ-016, FSQ-020 |

“Resolved” is scoped to the wording of the question and the static Rocket
software contract. It is not a printer operating recommendation.

## Principal direct findings

1. Rocket has no single recovered minimum-fiber-length setting. Public preset
   v15 stores 10 mm for both solid/cellular fiber-infill minimum line length,
   and 20 mm (Speedy) or 55 mm (ReinForced/Fortified) for minimum reinforced
   perimeter length. Boundary behavior still needs output evidence.
2. `FiberMinRadius` is 10 or 12 mm and is documented as the radius
   corresponding to minimum printing speed—not an absolute physical bend limit.
3. Rocket defines a macrolayer as a package of microlayers at coincident entity
   heights. Fiber height equals macrolayer height. Shell, plastic perimeter,
   infill, and thick-support heights are ratio-derived; current ratios are 1 or 2.
4. Reinforced entity order is explicit: first in layer, last in layer, or after
   other plastic/support entities but before external shell.
5. Rocket stores `CutDistance=58 mm`, `FiberRestartLength=55 mm`, and CutCode
   `M2800` then `M400`, while the code comment says `CUT DISTANCE 54.8`. The
   conflict and runtime precedence remain unresolved.
6. Rocket supports full/internal masks and support blocker/enforcer masks.
   Full/internal masks can locally change fiber-perimeter and fiber-infill
   settings. Overlapping height layups use higher priority, where 1 is highest;
   exact geometric mask-to-mask precedence still needs an output test.
7. FibreSeek documents automatic nozzle-offset calibration and signed manual
   X/Y correction, but no public acceptance tolerance. CFC nozzle/hotend service
   explicitly requires nozzle-offset recalibration.
8. No FibreSeek `NozzleOffsetTest.gcode` equivalent was found in the bounded
   corpus. This remains an open question, not a nonexistence claim.

## Runtime decision

No Rocket process was run. Static inspection found slicing exposed through a
stateful localhost `Aura.Monolith.API` endpoint, not a standalone side-effect-
free CLI or preserved request fixture. Launching the backend without a verified
request contract and containment recipe would not produce a deterministic,
reviewable experiment. The remaining runtime questions therefore have bounded
test designs, but no fabricated results.

No application, backend, slicing engine, firmware, G-code, printer, machine
command, network-controlled device, USB/serial interface, or hardware was run.

## Validation

`tools/validate_phase2fb.py` verifies question coverage, source resolution,
evidence-class separation, resolved-status sufficiency, static/runtime
distinction, direct/analog separation, Phase 2F-A byte invariants, canonical
summary hash/counts, fixtures, and optional NAS originals. The builder is
byte-deterministic.
