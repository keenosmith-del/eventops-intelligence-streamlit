"""Create independent ignored local configuration. Never prints secrets."""

import argparse
import os
import secrets
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument(
    "--provider-env",
    type=Path,
    help="Read only Gemini and Mailtrap settings from an approved file",
)
args = parser.parse_args()
path = ROOT / ".env"
config = dict(dotenv_values(ROOT / ".env.example"))
if path.exists():
    config.update(dotenv_values(path))
if args.provider_env:
    approved = dotenv_values(args.provider_env)
    for key in (
        "GEMINI_API_KEY",
        "MAILTRAP_API_TOKEN",
        "MAILTRAP_ACCOUNT_ID",
        "MAILTRAP_INBOX_ID",
    ):
        if approved.get(key):
            config[key] = approved[key]
for key in (
    "EVENTOPS_SERVICE_TOKEN",
    "N8N_WEBHOOK_TOKEN",
    "N8N_ENCRYPTION_KEY",
    "COMPANION_POSTGRES_PASSWORD",
):
    if not config.get(key):
        config[key] = secrets.token_urlsafe(40)
config["GEMINI_ENABLED"] = config.get("GEMINI_ENABLED", "false")
path.write_text("\n".join(f"{k}={v}" for k, v in config.items()) + "\n")
os.chmod(path, 0o600)
print("Independent local configuration saved; provider credentials not displayed.")
