# ADR 0015: Test the final release archive

- Status: Accepted
- Date: 2026-09-25

A source-tree test pass is not sufficient for a release. The final release ZIP must be created,
extracted into a fresh directory, and the complete cumulative pytest suite must be run from that
extracted tree. This catches stale, omitted, or differently packaged regression tests and files.
Package-version consistency (`pyproject.toml` and `toolspec.__version__`) remains a release gate.
