#!/usr/bin/env python3
"""Download & verify a remote e2e image corpus (GitHub Release asset).

The heavy PNG corpus is NOT committed; it lives as a tarball on a GitHub Release.
This tool fetches it into a git-ignored local dir, checks the SHA256 pinned in
tests/data/datasets.json, and extracts it. Idempotent: skips the download if the
target dir already holds a manifest (use --force to refetch).

Usable both as a CLI and as a library (`fetch(...)`) from the test fixture.

CLI:
    python tools/fetch_corpus.py                 # -> tests/data/synthetic_large
    python tools/fetch_corpus.py --dataset synthetic_v1 --dest /some/dir
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
DATASETS_JSON = _REPO / "tests" / "data" / "datasets.json"
DEFAULT_DEST = _REPO / "tests" / "data" / "synthetic_large"


def _load(dataset: str) -> dict:
    meta = json.loads(DATASETS_JSON.read_text())
    if dataset not in meta:
        raise KeyError(f"dataset {dataset!r} not in {DATASETS_JSON} "
                       f"(have: {', '.join(meta)})")
    return meta[dataset]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(dataset: str = "synthetic_v1", dest: Path | str | None = None,
          force: bool = False, quiet: bool = False) -> Path:
    """Ensure the dataset is present at `dest`; return the dir. Verifies SHA256."""
    dest = Path(dest) if dest else DEFAULT_DEST
    if (dest / "manifest.csv").exists() and not force:
        return dest

    info = _load(dataset)
    dest.mkdir(parents=True, exist_ok=True)
    if not quiet:
        print(f"fetching {dataset} <- {info['url']}")

    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        urllib.request.urlretrieve(info["url"], tmp_path)
        got = _sha256(tmp_path)
        if got != info["sha256"]:
            raise ValueError(
                f"SHA256 mismatch for {dataset}: expected {info['sha256']}, got {got}")
        with tarfile.open(tmp_path, "r:gz") as tar:
            # The 'data' filter refuses members that would escape `dest` via
            # absolute paths or '..' (CVE-2007-4559). It is the default from
            # Python 3.14 and available from 3.12; this project supports 3.8+,
            # so ask for it only where it exists. The tarball is SHA256-pinned
            # above, so this is defence in depth rather than the primary check.
            if hasattr(tarfile, "data_filter"):
                tar.extractall(dest, filter="data")
            else:
                tar.extractall(dest)
    finally:
        tmp_path.unlink(missing_ok=True)

    n = len(list(dest.glob("*.png")))
    if not quiet:
        print(f"extracted {n} images to {dest} (sha256 ok)")
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="synthetic_v1")
    ap.add_argument("--dest", default=None, help=f"target dir (default {DEFAULT_DEST})")
    ap.add_argument("--force", action="store_true", help="refetch even if present")
    args = ap.parse_args()
    path = fetch(args.dataset, args.dest, args.force)
    print(path)


if __name__ == "__main__":
    main()
