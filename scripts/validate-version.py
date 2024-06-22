"""
Assert that various version strings all match.

such as:
- git tag
- pyproject.toml version
- documentation version const

Only intended to be used by CI pipeline.
"""
import argparse
import os
import sys
import toml
from pathlib import Path

__repo = Path(__file__).parent.parent

# make conf.py importable
sys.path.append(str(__repo / 'docs'))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--check-tag", action="store_true")

    args = parser.parse_args()

    import conf
    check_against = conf.release
    versions_to_match = {
        "docs": conf.release,  # docs version string
    }

    with open(__repo / "pyproject.toml", "r") as ppt:
        # project version string
        versions_to_match["pyproject"] = (toml.load(ppt)["project"]["version"])

    if args.check_tag:
        # git tag version in github workflows
        versions_to_match["git_tag"] = (os.environ.get("TAG", ""))

    if not all([v == check_against for v in versions_to_match.values()]):
        print(f"versions did not match: {versions_to_match}")
        sys.exit(1)

    print(f"version strings <{check_against}> OK")
