"""基线快捷入口，复用统一入口的全部参数。"""
from pathlib import Path
import subprocess
import sys
if __name__=='__main__':
    raise SystemExit(subprocess.call([sys.executable,str(Path(__file__).resolve().parents[1]/'agent/run.py'),
                                     '--framework','baseline',*sys.argv[1:]]))
