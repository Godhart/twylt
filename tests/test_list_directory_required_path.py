import json
import os
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "list_directory" / "tool.py"

def _run(*args):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    runner = ROOT / ".twylt_example_test_runner.py"
    src = str(ROOT / "src")
    purelib = sysconfig.get_paths()["purelib"]
    runner.write_text(
        "import sys,runpy\n"
        f"sys.path[:0]=[{src!r},{purelib!r}]\n"
        f"sys.argv=[{str(EXAMPLE)!r}]+sys.argv[1:]\n"
        f"runpy.run_path({str(EXAMPLE)!r},run_name='__main__')\n",
        encoding="utf-8",
    )
    try:
        return subprocess.run(
            [sys.executable, "-S", str(runner), *args],
            cwd=ROOT, env=env, text=True, capture_output=True
        )
    finally:
        runner.unlink(missing_ok=True)

def test_list_directory_schema_requires_path():
    result=_run('{"describe":"schema"}')
    assert result.returncode==0
    schema=json.loads(result.stdout)["inputSchema"]
    assert "path" in schema["required"]
    assert schema["properties"]["path"]["description"] == "Directory to list"

def test_list_directory_missing_path_is_validation_error():
    result=_run("{}")
    assert result.returncode==2
    error=json.loads(result.stderr)["error"]
    assert error["source"]=="twylt"
    assert error["stage"]=="input"
    assert any(e["path"]=="path" and e["code"]=="required" for e in error["errors"])
