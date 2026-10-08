# ADR: Self-contained examples — TWYLT 1.1.1

Accepted, 2026-10-08. Examples illustrate cooperative controls rather than embed
policy implementations. Listing resolves the requested path and inspects children
before any is_dir may follow a link. Ping checks network before spawning a system
process. Echo has no business guardrails; common file-transport policy still applies.
Ping and echo copy only their own pedagogical contract/business code from essential
0.2.0; no pack dependency or unrelated helper code. Protocol/schema versions remain
separate from package release version. Runtime guardrails API is unchanged.
