# Loom capture session 2026-09-13T031552Z

- Purpose: preserve the evidence for the owner's 2026-09-12 evening
  calibration and bed-leveling session
  (`07_Troubleshooting/Loom/2026-09-12_calibration_bed_leveling/`).
- Authorization: project owner, 2026-09-12 — standing permission for any
  read-only operation on Loom ("You're always allowed to perform any read only
  operations on Loom"). The owner asked for today's session to be logged.
- Machine: Loom, project owner's FibreSeeker 3 at `<printer-ip>`.
- Started: `2026-09-13T03:15:52Z`; ended `2026-09-13T03:15:55Z`
  (capture-client clock).
- Requests issued to Loom in this session: three sequential GETs.
- State-changing requests, printer commands, extension calls, or shell access:
  none. Authentication material sent or stored: none.

## Captures

| Provenance ID | Method and endpoint | HTTP status | Body bytes | SHA-256 |
|---|---|---:|---:|---|
| LM-013 | `GET /server/files/logs/klippy.log.1` | 200 | 5,242,815 | `9ac3a46088cf2300f8f6755e24b2d6bc07a33467c8a6f154b4824bf5c9fbaf0e` |
| LM-014 | `GET /server/files/klippy.log` | 200 | 363,540 | `9a045050da0c653eb269245bf926d8c4238cb328faacdbcdf25e10ca65c8547e` |
| LM-015 | `GET /printer/objects/query?bed_mesh&save_variables&input_shaper` | 200 | 8,135 | `4cda2dfb33a3cc068b8e6aaf71a97d87da2eb5d6ee3ade0c15b77c2002049968` |

## Interpretation boundary

- Log timestamps are Loom local time, UTC−5. LM-013's `Last-Modified: Sun,
  13 Sep 2026 02:21:03 GMT` equals its last line `2026-09-12 21:21:03`;
  LM-014's `Last-Modified: 03:11:53 GMT` equals its last line `22:11:53`.
- LM-013 is Klipper's rotated log. It covers 2026-09-11 10:46:47 through
  2026-09-12 21:21:03 and is a superset of LM-012 (which ends 14:00:49).
  LM-014 continues from the 21:21:05 rollover through 22:11:53. The rollover
  config dump at the head of LM-014 reflects the configuration loaded at the
  last Klipper start (2026-09-11 14:35), not values saved later.
- LM-015 is a point-in-time state snapshot at 03:15:55Z (22:15 local). Its
  `input_shaper` object returned no status fields; shaper values come from the
  logs.
- Earlier in the same evening, before this session was opened, Claude made
  further read-only GETs of `klippy.log` and `/printer/objects/query` while
  guiding the owner. Those responses were kept only in a scratch directory and
  are not preserved evidence. The one value used from them (the pre-leveling
  `default` mesh spread) is labeled as unpreserved where it is cited.
- A keyword scan of all three bodies for API keys, passwords, bearer tokens,
  secrets, cookies, tokens, PSKs and SSIDs found no match. The logs contain
  local paths and hardware serial identifiers, which remain confined to raw
  evidence.
