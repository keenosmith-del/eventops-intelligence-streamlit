import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eventops.rag import SemanticIndex

index = SemanticIndex()
print(f"Validated and indexed {len(index.records)} records, vectors {index.vectors.shape}")
print(f"Source/model fingerprint: {index.signature}")
