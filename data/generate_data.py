"""Generate synthetic datasets for the HawkSightAI demo.

This script is a thin wrapper around the ``create_datasets``
function in ``hawksightai_project.tools.data_tools``.  Running this
file will regenerate the baseline and current CSV files in the
``data`` directory.  It can be useful if you wish to reset the
synthetic data or create a larger dataset.
"""

import argparse
import os

from ..tools.data_tools import create_datasets


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic datasets for HawkSightAI.")
    parser.add_argument("--base-dir", default="data", help="Directory to write CSV files to (default: data)")
    parser.add_argument("-n", type=int, default=500, help="Number of rows in the baseline dataset (default: 500)")
    args = parser.parse_args()
    create_datasets(base_dir=args.base_dir, n=args.n)
    print(f"Synthetic data written to {os.path.abspath(args.base_dir)}")


if __name__ == "__main__":
    main()