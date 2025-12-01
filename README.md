# twitterbot

A small Python bot that replies to @sponsetavnav tweets with a random dice rating in Norwegian: `Jeg gir denne posten terningkast N 🎲`.

Tested with Python 3.11.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file with your X/Twitter credentials (keys with read and write access **for the replying bot account**, e.g., `@terningskastbot`). Keep these values private—do not paste them into chats or commits:
   ```dotenv
   X_API_KEY=your_api_key
   X_API_SECRET=your_api_secret
   X_ACCESS_TOKEN=your_access_token
   X_ACCESS_TOKEN_SECRET=your_access_token_secret
   # Optional: set the default target account without passing --username
   TARGET_USERNAME=sponsetavnav
   ```

   The bot will fail fast with a clear error message if any of these variables are missing. The default target account to monitor is `@sponsetavnav`, so you don't need to change the username to have the bot reply to that profile.

## Usage

Reply to the most recent tweets from the target account (default `sponsetavnav` or `TARGET_USERNAME` if set):

```bash
python bot.py --limit 5
```

Arguments:
- `--username` – account to monitor without the `@` (default `sponsetavnav`).
- `--limit` – how many recent tweets to scan for a reply.
- `--state-file` – path to store tweet IDs already replied to (default `data/replied.json`).
- `--dry-run` – print planned replies without posting them.
- `--reply-backlog` – on a brand-new state file, reply to the currently visible tweets. By default the bot *skips* the backlog, baselines from the latest tweet, and only replies to future posts so it does not spam older tweets.

Run regularly (e.g., with cron) to respond to new tweets with a fresh dice roll. The bot stores replied tweet IDs and the newest seen tweet so it only replies to new posts; keep the state file on durable storage if you need continuity across runs.

## Deploying on Vercel

You can run the bot as a scheduled Vercel Serverless Function:

1. **Add the config file.** `vercel.json` defines a Python function at `api/run.py` and a cron that hits it every 30 minutes. Adjust the cron schedule if you want a different cadence.
2. **Set secrets in Vercel.** In your project’s **Settings → Environment Variables**, add:
   - `X_API_KEY`
   - `X_API_SECRET`
   - `X_ACCESS_TOKEN`
   - `X_ACCESS_TOKEN_SECRET`
   - Optional: `TARGET_USERNAME` (defaults to `sponsetavnav`), `TWEET_LIMIT` (defaults to `5`), `DRY_RUN` (set to `true` to test without posting), `STATE_FILE` (defaults to `/tmp/replied.json`), `REPLY_BACKLOG` (set to `true` to process existing tweets on first run).
3. **Deploy.** From this repo, run:
   ```bash
   vercel deploy --prod
   ```
   or connect the repository in the Vercel dashboard and trigger a deploy.

Notes:
- The serverless handler lives at `api/run.py` and returns JSON so you can see invocation results in Vercel logs.
- The default `STATE_FILE` writes to `/tmp`, which is ephemeral in serverless environments. For durable tracking of replied tweets you should back the state file with a persistent store (e.g., Vercel KV/Redis or S3) and point `STATE_FILE` to a mounted path or swap the persistence implementation to use that service. Without durable state, the bot will baseline from the latest tweet on each cold start to avoid replying to old posts.
