"""Create a mode-0600, ignored credential import. Import and immediately delete it."""

import json
import os
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
config = dotenv_values(ROOT / ".env")
items = [
    {
        "id": "eventops-service",
        "name": "EventOps companion service",
        "type": "httpHeaderAuth",
        "data": {"name": "X-EventOps-Token", "value": config["EVENTOPS_SERVICE_TOKEN"]},
    },
    {
        "id": "eventops-webhook",
        "name": "EventOps webhook",
        "type": "httpHeaderAuth",
        "data": {"name": "X-EventOps-Webhook", "value": config["N8N_WEBHOOK_TOKEN"]},
    },
]
if config.get("GEMINI_API_KEY"):
    items.append(
        {
            "id": "eventops-gemini",
            "name": "EventOps Gemini",
            "type": "googlePalmApi",
            "data": {"host": "https://generativelanguage.googleapis.com", "apiKey": config["GEMINI_API_KEY"]},
        }
    )
folder = ROOT / "n8n/.local"
folder.mkdir(exist_ok=True)
path = folder / "credentials.json"
path.write_text(json.dumps(items))
os.chmod(path, 0o600)
print("Ignored credential import prepared; delete after import.")
