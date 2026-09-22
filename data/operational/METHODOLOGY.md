# Phase 2F-A Methodology

## Acquisition

Phase 2F-A began at accepted Phase 2E `origin/main`
`43cdd7523ddc2505f8538f9f18b17ca624c82a5f`. The pre-fetch local SHA was
`e1bc43bf652bfcc820da784a79b6e34f6a915f26`; it was a clean ancestor and was
fast-forwarded after `git fetch origin`. Accepted Phase 2A–2E ancestry and
canonical counts were verified before acquisition.

The crawl was bounded to first-party pages relevant to continuous-fiber
engineering. Requests were serialized with a two-second post-request delay,
normal redirects, an identifying archival user agent, and immutable
per-record directories. The Anisoprint support/docs certificates were expired,
so only already-public first-party pages were acquired with TLS verification
explicitly disabled and that condition recorded. No authentication, CAPTCHA,
paywall, DRM, or anti-bot control was bypassed.

`tools/acquire_source.sh` is restartable: an existing URL/filename with the
recorded current SHA-256 returns success without a request; a nonidentical
existing record is refused. HTTP failures remain manifest records. Raw bytes,
headers, and retrieval metadata live on the NAS; extracted text is in the
separate `derived/text/AP-*` tree.

## Git corpora

The two public official repositories were acquired as full Git bundles and
checked out at immutable commits for static inspection:

- `anisoprint/aura-docs` — `3fa58f9590b581a3df3da6cd4f1c4ba919599bc0`,
  default branch `master`, CC-BY-4.0.
- `anisoprint/MKA-firmware` —
  `6e02973b1b8f325040cc3dbf66ac545ffc5c06b3`, default branch `main`,
  GPL-3.0-or-later.

The firmware was treated as untrusted data. It was not compiled, flashed, or
executed. `corpus/github_index.json` records file paths and SHA-256 values for
the extraction-critical source files.

## Extraction

Claims were manually curated into a deterministic JSONL build scaffold. Every
record contains exact source IDs and locations, source wording or close
paraphrase, normalized interpretation, scope, values/units/qualifiers,
historical context, evidence class, applicability, confidence, relationships,
and a FibreSeek question where applicable.

Procedures preserve `trigger → preparation → procedure → measurement →
adjustment → verification` when supported. Diagnostic records preserve
`symptom → probable cause → implicated subsystem → test → corrective action →
verification`. Code observations are explicitly typed as behavior, constant,
default, or comment and always have `NOT_GUIDANCE` status.

## Validation

Validation rejects unknown source IDs, empty locations, missing domains,
duplicate IDs, Anisoprint-to-`CONFIRMED_EQUIVALENT` promotion, code-as-guidance,
unqualified unitless values, invalid question/video links, loss of failed
acquisitions, canonical-count changes, and wrong Git commits. Ten regression
fixtures cover the specific high-risk cases requested for this phase.
