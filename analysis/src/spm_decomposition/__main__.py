"""CLI entry point: python -m spm_decomposition"""

import json
import sys
from pathlib import Path

from .decomposition import run_decomposition


def main():
    output_dir = Path(__file__).parent.parent.parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "decomposition.json"

    print("Running SPM child poverty decomposition...")
    result = run_decomposition()

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nOutput written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
