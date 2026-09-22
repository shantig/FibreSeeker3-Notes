# Loom capture session 2026-09-21T225059Z — Z homing fails (probe never triggers)

- Purpose: diagnose the owner's report that Z homing "keeps trying to go higher
  than what's possible" and had to be stopped by power-off, while checking the
  hotends for a clog.
- Authorization: project owner, 2026-09-14 — full live access.
- Machine: Loom, `<printer-ip>`, Moonraker 7125. At capture: `ready`,
  `standby`, `homed_axes = xy` (Z not homed), heaters as the owner left them.
- Started 2026-09-21T22:50:59Z. Client: curl, 30 s timeout. No credentials sent
  or stored.
- State-changing commands: none. `QUERY_PROBE` (22:52:53Z) reads the probe
  pin and does not move anything; result `probe: open`.
- Captures are session-local (`LM-` IDs and manifest records not yet assigned;
  session still open).

| Request | Body bytes | SHA-256 |
|---|---:|---|
| klippy-log | 1875312 | `35075cbbdb23670898705661a3acf3a9c42b52f4c22beb4115bf0c2ef28beb57` |
| objects-state | 1214 | `fa8b0ac81b74d9780f02dad790a0e4b75779599f82bccfe4138782b3700fa45b` |
| query-probe | 15 | `1aad36b0fb02621b951649811957ba7ad67d4838c2932d02088f7d6e8db74313` |
| gcode-store | 8261 | `5e40a986b1807e59b750d8374d5008d096c3964a349fed05617f9be0dc0fb392` |

Requests: `GET /server/files/logs/klippy.log`;
`GET /printer/objects/query?toolhead&print_stats&webhooks&probe&tension_sensor&gcode_move&idle_timeout`;
`POST /printer/gcode/script?script=QUERY_PROBE`; `GET /server/gcode_store?count=200`.

## Findings from klippy.log (file order; the machine clock is unreliable across reboots)

- One Z homing **succeeded** earlier today: 4 probe samples at (150,150) averaging
  -0.1038 mm, check delta -0.0038 mm (limit ±0.05 mm).
- The next two Z homings (after the reboots logged as 17:33 and 17:37 machine
  time) log `Z homing start: travel=375.150 max_attempts=4` and
  `attempt 1: forcepos Z=375.050 homepos Z=-0.100`, then **nothing**: no probe
  sample, no error. The next line in each case is the next boot. Reading: the
  probe never triggered, and the bed kept driving toward the nozzle until power
  was cut. The homing macro does XY first, parks at X150 Y150 with T0 (left
  nozzle) and then homes Z on `probe:z_virtual_endstop` (`[probe] pin = PF5`).
- After the last reboot the owner homed XY only (`G28 X0 Y0`, 22:49Z) and
  continued extrusion checks without Z homing.

## State-changing actions (owner present and ready; POST /printer/gcode/script)

