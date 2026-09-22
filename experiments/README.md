# Physical Experiments

This directory contains owner-authorized physical observations and experiments.
It is separate from manufacturer guidance, historical Anisoprint evidence,
Rocket static observations, and live read-only API captures.

## Evidence model

- `CONFIRMED`: supported directly by a preserved artifact or bounded repository
  inventory. Confirmation remains limited to what the artifact actually shows.
- `USER-OBSERVED`: reported by the project owner without a currently preserved
  primary measurement, image, video, or log.
- `STRONGLY INFERRED`: a derived interpretation supported by preserved records
  but not directly measured or stated by a primary artifact.
- `UNKNOWN / EVIDENCE MISSING`: cannot be established from available evidence.

Owner recollection is valuable evidence, but it is not silently upgraded to a
machine measurement. Approximate values remain text with their original
qualifiers. Manufacturer guidance requires separate first-party support.

## Layout

```text
experiments/
  schemas/
  Loom/<experiment-date>/
    README.md
    experiment_records.jsonl
    EVIDENCE_GAPS.md

sources/loom/experiments/<experiment-date>/
  source/
  derived/
  primary/{screenshots,videos,photos,logs,exports}/
```

Raw and source evidence belongs under `sources/`; structured observations and
interpretations belong here. Missing artifacts receive explicit placeholders
and gap records rather than reconstructed values.
