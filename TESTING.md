# TWYLT 1.1.1 validation

Python 3.12: 127 tests passed (116 previous regression cases and 11 new example cases).
The examples are based on GitHub TWYLT commit 4de2805d73df81b4eadb405e0bca7fe8e5c0dbc5.
Ping/echo were adapted from GitHub essential 0.2.0, commit
488e1a78f0400161884cd8034409b9d733880394, without a pack dependency.

New tests cover virtual directory paths, traversal, a requested symlink, a child
symlink checked before is_dir, network denial before executable discovery, safe
ping arguments, timeout and copied standalone examples. CLI echo remains usable
with network disabled. Ping is mocked; actual ICMP and Windows were not tested.

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python scripts/verify_package.py
```

Wheel build and CLI smoke from a separate venv are checked separately during release
preparation. The verifier above is also provided for a full dependency installation.
Python 3.10/3.11 and Windows were not executed. TWYLT protocol remains 1.8.
