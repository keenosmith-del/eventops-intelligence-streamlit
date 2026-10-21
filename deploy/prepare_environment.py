"""Prepare private release inputs; never creates cloud resources or rotates existing keys."""

import argparse
import json
import os
import secrets
import subprocess
from pathlib import Path

from dotenv import dotenv_values

from deploy.check import ROOT, SECRETS

p = argparse.ArgumentParser()
p.add_argument("--output", type=Path, default=ROOT / "deploy/production.env")
p.add_argument("--site", required=True, help="Approved public HTTPS origin; no credential or database URL")
p.add_argument(
    "--approved-provider-env",
    type=Path,
    help="Explicitly copy only Gemini/Mailtrap inputs from this companion's approved file",
)
args = p.parse_args()
if (
    args.output.resolve().is_relative_to(ROOT)
    and subprocess.run(["git", "check-ignore", "-q", str(args.output.resolve())], cwd=ROOT).returncode
):
    raise SystemExit("Secrets inside this repository must use a Git-ignored path")
if args.output.exists():
    raise SystemExit(
        "Existing release file preserved. Edit deliberately; never regenerate an encryption key."
    )
if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
    raise SystemExit(
        "Commit/review the release inputs first; production metadata must identify a clean revision."
    )
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
values = dict(dotenv_values(ROOT / "deploy/production.env.example"))
values.update({name: secrets.token_urlsafe(36) for name in SECRETS})
values.update(APP_SITE=args.site, RELEASE_TAG=revision[:12], RELEASE_REVISION=revision)
if args.approved_provider_env:
    approved = dotenv_values(args.approved_provider_env)
    for name in (
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "MAILTRAP_API_TOKEN",
        "MAILTRAP_ACCOUNT_ID",
        "MAILTRAP_INBOX_ID",
    ):
        values[name] = approved.get(name) or values.get(name) or ""
args.output.parent.mkdir(parents=True, exist_ok=True)
fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as f:
    f.write("\n".join(k + "=" + json.dumps(v or "") for k, v in values.items()) + "\n")
(ROOT / "deploy/.local/workflows").mkdir(parents=True, exist_ok=True)
print("Private release inputs prepared. Add the NEW database URL privately; Gemini remains disabled.")
