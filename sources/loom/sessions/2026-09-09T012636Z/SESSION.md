# Loom capture session 2026-09-09T012636Z

- Phase: 2H-B, passive architecture attribution.
- Scope: existing Moonraker and Klipper logs, plus the registered G-code help
  catalogue.
- Machine: Loom, project owner's FibreSeeker 3 at `<printer-ip>`.
- Started: `2026-09-09T01:26:36Z` (capture-client clock).
- Ended: `2026-09-09T01:33:12Z` (capture-client clock).
- Requests issued to Loom: three, sequentially.
- State-changing requests, printer commands, extension calls, or shell access:
  none.
- Authentication material sent or stored: none.

All three requests used documented passive GET surfaces. LM-008 and LM-009
downloaded the current files from Moonraker's read-only `logs` root. LM-010
queried Klipper's registered command descriptions. No command in the catalogue
was invoked. No guessed vendor route, extension method, file-write endpoint,
service action, or external/cloud endpoint was contacted.

## Captures

| Provenance ID | Method and endpoint | HTTP status | Body bytes | SHA-256 |
|---|---|---:|---:|---|
| LM-008 | `GET /server/files/moonraker.log` | 200 | 96,992 | `1eeb81b2f1d16d2d76c828c1ff800b9bb590ee368c1c06b9e14baa2236ab316d` |
| LM-009 | `GET /server/files/klippy.log` | 200 | 1,863,484 | `c3e85f7774b568c6ba36e8480b3fbe509ef027858efe1a8bb9d26cb47ec5329a` |
| LM-010 | `GET /printer/gcode/help` | 200 | 13,859 | `6d4b06ba3656350192c7b082ab21c82e38b0ed81716a27fa13904b51ae73d391` |

## Privacy and interpretation boundary

The logs contain local paths, network and hardware identifiers, historical
machine activity, and device metadata. Exact identifiers remain confined to
raw evidence unless technically necessary. A credential scan found no API key,
password, bearer credential, cookie, or nonempty WebSocket token. Historical
log entries describe machine actions that predate this passive capture; they
were not caused or repeated by this phase.

Log presence distinguishes loaded or observed behavior from current health.
The command-help response proves registration and description only, not safe
execution or physical behavior.
