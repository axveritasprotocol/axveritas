"""Axveritas MCP stdio connector.

Bridges a local stdio MCP client to the hosted Axveritas server
(https://axveritas.com/mcp). Standard library only.

Set AXVERITAS_API_KEY to your key (free trial at https://axveritas.com)
so tool calls are authorized; listing tools works without a key.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

REMOTE_URL = os.environ.get("AXVERITAS_URL", "https://axveritas.com/mcp")
API_KEY = os.environ.get("AXVERITAS_API_KEY", "").strip()
if API_KEY:
    REMOTE_URL += ("&" if "?" in REMOTE_URL else "?") + urllib.parse.urlencode({"api_key": API_KEY})

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
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            if body:  # notifications get an empty 202 reply
                sys.stdout.write(body + "\n")
                sys.stdout.flush()
    except Exception as e:
        try:
            rpc_id = json.loads(line).get("id")
        except Exception:
            rpc_id = None
        err = {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32000, "message": str(e)}}
        sys.stdout.write(json.dumps(err) + "\n")
        sys.stdout.flush()
