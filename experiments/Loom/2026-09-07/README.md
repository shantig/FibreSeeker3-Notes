# Loom physical-experiment backfill — 2026-09-07

## Scope and evidence quality

This is a retrospective reconstruction of physical work performed on Loom on
2026-09-07. The backfill was created on 2026-09-08 without contacting Loom.

Phase 2G-C adds NAS-primary evidence enrichment. The authoritative raw corpus is
`<archive>/FibreSeeker-KB-Archive/originals/incoming`; the repository
contains derived inventory/provenance records and claim-level summaries only.
The full raw media archive was not copied into normal Git.

LX-001 is the owner's next-day retrospective. LX-002 is the earlier bounded
repository inventory. LX-003 is the durable derived inventory for the refreshed
330-file NAS corpus. LX-004 is the derived primary-evidence enrichment report.

Claims are `CONFIRMED` only where supported by repository, cross-session, or
NAS-primary artifacts. Owner observations remain `USER-OBSERVED`. Derived
evidence-sufficiency conclusions remain `STRONGLY INFERRED`; unresolved matters
remain `UNKNOWN / EVIDENCE MISSING`.

Sequence numbers in `experiment_records.jsonl` are documentation order. They are
not timestamps. `REPORTED_SEQUENCE` preserves only explicit relative order in
the owner account; `RELATIVE_ONLY` and `UNKNOWN` do not establish full event
timing.

## Reconstructed chronology

### CONFIRMED

- At baseline `87cb85dff83a421e66e9ea21c96a23b9b1097427`, the repository
  contained no Sep 7 screenshots, video, photos, logs, exports, measurement
  notes, or prior experiment provenance record (LX-002). This is a bounded
  repository-search result, not a claim about external storage.
- The refreshed NAS inventory contains 330 files totaling 7,668,023,706 bytes:
  76 HEIC images, 145 JPEG images, 99 PNG screenshots, 9 QuickTime videos, and
  1 ZIP archive (LX-003/LX-004).
- No exact duplicate SHA-256 groups or same-filename collisions with different
  hashes were found in the 330-file NAS corpus. Ten same-stem HEIC/JPEG or
  JPG/JPEG variants exist and are treated as variants, not byte duplicates.
- Five Sep 7 MOV files (`IMG_3843.MOV`, `IMG_3844.MOV`, `IMG_3845.MOV`,
  `IMG_3846.MOV`, and `IMG_3853.MOV`) document door/thermal testing context.
- `IMG_3843.MOV` supports three short door-open intervals: about 4.1 seconds,
  about 4-5 seconds, and about 6-7 seconds. Temperature recovery curves were not
  recovered from the reviewed frames.
- Door-gap primary media is present. A gauge photo shows a visible `0.035 /
  0.88 mm` marking in adjacent door-gap context.
- Kapton tape placement primary media is present. A photo shows yellow tape on a
  vertical door seam; complete taped/untaped run boundaries remain unresolved.
- IR thermometer and ambient-display photos are present. Readable examples
  include 15.0 C, 64.2 C, 67.0 C, 47.4 C, 72.1 F / 42% RH, and 76.5 F / 46%
  RH. Measurement geometry and uncertainty are not established.
- Sparse R-nozzle display evidence represents heat-up/cooldown from
  approximately 36 C to 274 C and back down. No reviewed primary artifact proves
  exact 280 C target arrival.
- Energy-monitor screenshots are present, but unlabeled screenshots do not
  independently establish Loom versus Hearth attribution.
- Dedicated hotend/toolhead photo sequences are present. Plastic versus
  continuous-fiber role labels remain inferred unless directly supported by
  labeling/context.
- `FibreTouch_Log_2026-06-17_06-01-51.zip` is present and is valid printer
  evidence dated June 16-17, 2026. It is not classified as Sep 7 experiment
  evidence without direct linkage.
- The repository's first Loom network/API evidence is dated 2026-09-08
  (LM-001 through LM-004). It is separate from this physical session.

### USER-OBSERVED

- Chamber operation was around 60 C. An initial door opening appeared to cause
  an approximately 3 C immediate drop; later openings did not show the same
  dramatic instantaneous change.
- A physical door gap was altered with Kapton tape. At least two taped
  configurations and an untaped comparison were tried. The second taped and
  untaped comparisons were each described as approximately 90 minutes; the
  second taped test had observations around 30, 60, and 90 minutes.
- Testing was paused because further repetitions appeared to offer diminishing
  returns and firmware behavior might confound the result.
- Bed heating/cooling, IR bed-surface checks, room ambient readings, an R-nozzle
  heat-up, and later automatic/idle shutoff behavior were observed. The nozzle
  target was reported as 280 C and time-to-target as approximately one minute;
  those exact values remain owner-observed, not primary-confirmed.
- Loom power behavior was viewed with the existing smart plug across idle,
  calibration, heating, and experiment states. Its approximately five-minute
  resolution was judged inadequate for transients, motivating purchase of an
  Athom ESPHome no-relay monitor.
- The owner reports capturing photo sets of plastic and continuous-fiber
  hotend/toolhead areas. Primary media now confirms dedicated photo sequences,
  but the exact role labels remain inferred.
- Shutdown was discussed after Loom cooled. The owner reports that Loom was not
  yet network-connected during the Sep 7 session.

### STRONGLY INFERRED

- Available evidence still does not establish that Kapton improved chamber
  behavior. The missing traces, uncertain configuration details, non-repeatable
  apparent door response, and possible firmware confound prevent causal
  attribution.
- Media timestamps support only a partial chronology: June printer logs, Sep 6
  hotend/toolhead inspection, Sep 7 thermal/door/Kapton/power-observation media,
  and Sep 8 network/variant assets. File birth and modification times sometimes
  differ by hours, so complete session order remains unresolved.

### UNKNOWN / EVIDENCE MISSING

See `EVIDENCE_GAPS.md`. Complete synchronized temperature/power histories,
thermal recovery curves, firmware/control outputs, full run boundaries, device
attribution for power screenshots, exact hotend role labels, Sep 7 network-state
proof, and shutdown procedure evidence remain unresolved.

## Structured records

`experiment_records.jsonl` contains the claim-level evidence classification.
Validate it with `python3 tools/validate_experiments.py`.
