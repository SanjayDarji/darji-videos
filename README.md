# TheSDTrader Reels

Educational Hindi videos about the Indian stock market for the Instagram page **@thesdtrader**.
Not SEBI registered. Educational purposes only, not investment advice.

## How it works

1. Each Reel lives in `reels/YYYY-MM-DD_slug/` with a `video.mp4`, a `caption.txt` and an optional `cover.jpg` (used as the Reel cover).
2. The GitHub Action **Post Reel** runs every day at 19:00 India time. It posts the oldest reel whose date has arrived (one per day) through Meta's official Instagram API, then records it in `posted.json`.
3. The script refuses to post a caption that does not carry the SEBI / educational-only notice.

## Secrets the workflow needs

Add these under **Settings, Secrets and variables, Actions, Secrets**:

| Secret | What it is |
| --- | --- |
| `IG_ACCESS_TOKEN` | a Page access token (Facebook Login) or a system-user token (Unified Login) with the `instagram_content_publish` permission |
| `IG_USER_ID` | the ID of the Instagram professional account |

Meta's dashboard changes often, so treat menu names as approximate.

## Testing

Go to **Actions, Post Reel, Run workflow**. Tick **dry_run** to check the caption and video link without posting. Run it again without the tick to post the next due Reel.

## Adding a Reel

New Reels are drafted in `drafts/YYYY-MM-DD_slug/` (video, cover, caption, `package.md`, `spec.json` and the `voice/` clips). Once approved, move the folder's `video.mp4`, `cover.jpg` and `caption.txt` into `reels/YYYY-MM-DD_slug/` and commit to `main`. Only `reels/` is ever posted.

This repository is public, so everything committed here, including the face photo in `assets/`, can be seen by anyone.

## Making a Reel

`python3 -I tools/render_reel.py drafts/<folder> render` builds `video.mp4` from `spec.json` plus one Hindi voice clip per scene (`voice/s1.wav`, `s2.wav`, ...). Use `cover` to build `cover.jpg` and `preview` for a contact sheet. The brand tag, safe areas, subtitles, music and sound effects are built in.

## Files

- `scripts/post_reel.py`: posts the next due Reel
- `tools/render_reel.py`: the scene-based video and cover renderer (spec.json driven)
- `tools/make_video_sensex.py`: the one-off generator used for the first Reel
- `assets/face_original.png`: the reference photo used for the avatar and cover
- `drafts/`: Reels waiting for approval (never posted)
- `posted.json`: log of what was posted
