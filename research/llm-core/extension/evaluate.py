"""Configure the same frozen scorer for a separate extension output root."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import analyze
analyze.ROOT=Path(__file__).resolve().parent
sys.argv=['analyze','core'];analyze.main()
