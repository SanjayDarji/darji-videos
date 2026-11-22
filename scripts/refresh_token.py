#!/usr/bin/env python3
"""Refresh the long-lived Instagram token and write the new one to the file in argv[1].

Instagram tokens last 60 days and can be refreshed once they are at least 24 hours old.
The workflow then stores the new token back as the IG_ACCESS_TOKEN secret.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
if not token or len(sys.argv) != 2:
    sys.exit("Usage: IG_ACCESS_TOKEN=... refresh_token.py <output-file>")

query = urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": token})
try:
    with urllib.request.urlopen(f"https://graph.instagram.com/refresh_access_token?{query}", timeout=60) as resp:
        data = json.loads(resp.read().decode())
except urllib.error.HTTPError as err:
    sys.exit(f"Token refresh failed with HTTP {err.code}: {err.read().decode(errors='replace')}")

new_token = data["access_token"]
print(f"::add-mask::{new_token}")
with open(sys.argv[1], "w", encoding="utf-8") as f:
    f.write(new_token)
print(f"Token refreshed. Valid for about {data.get('expires_in', 0) // 86400} days.")
