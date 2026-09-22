# T2 results — extruder1 motor-truth test (2026-09-12)

Provenance: owner-performed on Loom and pasted into the Claude Code session on
2026-09-12. The console text below is reproduced verbatim from the owner's
paste (console order reversed to top-to-bottom chronological order; the
`MSLUT*`/`MSLUTSEL`/`MSLUTSTART` table registers are omitted because they were
identical in both dumps and are waveform tables, not status). Classification:
`USER-OBSERVED` — no independent machine capture of this transcript is
preserved.

## Sequence (owner times, Loom local)

| Time | Command | Owner observation |
|---|---|---|
| 2:18 PM | `DUMP_TMC STEPPER=extruder1` | output below (dump A) |
| 2:20 PM | `STEPPER_BUZZ STEPPER=extruder1` | "does nothing" |
| 2:22 PM | `DUMP_TMC STEPPER=extruder1` | output below (dump B) |

Starting state per T2 protocol: no filament loaded, heaters off. Not recorded:
whether the left-plastic feeder was watched during the buzz; whether the motor
could be felt.

## Dump A (2:18 PM, before buzz)

```
// GCONF:      00000008 multistep_filt=1
// GSTAT:      00000000
// IOIN:       40013c2c encb=1 enca=1 encn=1 comp_a1_a2=1 comp_b1_b2=1 output=1 ext_res_det=1 silicon_rv=1 version=0x40
// DRV_CONF:   00000001 current_range=1
// GLOBALSCALER: 0000007f globalscaler=127
// IHOLD_IRUN: 04061f08 ihold=8 irun=31 iholddelay=6 irundelay=4
// TPOWERDOWN: 0000000a tpowerdown=10
// TSTEP:      000fffff tstep=1048575
// TPWMTHRS:   000fffff tpwmthrs=1048575
// TCOOLTHRS:  00000000
// THIGH:      00000000
// ADC_VSUPPLY_AIN: 02cf09aa adc_vsupply=0x09aa(24.077V) adc_ain=0x02cf(219.439mV)
// ADC_TEMP:   000009f0 adc_temp=0x09f0(65.7C)
// MSCNT:      00000288 mscnt=648
// MSCURACT:   015a0148 cur_a=-184 cur_b=-166
// CHOPCONF:   34410153 toff=3 hstrt=5 hend=2 tbl=2 tpfd=4 mres=4(16usteps) intpol=1 dedge=1
// COOLCONF:   00000000
// DRV_STATUS: 81080032 sg_result=50 cs_actual=8 stallguard=1 stst=1
// PWMCONF:    c40c001d pwm_ofs=29 pwm_autoscale=1 pwm_autograd=1 pwm_reg=4 pwm_lim=12
// PWM_SCALE:  00000020 pwm_scale_sum=32
// PWM_AUTO:   0000001d pwm_ofs_auto=29
// SG4_THRS:   00000300 sg4_filt_en=1 sg4_angle_offset=1
// SG4_RESULT: 00000002 sg4_result=2
// SG4_IND:    02010101 sg4_ind_0=1 sg4_ind_1=1 sg4_ind_2=1 sg4_ind_3=2
```

## Dump B (2:22 PM, after buzz)

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
// ADC_VSUPPLY_AIN: 02cf09ac adc_vsupply=0x09ac(24.096V) adc_ain=0x02cf(219.439mV)
// ADC_TEMP:   000009f4 adc_temp=0x09f4(66.2C)
// MSCNT:      00000288 mscnt=648
// MSCURACT:   015a0148 cur_a=-184 cur_b=-166
// CHOPCONF:   34410153 toff=3 hstrt=5 hend=2 tbl=2 tpfd=4 mres=4(16usteps) intpol=1 dedge=1
// COOLCONF:   00000000
// DRV_STATUS: 81080032 sg_result=50 cs_actual=8 stallguard=1 stst=1
// PWMCONF:    c40c001d pwm_ofs=29 pwm_autoscale=1 pwm_autograd=1 pwm_reg=4 pwm_lim=12
// PWM_SCALE:  00000020 pwm_scale_sum=32
// PWM_AUTO:   0000001d pwm_ofs_auto=29
// SG4_THRS:   00000300 sg4_filt_en=1 sg4_angle_offset=1
// SG4_RESULT: 00000004 sg4_result=4
// SG4_IND:    03010302 sg4_ind_0=2 sg4_ind_1=3 sg4_ind_2=1 sg4_ind_3=3
```

## Reading

Field names are Klipper's own decoding as printed; Klipper omits fields whose
value is zero.

What the dumps show (as transcribed):

- **The driver chip is alive and has motor supply.** SPI reads succeed;
  `ADC_VSUPPLY` ≈ 24.1 V in both dumps.
- **No driver fault is latched.** `GSTAT = 0` (no reset, `drv_err`, or
  undervoltage flag). `DRV_STATUS` has no short-to-ground/supply bits
  (`s2ga/s2gb/s2vsa/s2vsb`) and no `ot`/`otpw`.
- **The driver is enabled and in standstill hold.** `IOIN` low byte `0x2c`/`0x2e`
  has bit 4 (`drv_enn`) clear; `CHOPCONF toff=3` (output stage not switched off
  by register); `DRV_STATUS stst=1`, `cs_actual=8` equal to `ihold=8`. This
  is consistent with the configuration: Loom's `[idle_timeout]` G-code only
  zeroes the plastic heater targets and does not run `M84` (LM-005; same in
  the last LM-012 config dump), so steppers stay enabled when idle.
- **The DIR input changed during the buzz.** `IOIN` bit 1 (`dir`) was 0 in dump
  A and 1 in dump B; the only command between the dumps was `STEPPER_BUZZ`.
  `INFERENCE`: the host scheduled extruder1 motion and the MCU drove the
  extruder1 DIR line into this driver.
- **`MSCNT` is 648 in both dumps.** This is **not discriminating**:
  `STEPPER_BUZZ` moves +1 mm then −1 mm ten times, so a driver that received
  every step returns to the same microstep position.
- `DRV_STATUS` open-load flags (`ola`/`olb`) are only evaluated during motion,
  so their absence in standstill dumps says nothing about the motor coils.
- `cs_actual` and `MSCURACT` are commanded values, not measured coil current,
  so they do not show that a motor is connected.
- Driver temperature 65.7–66.2 °C, below any warning flag. Whether that is
  normal for this board position is `UNKNOWN` (no comparison driver dumped).

Combined with the owner observation (no visible or audible motion):

- **Supported:** the fault lies between "host schedules extruder1 motion" and
  "motor shaft turns" — either STEP pulses are not reaching the driver, or the
  driver output / motor cable / connector / motor does not turn the shaft.
- **Weakened:** A-grip as the sole cause (the motor did not visibly move with
  no filament load at all).
- **Still open:** C-mapping (whether another feeder moved was not recorded).
- **Remaining discriminator:** whether the driver's microstep counter advances
  on a net, one-direction move. That is T3 in `OWNER_PROTOCOL.md`.
