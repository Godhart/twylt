from __future__ import annotations
import os, shutil, subprocess, sys, tempfile, venv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def run(cmd, cwd=ROOT):
    print("+", " ".join(map(str,cmd)))
    subprocess.run(list(map(str,cmd)),cwd=cwd,check=True)
def py(v):
    return v/("Scripts/python.exe" if os.name=="nt" else "bin/python")
def main():
    dist=ROOT/"dist"
    if dist.exists(): shutil.rmtree(dist)
    dist.mkdir()
    run([sys.executable,"-m","pip","wheel",".","--no-deps","--wheel-dir",str(dist)])
    wheels=list(dist.glob("twylt-*.whl"))
    assert len(wheels)==1, wheels
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        v1=td/"wheel"; venv.EnvBuilder(with_pip=True).create(v1)
        run([py(v1),"-m","pip","install",str(wheels[0])])
        run([py(v1),"-c","import twylt; assert twylt.__version__=='1.1.0'; print('wheel OK')"])
        v2=td/"editable"; venv.EnvBuilder(with_pip=True).create(v2)
        run([py(v2),"-m","pip","install","-e",".[test]"])
        run([py(v2),"-c","import twylt; assert twylt.__version__=='1.1.0'; print('editable OK')"])
    print("Packaging verification passed")
if __name__=="__main__": main()
