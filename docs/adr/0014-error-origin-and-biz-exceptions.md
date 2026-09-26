# ADR 0014: Error origin and business exceptions

- Status: Accepted
- Date: 2026-09-24

ToolSpec 1.7 makes JSON default. Errors identify `source` and `stage`. ToolSpec protocol failures exit 4; JSON-wrapped biz failures exit 5; input/output validation retain 2/3. Human mode preserves native biz exceptions. Only `Exception` is intercepted, not `BaseException`. Python reference: 1.6.0.
