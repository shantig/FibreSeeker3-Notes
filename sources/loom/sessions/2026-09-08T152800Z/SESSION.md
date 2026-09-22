# Loom capture session 2026-09-08T152800Z

- Scope: initial read-only Moonraker enumeration.
- Machine: Loom, project owner's FibreSeeker 3 at `<printer-ip>`.
- Started: `2026-09-08T15:28:00Z` (capture-client clock).
- Ended: `2026-09-08T15:28:01Z` (capture-client clock).
- Requests issued to Loom: one.
- State-changing requests or printer commands: none.
- Authentication material stored: none.

The server's HTTP `Date` header is `2026-09-08T15:28:04Z`, three seconds later
than the capture-client end timestamp. No clock-synchronization conclusion is
drawn from a single response.

## Captures

| Provenance ID | Method and endpoint | HTTP status | Body bytes | SHA-256 |
|---|---|---:|---:|---|
| LM-001 | `GET /printer/objects/list` | 200 | 5,333 | `180d85666f1e53fed9f773e050e4f4802806301abc584c30e3d4d0219e550823` |

The `configs/`, `logs/`, `system/`, `can/`, and `vendor-components/`
directories are intentionally empty placeholders. No evidence in those
categories was requested during this session.
