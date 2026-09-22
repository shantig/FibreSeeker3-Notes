# T3 results — step-reception test (2026-09-12)

Provenance: owner-performed on Loom and pasted into the Claude Code session on
2026-09-12. Console text is reproduced verbatim from the paste, reordered to
top-to-bottom chronological order. `MSLUT*`, `MSLUTSEL`, `MSLUTSTART` table
registers are omitted (identical in every dump; waveform tables, not status).
Classification: `USER-OBSERVED` — no independent machine capture of this
transcript is preserved.

## Owner observation (verbatim, 2026-09-12)

> fwiw, i see the pulley on top of the extruder/toolhead moving as if it's
> attempting to feed. what i still don't see or hear doing anything is when i
> try to load in the through filament runout sensor on the back. nothing moved.

Not stated: which pulley (right or left) moved during which command.

## Sequence (owner console times, Loom local)

| Time | Command |
|---|---|
| 2:35 PM | `DUMP_TMC STEPPER=extruder1` (dump 1) |
| 2:35 PM | `FORCE_MOVE STEPPER=extruder1 DISTANCE=1 VELOCITY=1` |
| 2:37 PM | `FORCE_MOVE STEPPER=extruder1 DISTANCE=1 VELOCITY=1` (repeated) |
| 2:37 PM | `DUMP_TMC STEPPER=extruder1` (dump 2) |
| 2:38 PM | `FORCE_MOVE STEPPER=extruder1 DISTANCE=-1 VELOCITY=1` |
| 2:38 PM | `DUMP_TMC STEPPER=extruder1` (dump 3) |
| 2:38 PM | `DUMP_TMC STEPPER=extruder` (dump 4, left plastic control) |
| 2:38 PM | `FORCE_MOVE STEPPER=extruder DISTANCE=1 VELOCITY=1` |
| 2:39 PM | `DUMP_TMC STEPPER=extruder` (dump 5) |

## Dump 1 — extruder1, 2:35 PM (before moves)

```
// GCONF:      00000008 multistep_filt=1
// GSTAT:      00000000
// IOIN:       40013f2e dir=1 encb=1 enca=1 encn=1 comp_a=1 comp_b=1 comp_a1_a2=1 comp_b1_b2=1 output=1 ext_res_det=1 silicon_rv=1 version=0x40
// DRV_CONF:   00000001 current_range=1
// GLOBALSCALER: 0000007f globalscaler=127
// IHOLD_IRUN: 04061f08 ihold=8 irun=31 iholddelay=6 irundelay=4
// TPOWERDOWN: 0000000a tpowerdown=10
// TSTEP:      000fffff tstep=1048575
// TPWMTHRS:   000fffff tpwmthrs=1048575
// TCOOLTHRS:  00000000
// THIGH:      00000000
// ADC_VSUPPLY_AIN: 02ce09ac adc_vsupply=0x09ac(24.096V) adc_ain=0x02ce(219.134mV)
// ADC_TEMP:   000009f8 adc_temp=0x09f8(66.8C)
// MSCNT:      00000288 mscnt=648
// MSCURACT:   015a0148 cur_a=-184 cur_b=-166
// CHOPCONF:   34410153 toff=3 hstrt=5 hend=2 tbl=2 tpfd=4 mres=4(16usteps) intpol=1 dedge=1
// COOLCONF:   00000000
// DRV_STATUS: 81080031 sg_result=49 cs_actual=8 stallguard=1 stst=1
// PWMCONF:    c40c001d pwm_ofs=29 pwm_autoscale=1 pwm_autograd=1 pwm_reg=4 pwm_lim=12
// PWM_SCALE:  00000020 pwm_scale_sum=32
// PWM_AUTO:   0000001d pwm_ofs_auto=29
// SG4_THRS:   00000300 sg4_filt_en=1 sg4_angle_offset=1
// SG4_RESULT: 00000004 sg4_result=4
// SG4_IND:    03010302 sg4_ind_0=2 sg4_ind_1=3 sg4_ind_2=1 sg4_ind_3=3
```

## Dump 2 — extruder1, 2:37 PM (after two +1 mm moves)

```
// GCONF:      00000008 multistep_filt=1
// GSTAT:      00000000
// IOIN:       4001352c encb=1 enca=1 encn=1 comp_a=1 comp_a1_a2=1 output=1 ext_res_det=1 silicon_rv=1 version=0x40
// DRV_CONF:   00000001 current_range=1
// GLOBALSCALER: 0000007f globalscaler=127
// IHOLD_IRUN: 04061f08 ihold=8 irun=31 iholddelay=6 irundelay=4
// TPOWERDOWN: 0000000a tpowerdown=10
// TSTEP:      000fffff tstep=1048575
// TPWMTHRS:   000fffff tpwmthrs=1048575
// TCOOLTHRS:  00000000
// THIGH:      00000000
// ADC_VSUPPLY_AIN: 02ce09af adc_vsupply=0x09af(24.126V) adc_ain=0x02ce(219.134mV)
// ADC_TEMP:   000009f8 adc_temp=0x09f8(66.8C)
// MSCNT:      00000148 mscnt=328
// MSCURACT:   019500df cur_a=223 cur_b=-107
// CHOPCONF:   34410153 toff=3 hstrt=5 hend=2 tbl=2 tpfd=4 mres=4(16usteps) intpol=1 dedge=1
// COOLCONF:   00000000
// DRV_STATUS: 8108002d sg_result=45 cs_actual=8 stallguard=1 stst=1
// PWMCONF:    c40c001d pwm_ofs=29 pwm_autoscale=1 pwm_autograd=1 pwm_reg=4 pwm_lim=12
// PWM_SCALE:  00000020 pwm_scale_sum=32
// PWM_AUTO:   0000001d pwm_ofs_auto=29
// SG4_THRS:   00000300 sg4_filt_en=1 sg4_angle_offset=1
// SG4_RESULT: 00000001 sg4_result=1
// SG4_IND:    01000100 sg4_ind_1=1 sg4_ind_3=1
```

