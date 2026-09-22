# Bounded Offline Rocket Test Plan

## Current state

No test in this plan was executed during Phase 2F-B. Rocket 1.3.2 exposes
slicing through a localhost `Aura.Monolith.API` service and no standalone,
side-effect-free CLI/request fixture was recovered. A later execution requires
a verified request schema, copied disposable resources, network/device
containment, and deterministic cleanup.

Every future run must deny external network access and printer discovery, use
no Moonraker/Klipper/USB/serial connection, write only into a unique temporary
directory, preserve all input and output bytes, record process/version hashes,
and terminate before any send/print action. Results are
`ROCKET_OFFLINE_RUNTIME`, never manufacturer guidance.

## Required harness gates

1. Copy the exact Rocket backend/resources into a fresh temporary directory;
   never mutate FS-122 or FS-125 originals.
2. Use a host-level sandbox that denies external network and device access while
   allowing only the explicitly required loopback endpoint.
3. Capture executable/DLL/profile/model/request hashes, environment variables,
   stdout/stderr, HTTP request/response, generated G-code, and exit status.
4. Prove the harness cannot enumerate or contact printers before supplying a
   slice request.
5. Use synthetic, non-proprietary geometry generated deterministically by a
   committed script. Do not use physical printer calibration values.
6. Diff only normalized generated output; preserve raw output separately.

## Test matrix

| Test | FSQs | Controlled variable | Required observation |
|---|---|---|---|
| RT-001 | 001, 004 | Fiber lines/perimeters immediately below, at, and above 10/20/55 mm | Suppressed, prolonged, connected, or emitted paths |
| RT-002 | 003, 004 | Hole diameter and wall/boundary clearance sweep | Fiber path termination/offset around holes and exterior contours |
| RT-003 | 010 | Ratio fields plus deliberately non-divisible/invalid values | API validation, coercion, rounding, or rejection |
| RT-004 | 011 | FiberPrintOrder 0/1/2 on identical geometry | Entity sequence at coincident Z; regression check only because static contract is resolved |
| RT-005 | 012, 015 | One-at-a-time changes to CutDistance, FiberRestartLength, and CutCode comment/body | G-code cut location, restart extrusion, emitted M2800/M400, precedence |
| RT-006 | 021 | SupportThickRatioToMacro and interface count sweep | `LAYER`/`MACROLAYER` markers, thick/thin/interface cadence and air-gap events |
| RT-007 | 022 | Two overlapping masks plus overlapping height layups with reversed priorities | Mask-to-mask, layup-to-layup, and mask-to-layup precedence |

## Stop conditions

Stop without retry if the backend attempts external network/device access,
requires credentials, writes outside the disposable directory, cannot accept a
fully local request, or exposes a print/send/device action in the code path.
Preserve the failure state as an experiment result; do not weaken containment.
