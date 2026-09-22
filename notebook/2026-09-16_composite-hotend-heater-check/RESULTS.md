# Loom heater/thermistor check on the new composite hotend — 2026-09-16

`EXPERIMENTAL`. FS's reply of 2026-09-16 gates reuse of the Composite Hotend on
a heating test: *"please perform a heating test to confirm that the heater
cartridge and thermistor are functioning normally."*

**No commands were issued.** The owner started the vendor nozzle-offset
calibration, which heats the tool itself, so the routine was observed rather
than driven. Telemetry logged at 1 Hz for 375 s:
`heater_log_calibration_2026-09-16.csv` (275 samples).

## Result: Plastic 1 and Plastic 2 pass

| Zone | Behaviour during the routine |
| --- | --- |
| `extruder` (Plastic 1, new hotend) | Held 220 °C (peak 221.8), then target dropped to 170 °C and settled **170.0–170.3 °C** with PID power 0.19–0.34 |
| `extruder1` (Plastic 2) | Held **119.7–121.0 °C** against a 120 °C target |
| `heater_bed` | Not targeted |

Regulation within **±0.3 °C** at a steady-state duty of roughly 25–30 % is
normal closed-loop behaviour. A thermistor displaced or encased in plastic, or a
failing cartridge, shows as sloppy regulation, drift, or saturated power; none
of that is present. **The FS-required heating test is satisfied for the plastic
zones.**

Caveat: logging began after the rise from ambient was already complete (first
sample 221.8 °C), so the ramp *rate* was not captured — only the overshoot,
step-down and settling, which are the more diagnostic parts.

## `OPEN QUESTION`: the Fibre zone sensor reads a constant value

`extruder2` (Fibre) reported **200.9 °C for all 375 s, total range 0.03 °C**,
at zero target and zero power, while the adjacent plastic zone swung 50 °C
(221.8 → 170.0). Yesterday's session logged the same zone at a constant 200.7 °C
while Plastic 1 ramped 37 → 210 °C.

The configuration shows this is **not a placeholder** — the fibre path has a real
heater and a real sensor:

```
[extruder2]
heater_pin = PB11
sensor_type = my_custom_resistance_adc
sensor_pin = PC4
min_temp = 0
max_temp = 380
```

**The reading is identical on two different hotend assemblies** (old, damaged;
new, fitted 2026-09-16), so whatever this is, it is **upstream of the hotend** —
config, wiring, or sensor type — and was not caused by the failure.

`INFERENCE`, and the reason this matters: with `min_temp = 0` a stuck 200.9 never
trips Klipper's protection. Two possibilities, both bad for the fibre path:

1. If a fibre-zone target above 200.9 is ever commanded, the heater is driven
   with no usable feedback until `verify_heater` faults.
2. If targets are always at or below 200.9, Klipper believes the zone is already
   hot and **the fibre heater never energises at all**.

Either way the fibre zone is not under closed-loop thermal control. FS's own
explanation for this failure is that *"the fibre becomes clogged and cannot
properly carry the molten plastic through the nozzle"* — a fibre zone with no
working temperature feedback is a candidate contributor to exactly that.

**Not tested deliberately.** Confirming it by commanding a target above 200.9
would mean driving a heater open-loop, which is not a safe test to run remotely.
This belongs in a question to FS instead.

## New operational knowledge

- The `calibration` state, already known from the extracted
  `STATE_TRANSITIONS` table as a legal target from `standby`, was observed live
  for the first time. `idle_timeout` reports `Printing` throughout, so an idle
  check alone will not distinguish it from a print.
- The nozzle-offset routine heats **Plastic 1 to 220 °C, then holds 170 °C**,
  with **Plastic 2 at 120 °C**, and emits
  `echo: [PRECALIBRATION] nozzle is heating, please wait...`.
- It runs with no bed mesh loaded (`// No mesh loaded to offset`) and toggles
  `min_extrude_temp` between 0 and 180 around the heat-up.

---

## The new hotend leaked at the same joint on its first extrusion

`USER-OBSERVED` + machine log, 2026-09-16 ~21:30–22:00. **The failure reproduced
on a brand-new composite hotend within about 100 mm of filament.**

### Timeline, including two errors of mine

