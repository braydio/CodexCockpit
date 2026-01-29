# Frameworks

Framework-driven execution is not implemented in this repository yet. The
control plane currently focuses on session-scoped execution and orchestration
runs via the driver interface.

## Planned Direction

Future framework support is expected to build on the orchestration layer and
introduce reusable, declarative workflows that map to driver sessions. When
that work begins, this document will define:

- The framework schema and validation rules.
- How frameworks map to orchestration plans and session runs.
- How framework steps declare definition-of-done requirements.

Until then, treat this document as a placeholder and reference
`docs/orchestration.md` for the current orchestration capabilities.