## Dump 3 — extruder1, 2:38 PM (after −1 mm move)

```
// GCONF:      00000008 multistep_filt=1
// GSTAT:      00000000
// IOIN:       4001372e dir=1 encb=1 enca=1 encn=1 comp_a=1 comp_b=1 comp_a1_a2=1 output=1 ext_res_det=1 silicon_rv=1 version=0x40
// DRV_CONF:   00000001 current_range=1
// GLOBALSCALER: 0000007f globalscaler=127
// IHOLD_IRUN: 04061f08 ihold=8 irun=31 iholddelay=6 irundelay=4
// TPOWERDOWN: 0000000a tpowerdown=10
// TSTEP:      000fffff tstep=1048575
// TPWMTHRS:   000fffff tpwmthrs=1048575
// TCOOLTHRS:  00000000
// THIGH:      00000000
// ADC_VSUPPLY_AIN: 02cf09ac adc_vsupply=0x09ac(24.096V) adc_ain=0x02cf(219.439mV)
// ADC_TEMP:   000009fc adc_temp=0x09fc(67.3C)
// MSCNT:      000001e8 mscnt=488
// MSCURACT:   010b0023 cur_a=35 cur_b=-245
// CHOPCONF:   34410153 toff=3 hstrt=5 hend=2 tbl=2 tpfd=4 mres=4(16usteps) intpol=1 dedge=1
// COOLCONF:   00000000
// DRV_STATUS: 81080038 sg_result=56 cs_actual=8 stallguard=1 stst=1
// PWMCONF:    c40c001d pwm_ofs=29 pwm_autoscale=1 pwm_autograd=1 pwm_reg=4 pwm_lim=12
// PWM_SCALE:  00000020 pwm_scale_sum=32
// PWM_AUTO:   0000001d pwm_ofs_auto=29
// SG4_THRS:   00000300 sg4_filt_en=1 sg4_angle_offset=1
// SG4_RESULT: 00000001 sg4_result=1
// SG4_IND:    01000100 sg4_ind_1=1 sg4_ind_3=1
```

## Dump 4 — extruder (left plastic control), 2:38 PM (before move)

```
// GCONF:      0000000c en_pwm_mode=1 multistep_filt=1
// GSTAT:      0000001d reset=1(Reset) uv_cp=1(Undervoltage!) register_reset=1 vm_uvlo=1
// IOIN:       4001303c encb=1 enca=1 drv_enn=1 encn=1 output=1 ext_res_det=1 silicon_rv=1 version=0x40
// DRV_CONF:   00000001 current_range=1
// GLOBALSCALER: 000000a3 globalscaler=163
// IHOLD_IRUN: 04061f06 ihold=6 irun=31 iholddelay=6 irundelay=4
// TPOWERDOWN: 0000000a tpowerdown=10
// TSTEP:      000fffff tstep=1048575
// TPWMTHRS:   00000117 tpwmthrs=279
// TCOOLTHRS:  00000000
// THIGH:      00000000
// ADC_VSUPPLY_AIN: 02d409a8 adc_vsupply=0x09a8(24.058V) adc_ain=0x02d4(220.965mV)
// ADC_TEMP:   000009c8 adc_temp=0x09c8(60.5C)
// MSCNT:      00000008 mscnt=8
// MSCURACT:   00f7000c cur_a=12 cur_b=247
// CHOPCONF:   34410153 toff=3 hstrt=5 hend=2 tbl=2 tpfd=4 mres=4(16usteps) intpol=1 dedge=1
// COOLCONF:   00000000
// DRV_STATUS: 81004000 stealth=1 cs_actual=0(Reset?) stallguard=1 stst=1
// PWMCONF:    c40c001d pwm_ofs=29 pwm_autoscale=1 pwm_autograd=1 pwm_reg=4 pwm_lim=12
// PWM_SCALE:  00000000
// PWM_AUTO:   0000001d pwm_ofs_auto=29
// SG4_THRS:   00000300 sg4_filt_en=1 sg4_angle_offset=1
// SG4_RESULT: 00000000
// SG4_IND:    00000000
```

## Dump 5 — extruder (left plastic control), 2:39 PM (after +1 mm move)

