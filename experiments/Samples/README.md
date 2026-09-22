# Physical sample registry

Every physical test print the owner keeps gets a **sample ID** that ties the
piece back to this knowledge base: the G-code that made it, the record that
reads it, and the photos.

## ID scheme

- Format **`XNNNN`**: the letter `X` and four digits, assigned in order and
  never reused (`X0001`, `X0002`, …). Printer, date and material live in the
  registry, not in the ID, so the ID stays short enough to print.
- The scheme was `SMP-NNNN` for its first hour; the owner switched it to `XNNNN`
  on 2026-09-15 before any piece was labelled. The seven early samples kept their
  numbers (`SMP-0005` became `X0005`); each registry entry notes its former ID.
- **One ID per print job.** Pieces inside a job are told apart by a piece label
  (`C`, `BL`, `+5`, `-3`, `A`, …). Where a piece already carries a printed
  label, such as the embossed number on a flow patch, that label is the piece
  label. Write a piece as `X0006/-5`.
- A failed or aborted print gets an ID only if the owner keeps it.

## How the ID gets onto the sample

- **From 2026-09-15 on, prints get an ID tag.** `make_sample_tag.py` makes a
  27 × 9 × 1.6 mm tag with the ID in raised 5 × 7 dot-matrix text (0.8 mm dots,
  slashed zero; well under 0.5 g in PLA). It is printed as its own object
  on the same plate, so it shares the job's settings and G-code.
  - The flow generator does this with `--sample-id`
    (`notebook/2026-09-15_pla-flow-pass-1/make_flow_patches.py`) and fails if
    the tag is missing from the G-code.
  - Any model, sliced for Loom with the tag already on the plate:
    `experiments/Samples/make_tagged_print.py` (checks the tag is in the
    G-code and that every `--set` override took effect).
  - For any other print: `python3 experiments/Samples/make_sample_tag.py
    XNNNN tag.stl`, then add `tag.stl` to the plate (Orca GUI: drag it in),
    clear of the part. `--preview` prints the bitmap without writing a file.
- **Earlier samples (X0001 to X0007) have no tag.** Mark them by hand —
  marker on the piece, or on the bag they are kept in.
- Keep the tag bagged or taped with its pieces.

## Photographing samples for comparison

Learned on flow pass 2 (X0007, 2026-09-15): handheld photos could not rank
1 % steps, while a controlled set located an under-extrusion step that touch
missed.

1. **Fix the camera** (stand or books) and keep the framing; move samples, not
   the phone.
2. **One light, room lights off**, low (10–20° above the table) so it rakes
   across the printed lines; then take a second shot with the light (or the
   samples) rotated 90°.
3. **Lock focus and exposure** (iPhone: long-press, "AE/AF LOCK") and keep one
   white balance for the whole series — neutral daylight suits white PLA.
4. **Put everything being compared in one frame**, closest candidates side by
   side; a single-sample frame cannot separate a real difference from a light
   change between shots.
5. **Keep the light even across the frame** (lamp further back, or along the
   rows).
6. **In frame:** a scale (cutting-mat grid) and the sample ID.
7. **Optional:** backlight (white screen, room dark) to reveal gaps; a blind
   touch ranking with labels taped over.
8. **Upload full-resolution originals, unedited**, to NAS `originals/incoming/`,
   and add the photo names to the sample's `photos` list.

## Registry

`samples.jsonl`, one JSON object per line, checked by
`python3 tools/validate_samples.py`:

| Field | Meaning |
| --- | --- |
| `sample_id` | `XNNNN`, consecutive from `X0001` |
| `printed_date` | local date the print ran (`YYYY-MM-DD`) |
| `printer` | machine, e.g. `Loom (FibreSeeker 3)` |
| `title` | what the sample is |
| `material` | material, nozzle/tool |
| `print_file` | repository path of the exact G-code printed |
| `print_file_sha256` | its SHA-256 (the validator re-hashes it) |
| `record` | repository path of the record that reads the sample |
| `pieces` | list of `{label, description}` |
| `photos` | owner photo names on the NAS (`originals/incoming/…`) |
| `id_marking` | `embossed-tag`, `handwritten` or `none` |
| `archive_status` | `archived`, `unknown` or `discarded` |
| `provenance_class` | `EXPERIMENTAL` |
| `notes` | anything else |

Update `id_marking` and `archive_status` when the owner labels or archives a
piece; never renumber. A sample's reading stays in its record — the registry
only points to it.