| Time | Event |
| --- | --- |
| 21:27 | Nozzle-offset calibration finished clean. Offsets moved X −32.823 → **−35.043** (−2.22 mm), Y −0.006 → −0.355, Z 2.570 → **2.652** |
| 21:34 | **My error:** I ran a 40 mm extrusion check on Plastic 1 **with no filament loaded** (`filament_sensor_1` `False`). Void; harmless. I had not checked the presence sensor |
| 21:44–45 | Owner loaded Plastic 1 and purged both sides from the HMI: `G0 V50` on Plastic 1, then `G1 E50` on Plastic 2 — the second ended with `ACTIVATE_RIGHT_P_EXTRUDER` |
| 21:49 | **My error:** 100 mm commanded for Plastic 1 went out of **Plastic 2**, because `extruder1` was still active. My script printed `active extruder: extruder1` and carried on. ~0.3 g of PLA from the right nozzle at 205 °C; no damage |
| ~21:53 | Re-run with `ACTIVATE_LEFT_P_EXTRUDER` and a fail-closed assertion on `toolhead.extruder`. 100 mm at 1 mm/s, 211 °C, free air at X120 Y150 Z60, **through Plastic 1** |
| ~21:55 | Owner: *"stop it"*, *"it's clogging"*. All heaters off immediately |
| — | Owner cleared the clog and measured **19.43 mm** |
| ~22:00 | Printer powered off for the night |

Both errors are now guarded against in
`docs/loom/PRINT_START_AND_STATE_MACHINE.md` ("Filament sensors").

### What the photos show

- `new_hotend_leak_first_extrusion_IMG_4497.jpg`,
  `new_hotend_leak_closeup_IMG_4500.jpg` — **white PLA pooled on top of the new
  heater block around the base of the heat-break**, the same location and form as
  the old assembly's leak (`2026-09-15-T7/clog_leak_over_block_IMG_4448.jpg`).
  Fresh PLA, not carbonized.
- `strands_P1_vs_P2_IMG_4492.jpg` — strands from both nozzles. The owner reported
  Plastic 1's as *"super thick"* compared with Plastic 2's. **Expected from
  geometry:** 0.7 mm vs 0.4 mm is an area ratio of (0.7/0.4)² = **3.06×**, so the
  same 240 mm³ emerges about three times thicker, a third as long, and three times
  slower at the tip, where it coils instead of drawing away. Thick, abundant
  output is not by itself a restriction.

**19.43 mm** — `USER-OBSERVED`, **confirmed by the owner** as the gap left at the
100 mm mark: **80.57 mm fed of 100 mm commanded, 19.4 % short**, the extruder
pushing until the path stalled. Not a calibration reading — the post-correction
verification at 5.49 on 2026-09-15 was under 1 mm over 100 mm, so the shortfall is
the restriction, not the step value.

### What this rules out

Two assemblies — one worn, one new — failing identically means the cause is **not**
wear, accumulated residue, carbonization, a defective individual part, or a
one-off assembly error. It is systemic to this machine or to how the head is being
run.

### Fibre state, and two hypotheses

`filament_sensor` (left **fibre**) read **`True`**. The owner **did not thread the
fibre through the new hotend and never unloaded it**, so fibre is present at the
upstream sensor but its tip is not in the new nozzle.

- **H-A, weakened:** a stationary fibre tip obstructing the nozzle while plastic is
  pushed around it. Undermined by the owner's answer — no fibre was threaded
  through the new hotend.
- **H-B, now leading (`INFERENCE`):** with no fibre occupying it, the new hotend's
  **fibre channel is an open bypass**. Molten plastic under pressure takes the
  empty channel instead of the 0.7 mm orifice and vents at the heat-break /
  guide-tube joint — exactly where both assemblies leaked. Consistent with FS's
  wording that the fibre is what should *"carry the molten plastic through the
  nozzle"*.
- **H-C, less likely:** a joint-seal or assembly problem. Two assemblies failing
  identically, and FS stating there is no special tightening procedure, both
  count against it.

H-A and H-B both put the relationship between the fibre channel and plastic-only
extrusion at the centre. **What state the fibre should be in for plastic-only
printing on this head is the question that matters**, and it is FS's design
knowledge.

### Decisive check, before cleaning

When the hotend comes off, **look inside the fibre guide tube / channel before
cleaning anything:**

- **Plastic inside the fibre channel** → supports H-B (bypass up the empty channel).
- **Channel clean, leak only on the outside of the joint** → points to H-C (seal).

Cleaning destroys this evidence.

### Not done tonight, deliberately

The owner offered to unload the fibre now. Recommended against: unloading needs
the head hot, which would bake tonight's fresh leak onto the block the owner
intends to clean tomorrow, and the owner's answer weakened the case that the
fibre in the feed is the cause. Better to see inside the channel and ask FS first.
