# ADR: Cooperative guardrails in TWYLT 1.1.0

Accepted, 2026-10-07. Generic policy and transport checks belong to TWYLT;
pack business helpers remain in their pack. Policy is opt-in in TWYLT and enabled
in image defaults. The allowed cwd root includes descendants but grants only
transport access in the actual cwd, not business filesystem access. No interception
of arbitrary Python/OS operations is claimed. Security remains the tool author's
responsibility; isolation belongs to OS/runner. Avoid duplicated implementations.
