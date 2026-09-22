#!/usr/bin/env python3
"""Build deterministic Phase 2F-B direct-evidence and FSQ status overlays."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/operational/fibreseek"
BASELINE = "d49899368227979c9ea743ed09fff9b4bba06c88"


def location(source_id: str, artifact: str, locator: str, sha256: str | None = None) -> dict:
    value = {"source_id": source_id, "artifact": artifact, "locator": locator}
    if sha256:
        value["sha256"] = sha256
    return value


records: list[dict] = []


def add(
    domain: str,
    fsq_ids: tuple[str, ...],
    evidence_class: str,
    source_ids: tuple[str, ...],
    source_locations: tuple[dict, ...],
    observation: str,
    interpretation: str,
    scope: str,
    guidance_status: str,
    status_effect: str,
    confidence: str,
    limitations: str,
) -> str:
    evidence_id = f"FSD-{len(records) + 1:04d}"
    records.append(
        {
            "evidence_id": evidence_id,
            "domain": domain,
            "fsq_ids": list(fsq_ids),
            "evidence_class": evidence_class,
            "source_ids": list(source_ids),
            "source_locations": list(source_locations),
            "observation": observation,
            "interpretation": interpretation,
            "scope": scope,
            "guidance_status": guidance_status,
            "status_effect": status_effect,
            "confidence": confidence,
            "limitations": limitations,
            "baseline_commit": BASELINE,
        }
    )
    return evidence_id


add(
    "manufacturability",
    ("FSQ-001", "FSQ-004"),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-122", "FS-125"),
    (
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Consts-B3pY6a9u.js", "English profile-settings entries infill-f-solid-min-segment-length, infill-f-cellular-min-segment-length, and minimum-perimeter-length", "89bd54528479f6ab262e0db653fe949e47b6aac457aaa6db59a9f1c05265397b"),
        location("FS-125", "Templates/Presets/Profiles.json", "all 48 v15 profiles; InfillFSolidMinSegmentLength, InfillFCellularMinSegmentLength, MinimumPerimeterLength", "dd9979672da1100f5e03c165d0cad78eb63c1ab276d20f56308474485b5638c8"),
    ),
    "Rocket labels both solid- and cellular-fiber Infill*MinSegmentLength as 'Minimum line length (mm)' and says it is the shortest printable line, with possible prolonging or polygon connection. All v15 profiles store 10 mm. A separate reinforced-perimeter field suppresses perimeters shorter than its value; v15 stores 20 mm for Speedy and 55 mm for ReinForced/Fortified profiles.",
    "Rocket has entity-specific profile thresholds, not one recovered universal FibreSeeker minimum segment length.",
    "Rocket 1.3.2 UI semantics and public preset v15 only.",
    "STATIC_SOFTWARE_SEMANTIC",
    "SUPPORTS_PARTIAL",
    "HIGH",
    "Static data does not show the resulting toolpath for a boundary-value geometry or establish a physical hardware minimum.",
)

add(
    "manufacturability",
    ("FSQ-002", "FSQ-004"),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-122", "FS-125"),
    (
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Consts-B3pY6a9u.js", "English entries fiber-min-radius and fiber-max-arc-segment-length", "89bd54528479f6ab262e0db653fe949e47b6aac457aaa6db59a9f1c05265397b"),
        location("FS-125", "Templates/Presets/Profiles.json", "all 48 v15 profiles; FiberMinRadius and FiberMaxArcSegmentLength", "dd9979672da1100f5e03c165d0cad78eb63c1ab276d20f56308474485b5638c8"),
    ),
    "Rocket labels FiberMinRadius 'Min. arc radius (mm)' and defines it as the arc radius corresponding to minimum printing speed. Current profiles store 10 or 12 mm; FiberMaxArcSegmentLength stores 1, 3, or 4 mm.",
    "The recovered radius is a trajectory speed-model parameter. It is not evidence of an absolute FibreSeeker hardware bend limit.",
    "Rocket 1.3.2 UI semantics and public preset v15 only.",
    "STATIC_SOFTWARE_SEMANTIC",
    "SUPPORTS_PARTIAL",
    "HIGH",
    "No direct first-party physical bend-radius specification or controlled generated-path observation was recovered.",
)

add(
    "manufacturability",
    ("FSQ-003", "FSQ-004"),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-122", "FS-125"),
    (
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Consts-B3pY6a9u.js", "English entries infill-f-solid-extend-into-perimeters, infill-f-cellular-extend-into-perimeters, holes-expansion, and outer-contour-expansion", "89bd54528479f6ab262e0db653fe949e47b6aac457aaa6db59a9f1c05265397b"),
        location("FS-125", "Templates/Presets/Profiles.json", "v15 values for InfillFSolidExtendIntoPerimeters, InfillFCellularExtendIntoPerimeters, HolesExpansion, and OuterContourExpansion", "dd9979672da1100f5e03c165d0cad78eb63c1ab276d20f56308474485b5638c8"),
    ),
    "Rocket exposes fiber-infill extension into perimeters and general hole/outer-contour dimensional compensation. Current profile values vary, but no UI claim defines a required reinforced-path clearance from holes or exterior boundaries.",
    "Related geometric controls exist, but they do not resolve a FibreSeeker hole-adjacent fiber clearance rule.",
    "Rocket 1.3.2 and preset v15.",
    "STATIC_SOFTWARE_SEMANTIC",
    "SUPPORTS_PARTIAL",
    "HIGH",
    "Extension/compensation values must not be reinterpreted as safety clearance or a manufacturability exclusion zone.",
)

add(
    "manufacturability",
    ("FSQ-001", "FSQ-004", "FSQ-008", "FSQ-010", "FSQ-021", "FSQ-022"),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-122",),
    (
        location("FS-122", "Rocket 1.3.2 backend/monolith/publish/Aura2SlicingEngine.dll", "static .NET metadata/string symbols including get_MinSegmentLengthUM, get_InfillFSolidMinSegmentLengthUM, get_InfillFCellularMinSegmentLengthUM, CreateMicroLayerMacro, CreateMicroLayerRegular, ProcessMacrolayersSupportAreasAsync, TrimByOtherMask, and mask/layup types", "e47603e52218552c6da42c6e863e2360756158ebbef41f0296e4e50c0bcddaba"),
    ),
    "The Rocket slicing-engine assembly contains code-level symbols for minimum segment lengths, regular/macro microlayers, macrolayer support processing, support-to-macro ratios, and mask trimming/layup constructs.",
    "The fields are consumed by slicing-engine code rather than being UI-only decorations.",
    "Static code indicators from Rocket 1.3.2; no method body was executed.",
    "STATIC_CODE_INDICATOR",
    "SUPPORTS_PARTIAL",
    "MEDIUM",
    "Metadata and symbol names alone do not prove the exact algorithm, precedence, or generated geometry.",
)

add(
    "calibration",
    ("FSQ-005",),
    "FIBRESEEK_FIRST_PARTY",
    ("FS-120", "FS-147"),
    (
        location("FS-120", "FibreSeeker 3 User Manual R1", "derived text lines 588-603 (Print Calibration / Nozzle Offset)"),
        location("FS-147", "Troubleshooting Layer Shifting in Plastic-Only or Fiber-Only Printing", "derived text lines 19-41 (automatic calibration followed by signed X/Y correction example)"),
    ),
    "FibreSeek's print-calibration menu includes Nozzle Offset for dual-nozzle registration. The layer-shift SOP says to measure plastic-to-fiber deviation and adjust X/Y by the measured millimetres; plastic right/up requires decreasing X/Y respectively.",
    "The method and correction sign are directly documented, but no public numeric pass/fail acceptance tolerance was recovered.",
    "FibreSeeker 3 manual and support SOP.",
    "MANUFACTURER_GUIDANCE",
    "SUPPORTS_PARTIAL",
    "HIGH",
    "The automatic calibration target, measurement pattern, and acceptance criterion remain unspecified in preserved public material.",
)

add(
    "calibration",
    ("FSQ-006",),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-120", "FS-122"),
    (
        location("FS-120", "FibreSeeker 3 User Manual R1", "Print Calibration section; bounded filename/G-code search"),
        location("FS-122", "Rocket 1.3.2 application and backend package", "bounded static filename/content search for NozzleOffsetTest and calibration G-code artifacts"),
    ),
    "A bounded search of the preserved FibreSeek manual and Rocket 1.3.2 package found the built-in Nozzle Offset workflow but did not locate NozzleOffsetTest.gcode or a public FibreSeek calibration G-code file.",
    "The question remains open; a bounded search miss is not evidence that no equivalent exists.",
    "Preserved public manual and Rocket 1.3.2 package only.",
    "BOUNDED_SEARCH_ABSENCE",
    "NO_RESOLUTION",
    "HIGH",
    "Unpublished printer-resident assets, later releases, or vendor-only service files were not available.",
)

add(
    "calibration",
    ("FSQ-007",),
    "FIBRESEEK_FIRST_PARTY",
    ("FS-133", "FS-137", "FS-139", "FS-142", "FS-144"),
    (
        location("FS-137", "Fiber Hotend Nozzle", "derived text lines 192-208: Calibration > Print Calibration > Nozzle offset after replacement"),
        location("FS-139", "Fiber Unclogging in Composite Hotend", "derived text lines 263-267: after removing composite hotend, nozzle offset only"),
        location("FS-133", "Composite Plastic Hotend Unclogging", "derived text lines 92-95: calibrate nozzle offset; select only Nozzle offset"),
        location("FS-142", "Plastic Hotend Ceramic Heater", "derived text around Perform XYZ Offset"),
        location("FS-144", "Plastic Hotend Unclogging", "derived text around final nozzle-offset calibration"),
    ),
    "FibreSeek service procedures require Print Calibration > Nozzle offset after CFC nozzle/hotend replacement or removal and after multiple FFF hotend service operations; the CFC nozzle SOP warns that skipping it may cause printing issues.",
    "Nozzle-offset recalibration is a direct post-service requirement. The corpus does not separately enumerate every possible FFF nozzle-only replacement trigger.",
    "FibreSeeker 3 public service SOPs.",
    "MANUFACTURER_GUIDANCE",
    "SUPPORTS_PARTIAL",
    "HIGH",
    "A comprehensive manufacturer matrix by replaced CFC/FFF component remains unavailable.",
)

add(
    "composite_layer_architecture",
    ("FSQ-008",),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-122",),
    (
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Consts-B3pY6a9u.js", "English macro-layer-height tip", "89bd54528479f6ab262e0db653fe949e47b6aac457aaa6db59a9f1c05265397b"),
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/generationResultMapperWorker-BiU3AB3X.js", "G-code parser markers ; LAYER: and ; MACROLAYER: and microMacroLayers mapping", "e64b8a71bf8afb70837f908766d9a7afe053d82756bc68b2d5b61c0f33932b97"),
    ),
    "Rocket defines a macrolayer as a layer package containing microlayers; a microlayer contains one or more print entities at the same height. Its example schedules shell events at 0.2/0.4/0.6 mm, plastic perimeters at 0.3/0.6 mm, and fiber at the 0.6 mm macrolayer boundary. Generated-code parsers separately track LAYER and MACROLAYER markers.",
    "Rocket's physical/algorithmic macrolayer model is directly defined at the static software-contract level.",
    "Rocket 1.3.2 UI and output-parser contract.",
    "STATIC_SOFTWARE_SEMANTIC",
    "RESOLVES",
    "HIGH",
    "A runtime G-code specimen would validate implementation, but is not required to identify the documented static model.",
)

add(
    "composite_layer_architecture",
    ("FSQ-009", "FSQ-010"),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-122", "FS-125"),
    (
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Consts-B3pY6a9u.js", "macrolayer, shell, perimeter, infill, and support layer-height tips", "89bd54528479f6ab262e0db653fe949e47b6aac457aaa6db59a9f1c05265397b"),
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Scene-B9JN9MXz.js", "Layer Thickness form maps ratio fields to displayed heights by MacroLayerHeight", "337e2618ef11605209cf5ce18727cbe177218d984c569cfc448b0f2f3a17515d"),
        location("FS-125", "Templates/Presets/Profiles.json", "MacroLayerHeight and *RatioToMacro across 48 v15 profiles", "dd9979672da1100f5e03c165d0cad78eb63c1ab276d20f56308474485b5638c8"),
    ),
    "Rocket says fiber layer height always equals macrolayer height. Plastic shell, perimeter, infill, and thick-support heights are separately exposed through integer RatioToMacro settings; current profiles use ratios 1 or 2.",
    "Plastic entity heights can differ from CCF height within a macrolayer package, but they are ratio-derived rather than arbitrary independent CCF/plastic schedules. Current presets divide evenly by construction.",
    "Rocket 1.3.2 UI/configuration model and public preset v15.",
    "STATIC_SOFTWARE_SEMANTIC",
    "RESOLVES",
    "HIGH",
    "This resolves independent selection semantics (FSQ-009), but static evidence does not prove rejection/rounding behavior for invalid non-divisible inputs (FSQ-010).",
)

add(
    "composite_layer_architecture",
    ("FSQ-011",),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-122", "FS-125"),
    (
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Consts-B3pY6a9u.js", "fiber-print-order tip and enum labels", "89bd54528479f6ab262e0db653fe949e47b6aac457aaa6db59a9f1c05265397b"),
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Scene-B9JN9MXz.js", "FIBER_FIRST=0, FIBER_LAST=1, FIBER_BEFORE_INSET0=2", "337e2618ef11605209cf5ce18727cbe177218d984c569cfc448b0f2f3a17515d"),
        location("FS-125", "Templates/Presets/Profiles.json", "FiberPrintOrder values across v15 profiles", "dd9979672da1100f5e03c165d0cad78eb63c1ab276d20f56308474485b5638c8"),
    ),
    "Rocket explicitly defines coincident-layer reinforced-entity ordering: first before all plastic, last after all plastic, or before external shell but after plastic infill/perimeters/support. Enum values are 0, 1, and 2 respectively; current presets use 0 or 1.",
    "The configurable entity-order contract is statically resolved.",
    "Rocket 1.3.2 and public preset v15.",
    "STATIC_SOFTWARE_SEMANTIC",
    "RESOLVES",
    "HIGH",
    "No runtime specimen was produced; the finding is a software setting contract, not a bonding recommendation.",
)

add(
    "cutter_feed_mechanics",
    ("FSQ-012", "FSQ-013"),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-122", "FS-125"),
    (
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Consts-B3pY6a9u.js", "cut-distance, fiber-restart-length, and cut-code tips", "89bd54528479f6ab262e0db653fe949e47b6aac457aaa6db59a9f1c05265397b"),
        location("FS-125", "Templates/Presets/ExtruderCs.json", "FibreSeeker 3 CFC extruder fields CutDistance=58, FiberRestartLength=55, CutCode containing M2800/M400 and comment CUT DISTANCE 54.8", "70279de5079246cb93ad8a624ff889ba40a966b6ee22cf22b9e927743e876428"),
    ),
    "Rocket defines cut distance as cut point to nozzle outlet and restart length as restart extrusion needed for the fiber tail to exit. FibreSeeker preset v15 stores 58 mm and 55 mm respectively, while CutCode contains M2800, M400, and a conflicting comment 'CUT DISTANCE 54.8'.",
    "Direct Rocket values and semantics are recovered, but their runtime precedence and the meaning of the 54.8 comment remain unresolved.",
    "Rocket public preset v15 and Rocket 1.3.2 UI.",
    "STATIC_SOFTWARE_SEMANTIC",
    "CONFLICT",
    "HIGH",
    "Stored software dimensions are not an owner measurement of the physical dead distance and must not be converted into an operating adjustment.",
)

add(
    "cutter_feed_mechanics",
    ("FSQ-015",),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-122", "FS-125"),
    (
        location("FS-125", "Templates/Presets/ExtruderCs.json", "FibreSeeker CFC CutCode", "70279de5079246cb93ad8a624ff889ba40a966b6ee22cf22b9e927743e876428"),
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/generationResultMapperWorker-BiU3AB3X.js", "parser constant '; Start to cut' and cut-block mapping", "e64b8a71bf8afb70837f908766d9a7afe053d82756bc68b2d5b61c0f33932b97"),
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Scene-B9JN9MXz.js", "static machine-control method cutCarbonFiber uses M2800", "337e2618ef11605209cf5ce18727cbe177218d984c569cfc448b0f2f3a17515d"),
    ),
    "The FibreSeeker preset configures M2800 followed by M400 as CutCode. Rocket's static G-code parser recognizes a '; Start to cut' marker, and its non-slicing machine-control code also identifies M2800 as the fiber-cut command.",
    "M2800 is the strongest direct command candidate and M400 is configured synchronization, but actual generated slice output was not observed in this phase.",
    "Static Rocket 1.3.2 package and public preset v15. Machine-control code was inspected only and never invoked.",
    "STATIC_CODE_INDICATOR",
    "SUPPORTS_PARTIAL",
    "HIGH",
    "Static configuration cannot prove when/how often the slicer emits the code or whether postprocessing transforms it.",
)

add(
    "cutter_feed_mechanics",
    ("FSQ-014",),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-120", "FS-122"),
    (
        location("FS-120", "FibreSeeker 3 User Manual R1", "bounded search of control/calibration/printing sections for fiber-specific safe pause boundaries"),
        location("FS-122", "Rocket 1.3.2 static package", "bounded search for documented fiber deposition state/pause contract"),
    ),
    "The bounded direct corpus search did not recover a manufacturer-defined fiber deposition state machine or safe mid-path pause boundary.",
    "FSQ-014 remains open; generic pause_resume resources are not fiber-specific safety guidance.",
    "Preserved public FibreSeek manual and Rocket 1.3.2 package.",
    "BOUNDED_SEARCH_ABSENCE",
    "NO_RESOLUTION",
    "HIGH",
    "Printer firmware configuration and vendor service documentation were not available for static inspection.",
)

add(
    "diagnostics",
    ("FSQ-016",),
    "FIBRESEEK_FIRST_PARTY",
    ("FS-120", "FS-130", "FS-132", "FS-147", "FS-149"),
    (
        location("FS-120", "FibreSeeker 3 User Manual R1", "bounded troubleshooting/calibration search"),
        location("FS-147", "Troubleshooting Layer Shifting in Plastic-Only or Fiber-Only Printing", "nozzle-offset workflow"),
        location("FS-149", "FibreSeeker 3 first-layer print failure", "first-layer diagnostic workflow"),
    ),
    "The public FibreSeek troubleshooting corpus addresses nozzle offset, bed gap/adhesion, and first-layer failures, but does not distinguish excessive from insufficient CCF nozzle compression by symptom.",
    "FSQ-016 remains open; analogous symptom mappings were not promoted.",
    "Preserved FibreSeeker 3 public manuals and SOPs.",
    "BOUNDED_SEARCH_ABSENCE",
    "NO_RESOLUTION",
    "HIGH",
    "A vendor diagnostic guide or owner-authorized physical observation is still required.",
)

add(
    "diagnostics",
    ("FSQ-017",),
    "FIBRESEEK_FIRST_PARTY",
    ("FS-135", "FS-139"),
    (
        location("FS-139", "Fiber Unclogging in Composite Hotend", "derived text lines 19-245: spool/break/feed/PTFE/extruder/tension-sensor/guide-tube/cutter/hotend branch chain"),
        location("FS-135", "Fiber Extruder Rubber Roller Replacement", "derived text lines 78-105: repeated 100 mm +/-0.5 mm fiber extrusion verification"),
    ),
    "FibreSeek provides a branched no-feed/clog diagnostic: inspect spool breaks/texture, heat to material temperature, isolate PTFE movement, observe spool rotation and cracking, inspect extruder debris/roller pressure, tension sensor, guide tube/cutter, and hotend; verify repeated feed and perform 100 mm +/-0.5 mm extrusion calibration after relevant service.",
    "This is a direct diagnostic chain for failed feeding that covers likely restart subsystems, but it is not explicitly a slicer cut/restart-state procedure.",
    "FibreSeeker 3 public fiber feed/service SOPs.",
    "MANUFACTURER_GUIDANCE",
    "SUPPORTS_PARTIAL",
    "HIGH",
    "Cut-command state, restart timing, and software-vs-mechanical fault isolation remain unresolved.",
)

add(
    "materials_process",
    ("FSQ-018",),
    "FIBRESEEK_FIRST_PARTY",
    ("FS-120", "FS-125"),
    (
        location("FS-120", "FibreSeeker 3 User Manual R1", "materials/specification sections listing X-CCF, X-CGF and CFC matrix examples"),
        location("FS-125", "Templates/Presets/ProfileGroups.json and ProfileMaterials.json", "v15 direct material/profile associations"),
    ),
    "Direct FibreSeek material evidence includes X-CCF and X-CGF, and preset v15 supplies CFC profile associations for PLA+X-CCF, PETG+X-CCF, PETG+X-CGF, and PA+X-CCF.",
    "These are current first-party software definitions and manual examples, not a blanket qualification matrix for arbitrary brands or substitutions.",
    "FibreSeeker 3 and public Rocket preset v15.",
    "MANUFACTURER_GUIDANCE",
    "SUPPORTS_PARTIAL",
    "HIGH",
    "No separate approved-brand list, compatibility matrix, SDS, or material qualification report was recovered.",
)

add(
    "materials_process",
    ("FSQ-019",),
    "FIBRESEEK_FIRST_PARTY",
    ("FS-120",),
    (
        location("FS-120", "FibreSeeker 3 User Manual R1", "derived text lines 825-839 and 883-893: sealed storage and hygroscopic-material drying"),
    ),
    "FibreSeek directs long-term material storage in a sealed container and says highly hygroscopic materials such as PETG, PC, and PACF should be dried before each print and kept sealed during printing.",
    "General storage/drying guidance is direct, but material-specific temperatures, durations, moisture limits, and any X-CCF heated-drying permission are absent.",
    "FibreSeeker 3 User Manual R1.",
    "MANUFACTURER_GUIDANCE",
    "SUPPORTS_PARTIAL",
    "HIGH",
    "The evidence must not be expanded into an X-CCF dryer setting.",
)

add(
    "maintenance",
    ("FSQ-020",),
    "FIBRESEEK_FIRST_PARTY",
    ("FS-120", "FS-139"),
    (
        location("FS-120", "FibreSeeker 3 User Manual R1", "derived text lines 883-928: every-use/50 h/300 h/600 h schedule"),
        location("FS-139", "Fiber Unclogging in Composite Hotend", "derived text lines 205-245: inspect/clean cutter area during clog recovery"),
    ),
    "FibreSeek publishes general maintenance intervals and instructs cutter-area inspection/cleaning during fiber-clog recovery, but no cutter-specific periodic inspection, adjustment, or replacement interval was recovered.",
    "FSQ-020 remains open.",
    "FibreSeeker 3 manual and support SOP.",
    "BOUNDED_SEARCH_ABSENCE",
    "NO_RESOLUTION",
    "HIGH",
    "General 300/600-hour maintenance must not be silently assigned to the cutter.",
)

add(
    "composite_layer_architecture",
    ("FSQ-021",),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-122", "FS-125"),
    (
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Consts-B3pY6a9u.js", "support-thick-ratio-to-macro and support interface layer count tips", "89bd54528479f6ab262e0db653fe949e47b6aac457aaa6db59a9f1c05265397b"),
        location("FS-125", "Templates/Presets/Profiles.json", "SupportThickRatioToMacro 1/2; top interface counts 2/3/4; bottom counts 1/2", "dd9979672da1100f5e03c165d0cad78eb63c1ab276d20f56308474485b5638c8"),
    ),
    "Rocket derives thick-support height from SupportThickRatioToMacro, describes thick support as the intersection of thin-support layers, and specifies top-interface thickness in whole macrolayer counts. Current profiles use thick-support ratios 1 or 2 and interface counts of 1-4.",
    "The static support cadence model and current values are recovered, but exact Z-event scheduling for complex support geometry remains unobserved.",
    "Rocket 1.3.2 and public preset v15.",
    "STATIC_SOFTWARE_SEMANTIC",
    "SUPPORTS_PARTIAL",
    "HIGH",
    "A deterministic offline slice is still needed to test interfaces, air gaps, and coincident support/entity ordering.",
)

add(
    "fiber_path_generation",
    ("FSQ-022",),
    "ROCKET_STATIC_OBSERVATION",
    ("FS-122",),
    (
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Scene-B9JN9MXz.js", "mask editor types and localized fiber/perimeter/infill controls", "337e2618ef11605209cf5ce18727cbe177218d984c569cfc448b0f2f3a17515d"),
        location("FS-122", "Rocket 1.3.2 app.asar/dist/assets/Consts-B3pY6a9u.js", "layup help: height intersections use higher priority and priority 1 is highest; mask/layup UI labels", "89bd54528479f6ab262e0db653fe949e47b6aac457aaa6db59a9f1c05265397b"),
        location("FS-122", "Rocket 1.3.2 backend/monolith/publish/Aura2SlicingEngine.dll", "static symbols FULL_MASK, INTERNAL_MASK, EnforceSupportMask, BlockSupportMask, TrimByOtherMask", "e47603e52218552c6da42c6e863e2360756158ebbef41f0296e4e50c0bcddaba"),
    ),
    "Rocket provides full/internal masks plus support blocker/enforcer masks. Full/internal masks can locally alter fiber-perimeter and fiber-infill generation and pattern settings. Height-band layups have explicit priority: overlapping ranges use the higher priority and 1 is highest. Mask records also carry priority and engine code includes trimming by other masks.",
    "Localized reinforcement and layup overlap priority are direct static features; exact overlap precedence between multiple geometric masks is not fully documented.",
    "Rocket 1.3.2 static UI and slicing-engine metadata.",
    "STATIC_SOFTWARE_SEMANTIC",
    "SUPPORTS_PARTIAL",
    "HIGH",
    "A controlled overlapping-mask slice is needed to resolve geometric mask-to-mask and mask-to-layup precedence.",
)


status_rows = [
    ("FSQ-001", "PARTIALLY_RESOLVED", ["FSD-0001", "FSD-0004"], "Rocket v15 exposes 10 mm minimum fiber-infill lines and 20/55 mm minimum reinforced perimeters.", "No universal physical minimum or boundary-value output is established.", "OFFLINE_RUNTIME_TEST"),
    ("FSQ-002", "PARTIALLY_RESOLVED", ["FSD-0002"], "Rocket uses 10/12 mm as the arc radius corresponding to minimum print speed.", "The physical FibreSeeker bend limit is not specified.", "VENDOR_CONFIRMATION"),
    ("FSQ-003", "PARTIALLY_RESOLVED", ["FSD-0003"], "Related infill/perimeter extension and dimensional-compensation fields exist.", "No required fiber clearance from holes or exterior boundaries is documented.", "OFFLINE_RUNTIME_TEST"),
    ("FSQ-004", "PARTIALLY_RESOLVED", ["FSD-0001", "FSD-0002", "FSD-0003", "FSD-0004"], "Static engine and UI evidence show minimum-length/radius fields are part of slicing logic.", "Exact suppression/prolonging behavior needs controlled generated paths.", "OFFLINE_RUNTIME_TEST"),
    ("FSQ-005", "PARTIALLY_RESOLVED", ["FSD-0005"], "Automatic Nozzle Offset and signed manual X/Y correction are documented.", "No numeric acceptance tolerance or target-pattern specification is public.", "VENDOR_CONFIRMATION"),
    ("FSQ-006", "OPEN", ["FSD-0006"], "No equivalent file was located in the bounded preserved static corpus.", "A search miss cannot establish nonexistence.", "VENDOR_CONFIRMATION"),
    ("FSQ-007", "PARTIALLY_RESOLVED", ["FSD-0007"], "Nozzle-offset calibration is explicitly required after CFC nozzle/hotend service and several FFF hotend procedures.", "A complete per-component CFC/FFF replacement matrix is absent.", "VENDOR_CONFIRMATION"),
    ("FSQ-008", "RESOLVED", ["FSD-0004", "FSD-0008"], "Rocket defines macrolayer, microlayer, coincident entity scheduling, and separate output markers.", "No material residual for the static software-model question.", "NONE"),
    ("FSQ-009", "RESOLVED", ["FSD-0009"], "Fiber height equals macrolayer height while plastic entity heights are separately ratio-derived.", "No material residual for whether the configuration model permits different heights.", "NONE"),
    ("FSQ-010", "PARTIALLY_RESOLVED", ["FSD-0004", "FSD-0009"], "Current integer ratio settings produce evenly dividing microlayers.", "Invalid-input rejection, coercion, or rounding is unobserved.", "OFFLINE_RUNTIME_TEST"),
    ("FSQ-011", "RESOLVED", ["FSD-0010"], "Rocket explicitly defines first, last, and before-external-shell fiber ordering.", "No material residual for the configurable ordering contract.", "NONE"),
    ("FSQ-012", "PARTIALLY_RESOLVED", ["FSD-0011"], "CutDistance=58, FiberRestartLength=55, and CutCode with 54.8 comment are directly recovered.", "Runtime precedence and the conflicting comment remain unresolved.", "OFFLINE_RUNTIME_TEST"),
    ("FSQ-013", "PARTIALLY_RESOLVED", ["FSD-0011"], "Rocket defines and stores cut/restart software distances.", "Physical dead distances have not been measured or vendor-confirmed.", "PHYSICAL_EXPERIMENT"),
    ("FSQ-014", "OPEN", ["FSD-0013"], "No fiber-specific safe pause/state contract was recovered.", "Firmware/vendor evidence is required.", "VENDOR_CONFIRMATION"),
    ("FSQ-015", "PARTIALLY_RESOLVED", ["FSD-0012"], "M2800 and M400 are configured, and Rocket recognizes cut markers.", "Actual generated output and postprocessor placement were not observed.", "OFFLINE_RUNTIME_TEST"),
    ("FSQ-016", "OPEN", ["FSD-0014"], "No direct symptom discriminator was recovered.", "Vendor guidance or an owner experiment is required.", "PHYSICAL_EXPERIMENT"),
    ("FSQ-017", "PARTIALLY_RESOLVED", ["FSD-0015"], "A direct branched fiber no-feed/clog diagnostic and feed verification exist.", "Cut/restart software-state fault isolation remains absent.", "VENDOR_CONFIRMATION"),
    ("FSQ-018", "PARTIALLY_RESOLVED", ["FSD-0016"], "Four current CFC matrix/reinforcement profile combinations are directly defined.", "Software definitions are not a full brand/material qualification matrix.", "VENDOR_CONFIRMATION"),
    ("FSQ-019", "PARTIALLY_RESOLVED", ["FSD-0017"], "Sealed storage and drying of named hygroscopic matrices are documented.", "Material-specific cycles/limits and X-CCF heated-drying permission remain absent.", "STATIC_FIRST_PARTY"),
    ("FSQ-020", "OPEN", ["FSD-0018"], "General intervals and recovery-time cutter inspection exist, but no cutter interval does.", "Cutter-specific service guidance is required.", "VENDOR_CONFIRMATION"),
    ("FSQ-021", "PARTIALLY_RESOLVED", ["FSD-0004", "FSD-0019"], "Thick-support ratios and interface cadence in macrolayers are directly defined.", "Complex Z scheduling and air-gap interactions need output evidence.", "OFFLINE_RUNTIME_TEST"),
    ("FSQ-022", "PARTIALLY_RESOLVED", ["FSD-0004", "FSD-0020"], "Rocket has localized reinforcement masks and explicit height-layup priority.", "Exact overlap precedence among geometric masks and layups remains unobserved.", "OFFLINE_RUNTIME_TEST"),
]

statuses = [
    {
        "question_id": qid,
        "phase2fa_status": "OPEN",
        "phase2fb_status": status,
        "direct_evidence_ids": evidence,
        "determination": determination,
        "residual_unknowns": residual,
        "next_resolution_class": next_class,
        "offline_runtime_performed": False,
    }
    for qid, status, evidence, determination, residual, next_class in status_rows
]

fixtures = {
    "schema_version": "1.0.0",
    "cases": [
        {"case_id": "2fb-minimum-fiber-entities", "fsq_id": "FSQ-001", "expected_status": "PARTIALLY_RESOLVED", "must_include_evidence": "FSD-0001"},
        {"case_id": "2fb-hole-clearance-not-inferred", "fsq_id": "FSQ-003", "expected_status": "PARTIALLY_RESOLVED", "must_include_evidence": "FSD-0003"},
        {"case_id": "2fb-xy-no-acceptance-promotion", "fsq_id": "FSQ-005", "expected_status": "PARTIALLY_RESOLVED", "must_include_evidence": "FSD-0005"},
        {"case_id": "2fb-nozzle-gcode-search-miss-open", "fsq_id": "FSQ-006", "expected_status": "OPEN", "must_include_evidence": "FSD-0006"},
        {"case_id": "2fb-macrolayer-model", "fsq_id": "FSQ-008", "expected_status": "RESOLVED", "must_include_evidence": "FSD-0008"},
        {"case_id": "2fb-independent-layer-model", "fsq_id": "FSQ-009", "expected_status": "RESOLVED", "must_include_evidence": "FSD-0009"},
        {"case_id": "2fb-nondivisible-runtime-needed", "fsq_id": "FSQ-010", "expected_status": "PARTIALLY_RESOLVED", "must_include_evidence": "FSD-0009"},
        {"case_id": "2fb-cut-distance-conflict", "fsq_id": "FSQ-012", "expected_status": "PARTIALLY_RESOLVED", "must_include_evidence": "FSD-0011"},
        {"case_id": "2fb-no-runtime-command-promotion", "fsq_id": "FSQ-015", "expected_status": "PARTIALLY_RESOLVED", "must_include_evidence": "FSD-0012"},
        {"case_id": "2fb-compression-remains-open", "fsq_id": "FSQ-016", "expected_status": "OPEN", "must_include_evidence": "FSD-0014"},
        {"case_id": "2fb-support-cadence", "fsq_id": "FSQ-021", "expected_status": "PARTIALLY_RESOLVED", "must_include_evidence": "FSD-0019"},
        {"case_id": "2fb-mask-overlap-not-overstated", "fsq_id": "FSQ-022", "expected_status": "PARTIALLY_RESOLVED", "must_include_evidence": "FSD-0020"}
    ],
}

static_index = {
    "schema_version": "1.0.0",
    "baseline_commit": BASELINE,
    "rocket_version": "1.3.2",
    "frontend_build": 1868,
    "backend_version": "1.3.1.480",
    "execution_performed": False,
    "source_id": "FS-122",
    "container_sha256": "ee76209d5f54e2c5d5f6be06ee2408e0bfae46ba56a4dfd17242e7b9e0de352c",
    "artifacts": [
        {"path": "Contents/Resources/app.asar", "sha256": "9c0948aaf2e74e3ca8270a6f37e8f2409ccade92af56d87988fe170289b2b739", "method": "read-only DMG mount; ASAR integrity-aware static extraction"},
        {"path": "app.asar/dist/assets/Consts-B3pY6a9u.js", "sha256": "89bd54528479f6ab262e0db653fe949e47b6aac457aaa6db59a9f1c05265397b", "role": "English UI semantics and labels"},
        {"path": "app.asar/dist/assets/Scene-B9JN9MXz.js", "sha256": "337e2618ef11605209cf5ce18727cbe177218d984c569cfc448b0f2f3a17515d", "role": "profile enums, mask editor, machine-control code observed statically"},
        {"path": "app.asar/dist/assets/generationResultMapperWorker-BiU3AB3X.js", "sha256": "e64b8a71bf8afb70837f908766d9a7afe053d82756bc68b2d5b61c0f33932b97", "role": "generated G-code parsing contract"},
        {"path": "backend/monolith/publish/Aura2SlicingEngine.dll", "sha256": "e47603e52218552c6da42c6e863e2360756158ebbef41f0296e4e50c0bcddaba", "role": "static .NET metadata/string index"}
    ],
    "profile_source": {"source_id": "FS-125", "version": 15, "profiles_sha256": "dd9979672da1100f5e03c165d0cad78eb63c1ab276d20f56308474485b5638c8", "extruder_cs_sha256": "70279de5079246cb93ad8a624ff889ba40a966b6ee22cf22b9e927743e876428"},
    "not_executed": ["Rocket Electron application", "Aura.Monolith.API backend", "Aura2SlicingEngine", "firmware", "G-code", "printer or machine-control commands"],
}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


write_jsonl(OUT / "records/direct_evidence.jsonl", records)
write_jsonl(OUT / "questions/fsq_status.jsonl", statuses)
(OUT / "fixtures").mkdir(parents=True, exist_ok=True)
(OUT / "static").mkdir(parents=True, exist_ok=True)
(OUT / "fixtures/regression_cases.json").write_text(json.dumps(fixtures, indent=2, sort_keys=True) + "\n", encoding="utf-8")
(OUT / "static/rocket_static_index.json").write_text(json.dumps(static_index, indent=2, sort_keys=True) + "\n", encoding="utf-8")

print(f"Wrote {len(records)} direct-evidence records, {len(statuses)} FSQ statuses, and {len(fixtures['cases'])} fixtures.")
