# Loom capture session 2026-09-09T020242Z

- Phase: 2H-C, passive source-recovery boundary check.
- Scope: registered Moonraker file roots and their permissions.
- Machine: Loom, project owner's FibreSeeker 3 at `<printer-ip>`.
- Capture timestamp: `2026-09-09T02:04:13Z` (HTTP response `Date`).
- Requests issued to Loom: one.
- State-changing requests, printer commands, extension calls, shell access,
  path traversal, or external service access: none.
- Authentication material sent or stored: none.

The documented passive `GET /server/files/roots` endpoint was used solely to
determine whether either requested implementation directory was registered for
file-manager read access. The response lists seven roots. Neither the Moonraker
component directory nor the Klipper `extras` directory is exposed. No file-list or file-download
request followed, because the requested source files are outside the returned
roots.

## Capture

| Provenance ID | Method and endpoint | HTTP status | Body bytes | SHA-256 |
|---|---|---:|---:|---|
| LM-011 | `GET /server/files/roots` | 200 | 569 | `564af0e029eb00c68d0bfbe9154e146dfe7b8bc331d997a15a5a126611e12985` |

## Privacy and interpretation boundary

The response contains local filesystem paths. These are retained in raw
evidence; interpreted documentation records only technically necessary source-
access conclusions and root names. No credential-like material is present.
