# Anisoprint Corpus Coverage

## Acquisition totals

Phase 2F-A added 35 `AP-*` manifest records: 34 acquired and one failed. Of the
acquired records, 30 are HTML pages, two are PDFs, and two are immutable Git
bundles. Eighteen records explicitly supersede prior discovery/history records;
`AP-142` is a preserved, byte-identical repeat of `AP-133` and is excluded from
technical coverage counts. The 32 acquired web documents include the seven
official lesson pages.

| Range | Coverage |
| --- | --- |
| `AP-114` | `aura-docs` full Git bundle and immutable source-file index |
| `AP-115` | `MKA-firmware` full Git bundle; static inspection only |
| `AP-116`–`AP-120` | Composer PDF/online manual, guide, XY procedure, and failed service G-code |
| `AP-121` | Composer firmware release/download inventory; packages not acquired or run |
| `AP-122` | first-party composite design rules |
| `AP-123`–`AP-124`, `AP-143`–`AP-148` | official curriculum and seven video lesson pages |
| `AP-125`–`AP-130` | CFC PA, CFC PETG, reinforcing fiber, PETG, and compatibility material pages |
| `AP-131`–`AP-141` | support, Composer, Aura, docs, quick-start, troubleshooting, supports, layup, editions |

## High-priority findings and conflicts

- `NozzleOffsetTest.gcode`: successfully sourced as an officially linked
  Composer service asset and calibration dependency in `AP-116`–`AP-119`.
  The exact public URL is
  `https://support.anisoprint.com/wp-content/uploads/2019/03/NozzleOffsetTest.gcode`,
  but retrieval returned 404 (`AP-120`). The bytes were not recovered.
- XY nozzle-offset calibration: sourced in `AP-119` and corroborated by
  `AP-116`–`AP-118`. Composer requires it after either nozzle replacement,
  measures centering in labeled X/Y cells, adjusts both offsets, and verifies
  by reprinting.
- Composite Z-offset calibration: sourced in `AP-116`–`AP-118`. It is the
  composite nozzle's relative Z position versus the plastic nozzle and is
  triggered by nozzle replacement, scratching, wall defects, path deviation,
  and adhesion symptoms.
- Minimum fiber-length rule: the often-repeated “about 45 mm” statement was
  **not** recovered as a generic fiber-length rule. Aura profile stores contain
  `MinimumPerimeterLength=45.0`, while distinct cellular/solid minimum-segment
  fields contain 10.0 or profile-scoped 20.0. Units for these database scalars
  remain unconfirmed by the stores themselves.
- Hole-adjacent rule: the Aura changelog says the minimum reinforced-perimeter
  setting affects reinforcement around smaller openings. No exact 12 mm
  hole-clearance rule was recovered. The value 12.0 occurs in the Sk3
  `FiberMinRadiusF` field; common Aura profiles contain 5.0. It is a radius
  field, not a hole-clearance field, and its source unit remains unresolved.
- Macrolayer semantics: sourced in `AP-107`, `AP-111`, `AP-114`, `AP-138`, and
  `AP-139`. A macrolayer is an abstraction/layer package; physically printed
  events are microlayers. Reinforced-entity height equals macrolayer height,
  other entity heights are integer fractions, coincident entity events share Z
  boundaries, and layup/support rules operate across this hierarchy.
- Cutter/feed/restart: `AP-107` defines `CutDistance` as cut-point-to-outlet
  distance and `FiberRestartLength` as restart extrusion, with the latter at
  least the former and Composer guidance 1–2 mm larger. `AP-115` statically
  exposes fiber-path state commands (`M1001`/`M1002`), cut/configuration commands
  (`M1010`/`M1011`), synchronized servo sequencing, and pause deferral to a path
  boundary. These are possible analogs only; they do not establish Rocket
  precedence or FibreSeek commands.

## Limitations and unavailable sources

- The official `NozzleOffsetTest.gcode` asset is unavailable at its live URL.
- Vimeo prohibits automated user-content crawling in its robots policy. Vimeo
  pages, streams, captions, and private resources were not scraped. The seven
  videos are inventoried from the official Anisoprint lesson pages only.
- No public transcript/caption URL was exposed in those archived lesson pages.
- The support/docs hosts presented expired TLS certificates; each affected
  retrieval records the explicit exception. Content origin was bounded to the
  official requested/final host, but current certificate authenticity could
  not be established at acquisition time.
- The crawl is intentionally scoped, not a mirror. Unlinked historical files,
  deleted downloads, and authenticated support content may remain unavailable.
- Profile scalars do not by themselves establish units, universal limits, or
  manufacturer recommendations.