```
// GCONF:      0000000c en_pwm_mode=1 multistep_filt=1
// GSTAT:      00000000
// IOIN:       4001382c encb=1 enca=1 encn=1 comp_b1_b2=1 output=1 ext_res_det=1 silicon_rv=1 version=0x40
// DRV_CONF:   00000001 current_range=1
// GLOBALSCALER: 000000a3 globalscaler=163
// IHOLD_IRUN: 04061f06 ihold=6 irun=31 iholddelay=6 irundelay=4
// TPOWERDOWN: 0000000a tpowerdown=10
// TSTEP:      000fffff tstep=1048575
// TPWMTHRS:   00000117 tpwmthrs=279
// TCOOLTHRS:  00000000
// THIGH:      00000000
// ADC_VSUPPLY_AIN: 02d309aa adc_vsupply=0x09aa(24.077V) adc_ain=0x02d3(220.660mV)
// ADC_TEMP:   000009d8 adc_temp=0x09d8(62.6C)
// MSCNT:      00000308 mscnt=776
// MSCURACT:   000c0108 cur_a=-248 cur_b=12
// CHOPCONF:   34410153 toff=3 hstrt=5 hend=2 tbl=2 tpfd=4 mres=4(16usteps) intpol=1 dedge=1
// COOLCONF:   00000000
// DRV_STATUS: 80064012 sg_result=18 stealth=1 cs_actual=6 stst=1
// PWMCONF:    c40c001d pwm_ofs=29 pwm_autoscale=1 pwm_autograd=1 pwm_reg=4 pwm_lim=12
// PWM_SCALE:  0000001c pwm_scale_sum=28
// PWM_AUTO:   00000023 pwm_ofs_auto=35
// SG4_THRS:   00000300 sg4_filt_en=1 sg4_angle_offset=1
// SG4_RESULT: 00000012 sg4_result=18
// SG4_IND:    0c0a0807 sg4_ind_0=7 sg4_ind_1=8 sg4_ind_2=10 sg4_ind_3=12
```

## Step-count check

`MSCNT` advances 16 counts per microstep at 16 microsteps (1,024 counts per
electrical cycle). Klipper's step count for a move is
`distance / (rotation_distance / (200 × 16))` (no `full_steps_per_rotation` or
`gear_ratio` configured for either extruder, LM-005).

| Stepper | Move(s) | Steps per 1 mm | Predicted `MSCNT` | Observed `MSCNT` |
|---|---|---:|---:|---:|
| extruder1 | start | — | — | 648 |
| extruder1 | +1 mm, +1 mm | 566 (5.65 mm) | (648 + 2·566·16) mod 1024 = **328** | **328** |
| extruder1 | −1 mm | 566 | (328 − 566·16) mod 1024 = **488** | **488** |
| extruder | start | — | — | 8 |
| extruder | +1 mm | 560 (5.719 mm) | (8 + 560·16) mod 1024 = **776** | **776** |

## Reading

What the dumps show (as transcribed):

- **Every commanded step reached the extruder1 driver.** Its microstep counter
  moved by exactly Klipper's step count, forward and back.
- **The DIR input follows the commanded direction:** `dir` = 0 after the
  forward moves (dump 2), 1 after the reverse move (dump 3).
- **No extruder1 fault appeared during motion:** `GSTAT` stays 0; no short,
  overtemperature, or warning flags.
- **The left-plastic control behaves the same way.** Its driver was disabled
  and showed power-on reset flags before its first move (dump 4:
  `drv_enn=1`, `GSTAT 0x1d`, `cs_actual=0`); after one +1 mm move it was
  enabled, the flags were cleared, and `MSCNT` matched the prediction (dump 5).
  This matches the first-enable pattern already seen in LM-009/LM-012.
- **Driver temperature is not an outlier.** The left driver reads 60.5–62.6 °C
  against 66–67 °C for extruder1, a similar range.

Conclusions:

- **Rejected:** STEP pulses not reaching the extruder1 driver (B-signal), and
  software not commanding extruder1.
- **Not independently established by the dumps:** whether current reaches the
  motor coils and turns the shaft. `MSCNT` is the driver's internal counter.
- **Owner observation:** a pulley on top of the toolhead moves as if feeding,
  while nothing moves or sounds at the rear filament runout sensor.
  - `INFERENCE`: if that pulley is the right-plastic one moving during the
    extruder1 moves, the extruder1 motor chain works (B-output rejected too).
    The drive gear is then on the toolhead, and the rear runout sensor is only
    an entry and sensor point with no motor of its own.
  - That would reconcile the earlier "silent motor, nothing grabs" reports:
    they were made at the rear sensor, where nothing is expected to move.
- **Consequence (INFERENCE):** the leading explanation becomes filament not
  reaching or not being gripped by the toolhead drive gear, class A — for
  example a tube obstruction or disconnection between the rear sensor and the
  toolhead, or a leftover filament piece at the extruder or hotend entry. This
  also fits the extruder1 encoder recording no filament motion during commanded
  feed (LM-012).
- **Still to confirm:** which pulley moved during which command (T4 step 1).
