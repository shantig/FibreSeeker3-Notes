# Loom capture session 2026-09-08T230535Z

- Phase: 2H-A, bounded configuration/extension discovery.
- Scope: passive Klipper configuration status, Moonraker configuration
  metadata, and connected-extension enumeration.
- Machine: Loom, project owner's FibreSeeker 3 at `<printer-ip>`.
- Started: `2026-09-08T23:05:35Z` (capture-client clock).
- Ended: `2026-09-08T23:07:42Z` (capture-client clock).
- Requests issued to Loom: three, sequentially.
- State-changing requests, printer commands, or extension methods: none.
- Authentication material sent or stored: none.

The three endpoints are documented passive `GET` surfaces. LM-005 queries the
already-loaded Klipper `configfile` status object; LM-006 queries Moonraker's
parsed server configuration; LM-007 lists connected extension agents. No
macro, G-code, vendor action, file API, shell-command API, service endpoint, or
guessed custom route was invoked.

## Captures

| Provenance ID | Method and endpoint | HTTP status | Body bytes | SHA-256 |
|---|---|---:|---:|---|
| LM-005 | `GET /printer/objects/query?configfile` | 200 | 226,337 | `6d590257942f3bfe3156c97566c37868c63c531eb032eb8882df4cacb50d1ba2` |
| LM-006 | `GET /server/config` | 200 | 7,436 | `938af83e0a09a76a96f9eb7b85838cd415cbb6a978c056e249e225d7ef374159` |
| LM-007 | `GET /server/extensions/list` | 200 | 110 | `0c82c1ed354f6d750a6dd4dd9322f2de7084409af9babf27edf5ce3b878ee949` |

## Privacy and interpretation boundary

LM-005 and LM-006 contain device paths, pins, filesystem paths, network
configuration, or local service locations. LM-007 contains the connected
agent's self-reported URL. These exact values remain in raw evidence and are
not reproduced in interpreted documentation unless technically necessary.
The server configuration exposes empty/default secret and password fields; no
nonempty password, API key, token, cookie, or authorization credential was
found in the captured bodies.

Configuration presence does not prove installed hardware health or runtime
use. Macro bodies document configured behavior but were not invoked. Component
and agent names do not establish authorship, purpose, or safety.
