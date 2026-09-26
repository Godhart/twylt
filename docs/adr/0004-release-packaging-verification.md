# ADR 0004: Release packaging verification

- Status: Accepted
- Date: 2026-09-23

## Context

0.2.1 passed source-level tests but Hatchling could not infer that distribution
`toolspec` must package `src/toolspec`. Pytest's `pythonpath = ["src"]`
masked this packaging error.

## Decision

Declare wheel contents explicitly:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/toolspec"]
```

Release verification is cumulative: run the complete historical pytest suite,
then perform a real PEP 517 wheel build, install that wheel in a clean virtual
environment and import it, and independently run `pip install -e '.[test]'` in another
clean environment and import it.

A release is not verified until both source regression tests and packaging
verification pass.

## Consequences

Broken wheel/editable metadata can no longer be hidden by source-level imports.
Packaging verification is slower and can require access to dependency indexes.
