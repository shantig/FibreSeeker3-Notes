# Glossary

Shorthand used throughout this knowledge base.

## Names

- **FibreSeeker 3 / FS3** — the FibreSeek continuous-fibre composite printer this
  KB is about.
- **Loom** — the project owner's individual FibreSeeker 3. "Loom" findings are
  scoped to that one machine at a point in time, not the model in general.
- **Rocket** — FibreSeek's slicer (Rocket Slicer). Descends from Anisoprint's
  Aura.
- **Aura / Composer** — Anisoprint's slicer and printer line, the FS3's lineage.
- **FibreTouch / AnisoTouch** — the on-machine Qt/QML touchscreen HMI.
- **3ric** — another FS3 owner ([3ricj/FibreSeeker3](https://github.com/3ricj/FibreSeeker3)),
  whose reported bugs this KB cross-checks.

## The two print heads

The FS3 is a dual-head machine. In this KB:

- **Plastic 1 / CFC side** — the left head, 0.7 mm nozzle. The composite side:
  it lays down both continuous **Fibre** and Plastic. Klipper extruder for the
  plastic zone plus a separate Fibre zone (`extruder2`).
- **Plastic 2 / FFF side** — the right head, 0.4 mm nozzle. Plain plastic only.
- **Fibre** — the continuous carbon/glass fibre co-extruded on the CFC side.

## IDs and labels

- **X-CCF / X-CGF** — FibreSeek's continuous carbon / glass fibre filaments.
- **XNNNN** (e.g. `X0008`) — a physical sample ID. Every KB test print gets one,
  a registry entry in `experiments/Samples/samples.jsonl`, and a printed tag.
- **FS-###, AP-###, LM-###, CM-###, LX-###, BM-###** — provenance record IDs in
  `sources/manifest.jsonl` (FibreSeek official, Anisoprint official, Loom
  live-API captures, community, Loom physical-experiment sources, bed-mesh
  profiles).
- **T1, T2, …** — the Nth test within a dated notebook session.

## Evidence labels

- **CONFIRMED** — directly present in a preserved first-party source or capture.
- **STRONGLY INFERRED / INFERENCE** — reasoned from evidence, not stated by it.
- **OPEN QUESTION** — unresolved or needs testing.
- **EXPERIMENTAL** — locally measured/observed under recorded conditions; kept
  separate from manufacturer guidance.

## Provenance classes

Each source carries exactly one: `FIBRESEEK_OFFICIAL`, `ANISOPRINT_OFFICIAL`,
`ACADEMIC`, `PATENT`, `COMMUNITY`, `INFERRED`, `EXPERIMENTAL`. See
[../sources/SOURCE_POLICY.md](../sources/SOURCE_POLICY.md).
