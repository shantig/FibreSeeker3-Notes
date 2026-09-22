# Loom capture session 2026-09-08T154557Z

- Scope: bounded read-only Moonraker host/application metadata.
- Machine: Loom, project owner's FibreSeeker 3 at `<printer-ip>`.
- Started: `2026-09-08T15:45:57Z` (capture-client clock).
- Ended: `2026-09-08T15:48:56Z` (capture-client clock).
- Requests issued to Loom: three, sequentially.
- State-changing requests or printer commands: none.
- Authentication material sent or stored: none.

The raw LM-003 and LM-004 responses contain machine, hardware, or network
identifiers. They are preserved exactly as requested but must not be reproduced
in interpreted documentation or public reports without a separate privacy
review.

## Captures

| Provenance ID | Method and endpoint | HTTP status | Body bytes | SHA-256 |
|---|---|---:|---:|---|
| LM-002 | `GET /server/info` | 200 | 1,803 | `9bbd2c4acf716c69a324127b3dc51367150eb0f345c9b9a1c1c4c852959ed592` |
| LM-003 | `GET /printer/info` | 200 | 462 | `f78f9b2d15e960b3f2d91e820d0455a4247289292c0da90b099a12fb72051e3c` |
| LM-004 | `GET /machine/system_info` | 200 | 1,723 | `3c5e07ebebbb510de69626dd892c354dd5c0cbbefe86f4594d7d45d57c4b5984` |

The `configs/`, `logs/`, `system/`, `can/`, and `vendor-components/`
directories are intentionally empty placeholders. The system and CAN findings
in this session came from LM-004 and remain preserved in its API capture.
