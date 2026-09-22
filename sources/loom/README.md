# Loom Raw Evidence

This tree preserves source evidence about the project owner's FibreSeeker 3,
Loom.

- `sessions/` contains immutable read-only live-system captures.
  Interpretations belong in `docs/loom/`.
- `experiments/` contains physical-experiment sources, derived inventories, and
  reserved primary-artifact paths. Interpretations belong in
  `experiments/Loom/`.

Follow `docs/loom/EVIDENCE_PROTOCOL.md` before every capture. In
particular, preserve exact response bytes and metadata, do not store secrets,
and never edit a completed capture in place.

The repository provenance class for these owner-observed captures is
`EXPERIMENTAL`. This is distinct from `FIBRESEEK_OFFICIAL` published material
and from `ANISOPRINT_OFFICIAL` legacy evidence.

Validate tracked Loom evidence offline with:

```sh
python3 tools/validate_loom_evidence.py
python3 tools/validate_experiments.py
```
