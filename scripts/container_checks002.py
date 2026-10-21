"""Local full-stack restart and persistence checks; never prints credentials."""

import json
import subprocess
import time
from pathlib import Path


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def snapshot():
    code = """import hashlib,json
from eventops.store import Store
with Store().engine.connect() as c:
 rows=c.exec_driver_sql('SELECT id,kind,payload FROM companion_objects ORDER BY id').all()
 print(json.dumps({'objects':len(rows),'reviews':sum(r[1]=='review' for r in rows),'sha256':hashlib.sha256(repr(rows).encode()).hexdigest()}))
"""
    return json.loads(command("docker", "compose", "exec", "-T", "processor", "python", "-c", code))


before = snapshot()
subprocess.run(["docker", "compose", "restart"], check=True)
deadline = time.monotonic() + 60
while True:
    state = [json.loads(line) for line in command("docker", "compose", "ps", "--format", "json").splitlines()]
    if len(state) == 5 and all(s.get("Health") == "healthy" for s in state):
        break
    if time.monotonic() > deadline:
        raise RuntimeError("Full stack did not become healthy within 60 seconds")
    time.sleep(1)
after = snapshot()
assert before == after and before["reviews"] > 0
stats = [
    json.loads(line)
    for line in command("docker", "stats", "--no-stream", "--format", "{{json .}}").splitlines()
]
stats = [
    {k: r[k] for k in ("Name", "MemUsage", "CPUPerc")}
    for r in stats
    if r["Name"].startswith("eventops-companion-full-")
]
report = {
    "environment": "Local Docker Linux ARM64; one observation, not a hosted load benchmark",
    "restart_preserved_all_object_payloads": True,
    "before": before,
    "after": after,
    "services": [{"service": s["Service"], "health": s["Health"]} for s in state],
    "resource_sample": stats,
}
Path("docs/iterations/002/evidence/container-runtime.json").write_text(json.dumps(report, indent=2))
print("Five services healthy; all object payloads and reviews preserved across full restart.")
