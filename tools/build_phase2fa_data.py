#!/usr/bin/env python3
"""Build deterministic Phase 2F-A curated JSONL artifacts.

The input claims below are intentionally reviewable curation, not an automated
promotion pipeline. Running this script only rewrites derived repository files.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/operational"


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for r in records)
    path.write_text(text, encoding="utf-8")


records: list[dict] = []


def add(
    domain: str,
    concept: str,
    source_id: str,
    location: str,
    claim: str,
    interpretation: str,
    *,
    value=None,
    unit=None,
    qualifier=None,
    systems=("Anisoprint analog corpus",),
    machines=(),
    software=(),
    materials=(),
    assertion="DOCUMENTATION_CLAIM",
    guidance="HISTORICAL_ANISOPRINT_DESCRIPTION",
    context="Historical first-party Anisoprint material; no FibreSeek equivalence established.",
    applicability="UNRESOLVED",
    confidence="HIGH",
    relationships=(),
    question=None,
    notes="",
    extra_sources=(),
    extra_refs=(),
) -> str:
    rid = f"OPK-{len(records) + 1:04d}"
    refs = [{"source_id": source_id, "location": location}]
    refs.extend({"source_id": sid, "location": loc} for sid, loc in extra_refs)
    source_ids = list(dict.fromkeys([source_id, *extra_sources, *(r["source_id"] for r in refs)]))
    records.append({
        "record_id": rid,
        "domain": domain,
        "concept": concept,
        "manufacturer_scope": "ANISOPRINT",
        "system_scope": list(systems),
        "machine_scope": list(machines),
        "software_scope": list(software),
        "material_scope": list(materials),
        "source_ids": source_ids,
        "source_references": refs,
        "source_claim": claim,
        "normalized_interpretation": interpretation,
        "value": value,
        "unit": unit,
        "qualifier": qualifier,
        "evidence_classification": "ANISOPRINT_OFFICIAL",
        "assertion_kind": assertion,
        "guidance_status": guidance,
        "historical_context": context,
        "fibreseek_applicability": applicability,
        "confidence": confidence,
        "relationships": [{"type": t, "target": target, "notes": n} for t, target, n in relationships],
        "unresolved_fibreseek_question": question,
        "notes": notes,
    })
    return rid


# Calibration: keep procedures and values distinct.
add("calibration", "build-plate calibration trigger", "AP-117", "derived text lines 171–177; manual §7.4", "Recalibrate after transport or changes that affect build-plate position; thickness variation across a large part is also a symptom.", "Composer build-plate calibration is condition-triggered, not merely periodic.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG", question="What events trigger FibreSeeker build-plate recalibration?")
add("calibration", "build-plate calibration procedure", "AP-117", "derived text lines 173–177; manual §7.4", "Clean and preheat nozzles and plate, set three points, then fine-tune with 80 gsm paper sliding with slight friction.", "Composer chain: trigger → thermal/clean preparation → three-point adjustment → paper-drag measurement → Z-axis calibration.", value=80, unit="gsm", qualifier="paper basis weight; slight-friction acceptance criterion", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("calibration", "plastic-nozzle Z calibration trigger", "AP-117", "derived text lines 178–182; manual §7.5", "Run Z-axis calibration after plastic-nozzle replacement or first-layer layup problems.", "Composer ties plastic nozzle replacement and first-layer symptoms to Z calibration.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="POSSIBLE_ANALOG", question="What FibreSeeker recalibration is required after FFF nozzle replacement?")
add("calibration", "plastic-nozzle Z verification", "AP-117", "derived text lines 179–181; manual §7.5", "Fine-tune with 80 gsm paper, then print and inspect the brim and first layer.", "Composer verifies plastic Z calibration with both a drag gauge and a print result.", value=80, unit="gsm", qualifier="paper gauge followed by brim/first-layer inspection", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("calibration", "composite-nozzle Z offset semantics", "AP-117", "derived text lines 183–186; manual §7.6", "Composite Z offset is the relative Z position of the composite nozzle versus the plastic nozzle.", "This is nozzle-to-nozzle vertical registration, distinct from build-plate and plastic Z calibration.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="POSSIBLE_ANALOG", relationships=(("semantically_similar", "Rocket composite/plastic Z-offset fields", "Same calibration concept; runtime relationship remains unverified."),), question="What is FibreSeeker's composite-to-plastic nozzle Z-offset method?")
add("calibration", "composite-nozzle Z offset trigger and symptoms", "AP-117", "derived text lines 183–186 and 208–210; manual §§7.6, 7.8", "Run after either nozzle is replaced and when the composite nozzle scratches, walls degrade, fiber leaves its path, or fiber fails to adhere.", "Composer couples nozzle replacement and several print symptoms to composite Z-offset calibration.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="POSSIBLE_ANALOG")
add("calibration", "composite/plastic XY offset procedure", "AP-119", "derived text lines 14–17", "After either nozzle is replaced, print NozzleOffsetTest.gcode, find the centered cell for each axis, apply its labeled correction, reprint, and verify centering.", "Composer XY registration chain: replacement trigger → service print → cell-centering measurement → X/Y adjustment → repeat-print verification.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="POSSIBLE_ANALOG", relationships=(("semantically_similar", "Rocket nozzle-offset fields", "Possible calibration analog only."),), question="What is FibreSeeker's nozzle-to-nozzle XY calibration method?")
add("calibration", "NozzleOffsetTest.gcode acquisition state", "AP-120", "manifest record and preserved HTTP response metadata", "Three official Composer pages link the same asset, but its public URL returned HTTP 404 during Phase 2F-A.", "The service-code existence and role are sourced, but its bytes are unavailable; no substitute is accepted.", machines=("Composer A3/A4",), assertion="DOCUMENTATION_CLAIM", guidance="NOT_GUIDANCE", applicability="NO_KNOWN_EQUIVALENT", confidence="HIGH", extra_sources=("AP-117", "AP-118", "AP-119"), extra_refs=(("AP-117", "derived text line 189"), ("AP-118", "derived text line 73"), ("AP-119", "derived text line 14")), question="Is there an official FibreSeeker XY-calibration service file or G-code?")

# Manufacturability. Numeric profile values deliberately retain unknown units.
add("manufacturability", "minimum reinforced perimeter field", "AP-103", "immutable Aura 2.5.8 settings store; profile field MinimumPerimeterLength", "Many Aura profiles store MinimumPerimeterLength=45.0.", "The recovered 45-valued field is minimum reinforced perimeter length, not evidence of a universal minimum continuous-fiber segment length.", value=45.0, unit=None, qualifier="profile scalar; unit not independently established by this source", software=("Aura 2.5.8",), assertion="PROFILE_VALUE", guidance="NOT_GUIDANCE", applicability="UNRESOLVED", relationships=(("corrects", "informal ~45 mm minimum-fiber shorthand", "The exact field meaning is narrower."),), question="What is FibreSeeker's minimum reinforced-perimeter length, if any?", notes="Do not normalize this value to 45 mm without a source that establishes the unit.")
add("manufacturability", "minimum reinforced perimeter feature behavior", "AP-106", "Aura changelog, 2.4.0 section; Minimum length of reinforced perimeter", "Aura added an override-capable minimum reinforced-perimeter-length setting so smaller openings could be reinforced when overridden.", "The constraint governs reinforced perimeter eligibility around small openings; it is not a generic hole-clearance value.", software=("Aura 2.4.0+",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="CONCEPTUAL_ANALOG", relationships=(("corrects", "informal ~12 mm hole-clearance shorthand", "No 12 mm clearance rule was recovered."),), question="How does Rocket decide whether a hole-adjacent reinforced perimeter is feasible?")
add("manufacturability", "cellular fiber minimum-segment profile field", "AP-104", "immutable Aura 2.6.2 settings store; InfillFCellularMinSegmentLength", "Recovered Aura profiles store InfillFCellularMinSegmentLength=10.0.", "Aura has a distinct cellular-fiber minimum-segment field; its profile value is not a FibreSeek limit and its unit remains unconfirmed in this source.", value=10.0, unit=None, qualifier="profile scalar; unit unknown", software=("Aura 2.6.2",), assertion="PROFILE_VALUE", guidance="NOT_GUIDANCE", applicability="POSSIBLE_ANALOG", question="What is FibreSeeker's minimum continuous-fiber trajectory segment length?")
add("manufacturability", "solid fiber minimum-segment profile field", "AP-104", "immutable Aura 2.6.2 settings store; InfillFSolidMinSegmentLength", "CFC PETG profiles include a solid-fiber minimum-segment value of 20.0 while many other profiles use 10.0.", "Minimum segment values can be profile/material scoped rather than universal.", value="10.0 or 20.0", unit=None, qualifier="profile-dependent scalars; unit unknown", software=("Aura 2.6.2",), materials=("CFC PETG",), assertion="PROFILE_VALUE", guidance="NOT_GUIDANCE", applicability="POSSIBLE_ANALOG", question="Are FibreSeeker minimum trajectory lengths material, pattern, or profile dependent?")
add("manufacturability", "fiber minimum-radius profile field", "AP-105", "immutable Sk3 template settings store; FiberMinRadiusF", "The Sk3 X-CCF profile stores FiberMinRadiusF=12.0; common Aura profiles inspected store 5.0.", "The recovered 12 value concerns trajectory radius, not clearance around holes, and varies by profile generation.", value="12.0 (Sk3); 5.0 (common Aura profiles)", unit=None, qualifier="profile scalars; source unit unknown", software=("Aura Sk3 template", "Aura 2.5.8/2.6.2"), assertion="PROFILE_VALUE", guidance="NOT_GUIDANCE", applicability="POSSIBLE_ANALOG", extra_sources=("AP-103", "AP-104"), extra_refs=(("AP-103", "settings store field FiberMinRadiusF"), ("AP-104", "settings store field FiberMinRadiusF")), relationships=(("corrects", "informal ~12 mm hole-clearance shorthand", "The 12-valued field is a radius field."),), question="What is FibreSeeker's minimum supported fiber bend/path radius?")

# Composite layer architecture.
add("composite_layer_architecture", "macrolayer abstraction", "AP-111", "derived text lines 27–40; aura-docs docs/aura/macrolayers/index.md lines 1–29", "A macrolayer is an abstraction; every physically printed layer is called a microlayer.", "Macrolayer is a scheduling/package construct rather than an additional physical deposition pass.", software=("Aura",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="POSSIBLE_ANALOG", relationships=(("same_name_field", "Aura MacroLayerHeight / recovered Rocket MacroLayerHeight", "Naming continuity exists; physical equivalence is unresolved."),), question="What is Rocket's exact physical and algorithmic macrolayer model?", extra_sources=("AP-114",), extra_refs=(("AP-114", "commit 3fa58f9; docs/aura/macrolayers/index.md lines 24–29"),))
add("composite_layer_architecture", "macrolayer layer-package definition", "AP-107", "derived text lines 308–309", "Macrolayer height is the height of a package containing microlayers; microlayers contain entities sharing a height.", "Aura groups entity-specific Z events into a repeating layer package.", software=("Aura",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="POSSIBLE_ANALOG", relationships=(("same_name_field", "Rocket MacroLayerHeight", "Same-name lineage; no automatic hardware equivalence."),), question="Does Rocket use MacroLayerHeight as a scheduling package, a CCF layer height, or both?")
add("composite_layer_architecture", "reinforced entity height", "AP-111", "derived text lines 37–40", "Aura automatically treats macrolayer height as the reinforced perimeter and reinforced infill layer height.", "Within Aura MLT, continuous-fiber deposition occurs at macrolayer cadence.", software=("Aura",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="POSSIBLE_ANALOG", question="Is FibreSeeker CCF layer height fixed to a macrolayer cadence?")
add("composite_layer_architecture", "microlayer divisibility rule", "AP-111", "derived text lines 39–40", "Other entity layer heights are fractions of macrolayer height; examples for 0.36 mm are 0.18, 0.12, and 0.09 mm.", "Aura documents an integer-ratio/divisibility scheduling rule for entity microlayers within a macrolayer.", value="0.36 → 0.18, 0.12, 0.09", unit="mm", qualifier="documented example: 1/2, 1/3, 1/4", software=("Aura",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="POSSIBLE_ANALOG", question="Must Rocket plastic/support microlayer heights evenly divide the CCF/macrolayer height?")
add("composite_layer_architecture", "microlayer Z-event scheduling example", "AP-107", "derived text lines 308–309", "For a 0.6 mm package, 0.2 mm shell and 0.3 mm plastic perimeter events occur at Z=0.2, 0.3, 0.4, and co-occur with fiber at Z=0.6.", "Aura schedules entity deposition at each entity-height multiple; coincident events share a microlayer at the package boundary.", value="Z 0.2, 0.3, 0.4, 0.6", unit="mm", qualifier="worked scheduling example", software=("Aura",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="POSSIBLE_ANALOG", question="How does Rocket order coincident plastic and CCF entities at a shared Z boundary?")
add("composite_layer_architecture", "first-layer exception", "AP-107", "derived text lines 320–325", "Aura's first layer has no macrolayer microlayer structure and does not belong to a macrolayer.", "The repeating package begins above an exceptional first layer.", software=("Aura",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="POSSIBLE_ANALOG", question="Does Rocket exclude its first layer from macrolayer scheduling?")
add("composite_layer_architecture", "support height scheduling", "AP-138", "derived text lines 38–48; aura-docs supports", "Thin support uses external-shell layer height; thick support combines thin layers where possible; interface thickness is counted in macrolayers but printed at external-shell height.", "Support cadence is coupled to both microlayer height and macrolayer counts.", software=("Aura 1.27+",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="POSSIBLE_ANALOG", question="What FibreSeeker/Rocket support cadence and layer-height coupling rules exist?", extra_sources=("AP-114",), extra_refs=(("AP-114", "commit 3fa58f9; docs/aura/supports/index.md"),))
add("composite_layer_architecture", "layup region priority", "AP-139", "derived text lines 27–39; aura-docs layuprule", "Layup ranges align to visible macrolayers and a later/higher-priority rule covers earlier rules where they overlap.", "Aura maps macrolayer ranges into layup regions with explicit override priority.", software=("Aura",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="CONCEPTUAL_ANALOG", question="Does Rocket have layup regions and what rule precedence applies?", extra_sources=("AP-114",), extra_refs=(("AP-114", "commit 3fa58f9; docs/aura/layuprule/index.md"),))

# Fiber path generation.
add("fiber_path_generation", "reinforced perimeter entity", "AP-112", "derived text entity descriptions; aura-docs docs/aura/entities/index.md", "Aura distinguishes reinforced perimeters from plastic perimeters and fiber infill entities.", "Reinforced boundary trajectories are a separate generated entity class.", software=("Aura",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="CONCEPTUAL_ANALOG")
add("fiber_path_generation", "microinfill gap filling", "AP-112", "derived text line 49; aura-docs entities lines 27–32", "Microinfill automatically fills gaps between external and internal plastic shells created by macrolayer combining.", "Aura generates compensating plastic geometry caused by differing entity layer cadences.", software=("Aura",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="CONCEPTUAL_ANALOG")
add("fiber_path_generation", "solid infill boundary behavior", "AP-112", "derived text line 51; aura-docs entities lines 32–34", "Solid infill forms top/bottom surfaces and includes overhangs as the first bottom solid layer in a macrolayer.", "Aura classifies horizontal skins and overhang-related solid regions within macrolayer structure.", software=("Aura",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="CONCEPTUAL_ANALOG")
add("fiber_path_generation", "mask-localized settings", "AP-113", "published mask documentation; aura-docs docs/aura/premium/masks/index.md", "Masks apply local parameter sets to intersected model areas and resolve overlaps by priority.", "Aura supports localized reinforcement/process overrides using geometric masks.", software=("Aura Premium",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="CONCEPTUAL_ANALOG", extra_sources=("AP-114",), extra_refs=(("AP-114", "commit 3fa58f9; docs/aura/premium/masks/index.md"),))
add("fiber_path_generation", "fiber/plastic intersection acceptance", "AP-117", "derived text lines 201–210; manual §7.8", "The Composer test print expects fiber perimeters to be surrounded by plastic without intersections or displacement.", "Nonintersection and registration are visual acceptance criteria for the historical test part.", machines=("Composer A3/A4",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")

# Design rules, kept separate from machine constraints.
add("design_rules", "fiber alignment with primary load", "AP-122", "Basic Rules for Design; load-orientation section", "Anisoprint design guidance aligns continuous fibers with the dominant load path.", "General composite design principle; not a machine manufacturability limit.", systems=("General composite design",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("design_rules", "bending face reinforcement", "AP-122", "Basic Rules for Design; bending examples", "For bending, the guidance places reinforcement near tensile/compressive outer regions rather than the neutral core.", "General sandwich/beam load-placement principle, separate from slicer constraints.", systems=("General composite design",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("design_rules", "interlaminar loading caution", "AP-122", "Basic Rules for Design; layer-orientation examples", "The guidance warns that layered composites are weak for loads acting to separate layers.", "Part orientation should avoid relying on weak interlayer loading paths.", systems=("General composite design",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("design_rules", "stress-concentration reinforcement", "AP-122", "Basic Rules for Design; holes and local-load examples", "The guide recommends directing/localizing fibers around holes and concentrated loads.", "Hole reinforcement is a structural design objective distinct from the software's path-feasibility rules.", systems=("General composite design",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG", question="What FibreSeeker geometry is required to realize structurally useful hole reinforcement?")
add("design_rules", "anisotropic laminate planning", "AP-122", "Basic Rules for Design; composite anisotropy discussion", "Strength depends on reinforcement direction, so layup and part orientation are designed together.", "The corpus treats continuous-fiber parts as directional laminates, not isotropic solids.", systems=("General composite design",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")

# Materials and process values remain machine/material/version scoped.
add("materials_process", "CFC PA reinforcement system", "AP-125", "official CFC PA training material page", "CFC PA combines continuous reinforcing fiber with a polyamide matrix for Composer processing.", "Historical material system statement, not FibreSeek compatibility evidence.", machines=("Composer A3/A4",), materials=("CFC PA",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="UNRESOLVED")
add("materials_process", "CFC PETG reinforcement system", "AP-127", "datasheet v2.1, pages 1–2 / derived text", "CFC PETG is a continuous-fiber coextrusion material with PETG matrix documented for Anisoprint systems.", "Material identity and properties are historically/version scoped.", materials=("CFC PETG v2.1",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="UNRESOLVED")
add("materials_process", "open matrix material compatibility", "AP-130", "Composer A4 material compatibility article", "Composer plastic extruders are presented as open to third-party 1.75 mm thermoplastics subject to processing constraints.", "The historical Composer's open-material claim does not establish FibreSeek compatibility.", value=1.75, unit="mm", qualifier="filament diameter", machines=("Composer A4",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="NO_KNOWN_EQUIVALENT")
add("materials_process", "CFC PETG drying/storage", "AP-127", "datasheet v2.1; storage/processing section", "The datasheet gives material-specific storage and drying handling for CFC PETG.", "Moisture control is material-specific process guidance; exact values must be taken from the datasheet for that version, not generalized.", materials=("CFC PETG v2.1",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG", question="What drying and storage limits apply to FibreSeek-qualified matrix/fiber materials?")
add("materials_process", "test-print adhesion selection", "AP-117", "derived text lines 198–202; manual §7.8", "Composer's test workflow selects adhesive according to plastic family and requires a smooth, uniform, adhered composite purge line.", "Bed adhesion and purge-line appearance form pre-print/process acceptance observations.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")

# Cutter/feed: documentation fields and static firmware behavior are distinct.
add("cutter_feed_mechanics", "CutDistance semantics", "AP-107", "Aura settings reference; extruder Cut distance field", "Cut distance is the distance from the fiber cut point to the composite-nozzle outlet and is manufacturer-set.", "This geometry compensates the dead length between cutter and deposition outlet.", software=("Aura",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_DESCRIPTION", applicability="POSSIBLE_ANALOG", relationships=(("same_name_field", "Rocket CutDistance", "Exact field-name continuity; runtime precedence is unresolved."),), question="What physical distance does Rocket CutDistance represent and where is it applied?")
add("cutter_feed_mechanics", "FiberRestartLength constraint", "AP-107", "Aura settings reference; Fiber restart length field", "Fiber restart length is the extrusion during restart; it must be at least CutDistance and Composer guidance sets it 1–2 mm larger.", "Historical Aura expresses an ordering constraint FiberRestartLength ≥ CutDistance and a Composer-specific margin.", value="CutDistance + 1–2", unit="mm", qualifier="Composer recommendation; lower bound is CutDistance", software=("Aura",), machines=("Composer A3/A4",), assertion="DOCUMENTATION_CLAIM", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="POSSIBLE_ANALOG", relationships=(("same_name_field", "Rocket FiberRestartLength", "Same-name continuity; no runtime equivalence established."),), question="What is Rocket's runtime precedence among CutDistance, FiberRestartLength, and CutCode?")
add("cutter_feed_mechanics", "fiber polygon state commands", "AP-115", "commit 6e02973; GCodes.md lines 111–112 and src/core/commands/gcode/composer/m1001_m1002.h", "M1001 starts and M1002 ends a fiber-reinforced polygon; code toggles printing_with_fiber.", "Firmware marks a state interval around continuous-fiber paths.", software=("MKA-firmware 6e02973",), machines=("Composer family configurations",), assertion="CODE_BEHAVIOR", guidance="NOT_GUIDANCE", applicability="POSSIBLE_ANALOG", question="Does Rocket emit an equivalent fiber-path state envelope?")
add("cutter_feed_mechanics", "pause deferred until fiber path end", "AP-115", "commit 6e02973; m1001_m1002.h and nextion_hmi/PrintPause.cpp", "Static code defers a requested pause while printing_with_fiber and processes it after M1002 ends the path.", "The historical firmware protects continuous-fiber path continuity by deferring pause to a boundary.", software=("MKA-firmware 6e02973",), assertion="CODE_BEHAVIOR", guidance="NOT_GUIDANCE", applicability="CONCEPTUAL_ANALOG", question="Can FibreSeeker pause mid-fiber path, and if not, where are safe state boundaries?")
add("cutter_feed_mechanics", "fiber cut commands", "AP-115", "commit 6e02973; GCodes.md lines 118–119; m1010_m1011.h", "M1010 invokes cutting; M1011 configures servo ID, active cut angle, and neutral angle.", "Cut execution and cutter-configuration commands are separate in MKA firmware.", software=("MKA-firmware 6e02973",), assertion="CODE_BEHAVIOR", guidance="NOT_GUIDANCE", applicability="POSSIBLE_ANALOG", relationships=(("possible_analog", "Rocket CutCode", "Potential command-generation relationship only."),), question="What exact commands does Rocket CutCode emit and when?")
add("cutter_feed_mechanics", "cut-fiber state transition", "AP-115", "commit 6e02973; src/core/tools/tools.cpp lines 379+", "cut_fiber synchronizes queued motion, drives the servo to its active angle then neutral angle, and updates cut state.", "The implementation exposes synchronization → actuation → neutralization → state-update sequencing.", software=("MKA-firmware 6e02973",), assertion="CODE_BEHAVIOR", guidance="NOT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("cutter_feed_mechanics", "firmware hotend-offset constants", "AP-115", "commit 6e02973; config/COMPOSER_A4_I/Configuration_Core.h lines 670–672", "One Composer A4 configuration contains X=17.1, Y=-2.2, Z=1.65 mm second-hotend offsets.", "These are model/configuration code constants, not universal manufacturer recommendations and not FibreSeek settings.", value="17.1, -2.2, 1.65", unit="mm", qualifier="COMPOSER_A4_I code configuration only", software=("MKA-firmware 6e02973",), machines=("Composer A4 I configuration",), assertion="CODE_CONSTANT", guidance="NOT_GUIDANCE", applicability="NO_KNOWN_EQUIVALENT", question="What are FibreSeeker's measured nozzle offsets and authoritative storage location?")

# Diagnostics represented as evidence-backed chains.
add("diagnostics", "fiber leaves trajectory or does not adhere", "AP-117", "derived text lines 201–210; manual §7.8", "If early fiber leaves its trajectory or fails to adhere to the prior layer, run composite Z-offset calibration.", "symptom → probable registration/compression issue → composite Z subsystem → Z-offset procedure → repeat quality inspection.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("diagnostics", "composite nozzle too low", "AP-118", "Composer Guide §2.3 Z-offset calibration", "An overly wide calibration line, scratching, or absent fiber output indicates the composite nozzle may be too low.", "symptom → excessive compression/obstruction → composite-nozzle Z → adjust offset → reprint calibration line.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("diagnostics", "composite nozzle too high", "AP-118", "Composer Guide §2.3 Z-offset calibration", "A calibration line that is too narrow/high or does not stick indicates the composite nozzle may be too high.", "symptom → under-compression → composite-nozzle Z → adjust offset → reprint calibration line.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("diagnostics", "part releases from build plate", "AP-117", "derived text lines 329–332; manual §11.1", "Check bed temperature and adhesive first; if both are correct, recalibrate plastic Z/first-layer height.", "release symptom → thermal/adhesion/Z causes → check process inputs → Z calibration if needed → first-layer verification.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("diagnostics", "plastic not extruded", "AP-117", "derived text lines 333–336; manual §11.2", "Check loading/feed and processing temperature before diagnosing a clogged nozzle.", "no extrusion → feed/temperature/clog candidates → ordered checks → unclog action → extrusion verification.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("diagnostics", "fiber clogged in cutter", "AP-117", "derived text lines 364–372; manual §11.7", "The manual provides a safe access/removal sequence for fiber clogged inside the cutter.", "clog symptom → cutter subsystem → unload/access test → remove obstruction → reload/cut verification.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("diagnostics", "fiber break before cutter", "AP-117", "derived text lines 374–386; manual §§11.8–11.9", "Fiber broken in the upstream PTFE tube may result from incorrect cutter position; manual cutting is the test.", "breakage → possible cutter misalignment → manual cut test → reposition cutter → manual or service-code verification.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")

# Maintenance.
add("maintenance", "nozzle replacement recalibration bundle", "AP-117", "manual §§7.5–7.7", "Plastic-nozzle replacement triggers plastic Z, composite Z, and XY checks; composite-nozzle replacement triggers composite Z and XY checks.", "Nozzle service has an explicit dependent calibration bundle in Composer documentation.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="POSSIBLE_ANALOG", question="What dependent calibration bundle follows each FibreSeeker nozzle replacement?")
add("maintenance", "cutter position inspection", "AP-117", "derived text lines 379–386; manual §11.9", "Transport or a loose bolt can alter cutter position; inspect the opening/alignment and verify with a manual cut.", "Cutter alignment is an inspect-adjust-verify maintenance operation.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("maintenance", "pre-calibration cleaning and heating", "AP-117", "derived text line 173; manual §7.4 notice", "Clean and heat nozzles and plate to printing temperature before build-plate, Z-axis, and Z-offset calibration.", "Calibration preparation controls contamination and thermal-state error.", machines=("Composer A3/A4",), assertion="PROCEDURE", guidance="HISTORICAL_ANISOPRINT_GUIDANCE", applicability="CONCEPTUAL_ANALOG")
add("maintenance", "pre-print fiber-path cleaning reminder", "AP-115", "commit 6e02973; static firmware UI strings/comments around print-start workflow", "Firmware source contains a user-facing cleaning reminder before print start.", "This is a code-embedded maintenance reminder, not proof of FibreSeek service intervals.", software=("MKA-firmware 6e02973",), assertion="COMMENT", guidance="NOT_GUIDANCE", applicability="NO_KNOWN_EQUIVALENT")


videos = [
    ("AP-143", "What is anisoprinting?", "464805427", "5:10", ["fundamentals", "reinforcement"], []),
    ("AP-144", "Technology implementation", "464802130", "4:46", ["fundamentals", "hardware_operation", "reinforcement"], []),
    ("AP-145", "Open vs. closed systems", "464801522", "2:20", ["fundamentals", "materials"], ["AP-130"]),
    ("AP-146", "Basics of composites", "464803197", "4:54", ["fundamentals", "design"], ["AP-122"]),
    ("AP-147", "Basic rules of composites design", "464805988", "4:30", ["design", "reinforcement"], ["AP-122"]),
    ("AP-124", "Introduction to Aura", "464790071", "12:36", ["Aura", "macrolayers", "reinforcement"], ["AP-111", "AP-112"]),
    ("AP-148", "Unpacking and first print", "464788529", "8:25", ["hardware_operation", "calibration", "maintenance", "diagnostics"], ["AP-117", "AP-133"]),
]
manifest = {json.loads(line)["record_id"]: json.loads(line) for line in (ROOT / "sources/manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()}
video_records = []
for sid, title, host_id, duration, relevance, written in videos:
    src = manifest[sid]
    video_records.append({
        "video_id": f"VID-{sid}", "title": title, "course": "Official Anisoprint training curriculum",
        "canonical_page": src["source_url"], "page_source_id": sid, "host": "VIMEO",
        "host_video_id": host_id, "host_url": f"https://vimeo.com/{host_id}",
        "publication_date": "2020-09-15", "duration": duration,
        "description": "Lesson metadata exposed on the official Anisoprint page; video stream was not acquired.",
        "relevance": relevance, "related_written_source_ids": written,
        "transcript_status": "NOT_PUBLICLY_EXPOSED", "transcript_source_id": None,
        "annotation_status": "READY_FOR_HUMAN_NOTES",
        "notes": "The Anisoprint page establishes official status. Vimeo robots prohibit automated user-content crawling; no Vimeo page, stream, caption, or private resource was scraped.",
    })


question_specs = [
    ("manufacturability", "What is FibreSeeker's minimum continuous-fiber segment length?", "Short paths may be unprintable or require cut/restart behavior.", ["minimum-segment"], "Direct FibreSeek/Rocket documentation or controlled generated-path evidence.", "STATIC_FIRST_PARTY"),
    ("manufacturability", "What is the minimum supported FibreSeeker fiber bend/path radius?", "Tight curvature can damage continuity and registration.", ["minimum-radius"], "FibreSeek specification, vendor confirmation, or controlled coupon series.", "VENDOR_CONFIRMATION"),
    ("manufacturability", "What clearance is required between reinforced paths and holes or exterior boundaries?", "This controls reinforceable feature size and stress-concentration design.", ["perimeter"], "First-party geometry rules plus offline Rocket toolpath inspection.", "OFFLINE_RUNTIME_TEST"),
    ("manufacturability", "Does Rocket enforce minimum length/radius/clearance geometrically?", "A hidden slicer filter may suppress requested reinforcement.", ["minimum"], "Static package analysis and offline, no-printer slicing tests.", "OFFLINE_RUNTIME_TEST"),
    ("calibration", "What is FibreSeeker's nozzle-to-nozzle XY calibration method and acceptance criterion?", "XY registration controls fiber/plastic placement.", ["XY offset"], "FibreSeek manual/service artifact or owner-authorized physical calibration.", "STATIC_FIRST_PARTY"),
    ("calibration", "Is there an official FibreSeeker calibration G-code equivalent to NozzleOffsetTest.gcode?", "A deterministic test pattern would make calibration reproducible.", ["NozzleOffsetTest"], "Official package/manual search or vendor confirmation.", "STATIC_FIRST_PARTY"),
    ("calibration", "What recalibration follows FibreSeeker CCF or FFF nozzle replacement?", "Service can alter Z and XY registration.", ["replacement"], "FibreSeek maintenance documentation or vendor confirmation.", "VENDOR_CONFIRMATION"),
    ("composite_layer_architecture", "What is Rocket's exact macrolayer model?", "It controls physical layer cadence and interpretation of profile fields.", ["macrolayer"], "Rocket static analysis plus controlled offline slice comparison.", "OFFLINE_RUNTIME_TEST"),
    ("composite_layer_architecture", "Are plastic and CCF layer heights independently selectable in Rocket?", "Independence determines feasible layer packages.", ["reinforced entity"], "UI/schema analysis and offline generated G-code inspection.", "OFFLINE_RUNTIME_TEST"),
    ("composite_layer_architecture", "Must Rocket microlayer heights divide CCF or macrolayer height evenly?", "Invalid ratios may be rejected or rescheduled.", ["divisibility"], "Offline boundary-value slicing tests.", "OFFLINE_RUNTIME_TEST"),
    ("composite_layer_architecture", "How are coincident entity events ordered in Rocket Z scheduling?", "Order affects bonding and surface formation.", ["Z-event"], "Offline G-code comparison across controlled profiles.", "OFFLINE_RUNTIME_TEST"),
    ("cutter_feed_mechanics", "What is runtime precedence among Rocket CutDistance, FiberRestartLength, and CutCode?", "Incorrect precedence changes cut and restart placement.", ["CutDistance", "FiberRestartLength", "cut commands"], "Static Rocket analysis and controlled offline G-code generation.", "OFFLINE_RUNTIME_TEST"),
    ("cutter_feed_mechanics", "What are FibreSeeker's physical cut/restart dead distances?", "Dead distance determines start/stop exclusion zones.", ["CutDistance"], "Vendor dimensions or owner-authorized measurement.", "PHYSICAL_EXPERIMENT"),
    ("cutter_feed_mechanics", "What state transitions and safe pause boundaries exist during FibreSeeker fiber deposition?", "Mid-path interruption may damage continuity or hardware state.", ["pause deferred"], "Firmware/vendor documentation; no hardware command execution.", "VENDOR_CONFIRMATION"),
    ("cutter_feed_mechanics", "Which fiber commands, if any, are emitted by Rocket?", "Command semantics connect slicer fields to runtime behavior.", ["fiber polygon", "fiber cut"], "Static Rocket artifact analysis and offline output generation.", "OFFLINE_RUNTIME_TEST"),
    ("diagnostics", "What FibreSeeker symptoms distinguish excessive from insufficient CCF nozzle compression?", "Opposite Z errors require opposite corrections.", ["too low", "too high"], "FibreSeek service guide or controlled owner observation.", "PHYSICAL_EXPERIMENT"),
    ("diagnostics", "What is the FibreSeeker diagnostic chain for failed fiber restart?", "Restart failures can originate in cut, feed, heat, or path state.", ["fiber cut", "FiberRestartLength"], "Vendor workflow plus instrumented offline/runtime evidence.", "VENDOR_CONFIRMATION"),
    ("materials_process", "Which reinforcement and matrix combinations are FibreSeek-qualified?", "Analog material compatibility cannot authorize FibreSeek operation.", ["CFC PA", "CFC PETG"], "FibreSeek first-party compatibility matrix.", "STATIC_FIRST_PARTY"),
    ("materials_process", "What drying, storage, and moisture limits apply to FibreSeek-qualified materials?", "Moisture changes feed and bonding behavior.", ["drying/storage"], "Material-specific FibreSeek/vendor datasheets.", "STATIC_FIRST_PARTY"),
    ("maintenance", "What are FibreSeeker cutter inspection, adjustment, and replacement intervals?", "Cutter wear can cause incomplete cuts and breakage.", ["cutter position"], "FibreSeek service schedule or vendor confirmation.", "VENDOR_CONFIRMATION"),
    ("composite_layer_architecture", "What support-layer cadence rules exist in Rocket?", "Support heights may constrain all entity ratios.", ["support height"], "Offline Rocket profile and G-code study.", "OFFLINE_RUNTIME_TEST"),
    ("fiber_path_generation", "Does Rocket provide masks or localized reinforcement and what priority rules apply?", "Local reinforcement requires predictable overlap behavior.", ["mask-localized"], "Static/UI inspection and offline overlapping-region test.", "OFFLINE_RUNTIME_TEST"),
]


def match_ids(needles: list[str]) -> list[str]:
    found = []
    for rec in records:
        haystack = f"{rec['concept']} {rec['normalized_interpretation']}"
        if any(n.lower() in haystack.lower() for n in needles):
            found.append(rec["record_id"])
    if not found:
        raise RuntimeError(f"question has no motivating records: {needles}")
    return found[:4]


questions = []
for i, (domain, question, why, needles, evidence, resolution) in enumerate(question_specs, 1):
    questions.append({
        "question_id": f"FSQ-{i:03d}", "domain": domain, "question": question,
        "why_it_matters": why, "motivating_analog_record_ids": match_ids(needles),
        "evidence_needed": evidence, "resolution_class": resolution, "status": "OPEN",
        "notes": "Generated from analog evidence; it does not imply that FibreSeek shares the Anisoprint behavior.",
    })


fixtures = [
    {"fixture_id": "2FA-01", "topic": "macrolayer semantics", "record_ids": ["OPK-0014", "OPK-0015"], "must_hold": "macrolayer is an abstraction/layer package; not an extra physical layer"},
    {"fixture_id": "2FA-02", "topic": "nozzle XY calibration", "record_ids": ["OPK-0007"], "must_hold": "Composer analog only; service print and repeat verification"},
    {"fixture_id": "2FA-03", "topic": "composite Z-offset calibration", "record_ids": ["OPK-0005", "OPK-0006"], "must_hold": "relative nozzle Z; not FibreSeek guidance"},
    {"fixture_id": "2FA-04", "topic": "minimum fiber length", "record_ids": ["OPK-0009", "OPK-0011", "OPK-0012"], "must_hold": "45 is perimeter field; segment fields are distinct; units unresolved"},
    {"fixture_id": "2FA-05", "topic": "hole-adjacent fiber constraint", "record_ids": ["OPK-0010", "OPK-0013"], "must_hold": "no 12 mm hole-clearance rule recovered"},
    {"fixture_id": "2FA-06", "topic": "cutter/restart behavior", "record_ids": ["OPK-0037", "OPK-0038", "OPK-0041"], "must_hold": "same-name analog relationships do not establish Rocket precedence"},
    {"fixture_id": "2FA-07", "topic": "diagnostic/failure-mode chain", "record_ids": ["OPK-0046"], "must_hold": "symptom, subsystem, corrective action, and verification remain linked"},
    {"fixture_id": "2FA-08", "topic": "training-video-derived claim", "synthetic_record": {"assertion_kind": "HUMAN_TIMESTAMP_NOTE", "guidance_status": "UNVERIFIED_NOTE", "fibreseek_applicability": "UNRESOLVED", "source_reference": "VID-AP-124 @ 12:43"}, "must_hold": "timestamp note cannot become FibreSeek evidence without validation"},
    {"fixture_id": "2FA-09", "topic": "firmware code constant", "record_ids": ["OPK-0043"], "must_hold": "code constant remains NOT_GUIDANCE"},
    {"fixture_id": "2FA-10", "topic": "analog value promotion", "record_ids": ["OPK-0009"], "must_hold": "Anisoprint value cannot become FibreSeek operating value"},
]


write_jsonl(OUT / "records/operational_knowledge.jsonl", records)
write_jsonl(OUT / "training/video_inventory.jsonl", video_records)
write_jsonl(OUT / "questions/fibreseek_validation_questions.jsonl", questions)
(OUT / "fixtures").mkdir(parents=True, exist_ok=True)
(OUT / "fixtures/regression_cases.json").write_text(json.dumps({"schema_version": "1.0.0", "cases": fixtures}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {len(records)} operational records, {len(video_records)} videos, {len(questions)} questions, and {len(fixtures)} fixtures.")
