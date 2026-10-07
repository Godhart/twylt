# TWYLT 1.1.0 validation

Python 3.12: 116 tests passed, including 101 preserved regressions and 15 new
policy/transport/bootstrap tests (parameterized cases counted individually).
Wheel built and imported from an isolated venv; editable installation checked.

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python scripts/verify_package.py
```

The last command is a reproducible packaging check requiring pip access; during
preparation wheels were separately built and installed with no dependencies into
a venv using the runtime's Pydantic. Python 3.10/3.11 and Windows were not executed.
The protocol remains 1.8. Guardrails are cooperative checks, not OS isolation.
