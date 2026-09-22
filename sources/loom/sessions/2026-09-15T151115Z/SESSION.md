# Loom capture session 2026-09-15T151115Z

- Purpose: preserve the configuration evidence behind the 2026-09-15 retraction
  session (`07_Troubleshooting/Loom/2026-09-15-T1/RESULTS.md`) — specifically
  that `[firmware_retraction]` is **not** defined on the machine and that
  Moonraker's `config` root is read-only.
- Authorization: project owner, 2026-09-14 — full live access (reads, writes,
  shell, configuration).
- Machine: Loom, project owner's FibreSeeker 3 at `<printer-ip>`, Moonraker on
  port 7125.
- Started `2026-09-15T15:13:35Z`, ended `2026-09-15T15:13:46Z` (capture-client
  clock). Two sequential GETs. An earlier pair of reads at 15:11:15Z went
  through the on-device nginx proxy on port 80 and was replaced by these, byte
  for byte identical, so that every capture here addresses Moonraker directly
  as the evidence protocol expects.
- State-changing requests in **this capture session**: none. Authentication
  material sent or stored: none. The printing work of the wider interactive
  session is recorded separately in the troubleshooting record; its individual
  API calls were not preserved as byte-for-byte captures.

## Captures

| Provenance ID | Method and endpoint | HTTP status | Body bytes | SHA-256 |
|---|---|---:|---:|---|
| LM-022 | `GET /server/files/config/printer.cfg` | 200 | 9,541 | `33322fd444f3cf04d19734e8043fb4e0ad33e7f06979448e49c2b5aec21471b7` |
| LM-023 | `GET /server/files/roots` | 200 | 569 | `564af0e029eb00c68d0bfbe9154e146dfe7b8bc331d997a15a5a126611e12985` |

## Handling notes

- **LM-022 is the post-print state.** The same endpoint was read earlier in the
  interactive session, at 2026-09-15 09:17 local, giving 9,545 bytes, SHA-256
  `f8eb094339fa268004f97afd23a4536cd5a9642f7c2240a0dd3b676d26654230`. That
  earlier read was not preserved with headers and is **not** committed; only
  its digest is recorded here and in the troubleshooting record.
- **The file changed during the print.** The only difference between the two
  reads is the `[bed_mesh runtime_active]` block, replaced with the fresh
  full-bed probe taken at 09:30–09:51 local. The response `Last-Modified` is
  `2026-09-15 14:50:03 GMT`, which is when that probe finished. No `SAVE_CONFIG`
  was issued by this session. `INFERENCE`: the vendor mesh routine writes
  `printer.cfg` directly so a fresh mesh survives reboot — `save_config_pending`
  stayed `true` and still lists `bed_mesh runtime_active` afterwards, so this is
  not Klipper's own `SAVE_CONFIG` path (which restarts).
- **`[firmware_retraction]` is absent** from LM-022, and
  `configfile.settings` has no `firmware_retraction` key. Bounded search
  absence, not proof the module cannot be loaded: the vendor Klipper fork does
  ship `klippy/extras/firmware_retraction.py`.
- **LM-023 substantiates the write boundary**: `config` and `logs` are `r`;
  `gcodes`, `usb` and `timelapse` are `rw`.
