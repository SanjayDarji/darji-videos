# TheSDTrader Reels

Educational Hindi videos about the Indian stock market for the Instagram page **@thesdtrader**.
Not SEBI registered. Educational purposes only, not investment advice.

## How it works

1. Each Reel lives in `reels/YYYY-MM-DD_slug/` with a `video.mp4` and a `caption.txt`.
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

Create `reels/2026-11-23_what-is-share-market/` with `video.mp4` (vertical 1080x1920, under 90 seconds) and `caption.txt` (Hindi caption, hashtags, SEBI notice), then commit to `main`.

## Files

- `scripts/post_reel.py`: posts the next due Reel
- `tools/make_video_sensex.py`: the video generator used for the first Reel
- `posted.json`: log of what was posted
