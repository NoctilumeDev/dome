"""Run the unchanged core collector against a new, separately frozen root."""
import sys
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'llm-core'))
import run as collector
collector.ROOT=R
if __name__=='__main__':collector.main()
