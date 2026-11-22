#!/usr/bin/env python3
"""Post the next due Reel from reels/ to Instagram.

Uses Meta's Instagram API through graph.facebook.com (Facebook Login or Unified Login
tokens), standard library only. Set GRAPH_HOST=graph.instagram.com for an old-style
Instagram Login token.

Folder layout: reels/YYYY-MM-DD_slug/video.mp4 and reels/YYYY-MM-DD_slug/caption.txt
A reel is "due" once its date (India time) has arrived. One reel is posted per day.

Environment:
  IG_ACCESS_TOKEN  Page or system-user access token (not needed for a dry run)
  IG_USER_ID       Instagram professional account id (not needed for a dry run)
  REEL             folder name under reels/ to post right now (optional)
  DRY_RUN          "true" checks everything but posts nothing
  REPO             owner/name, used to build the public video URL
  COMMIT_SHA       commit the video URL is pinned to (optional)
  IG_API_VERSION   Graph API version (default v27.0)
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REELS = os.path.join(ROOT, "reels")
LOG = os.path.join(ROOT, "posted.json")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
VERSION = os.environ.get("IG_API_VERSION", "v27.0")
HOST = os.environ.get("GRAPH_HOST", "").strip() or "graph.facebook.com"
BASE = f"https://{HOST}/{VERSION}"


def log(msg):
    print(msg, flush=True)


def load_state():
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            return json.load(f)
    return {"posted": {}}


def save_state(state):
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def reel_date(name):
    try:
        return dt.date.fromisoformat(name[:10])
    except ValueError:
        return None


def list_reels():
    names = []
    for name in sorted(os.listdir(REELS)):
        folder = os.path.join(REELS, name)
        if (
            os.path.isdir(folder)
            and reel_date(name)
            and os.path.exists(os.path.join(folder, "video.mp4"))
            and os.path.exists(os.path.join(folder, "caption.txt"))
        ):
            names.append(name)
    return names


def pick(state, today):
    forced = os.environ.get("REEL", "").strip()
    names = list_reels()
    if forced:
        if forced not in names:
            sys.exit(f"Reel '{forced}' not found (it needs video.mp4 and caption.txt).")
        if forced in state["posted"]:
            sys.exit(f"'{forced}' was already posted.")
        return forced
    if any(v.get("posted_on") == today.isoformat() for v in state["posted"].values()):
        log("A reel was already posted today. Nothing to do.")
        return None
    due = [n for n in names if n not in state["posted"] and reel_date(n) <= today]
    return due[0] if due else None


def call(method, url, token, body=None, fatal=True):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as err:
        detail = err.read().decode(errors="replace")
        msg = f"Instagram API error {err.code} on {method} {url.split('?')[0]}: {detail}"
        if fatal:
            sys.exit(msg)
        log(msg)
        return {}


def video_urls(name):
    repo = os.environ.get("REPO", "SanjayDarji/darji-videos")
    sha = os.environ.get("COMMIT_SHA", "").strip()
    path = f"reels/{name}/video.mp4"
    urls = []
    if sha:
        urls.append(f"https://cdn.jsdelivr.net/gh/{repo}@{sha}/{path}")
    urls.append(f"https://raw.githubusercontent.com/{repo}/main/{path}")
    return urls


def reachable(url):
    req = urllib.request.Request(url, headers={"Range": "bytes=0-0", "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            log(f"  {url} -> {resp.status} {resp.headers.get('Content-Type', '')}")
            return resp.status in (200, 206)
    except Exception as err:  # noqa: BLE001 - report any failure and try the next URL
        log(f"  {url} -> {err}")
        return False


def check_caption(caption):
    if "SEBI" not in caption:
        sys.exit("Caption must carry the SEBI / educational-only notice. Refusing to post.")
    if len(caption) > 2200:
        sys.exit(f"Caption is {len(caption)} characters; Instagram allows 2,200.")
    if caption.count("#") > 30:
        sys.exit("Caption has more than 30 hashtags; Instagram allows 30.")


def main():
    today = dt.datetime.now(IST).date()
    dry_run = os.environ.get("DRY_RUN", "").lower() == "true"
    state = load_state()

    name = pick(state, today)
    if not name:
        log(f"No reel is due on {today}.")
        return
    log(f"Reel: {name}")

    with open(os.path.join(REELS, name, "caption.txt"), encoding="utf-8") as f:
        caption = f.read().strip()
    check_caption(caption)

    log("Checking the public video URL:")
    url = next((u for u in video_urls(name) if reachable(u)), None)
    if not url:
        if dry_run:
            log("Dry run: no public URL is reachable yet (push the video to main first).")
        else:
            sys.exit("The video is not reachable at a public URL. Not posting.")

    if dry_run:
        log("Dry run finished. Nothing was posted.")
        return

    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not token:
        sys.exit("IG_ACCESS_TOKEN is not set. Add it under Settings > Secrets and variables > Actions.")
    ig = os.environ.get("IG_USER_ID", "").strip()
    if not ig:
        sys.exit("IG_USER_ID is not set. Add the Instagram account ID as a repository secret.")

    container = call(
        "POST",
        f"{BASE}/{ig}/media",
        token,
        {"media_type": "REELS", "video_url": url, "caption": caption, "share_to_feed": True},
    )["id"]
    log(f"Container created: {container}")

    for _ in range(40):  # about 10 minutes
        time.sleep(15)
        status = call("GET", f"{BASE}/{container}?fields=status_code,status", token)
        code = status.get("status_code")
        log(f"  status: {code}")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram could not process the video: {status}")
    else:
        sys.exit("Timed out waiting for Instagram to process the video.")

    media_id = call("POST", f"{BASE}/{ig}/media_publish", token, {"creation_id": container})["id"]
    permalink = call("GET", f"{BASE}/{media_id}?fields=permalink", token, fatal=False).get("permalink")
    log(f"Published: {permalink or media_id}")

    state["posted"][name] = {
        "media_id": media_id,
        "permalink": permalink,
        "posted_on": today.isoformat(),
        "posted_at": dt.datetime.now(IST).isoformat(timespec="seconds"),
    }
    save_state(state)


if __name__ == "__main__":
    main()
