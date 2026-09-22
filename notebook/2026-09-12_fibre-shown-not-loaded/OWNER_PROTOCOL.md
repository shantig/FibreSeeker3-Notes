# Owner protocol — Loom fibre channel shown as not loaded

`EXPERIMENTAL` owner-performed diagnostic, prepared 2026-09-12 from
`DIAGNOSIS.md`. Not manufacturer guidance. Shant performs every step; Claude
does not operate Loom.

## F1 — read-only state check (step 2 performed; issue resolved — see `DIAGNOSIS.md` §7)

**Question:** does the controller's fibre presence switch agree with the
physical fibre, and what data does the HMI hold for the Fibre channel?

**Starting state:**
- Fibre loaded exactly as it is now; do not reload or unload first.
- No print, no load/unload flow running; heaters may be on or off (no heating
  needed).

**Action:**
1. In the G-code console, send `QUERY_FILAMENT_SENSOR SENSOR=filament_sensor`
   and copy the response.
2. On FibreTouch, open the filament screen, select the Fibre (X-CCF) ring and
   tap **Edit**. Photograph every field shown, including anything empty or
   "null". **Back out without saving.**
3. Note any other screen or popup that says the fibre is not loaded (photo, and
   what you were trying to do when it appeared).
4. Write down how the fibre was loaded and calibrated earlier: HMI Load flow
   to the end, manual feeding, calibration menu, or console commands; and how
   each flow ended (finished, cancelled, exited).

**Expected observations:** a line saying `filament_sensor` filament detected
or not detected; the Edit page fields for the Fibre channel.

**Hypotheses tested and reading:** see the table in `DIAGNOSIS.md` §5.
- Sensor detected → the problem is HMI state or spool data.
- Sensor not detected → the fibre presence switch.

**Evidence to record:** console text verbatim; Edit page photos; any
"not loaded" popup photos; the loading history from step 4; times.

**Stop conditions:**
- Do not press Load, Unload, Cut, or any fibre move while doing F1.
- Do not save changes on the Edit page.
- If any popup asks to perform an action (load, cut, calibrate), dismiss or
  cancel it and photograph it instead.
- Any console error: stop and copy it.

## After F1

Send Claude the results. A read-only klippy.log (and, if authorized,
moonraker.log) capture would show how the fibre load or calibration flow ended
(H3). Klipper also logs a `Fiber filament ran out` message whenever the fibre
switch drops out outside a print. Any such GET needs a new owner authorization.
