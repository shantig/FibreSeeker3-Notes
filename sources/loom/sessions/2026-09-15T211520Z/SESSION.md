# Loom capture session 2026-09-15T211520Z

- Purpose: preserve FibreSeek's factory plastic-only Benchy for comparison with
  the owner's Orca-sliced Benchy X0008
  (`07_Troubleshooting/Loom/2026-09-15-T4/RESULTS.md`). Owner request: "read
  DemoFiles/PLA-Benchy on Loom and compare its settings with X0008".
- Authorization: project owner, 2026-09-14 — full live access.
- Machine: Loom, `<printer-ip>`, Moonraker on port 7125. Read after X0008
  completed; the printer was idle.
- Started `2026-09-15T21:15:20Z`, ended `2026-09-15T21:15:21Z`. One GET. No state
  change from this capture. Authentication material sent or stored: none.

## Captures

| Provenance ID | Method and endpoint | HTTP status | Body bytes | SHA-256 |
|---|---|---:|---:|---|
| LM-026 | `GET /server/files/gcodes/DemoFiles/PLA-Benchy.gcode` | 200 | 3,827,093 | `80350a00c07b81dc4be5c26993b05cc8e304ee79d9c682d54e75ba2b7285248b` |

## Handling notes

- FibreSeek-authored content (Rocket Slicer 1.3.1.480, generated 2026-07-15,
  `PRINTING_MODE: Plastic Only`), installed with the demo files
  (`Last-Modified` 2026-09-11 16:07:40 GMT, same batch as LM-021). Preserved as
  found; it is a sample file, not manufacturer guidance by itself.
- The body carries an embedded `; SESSION: {…}` JSON profile. Its field names
  (`EWUM`, `InsetXP`, `CSEMs`/`PSEMs`, `IsAnisoprintApproved`) follow Anisoprint
  Aura conventions. That is FibreSeek software carrying Anisoprint-heritage
  structure, **not** Anisoprint evidence. `INFERENCE`: several of its values
  disagree with the moves actually emitted (see the troubleshooting record), so
  the plastic-only G-code body was generated from different settings than the
  embedded profile shows.
- The end of the file holds a base64 thumbnail; no credentials or tokens.
