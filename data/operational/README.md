# Operational Knowledge

This directory is a derived, reviewable representation of official historical
Anisoprint evidence relevant to continuous-fiber operation. It is deliberately
separate from the accepted Phase 2A canonical/query contracts.

## Contents

- `records/operational_knowledge.jsonl` — 54 source-resolved operational records.
- `schemas/` — operational, training-video, and validation-question contracts.
- `taxonomy.json` — nine controlled domains plus procedure, diagnostic, and
  layer-hierarchy chains.
- `training/video_inventory.jsonl` — seven official lesson records prepared for
  timestamped human annotation.
- `questions/fibreseek_validation_questions.jsonl` — 22 open FibreSeek questions.
- `corpus/github_index.json` — static file/hash index for immutable `aura-docs`
  and `MKA-firmware` commits.
- `fixtures/regression_cases.json` — ten required evidence-boundary regressions.

Regenerate curated outputs with `python3 tools/build_phase2fa_data.py`. Rebuild
the Git index from checkouts pinned to the recorded commits with
`tools/index_anisoprint_git.py`. Validate with:

```sh
python3 tools/validate_operational_knowledge.py
python3 tools/validate_operational_knowledge.py --verify-archive
```

The second command additionally hashes Phase 2F-A originals on the mounted NAS.
No record in this directory is FibreSeek-confirmed. A `POSSIBLE_ANALOG` state
means the concept merits investigation, not that a value or procedure transfers.

Phase 2F-B direct FibreSeek/Rocket evidence is an additive overlay under
`fibreseek/`; it does not modify the Phase 2F-A analog records or questions.
See `PHASE_2FB.md` for methodology and results. Regenerate and validate it with:

```sh
python3 tools/build_phase2fb_data.py
python3 tools/validate_phase2fb.py --verify-archive
```
