# TheSDTrader Reels

Educational Hindi videos about the Indian stock market for the Instagram page **@thesdtrader**.
Not SEBI registered. Educational purposes only, not investment advice.

## How it works

1. Each Reel lives in `reels/YYYY-MM-DD_slug/` with a `video.mp4` and a `caption.txt`.
2. The GitHub Action **Post Reel** runs every day at 19:00 India time. It posts the oldest reel whose date has arrived (one per day) through Instagram's official API, then records it in `posted.json`.
3. The script refuses to post a caption that does not carry the SEBI / educational-only notice.

## One-time setup (about 15 minutes, on a computer)

Meta changes its dashboard now and then, so the menu names may differ slightly.

1. Your Instagram account must be a **Business or Creator** account.
2. Go to https://developers.facebook.com, log in and create an app (type **Business**). Add the Instagram product, **API setup with Instagram login**.
3. Add `thesdtrader` as an Instagram tester or account in the app, and accept the invitation in the Instagram app (Settings, Apps and websites, Tester invitations).
4. In the app dashboard click **Generate token** for the account, with the permissions `instagram_business_basic` and `instagram_business_content_publish`. Copy the token and the Instagram account ID shown next to it.
5. In this repo go to **Settings, Secrets and variables, Actions** and add two secrets:
   - `IG_ACCESS_TOKEN`: the token
   - `IG_USER_ID`: the Instagram account ID
6. Go to **Actions, Post Reel, Run workflow**. Tick **dry_run** first to check everything, then run again without it to post the first Reel.

The token lasts 60 days. For automatic renewal, add a fine-grained personal access token (permission: Secrets, read and write, for this repo only) as a secret named `GH_PAT`. The **Refresh Instagram token** workflow then renews it twice a month. Without it, repeat step 4 and update `IG_ACCESS_TOKEN` before it expires.

## Adding a Reel

Create `reels/2026-11-23_what-is-share-market/` with `video.mp4` (vertical 1080x1920, under 90 seconds) and `caption.txt` (Hindi caption, hashtags, SEBI notice), then commit to `main`.

## Files

- `scripts/post_reel.py`: posts the next due Reel
- `scripts/refresh_token.py`: renews the Instagram token
- `tools/make_video_sensex.py`: the video generator used for the first Reel
- `posted.json`: log of what was posted
