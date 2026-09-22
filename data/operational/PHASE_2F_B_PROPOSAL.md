# Phase 2F-B Proposal (Implemented)

This proposal was authorized and implemented from immutable Phase 2F-A commit
`d49899368227979c9ea743ed09fff9b4bba06c88`. The completed methodology,
evidence, question statuses, limitations, and remaining validation plan are in
`PHASE_2FB.md`. This file is retained as the pre-implementation scope record.

Phase 2F-B should be a separately authorized FibreSeek-focused validation pass,
not more analog accumulation. Recommended scope:

1. Exhaust static FibreSeek/Rocket manuals, resources, profile schemas, UI
   strings, and packages against the 22-question backlog.
2. Add deterministic offline Rocket test cases only if explicitly authorized:
   no printer connection, no hardware control, and captured inputs/outputs.
3. Resolve macrolayer scheduling, minimum path filters, support cadence, and
   cutter-field precedence using boundary-value profiles and generated G-code.
4. Promote a concept only when direct FibreSeek evidence supports it; retain
   analog records unchanged and add new FibreSeek records separately.
5. Prepare, but do not automatically perform, vendor questions and physical
   experiments for remaining dead distances, calibration acceptance, and
   material limits.

Phase 2F-B should not add RAG, embeddings, semantic search, autonomous agents,
hardware control, or a redesign of the accepted query/LLM architecture.
