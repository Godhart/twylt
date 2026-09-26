# ADR 0003: Cumulative regression test policy

- Status: Accepted
- Date: 2026-09-23

## Context

Version 0.2.0 introduced tests for new describe modes, but accidentally
replaced rather than extended the 0.1.x regression suite. This weakened
compatibility guarantees even though the package intended to preserve the
0.1.x API and execution contract.

## Decision

The project's automated test suite is cumulative across releases.

Tests from an earlier release must be retained in later releases, either
unchanged or adapted when implementation structure changes. A historical
test may be removed only when the corresponding public contract is
intentionally changed; that change must be documented in the changelog and
an ADR.

New feature tests extend the regression baseline and never silently replace
it.

The 0.1.x regression baseline covers at least:

- brief/schema/few_shots describe behavior;
- Pydantic input and output validation;
- input.json/output.json execution;
- describe modes not touching output.json;
- native exceptions producing a non-zero process exit and traceback;
- failed execution not leaving stale output.json.

## Consequences

The suite grows over time, but every release verifies both new behavior and
compatibility with established behavior. Refactors may adapt tests to new
internal structure but must preserve the observable contract.
