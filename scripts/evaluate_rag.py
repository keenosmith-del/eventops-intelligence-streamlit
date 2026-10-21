import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eventops.evaluation import evaluate
from eventops.rag import SemanticIndex

if __name__ == "__main__":
    start = time.perf_counter()
    index = SemanticIndex()
    initialization = time.perf_counter() - start
    dataset = json.loads(Path("data/evaluation/rag-v2.json").read_text())
    report = evaluate(index, dataset["cases"])
    report["environment"] = {
        "python": sys.version.split()[0],
        "index_initialization_seconds": initialization,
        "samples": 1,
        "model": "BAAI/bge-small-en-v1.5",
        "corpus_records": len(index.records),
    }
    Path("docs/iterations/002/evidence/rag-evaluation.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report["metrics"], indent=2))
