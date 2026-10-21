import json
from pathlib import Path


def validate(path):
    graph = json.loads(path.read_text())
    nodes = {n["name"]: n for n in graph["nodes"]}
    assert len(nodes) == len(graph["nodes"])
    for source, ports in graph["connections"].items():
        assert source in nodes
        for branches in ports.values():
            for branch in branches:
                for connection in branch:
                    assert connection["node"] in nodes
    for n in nodes.values():
        assert "$env" not in json.dumps(n), "Workflow nodes must not read environment variables"
        if n["type"].endswith(".webhook"):
            assert n["parameters"]["authentication"] == "headerAuth"
    if path.name == "verification.json":
        for source in ["Calendar", "Email", "Web"]:
            assert nodes["Read " + source]["onError"] == "continueRegularOutput"
            assert nodes["Extract " + source]["onError"] == "continueRegularOutput"
            assert "Checkpoint " + source in nodes
    else:
        assert nodes["Gemini read-only analyst"]["type"] == "@n8n/n8n-nodes-langchain.agent"
        assert len([n for n in nodes.values() if n["type"].endswith(".toolCode")]) == 3
    return len(nodes)


if __name__ == "__main__":
    for path in Path("n8n").glob("*.json"):
        print(path.name, validate(path), "nodes validated; import/execution evidence is separate")
