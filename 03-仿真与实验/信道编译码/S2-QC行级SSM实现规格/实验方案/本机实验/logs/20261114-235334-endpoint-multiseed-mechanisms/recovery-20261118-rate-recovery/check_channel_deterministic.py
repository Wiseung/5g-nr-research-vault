from pathlib import Path
import sys,runpy
LOCAL=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(LOCAL))
from formal_core import configure
configure()
runpy.run_path(str(LOCAL/'check_channel.py'),run_name='__main__')
