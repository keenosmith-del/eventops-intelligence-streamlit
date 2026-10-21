"""Minimal in-container checks. External provider availability is separate."""

import sys
import urllib.request

kind = sys.argv[1]
if kind == "processor":
    req = urllib.request.Request("http://127.0.0.1:8766/health")
else:
    req = urllib.request.Request("http://127.0.0.1:8090/health")
try:
    with urllib.request.urlopen(req, timeout=3) as response:
        assert response.status == 200
except Exception:
    raise SystemExit(1) from None
