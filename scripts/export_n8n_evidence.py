"""Read a temporary local n8n SQLite snapshot; export only sanitized node metadata."""

import argparse
import json
import sqlite3
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("database")
parser.add_argument("--output", required=True)
parser.add_argument("--origin", default="Actual isolated Iteration 002 n8n records")
args = parser.parse_args()
con = sqlite3.connect(args.database)
executions = []
for eid, wid, status, start, stop, raw, workflow in con.execute(
    "SELECT e.id,e.workflowId,e.status,e.startedAt,e.stoppedAt,d.data,d.workflowData FROM execution_entity e JOIN execution_data d ON e.id=d.executionId ORDER BY e.id"
):
    pool = json.loads(raw)

    def resolve(v, ref=True, depth=0):
        if depth > 45:
            return None
        if ref and isinstance(v, str) and v.isdigit() and int(v) < len(pool):
            return resolve(pool[int(v)], False, depth + 1)
        if isinstance(v, dict):
            return {k: resolve(x, True, depth + 1) for k, x in v.items()}
        if isinstance(v, list):
            return [resolve(x, True, depth + 1) for x in v]
        return v

    result = resolve(pool[0], False)
    types = {n["name"]: n["type"] for n in json.loads(workflow)["nodes"]}
    nodes = [
        {
            "node": name,
            "type": types.get(name),
            "invocations": len(entries),
            "statuses": [e.get("executionStatus") for e in entries],
            "execution_ms": [e.get("executionTime") for e in entries],
        }
        for name, entries in result.get("resultData", {}).get("runData", {}).items()
    ]
    executions.append(
        {
            "execution_id": str(eid),
            "workflow_id": wid,
            "status": status,
            "started_at": start,
            "finished_at": stop,
            "nodes": nodes,
        }
    )
Path(args.output).write_text(
    json.dumps(
        {
            "origin": args.origin + "; only node metadata, no headers/credentials/model thoughts",
            "executions": executions,
        },
        indent=2,
    )
)
print("Sanitized executions:", len(executions))
