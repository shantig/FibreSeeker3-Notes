# Loom capture session 2026-09-13T054125Z

- Purpose: preserve the evidence for the Stage 1 plastic-plus-fibre test print
  (`07_Troubleshooting/Loom/2026-09-12_calibration_bed_leveling/test_print/STAGE1_RESULTS.md`).
- Authorization: project owner, 2026-09-12 — standing permission for any
  read-only operation on Loom. The owner asked for Stage 1 to be logged.
- Machine: Loom, project owner's FibreSeeker 3 at `<printer-ip>`.
- Started: `2026-09-13T05:41:25Z`; ended `2026-09-13T05:41:55Z`
  (capture-client clock).
- Requests issued to Loom in this session: seven sequential GETs. One was
  discarded; see below.
- State-changing requests, printer commands, extension calls, or shell access:
  none. Authentication material sent or stored: none.

## Captures

| Provenance ID | Method and endpoint | HTTP status | Body bytes | SHA-256 |
|---|---|---:|---:|---|
| LM-016 | `GET /server/files/klippy.log` | 200 | 2,094,194 | `e6881f9843ae994d54d5358f5dd33c472762f6627b03c85991de70c6c148295d` |
| LM-017 (derived) | excerpt of `GET /server/files/logs/moonraker.log.2026-09-12` | 200 | 17,017 | `c93c585572571a90eccbf0e428b9965bdb385b1c9176f6b494d3e537d561c84c` |
| LM-018 | `GET /server/files/logs/print_logs/anisotouch_2026-09-12.log` | 200 | 2,599,445 | `e2747f7d9e6863265ca1ae5e566fdc26c9ac2eb48613a1220f2d801239be0be9` |
| LM-019 | `GET /server/files/logs/fibretouch-ai.log` | 200 | 141,414 | `0764207e4583783e00c601aa56c9e59437ff668d2c0cd0788af147eca2a99a9e` |
| LM-020 | `GET /server/history/list?limit=1&order=desc` | 200 | 1,700 | `1f7c84b6528b53c6a1442224e1072340a2c2593987c93e3e44bc10f0fe85ba3d` |
| LM-021 | `GET /server/files/gcodes/DemoFiles/PETG-Scraper.gcode` | 200 | 1,519,612 | `72ebec2d1fa803a584e8e6775b94f237bb6c65b4a0c603c40096e6e9c2cb7a7b` |

## Handling notes

- **Discarded request.** A first GET of `/server/files/logs/moonraker.log`
  returned the post-midnight file (Moonraker rotated its log at 00:00 local).
  It did not cover the print, so it was discarded and never recorded. The
  rotated `moonraker.log.2026-09-12` was fetched instead.
- **Why LM-017 is an excerpt.** The full `moonraker.log.2026-09-12` response
  (312,389 bytes, SHA-256
  `13d2dbcbadf4d7c6b9781eeb083f912e7af5c08968c1e82625c2c6387e439e92`) contains a
  Moonraker websocket one-shot token in a 17:16 request line. It is therefore
  **not committed**.
  - LM-017 is every line timestamped in [2026-09-12 22:25, 2026-09-13 00:10),
    unmodified, and contains no token.
  - The excerpt sits under `logs/` rather than `moonraker-api/` because it is
    not a byte-exact API response.
- **Timestamps.** Log timestamps are Loom local time (UTC−5). LM-016
  `Last-Modified 05:05:36 GMT` equals its last line `2026-09-13 00:05:36`.
- **Coverage.** LM-016 is the same `klippy.log` as LM-014, later: it starts at
  the 21:21:05 rollover and ends at 00:05:36. LM-018 ends at 23:59:59, when the
  HMI log rotates daily.
- **Not preserved.** The AI service's rolling `ai_errors/print_error_*.jpg`
  camera snapshots were viewed read-only in scratch during the print but are
  not preserved.
- **Credential scan.** All committed bodies were scanned for API keys,
  passwords, bearer tokens, secrets, cookies, tokens, PSKs, SSIDs, e-mail
  addresses and account identifiers. There were no credential matches. Hits
  were only HMI account-page UI state strings (LM-018) and a slicer field name
  containing "psk" (LM-021).
