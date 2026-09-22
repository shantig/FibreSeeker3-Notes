# Loom Evidence Protocol

## Scope

Loom is a live FibreSeeker 3 at `<printer-ip>`.

The owner authorized full live access on 2026-09-14, replacing the earlier
read-only limit:

- Moonraker reads and writes, websocket/JSON-RPC, G-code, and macros;
- homing, motion, extrusion, cutting, heating, and fans;
- SSH/shell, services, configuration, database, and files;
- static and dynamic reverse engineering of on-device software, including the
  FibreTouch Qt HMI (screenshots, process inspection, binary copies).

Evidence captured before 2026-09-14 was taken under the read-only limit, and
its records remain accurate for that period.

## Recording live work

- Log every state-changing action (G-code, macro, config or file change,
  service action, shell command that writes) with UTC time, the exact command,
  and the observed result, in the session's `SESSION.md`.
- Copy a file from Loom before changing it, and record both SHA-256 digests.
- Keep large binaries (the HMI app, libraries, firmware images) on the NAS and
  record their paths and digests in the repository.
- Keep secrets out of every capture and transcript: passwords, keys, tokens,
  cookies, Wi-Fi and cloud-account configuration.

## Capture procedure

1. Create one timestamped directory under `sources/loom/sessions/`.
2. Record the exact method and URL, UTC start/end time, HTTP status, client tool,
   timeout, and any error. Never store authorization headers, cookies, API keys,
   passwords, Wi-Fi configuration, tokens, or other secrets.
3. Preserve response headers and body byte-for-byte before interpretation.
4. Record SHA-256 and byte size for each preserved response body.
5. Treat raw captures as immutable. A repeated or corrected capture gets a new
   timestamped session or request directory.
6. Add a provenance-ledger record only after the capture is complete and its
   digest has been checked.

## Session layout

```text
sources/loom/
  README.md
  sessions/<UTC-session-id>/
    SESSION.md
    moonraker-api/<request-name>/
      request.json
      response-headers.txt
      response-body.json
      sha256.txt
    configs/
    logs/
    system/
    can/
    vendor-components/
    hmi/
    shell/
```

The category directories reserve separate evidence boundaries:

- `moonraker-api/`: unmodified HTTP API responses;
- `configs/`: explicitly selected configuration copies after secret review;
- `logs/`: existing logs, with privacy/secret review before commit;
- `system/`: passive host, service, process, and version metadata;
- `can/`: passive CAN interface and discovered-device topology;
- `vendor-components/`: code/metadata specific to non-upstream Moonraker
  components;
- `hmi/`: touchscreen screenshots and FibreTouch process/binary metadata;
- `shell/`: SSH command transcripts, secrets removed.

## Interpretation boundary

Every claim must cite a capture and use one of the labels in `README.md`.
Configuration presence does not prove runtime execution. An object name does
not prove hardware presence. A component name does not establish its vendor,
purpose, safety, or upstream divergence. Negative search results are bounded
search absences, not proof of nonexistence.
