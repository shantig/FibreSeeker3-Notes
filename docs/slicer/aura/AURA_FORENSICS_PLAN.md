# Aura Forensics Plan

## Objective and evidence boundary

Recover public, officially distributed Aura definitions and schemas without
executing unknown software. Target printer definitions, plastic definitions,
fiber/composite definitions, profiles, material-compatibility mappings, sample
projects, and parameter schemas. Recovered Anisoprint data remains
`ANISOPRINT_OFFICIAL`; it is not FibreSeek configuration unless an independent
FibreSeek source proves equivalence.

## Candidate public inputs

1. Current Aura 2.6.2 distribution and the separate APAC package.
2. Aura 2.5.8 stable distribution for a version-to-version baseline.
3. Aura 2.6.1 beta and “Sk3 template preview” only after stable packages.
4. Official sample projects added in Aura 2.2.0 and the Clear PETG/CFC PETG
   wand project added in 2.4.8.
5. User-exported public `.auproj`, `.auprojx`, settings exports, `.aus.json`
   sessions, CLI JSON, and official calibration G-code.
6. Official documentation, changelogs, and the `cli-inputfile.schema.json`
   named by the Aura CLI documentation.

## Expected formats and locations

- Windows installers: `.exe`, MSI/MSIX payloads, PE/COFF assemblies, embedded
  CAB/ZIP/7z resources, and .NET resources/configuration.
- Projects: legacy `.auproj`, current `.auprojx`, and associated STL/STP/OBJ/3DS
  geometry references.
- Settings/session exports: `.aus.json`, JSON, XML, ZIP containers, or custom
  files that may reveal their container type through magic bytes.
- Data stores: SQLite (`.db`, `.sqlite`, `.sqlite3`), JSON, XML, CSV, protobuf,
  MessagePack, .NET resource files, or embedded compressed blobs.
- Schemas/config: `cli-inputfile.schema.json`, `.config`, YAML/TOML/INI, and
  application resources.
- Typical Windows locations to search in extracted payloads: `Program Files`,
  `ProgramData/Anisoprint/Aura 2`, user AppData paths, `resources`, `profiles`,
  `materials`, `printers`, `samples`, `schemas`, and `logs`.

## Safe static workflow

1. Acquire each package as an immutable original, recording redirects, UTC,
   filename, MIME, byte size, SHA-256, and any publisher signature.
2. Work only on a copied payload in a temporary, non-executable directory.
3. Identify format from magic bytes, not extension.
4. List archive/container contents before extraction; reject absolute paths,
   parent traversal, device files, and suspiciously large expansion ratios.
5. Extract with networking disabled and without launching setup helpers.
6. Inventory files by path, size, MIME, hash, and entropy; compare versions.
7. Search text and strings for `printer`, `plastic`, `fiber`, `composite`,
   `profile`, `compatib`, `approved`, `temperature`, `feedrate`, `layer`,
   `extrusion`, schema names, extensions, GUIDs, and database connection strings.
8. Inspect recognized JSON/XML/SQLite/resource containers read-only. Export
   recovered records to derived data while preserving exact source offsets and
   hashes.
9. Validate relationships: profile-to-printer, profile-to-plastic/composite,
   slot/extruder types, material IDs, approved flags, versions, and overrides.
10. Diff 2.5.8 against 2.6.2 to separate stable official data from beta/Sk3
    additions. Do not interpret renamed IDs as semantic equivalence without
    evidence.

## macOS and Linux tools

- Identification/hashing: `file`, `shasum -a 256`, `xxd`, `hexdump`, `stat`,
  `strings`, `exiftool`.
- Safe archive listing/extraction: `7zz l`, `7zz x`, `bsdtar -tf`, `unar`,
  `cabextract`, `msiextract`/`lessmsi` where available.
- PE/.NET inspection: `objdump`, `llvm-objdump`, `pefile` tooling, `ilspycmd`,
  `dnfile`, and resource-only inspection. No assembly loading or execution.
- Structured data: `jq`, `yq`, `xmllint`, `sqlite3 -readonly`, `csvkit`,
  `protoc --decode_raw`, JSON Schema validators.
- Searching/comparison: `rg`, `diff -ru`, `git diff --no-index`, `cmp`,
  `radiff2` for coarse binary comparison.
- Optional sandboxing for parsers: disposable VM/container with read-only input,
  no network, no shared home directory, strict CPU/memory limits, and no printer
  or USB access.

## Deliverables for a later phase

- Package-level acquisition records and checksums.
- File inventories and version diffs.
- Raw extracted official settings in an immutable derived tree.
- Normalized printer/plastic/composite/profile tables with source IDs and field
  mappings.
- Compatibility graph with explicit version scope.
- Parameter dictionary with units, defaults, bounds, and source locations.
- A gaps report distinguishing encrypted/obfuscated/licensed data from data not
  present in the public distributions.

## Stop conditions

Stop and seek review before dynamic execution, decompilation beyond metadata and
resource inspection, bypassing licenses, decrypting protected stores, contacting
update APIs beyond ordinary client-visible URLs, or analyzing private/customer
packages. Never connect recovered code or G-code to a printer during forensics.
