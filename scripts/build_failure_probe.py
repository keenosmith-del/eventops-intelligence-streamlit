"""Generate a local-only diagnostic workflow; actual HTTP failures, no provider simulation claims."""

import json
from pathlib import Path

base = json.loads(Path("n8n/verification.json").read_text())
base["id"] = "EventOpsFailureProbe"
base["name"] = "EventOps · controlled HTTP failure diagnostics"
for n in base["nodes"]:
    if n["name"] == "Verification webhook":
        n["parameters"]["path"] = "eventops-failure-probe"
        n["webhookId"] = "eventops-failure-probe"
    if n["name"] == "Validate and reserve request":
        n["parameters"]["jsonBody"] = (
            "={{ {owner:$json.body.owner,request_id:$json.body.request_id,event_id:'EVT-101',limit:5,scenario:'assessment_event',execution_id:$execution.id} }}"
        )
    if n["name"] == "Read Calendar":
        n["parameters"]["url"] = (
            "={{ $('Verification webhook').first().json.body.probe === 'invalid_calendar' ? 'http://scenario:8090/malformed' : $('Allowed source configuration').first().json.calendar }}"
        )
    if n["name"] == "Read Web":
        n["parameters"]["url"] = (
            "={{ ({http401:'http://scenario:8090/http401',http403:'http://scenario:8090/http403',http429:'http://scenario:8090/http429',http500:'http://scenario:8090/http500',timeout:'http://scenario:8090/slow',malformed:'http://scenario:8090/malformed',dns:'http://eventops-synthetic-unresolvable.invalid/records'})[$('Verification webhook').first().json.body.probe] || $('Allowed source configuration').first().json.web }}"
        )
        n["parameters"]["options"]["timeout"] = 1000
    if n["name"] == "Extract Web":
        n["parameters"]["url"] = (
            "={{ $('Verification webhook').first().json.body.probe === 'processing_unavailable' ? 'http://scenario:8090/unavailable' : 'http://processor:8766/stages/extract' }}"
        )
path = Path("n8n/.local/failure-probe.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(base, indent=2))
print("Local-only controlled failure probe generated; not an external provider workflow.")
