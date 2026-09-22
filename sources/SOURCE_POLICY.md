# Source and Preservation Policy

## Provenance classes

Every source, extracted fact, normalized value, and recommendation must carry
exactly one of these classes:

- `FIBRESEEK_OFFICIAL` — published or authored by FibreSeek/FibreSeeker.
- `ANISOPRINT_OFFICIAL` — published or authored by Anisoprint.
- `ACADEMIC` — scholarly publication or institutional research record.
- `PATENT` — patent application, grant, or official patent-family record.
- `COMMUNITY` — reseller, forum, video, repository, interview, or other third party.
- `INFERRED` — analyst-derived conclusion not stated directly by a source.
- `EXPERIMENTAL` — locally measured or observed result under recorded conditions.

`ANISOPRINT_OFFICIAL` is not interchangeable with `FIBRESEEK_OFFICIAL`.
Anisoprint rules may be presented as legacy context or a hypothesis to test, but
must not become FibreSeek-specific guidance without explicit FibreSeek evidence
or a separately labelled experiment.

## Acquisition records

The canonical ledger is `sources/manifest.jsonl`, one JSON object per line.
The schema is `sources/manifests/manifest.schema.json`. Discovery records may
leave acquisition-only fields `null`. After a download, the record must include:

- source URL and final URL after redirects;
- title and publisher;
- provenance class;
- retrieval timestamp in UTC;
- original filename and immutable local path;
- SHA-256 digest and detected MIME type;
- document/version date when known;
- notes and obvious license/copyright status.

Record HTTP status, redirects, and failures. Never replace an existing manifest
line silently: append a superseding record and link it with `supersedes_id`.

## Storage layout

1. Preserve downloaded originals byte-for-byte in an `originals/` tree under
   the NAS archive root.
2. Store extracted text/OCR in a separate `derived/text/` tree.
3. Store normalized profiles/data in `derived/normalized/` or the matching Git
   knowledge-base directory when redistribution and size permit.
4. Store summaries and interpretations separately from both originals and
   extracted text.
5. Never edit an original to repair metadata, filenames, PDF structure, or OCR.

Suggested archive layout:

```text
FibreSeeker-KB-Archive/
  originals/<provenance>/<record-id>/
  derived/text/<record-id>/
  derived/normalized/<record-id>/
  logs/
```

## Network and executable safety

- Use one request at a time by default, identify the client when practical, and
  pause at least two seconds between automated requests to the same host.
- Respect access controls, rate-limit responses, and robots directives; do not
  bypass authentication or anti-bot controls.
- Fetch index pages before assets and avoid repeated downloads when metadata,
  ETag, Last-Modified, size, and SHA-256 already match.
- Vendor installers, firmware, macros, scripts, and binaries may be run or
  instrumented for analysis on copies; originals stay untouched. Loom live work
  follows `docs/loom/EVIDENCE_PROTOCOL.md`.
- Verify signatures/hashes when publishers provide them. Record their absence.
- Inspect sample projects and G-code before sending them to Loom, and print
  from a copy.

## Citation and knowledge rules

- Prefer first-party documents over marketing summaries and reseller pages.
- Preserve the document date and software/hardware version because CFC settings
  are version-sensitive.
- Distinguish a source's claim from a verified physical result.
- Record unanswered questions explicitly. Absence of evidence is not permission
  to infer a parameter.
- Conflicting values remain side-by-side until their scope and version can be
  resolved.
