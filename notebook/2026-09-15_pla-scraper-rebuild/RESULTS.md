# Loom PLA-only scraper rebuilt from composite G-code — 2026-09-15

Physical sample **X0009** (`experiments/Samples/samples.jsonl`) — **built, not
yet printed**. `EXPERIMENTAL`. For Plastic 2 (FFF, right, 0.4 mm).

## Why

The owner wants a plastic-only PLA copy of the scraper to compare against
X0001, the Stage 1 PETG + fibre print of the same part, and asked whether the
G-code could be converted to a model or stripped of its fibre path instead of
re-slicing. Both demo scrapers on Loom (`DemoFiles/PLA-Scraper.gcode`,
`PETG-Scraper.gcode`) are `PRINTING_MODE: Plastic and Composite`, so neither can
be printed plastic-only as-is, and no model file for the part exists in the
repository, on the NAS, on Loom or in the extracted vendor packages.

## What was done

`experiments/Samples/gcode_to_solid_stl.py` (new) rebuilds a printable solid
from the sliced composite file (LM-021,
`sources/loom/sessions/2026-09-13T054125Z/…/response-body.gcode`):

1. Collect the wall loops of each layer (`Inset XP` and `Inset 0`, Plastic 2
   moves only; `Skirt` and `Priming line` skipped; the fibre inset `Inset XF` is
   inside the walls and is ignored).
2. Classify each loop by nesting: outermost loops are solid outlines; a nested
   loop is a **hole** only if it stands more than 1.5 line widths clear of its
   parent — a loop that hugs its parent is the next concentric wall and is
   dropped. This keeps the lattice openings and the frame's big opening while
   discarding duplicate wall passes.
3. Fill the outlines minus the holes on a 0.2 mm raster, grow the filled area by
   half a line width (the toolpath is the centre of the extrusion), stack the
   layers and write the surface as a binary STL.

Checks: the reconstructed cross-sections match a raster of *all* layer-1
extrusion (blade solid at one end, open frame, lattice at the other), and the
bounding box matches the original print: **133.3 × 46.2 × 6.16 mm**, 25 macro
layers. `analysis_reconstructed_layers.png` shows layers 1, 13 and 49.

`INFERENCE`: this is the printed shape, not the vendor's CAD. It is quantised to
0.2 mm in X/Y and to the file's 0.24 mm macro-layer in Z, so sloped faces carry
0.24 mm steps and dimensions can differ by about ±0.1 mm.

## Sliced print

```
python3 experiments/Samples/make_tagged_print.py --sample-id X0009 \
  --reference notebook/2026-09-14_pla-temperature-tower/loom_T1.3mf \
  --out notebook/2026-09-15_pla-scraper-rebuild --name loom_scraper_pla_X0009 \
  --set nozzle_temperature=205 --set nozzle_temperature_initial_layer=210 \
  --set filament_flow_ratio=0.96 \
  notebook/2026-09-15_pla-scraper-rebuild/scraper_from_LM-021.stl
```

Large artefacts live on the NAS, not in git (the STL is reproducible from
LM-021 with the checked-in script): `derived/models/X0009/` holds
`scraper_from_LM-021.stl` (31 MB, sha256 `2563e9d992561c6891d3ee4b685142e9eb33e4e378ce1bb035bbc715844026cb`) and
`loom_scraper_pla_X0009.3mf` (sha256 `baa1ad64a4caa458cca4197a6a5de3a092e2ac741b0c7e3f8415ce44704c1bde`).

`loom_scraper_pla_X0009.gcode` (sha256 `9abf6eb3aff9788acd6f3ee0ded246e2a46a20bca15facb36d27879428213060`): 30 layers, 6.00 mm, 8.69 g, estimated 40 m 48 s,
X 86.6–218.4, Y 124.8–180.2, with the X0009 ID tag on the plate. Tuned Plastic 2
settings (205 °C, first layer 210 °C, flow 0.96); tag presence and all three
overrides verified in the G-code.

## Note for the print start

The touchscreen's visit to the PLA-Scraper demo at 16:23 left
`printing_info_left_preheat_temperature = 230` and `print_mode = 1` in
`variables.cfg`. A Plastic 2 print must set the left preheat back to 0 explicitly,
or the CFC nozzle will be heated to 230 °C for no reason.

## Results

**Print cancelled at layer 24 of 30** (18:20:34 start, cancelled 19:06:51 at the
owner's request; Moonraker history `cancelled`, `print_duration` 2,229 s,
`filament_used` 3,563 mm). Heaters went to 0 and the head parked; prep variables
restored to 10/10/290/290 with auto-levelling off. Camera frames kept here:
`camera_during_print_19-06.jpg` (toolhead blocks most of the plate; the part and
its tag are visible) and `camera_after_cancel_19-08.jpg`. The camera cannot
resolve the surface problem the owner saw in person.

### What went wrong: stringing across the lattice

`USER-OBSERVED` (owner stood the part up on the plate for the camera;
`camera_part_standing_stringing.jpg`, `camera_lattice_stringing_zoom.jpg`):

- The **geometry printed faithfully** — continuous ribs, sharp corners, open
  lattice triangles, the blade end solid, the part flat and well adhered. The
  reconstruction itself is not the problem.
- The defect is **webbing across the lattice openings**: strands spanning the
  triangles, loops, tufts of fuzz, and a curl of filament hooked on one end.
- `INFERENCE`: the lattice is the worst case for ooze — dozens of short hops
  between thin ribs on every layer — while a Benchy is mostly continuous wall.
  The profile's retraction (0.5 mm @ **15 mm/s, no wipe**) is what the 2026-09-15
  retraction test already flagged as weak, and FibreSeek's own PLA profile uses
  the same length at **30 mm/s with wipe** (LM-026). Follow-up print X0010
  repeats this file with 35 mm/s and wipe on
  (`../2026-09-15-T6/RESULTS.md`).

**Not usable for the strength comparison.** `USER-OBSERVED`: while the print was
running the owner judged the part "didn't come out so well" and decided not to
test with it — "I'd rather test it properly" — and will ask FibreSeek for the
original model instead. The print was allowed to finish.

`INFERENCE`: the reconstruction's own limits are the likely cause — the shape is
quantised to 0.2 mm in X/Y and to the file's 0.24 mm macro layer in Z, so sloped
and curved faces carry visible steps, and edges sit within about ±0.1 mm of the
vendor geometry. That is acceptable for checking a shape, not for a part whose
strength and finish are the point.

Follow-ups:
- Owner to ask FibreSeek for the scraper model; a real model re-sliced in
  OrcaSlicer would make PLA vs PETG vs PETG-plus-fibre comparisons clean.
- `gcode_to_solid_stl.py` stays useful for recovering a *shape* when no model
  exists (its own record of what it can and cannot do is above), but it should
  not be used for parts that are to be tested mechanically.
- The comparison caveat stands for any future pair: X0001 (PETG + fibre) versus a
  PLA print differs in both matrix and fibre; a PETG-only print isolates the fibre.
