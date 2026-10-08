import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'llm-core'))
import analyze
analyze.ROOT=Path(__file__).resolve().parent
sys.argv=['analyze','core'];analyze.main()
