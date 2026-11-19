import sys
import json
import urllib.request

REMOTE_URL = "https://axveritas.onrender.com/mcp"

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = urllib.request.Request(
        REMOTE_URL,
        data=line.encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            if body:
                sys.stdout.write(body + "\n")
                sys.stdout.flush()
    except Exception as e:
        err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(e)}}
        sys.stdout.write(json.dumps(err) + "\n")
        sys.stdout.flush()
