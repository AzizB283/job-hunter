# Job-hunter

Job-hunter fetches remote job postings from multiple platforms, filters them by keywords or time window, and can either notify via Telegram (CLI script) or show results in a web UI.

## What’s new
- A lightweight Flask web UI (`app.py`) where users can enter keywords and a time window (hours) and view matching jobs in the browser.
- UI shows a timeline of matching job posts with source and published timestamp; links open in a new tab.
- Server-side logging added to `jobhunter.log` for debugging and to inspect filtering decisions.

> Note: `get_jobs.py` was left untouched and still contains the original CLI scraping + Telegram notification logic.

## Features
- Scrapes multiple sources: Remote OK, Remote.io, Working Nomads, We Work Remotely (same sources as `get_jobs.py`).
- Web UI to enter keywords (comma/newline separated) and a time window (hours). 0 = any time.
- Optionally view the raw source responses in `debug/` (the scrapers save JSON there).
- Logs in `jobhunter.log` for detailed per-source diagnostics.

## Files of interest
- `get_jobs.py` — original CLI/Telegram script (unchanged).
- `app.py` — Flask web UI and new server-side scraper endpoints.
- `templates/index.html` — UI template used by `app.py`.
- `debug/` — saved raw responses per source (JSON).
- `jobhunter.log` — runtime log file created by `app.py`.
- `requirements.txt` — Python dependencies required for the UI (Flask, requests, feedparser, python-dotenv).

## Quick start (run the web UI in a virtualenv)
1. Open a terminal and change into the project directory:
   ```bash
   cd /var/www/html/job-hunter
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Start the Flask UI:
   ```bash
   python3 app.py
   ```
   The app runs on port `8000` by default. Open http://localhost:8000 in your browser.

5. Use the form: enter keywords (comma or newline separated) and number of hours (0 = any). Click Search.

6. Inspect logs for debugging:
   ```bash
   tail -f jobhunter.log
   ```

## Running the original CLI script
If you still want to run the CLI job fetcher that sends Telegram messages, run:
```bash
python3 get_jobs.py
```
Make sure you have a `.env` file with `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` if you want Telegram notifications.

## Troubleshooting
- If the UI shows no results but `get_jobs.py` prints items, check `jobhunter.log` for parsing, date, and matching diagnostics.
- If templates or static assets changed, restart `app.py`.

## Contributing
Add new sources by creating a fetch function (normalized output: title/link/source/published) and register it in `app.py`.

## License
MIT

