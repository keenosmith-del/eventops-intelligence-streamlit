"""Explicit local/hosted n8n publication. No cloud API, history reset or replay."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from dotenv import dotenv_values

from deploy.check import ROOT, compose_command, run_compose, validate_values
from scripts.validate_workflows import validate


def publish(env_file, rehearsal=False):
    values = dotenv_values(env_file)
    if validate_values(values, rehearsal):
        raise ValueError("Deployment preflight must pass before workflow publication")
    folder = ROOT / "deploy/.local/workflows"
    folder.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/build_workflows.py"),
            "--processor-url",
            "http://processor:8766",
            "--revision",
            values["RELEASE_REVISION"],
            "--output",
            str(folder),
        ],
        check=True,
    )
    manifest = {
        "revision": values["RELEASE_REVISION"],
        "processor_origin": "http://processor:8766",
        "files": {
            p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "nodes": validate(p)}
            for p in [folder / "verification.json", folder / "gemini-agent.json"]
        },
    }
    folder.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2))
    credentials = [
        {
            "id": "eventops-service",
            "name": "EventOps companion service",
            "type": "httpHeaderAuth",
            "data": {"name": "X-EventOps-Token", "value": values["EVENTOPS_SERVICE_TOKEN"]},
        },
        {
            "id": "eventops-webhook",
            "name": "EventOps webhook",
            "type": "httpHeaderAuth",
            "data": {"name": "X-EventOps-Webhook", "value": values["N8N_WEBHOOK_TOKEN"]},
        },
    ]
    if values.get("GEMINI_API_KEY"):
        credentials.append(
            {
                "id": "eventops-gemini",
                "name": "EventOps Gemini",
                "type": "googlePalmApi",
                "data": {
                    "host": "https://generativelanguage.googleapis.com",
                    "apiKey": values["GEMINI_API_KEY"],
                },
            }
        )
    command = compose_command(env_file, rehearsal)
    # Secret JSON is sent over stdin, stored only in container tmpfs, always removed.
    shell = "umask 077; trap 'rm -f /tmp/eventops-credentials.json' EXIT; cat > /tmp/eventops-credentials.json; n8n import:credentials --input=/tmp/eventops-credentials.json"
    run_compose(
        command + ["exec", "-T", "n8n", "sh", "-c", shell],
        input=json.dumps(credentials),
        text=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for filename in ("verification.json", "gemini-agent.json"):
        run_compose(
            command + ["exec", "-T", "n8n", "n8n", "import:workflow", "--input=/workflows/" + filename],
            check=True,
        )
    for wid in ("EventOpsVerify01", "EventOpsAgent01"):
        run_compose(command + ["exec", "-T", "n8n", "n8n", "publish:workflow", "--id=" + wid], check=True)
    run_compose(command + ["restart", "n8n", "runners"], check=True)
    print(json.dumps({"status": "published", "manifest": manifest, "replay": "never_automatic"}, indent=2))
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--env-file", type=Path, required=True)
    p.add_argument("--rehearsal", action="store_true")
    p.add_argument(
        "--publish", action="store_true", help="Explicitly import/rebind/publish into the chosen n8n"
    )
    args = p.parse_args()
    if not args.publish:
        p.error("Publication requires --publish; preserve previous workflow artifacts and back up n8n first")
    try:
        publish(args.env_file, args.rehearsal)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "publication_failed",
                    "category": type(exc).__name__,
                    "note": "Inspect private operator logs; no automatic replay",
                }
            )
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
