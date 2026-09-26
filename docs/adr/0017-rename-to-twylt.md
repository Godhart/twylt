# ADR 0017: Rename ToolSpec to TWYLT

- Status: Accepted
- Date: 2026-09-26

## Context

The name ToolSpec collides with existing software and, in particular, an existing Python package. A distinct project identity and package namespace are required before public publication.

## Decision

Rename the project and protocol to **TWYLT**, recursively expanded as **TWYLT Wraps Your Local Tool**.

The public Python distribution and import package are `twylt`; the specification is `TWYLT.md`. The first release under the new identity is TWYLT 1.0.0, succeeding ToolSpec 1.6.2.

Protocol-owned JSON error sources change from `toolspec` to `twylt`, so the protocol format advances from 1.7 to 1.8. Current environment variables are `TWYLT_DEBUG` and `TWYLT_ERROR_FORMAT`. The Python implementation accepts `TOOLSPEC_DEBUG` and `TOOLSPEC_ERROR_FORMAT` as transitional compatibility fallbacks, with the TWYLT names taking precedence.

Historical changelog entries and ADRs retain the names and versions that were current when those decisions were made.
