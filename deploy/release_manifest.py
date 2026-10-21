"""Checksums of release inputs only; never includes .env, storage or credential files."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from deploy.check import ROOT


def manifest():
    paths = set()
    for pattern in (
        "app.py",
        "Dockerfile",
        "requirements*.txt",
        "eventops/*.py",
        "scripts/build_workflows.py",
        "n8n/*.json",
        "deploy/*.py",
        "deploy/*.yaml",
        "deploy/*.Dockerfile",
        "deploy/Caddyfile",
        "deploy/*.env.example",
        ".github/workflows/quality.yml",
        ".dockerignore",
    ):
        paths.update(ROOT.glob(pattern))
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    return {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "working_tree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        ),
        "files": hashes,
        "source_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
        "deployment": "not_performed",
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = manifest()
    if args.output:
        args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "files"}, indent=2))
