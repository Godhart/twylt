from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "examples" / "list_directory"))
from tool import Input, ListDirectory


def test_list_directory(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub").mkdir()
    result = ListDirectory().biz(Input(path=str(tmp_path)))
    assert [(x.name, x.is_dir) for x in result.entries] == [
        ("a.txt", False),
        ("sub", True),
    ]