| UTC | Command | Result |
|---|---|---|
| 23:03:11Z | `G28 X Y` | {"result":"ok"} |
| 23:03:38Z | `T0 MOVE_Z=0` | {"result":"ok"} |
| 23:03:44Z | `G90` | {"result":"ok"} |
| 23:03:45Z | `G1 X150 Y150 F6000` | {"result":"ok"} |
| 23:03:45Z | `M400` | {"result":"ok"} |
| 23:08:43Z | `SET_KINEMATIC_POSITION Z=31.8` | {"result":"ok"} |
| 23:08:44Z | `PROBE SAMPLES=1` | `!! No trigger on probe after full movement` (Moonraker HTTP 400) |

  File \"/home/anisoprint/moonraker/moonraker/components/application.py\", line 705, in _process_http_request
    result = await self.api_defintion.request(

  File \"/home/anisoprint/moonraker/moonraker/components/klippy_connection.py\", line 783, in request
    return await self._request_standard(web_request)

  File \"/home/anisoprint/moonraker/moonraker/components/klippy_connection.py\", line 880, in _request_standard
    return await base_request.wait(timeout)

  File \"/home/anisoprint/moonraker/moonraker/components/klippy_connection.py\", line 991, in wait
    return await asyncio.wait_for(asyncio.shield(self._fut), to)

  File \"/usr/lib/python3.8/asyncio/tasks.py\", line 494, in wait_for
    return fut.result()

moonraker.utils.exceptions.ServerError: No trigger on probe after full movement


The above exception was the direct cause of the following exception:


Traceback (most recent call last):

  File \"/home/anisoprint/moonraker-env/lib/python3.8/site-packages/tornado/web.py\", line 1790, in _execute
    result = await result

  File \"/home/anisoprint/moonraker/moonraker/components/application.py\", line 691, in post
    await self._process_http_request(RequestType.POST)

  File \"/home/anisoprint/moonraker/moonraker/components/application.py\", line 711, in _process_http_request
    raise tornado.web.HTTPError(

tornado.web.HTTPError: HTTP 400: No trigger on probe after full movement
"}} |
| 23:08:55Z | `G90` | {"result":"ok"} |
| 23:08:55Z | `G1 Z6 F600` | {"result":"ok"} |
| 23:08:55Z | `M400` | {"result":"ok"} |

Test design: owner measured the left-nozzle-to-bed gap at X150 Y150 as 34.8 mm. Logical Z was set 3 mm low (31.8), so `PROBE` (to position_min -4, 10 mm/s) could overtravel contact by at most ~1 mm. The move ran its full 35.8 mm in ~3.6 s with no trigger; the bed was then backed off to logical Z 6 (physical gap ~9 mm). Earlier the owner had jogged Y from the HMI while measuring (23:07:55–23:08:35Z) and returned it to Y150.

Source note: the decrypted 2.2.42 config (_zipcrypto_work) shows Loom's probe section matches `piezoelectric_ceramic_v2.0.cfg`, titled 机头压电陶瓷方案配置 (toolhead piezoelectric-ceramic scheme): the piezo is in the toolhead and its signal reaches main-MCU pin PF5. `PROBE_START`/`PROBE_END` (called by ALL_FANS_OFF/ON) are not registered commands in the running Klipper (HELP output).

## Owner-started nozzle-offset calibration, emergency stop

- 23:13:35Z the owner jogged Z to 150 from the HMI (Z was homed only by the
  SET_KINEMATIC_POSITION above) and at 23:14:59Z started `START_CALIBRATION`
  (nozzle offset) on the HMI.
- 23:15:35Z `Z homing start: travel=375.150 max_attempts=4`, attempt 1 from ~150 mm.
  No probe trigger. Moonraker's gcode store then shows
  `Z homing failed (No trigger on z after full movement), will retry`,
  `retry 1/3: cur Z=-0.100 lift 8.0 mm`, and `attempt 2` starting. INFERENCE from
  the timing (150 mm at 12 mm/s ≈ 12.5 s to contact, 375 mm ≈ 31 s full travel):
  the bed pressed against the nozzle with the Z motor stalling for roughly 18 s
  before the retry.
- **23:16:26Z `POST /printer/emergency_stop`** (Claude, during attempt 2, after
  confirming no probe result in the gcode store). Klipper is in shutdown until
  restarted.

- 23:18:02Z `FORCE_MOVE STEPPER=stepper_z DISTANCE=150 VELOCITY=10` (owner request "move z to 150"; Z unhomed after the e-stop restart, so a raw stepper move away from the nozzle: +Z lowers the bed, same direction as the vendor G28 clearance move) → {"result":"ok"}. Bed was ~0–8 mm below the nozzle at the e-stop (INFERENCE), so now ~150–158 mm.

## After the owner re-checked the toolhead (fan cable had been in the wrong socket), hand-push test

- Loom restarted; 23:34:36Z ready, unhomed, nozzles 36 °C, `QUERY_PROBE` → open.
- 23:35:55Z `SET_KINEMATIC_POSITION Z=1` then `PROBE SAMPLES=1 PROBE_SPEED=0.5`
  (5 mm of travel, bed ~145 mm below the nozzle). Owner pushed the left nozzle
  tip upward during the window. Result after 10.6 s: `!! No trigger on probe
  after full movement`.
- `M84` afterwards to clear the artificial homed state → {"result":"ok"}.
- 23:36:59Z repeat with the owner tapping sharply upward on the left, then the
  right, nozzle tip: `SET_KINEMATIC_POSITION Z=1`, `PROBE SAMPLES=1 PROBE_SPEED=0.5`
  → after 10.5 s `!! No trigger on probe after full movement`; `M84` → ok.
  Neither nozzle produces a trigger by hand: the fault is in the signal chain
  (sensor, its board, connector or wiring), not in bed-to-nozzle force transfer.

## Owner-run nozzle-offset calibration succeeds (23:39–23:48Z)

The owner had found the toolhead front-cover fan cable in the wrong toolhead-board
socket and re-plugged it before the hand tests. After the second hand test, the
owner started the calibration from the HMI.

- Z homing ran twice (23:38:58Z and 23:44:09Z by gcode-store time) and each
  finished on **attempt 1**: no `will retry` line, and the calibration went on.
  No `probe at …`/`Z homing probe check` lines appear in the gcode store for
  these runs.
- Result: `XYZ_ALIGN=1 x_offset=-32.988531 y_offset=0.034813 z_offset=2.656650`,
  `Update xyz offset config file success`, `calibration process finished`.
  Against 2026-09-17: X −33.073 → −32.989 (+0.084), Y +0.047 → +0.035,
  Z 2.654 → 2.657 (+0.003). The remove/clean/refit left the offsets essentially
  unchanged.

| Capture | Bytes | SHA-256 |
|---|---:|---|
| `GET /server/gcode_store?count=1000` → `moonraker-api/gcode-store-calibration/` | 60573 | `91d34f906f49c8fe863c34327e7c0fc00c1d47891ea2e84691fed6fa1b6e6669` |
| `GET /server/files/config/xyz_offset.ini` → `configs/xyz-offset/` | 172 | `6ac8ad4e0c0ba7ad891d1d8fca600e341bacc0ee1838cb8805ea0b466db774da` |

## Interpretation

- `CONFIRMED` (owner observation + timeline): with the fan cable in the wrong
  socket the Z probe never triggered (two HMI homings, one HMI calibration, one
  controlled `PROBE`). After re-plugging it, vendor homing works.
- `OPEN QUESTION`: the two hand-tap tests ran **after** the re-plug and still
  did not trigger. `INFERENCE`: those tests used a bare `PROBE`, whereas the
  vendor `G28` macro sets `SET_PIN PIN=servo_switch VALUE=0` (toolhead PB9) before
  homing, and hand taps are not a like-for-like load. The hand test is therefore
  **not a valid probe check** as run; do not reuse it without `servo_switch=0`.
- HMI error 10047 reads "Z axis homing false trigger", but the vendor error table
  (`error_info.xlsx`, 2.2.42) defines 10047 as `No trigger on %1 after full
  movement`; the English string is a mistranslation of 误触发.
- The vendor Z homing allows `travel=375.150` and 4 attempts, so a dead probe
  presses the bed into the nozzle for up to ~30 s per attempt before retrying.
- Session closed 23:5xZ. Loom: calibrated, idle.
