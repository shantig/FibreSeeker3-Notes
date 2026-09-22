# FibreSeeker 3 Knowledge Base

An evidence-first knowledge base for running the **FibreSeek FibreSeeker 3**
continuous-fibre composite printer (CFC). The FibreSeeker 3 and its Rocket
slicer descend from Anisoprint's Composer and Aura; the official documentation
is thin, so this repository works out how the machine and its software actually
behave and writes it down with the evidence attached.

It is one owner's working notebook for a machine nicknamed **Loom**, plus a
reverse-engineered data model of the Rocket/Aura slicer settings. Where a claim
can't be backed by first-party evidence, it says so.

## Start here

- **[docs/findings.md](docs/findings.md)** — the practical findings, each
  labelled and linked to its evidence. Start here if you own an FS3.
- **[docs/loom/](docs/loom/)** — how the machine works: architecture, macros,
  the print-start sequence and state machine, calibration.
- **[docs/firmware/](docs/firmware/)** — static firmware analysis and the
  2.2.30 → 2.2.42 version diff.
- **[notebook/](notebook/)** — dated calibration and troubleshooting sessions.
- **[docs/glossary.md](docs/glossary.md)** — the shorthand (Loom, Plastic 1/2,
  sample IDs, evidence labels).
- **[docs/how-this-kb-works.md](docs/how-this-kb-works.md)** — the evidence
  model, provenance ledger, and the query/data layer.

## Evidence labels

Every non-obvious claim carries one:

- **CONFIRMED** — directly present in a preserved first-party source or capture.
  A Loom observation is time- and machine-scoped; it is not automatically true
  of every FS3.
- **INFERENCE / STRONGLY INFERRED** — reasoned from evidence, not stated by it.
- **OPEN QUESTION** — unresolved or needs testing.
- **EXPERIMENTAL** — a locally measured or observed result under recorded
  conditions, kept separate from manufacturer guidance.

FibreSeek-specific guidance requires FibreSeek evidence. Legacy Anisoprint
material is preserved for comparison but is never silently promoted into
FibreSeek guidance.

## Using the tools

Everything is standard-library Python 3 (only `tools/extract_pdf_text.py` needs
`pypdf`). No build step.

```bash
# Run the test suite
python3 -m unittest discover -s tools/tests -p 'test_*.py'

# Build the disposable query index, then ask the KB a question
python3 tools/query_kb.py index rebuild
python3 tools/query_kb.py answer "What temperature for X-CCF?"
```

See [docs/how-this-kb-works.md](docs/how-this-kb-works.md) for the query layer,
view modes, and the deterministic-safety design.

## Layout

| Path | What's in it |
|---|---|
| `docs/` | Human-readable findings (machine, firmware, slicer, community). |
| `notebook/` | Dated calibration, test-print, and troubleshooting sessions. |
| `experiments/` | Physical-experiment records and the sample-ID registry. |
| `data/` | The normalized Rocket/Aura data model and operational-knowledge corpus. |
| `sources/` | Provenance ledger, source policy, and preserved raw evidence. |
| `tools/` | Extractors, generators, the query/agent/LLM layers, validators, tests. |
| `project/` | Project state (`STATUS`, `TODO`, `NEXT_HANDOFF`) and history. |

## Scope and status

This is a live, working knowledge base maintained by the owner with an AI
coding assistant. Findings are dated and evidence-linked; treat the Loom
observations as one machine's behaviour, not a spec. Contributions and
corrections from other FS3 owners are welcome — please keep the evidence
labels.
