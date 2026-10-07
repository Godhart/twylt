# Migration to TWYLT 1.1.0

This is an additive Python implementation release; TWYLT protocol stays 1.8.
Existing tools retain their behavior with TWYLT_GUARDRAILS unset. Existing copies
of pack-specific Workspace policies are unaffected until those packs migrate.
Do not assume the environment flag disables guardrails embedded in older packs.

Install this release from the supplied source or wheel; it has not been published
by this task. Install essential 0.2.0 in the same Python environment as the runner.
Remove copied guardrails and WorkspaceTransport inheritance from migrated tools.
Use twylt.guardrails.Workspace/check_network in business operations. Built-in
file transport checks now belong to Tool.run(), including removal of old output.

The saved baseline was twylt-1.0.0.zip. GitHub was inaccessible during preparation;
reconcile repository-only changes before applying this release to a newer branch.

See docs/GUARDRAILS.md for all environment variables, cwd subtree semantics,
cooperative enforcement limits and exit code 6. Tests include original regressions.
