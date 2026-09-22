# Community tool: "G-Code Modifier" (vilos.com) — FibreSeeker 3 G-code analysis

Provenance `COMMUNITY` (CM-005). Shared by the owner 2026-09-15 as a community
member's tool for analysing G-code from the FibreSeeker 3; the author reportedly
sees many errors in FibreSeek Rocket Slicer output. **That claim is the author's,
not verified here.** This note is a static review of the tool's code, cross-checked
against first-party Rocket G-code already in the repo. Conclusions drawn from
reading code, not from running it, are labelled `INFERENCE`.

## Source

- URL: `http://vilos.com/fibreseeker3gcode/gcode-modifier.html`
- Retrieved 2026-09-15T16:37:30Z, HTTP 200, `Last-Modified` 2026-09-14 19:19:59 GMT,
  783,462 bytes, sha256
  `bea4e949c9e15f797f2a49d8f640fc530b8c58d02ca5591ad5adc2834d75d25d`.
- Original preserved byte-for-byte on the NAS:
  `originals/COMMUNITY/CM-005/gcode-modifier.html` (+ `response-headers.txt`).
- **Where it comes from (CM-006).** The page is the built bundle from GitHub pull
  request [little-did-I-know/Gcode#30](https://github.com/little-did-I-know/Gcode/pull/30)
  by user `3ricj` — "Add FibreSeeker Rocket Slicer support (parse & view)",
  **open, not merged**, created 2026-09-14T19:37:20Z, head commit `fcc7576`.
  After normalising line endings (the web server serves CRLF) it is
  byte-identical to `gcode-modifier.html` at that commit (sha256
  `10188f71…27463`). The upstream project is a general G-code
  viewer/modifier/analyser, MIT-licensed, not specific to FibreSeek.
  Plan, PR metadata and bundle are preserved at `originals/COMMUNITY/CM-006/`.

## What it is

A single self-contained HTML page (one ~16,700-line inline script, no external
scripts or stylesheets). Static scan found **no network calls** in the code
(`fetch`, `XMLHttpRequest`, `sendBeacon`, `WebSocket`: none); a dropped file is
parsed in the browser. It is a general G-code viewer/editor for Bambu, Klipper,
Marlin and RRF, with a 3D viewer, heatmaps, and editing tools (pauses,
filament changes, custom G-code insertion, Z-offset, fan-profile rules), plus an
analysis layer: motion, structural (overhang), thermal (warp), retraction
(stringing risk) and flow engines feeding a "Diagnostics"/"Insights" panel.

## FibreSeek-specific support

Everything FibreSeek-specific is in the **parser**; none of it is in the analysis:

- Detects Rocket files by `Generated with FibreSeek Rocket Slicer` in the header.
- Layer marker `; LAYER:N [z]`; section headers `; <name> start` mapped to
  feature types (e.g. `Inset XP` → outer wall, `Fiber infill` → FIBER,
  `Cellular infill` → infill).
- Reads **`U` as the fibre axis and `V` as a secondary material axis, both
  relative**, and marks moves that feed U or V without an E word as extruding;
  ignores the `P` word ("process parameter").

### Cross-check against first-party Rocket G-code

Checked on `DemoFiles/PETG-Scraper.gcode` (Rocket 1.3.1.480, LM-021):

- `E` appears only with **T1** (plastic, right nozzle): 38,773 positive and
  1,855 negative moves.
- `U` and `V` appear only with **T0** (the composite head, `T0 R ; switch
  extruder type to:FIBER`), in `Inset XF` and priming sections. `U` advances
  about 1:1 with path length (`X107.9→115.9` with `U8`) and never goes
  negative; `V` is small per-segment plastic feed and **does** go negative
  (34 moves). A fibre section is `M1001 L<len>` … `M2800` (cut) … `M1002`, with
  `G1 F1500 U55` / `G1 F600 V5` restart feeds.
- So the tool's axis reading is **consistent** with the evidence: `U` behaves
  like fibre feed and `V` like the composite nozzle's matrix plastic, both
  relative. `INFERENCE` for what `U`/`V` physically drive (Loom's `gcode_move`
  reports `material_gcode_position {e, u, v}`, and the vendor preprint primes
  the left nozzle with `G1 V4` / `G1 V-2`, which fits).

## Where its "errors" on Rocket files may come from

`INFERENCE` from the code; not confirmed by running the tool:

- **The fibre flags are never used.** The parser sets `move.fiber`, `uLength`
  and `vLength`, but no analysis engine reads them. Composite moves enter every
  engine as ordinary extrusion with zero E.
- **Retraction/stringing analysis only tracks `E` (and `G10`/`G11`).** `V`
  retractions and fibre cuts (`M2800`) are invisible, so travel after a
  composite section looks unretracted and can be reported as stringing risk
  even when Rocket did retract `V` or cut the fibre. Continuous fibre also
  cannot retract by design, so "no retraction" is expected there.
- **Flow analysis skips moves with zero E**, so composite sections are simply
  not analysed (no false flow alarms from them, but no coverage either).
- **The rest are generic FDM heuristics** (minimum layer time, >30 %
  volumetric-flow jumps, first-layer average speed > 60 mm/s, many >20 mm
  travels, overhangs, warp risk). There are **no rules specific to Rocket
  defects**. Rocket's plastic-only moves can still trip these, and some may be
  real (e.g. aggressive speeds), but a warning here is not evidence of a
  slicer bug.
- **Command decoder:** `M1002` is described as Bambu's "System Control
  Multiplex" (`judge_flag` etc.); on FibreSeek it ends a fibre section.
  `M1001` and `M2800` are not in its dictionary. Cosmetic in the editor, but a
  reader could be misled.
- **The PR states the same limits itself.** Its "known limitations" say fibre
  `U`/`V` feed is not yet in the flow/thermal calculations, a few analyzer
  line-scans still only match the no-space `;LAYER:` marker, and its
  pause/filament-change snippets emit `G1 E…` retracts "which won't retract
  fiber (U)". Its scope is parse and view, not error detection.
- **Export risk:** the tool can modify and export G-code. Any edit that inserts
  moves or pauses inside a fibre section (between `M1001` and `M1002`) is
  outside anything the tool models — and its pause/filament snippets retract only
  `E`, which on the composite head moves nothing. Do not print tool-modified
  Rocket files
  without inspecting the fibre sections first (per `SOURCE_POLICY.md`, print
  from a copy).

## Rocket format claims in the PR plan (community, from the author's own file)

The plan documents a Rocket 1.3.1.480 file dated 2026-09-14 (1,264,187 lines,
912 layers) that is **not** in this repository. Claims worth checking against
first-party files when we have a matching one:

- `; LAYER:<n> [<absolute Z>]` is 1-based; layer heights vary (0.2, 0.35, 0.5,
  then 0.15 mm steps in that file).
- 455 `; MACROLAYER:<n> [<z>]` markers group layers. **Checked on LM-021:** the
  49-layer demo has 24 `MACROLAYER` markers, one per two plastic layers, each
  sitting at the Z of the following layer (`LAYER:1 [0.2]`, `LAYER:2 [0.32]`,
  `MACROLAYER:2 [0.44]`, `LAYER:3 [0.44]` …; plastic steps of 0.12 mm there).
  `INFERENCE`: a macro-layer is the composite layer spanning two plastic
  layers. `OPEN QUESTION` until confirmed by FibreSeek or a print.
- Fibre cut events: `; Start to cut` → `M2800` → `M400` → `;CUT DISTANCE <n>` →
  `; Cutting completed.`, bracketed by `M1001 L80` / `M1002`.
- `U` positive = feed fibre; `V` positive feed / negative retract
  (`V-4 ; Retract`); `P` constant per move (~0.034) with unknown meaning —
  LM-021 shows per-section `P` values (0.07 on the priming line, 0.048–0.052 on
  `Inset XF`; 921 of 1,068 `P` words on U/V moves are `P0.048`, others 0.052,
  0.07, 0.095, 0.104, 0.14), so it is not a single constant. `OPEN QUESTION`:
  what `P` is.
- `;CUT DISTANCE 54.8` in LM-021 (18 occurrences) — same comment form.
- No `G2`/`G3` arcs.

## Usefulness here

- Good for **viewing** Rocket files: section types, per-layer structure, the U/V
  split, and the plastic-side heuristics.
- **Not** a validator of Rocket correctness; its Rocket-specific findings need
  independent confirmation against the G-code and, where it matters, a print.
- `OPEN QUESTION`: what the author's specific Rocket "errors" are. Worth asking
  them for examples — concrete ones can be checked against LM-021 and against
  Loom's behaviour.
- Not run against Rocket files in this review: loading FibreSeek G-code into the
  hosted third-party page was declined in-session as a data-exfiltration risk,
  even though the static scan found no network code. A run would need either the
  owner's go-ahead or an isolated offline copy.
