from pathlib import Path
from eda.src.pipeline.run_eda import run

if __name__ == "__main__":
    eda_root = Path(__file__).resolve().parents[1]
    run(eda_root)