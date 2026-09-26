import json
import os
import subprocess
import sys
import sysconfig
from pathlib import Path


def _run_script(tmp_path, body, *args):
    script = tmp_path / "tool_script.py"
    script.write_text(body, encoding="utf-8")
    env = os.environ.copy()
    # The test subprocess must exercise TWYLT only. Some host environments
    # inject Python startup hooks via PYTHONPATH/sitecustomize which can write
    # unrelated diagnostics to stderr and invalidate the wire-protocol check.
    src = str(Path(__file__).parents[1] / "src")
    site_packages = sysconfig.get_paths()["purelib"]
    wrapper = tmp_path / "runner.py"
    wrapper.write_text(
        "import sys,runpy\n"
        f"sys.path[:0] = [{src!r}, {site_packages!r}]\n"
        f"sys.argv = [{str(script)!r}] + sys.argv[1:]\n"
        f"runpy.run_path({str(script)!r}, run_name='__main__')\n",
        encoding="utf-8",
    )
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [sys.executable, "-S", str(wrapper), *args],
        cwd=tmp_path, env=env, text=True, capture_output=True
    )


SCRIPT = """
from pydantic import BaseModel
from twylt import Tool

class I(BaseModel):
    x: int

class O(BaseModel):
    y: int

class T(Tool[I, O]):
    input_model = I
    output_model = O
    def biz(self, data):
        raise RuntimeError("native boom")

T.run()
"""


def _input(tmp_path):
    (tmp_path / "input.json").write_text('{"x": 1}', encoding="utf-8")


def test_biz_exception_default_json_regression(tmp_path):
    _input(tmp_path)
    result = _run_script(tmp_path, SCRIPT)
    assert result.returncode == 5
    assert result.stdout == ""
    error = json.loads(result.stderr)["error"]
    assert error["type"] == "execution_error"
    assert error["source"] == "tool"
    assert error["stage"] == "biz"
    assert error["exception"] == {"type": "RuntimeError", "message": "native boom"}
    assert "traceback" not in error


def test_biz_exception_json_debug_has_traceback_regression(tmp_path):
    _input(tmp_path)
    result = _run_script(tmp_path, SCRIPT, "--debug")
    assert result.returncode == 5
    error = json.loads(result.stderr)["error"]
    assert "Traceback" in error["traceback"]
    assert "native boom" in error["traceback"]


def test_biz_exception_human_preserves_native_traceback_regression(tmp_path):
    _input(tmp_path)
    result = _run_script(tmp_path, SCRIPT, "--error-format", "human")
    assert result.returncode != 0
    assert "Traceback" in result.stderr
    assert "RuntimeError" in result.stderr
    assert "native boom" in result.stderr


def test_native_exception_does_not_write_output_regression(tmp_path):
    _input(tmp_path)
    result = _run_script(tmp_path, SCRIPT)
    assert result.returncode == 5
    assert not (tmp_path / "output.json").exists()


def test_native_exception_removes_stale_output_regression(tmp_path):
    _input(tmp_path)
    (tmp_path / "output.json").write_text('{"stale": true}', encoding="utf-8")
    result = _run_script(tmp_path, SCRIPT)
    assert result.returncode == 5
    assert not (tmp_path / "output.json").exists()
