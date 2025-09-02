# Job-hunter

Job-hunter is a small Python project that fetches remote job postings from multiple job platforms, filters them by configurable keywords (e.g. frontend/web roles), and sends matching notifications to a Telegram chat. This repository is public and intended to be easy for others to clone, configure and run.

## Features
- Fetches remote job listings from several platforms (RemoteOK, WeWorkRemotely, WorkingNomads, Remote.io, GitHub, Wellfound — where supported).
- Normalizes and filters jobs by keywords/tags.
- Sends formatted notifications to Telegram via a bot.
- Saves raw responses to `debug/` for inspection.

## Quick start (Clone & run)
1. Clone the repo:

   git clone https://github.com/<your-username>/job-hunter.git
   cd job-hunter

2. Create a virtual environment and install dependencies:

   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirement.txt

3. Create a `.env` file in the repository root with your Telegram settings:

   TELEGRAM_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=-1001234567890

4. Run a job-fetcher script:

- `python3 get_jobs.py` 

Or use the helper script: `./run_jobs.sh` (make executable: `chmod +x run_jobs.sh`).

## Configuration
- Keyword filters (tags) are defined near the top of the runner scripts as lists (e.g. `my_tags`). Edit those lists to customize which jobs you want to receive.
- Toggle Telegram notifications by leaving `TELEGRAM_TOKEN` or `TELEGRAM_CHAT_ID` empty — the scripts will run in debug/local mode.
- Adjust `MAX_AGE` or similar variables in the scripts to control how old a job can be to trigger a notification.

## Debugging
- Raw API/RSS responses are saved into `debug/` (e.g. `debug/remoteok.json`). Inspect these files when a source changes or parsing breaks.
- Check logs or the terminal output for errors. Verify Telegram bot token and chat ID if messages are not delivered.

## Repository structure
- `get_jobs.py` — runners and scrapers
- `requirement.txt` — Python dependencies
- `run_jobs.sh` — convenience wrapper to run the script
- `debug/` — saved raw responses
- `progress/` — progress or state files

## Contributing
Contributions welcome. If you add a new source, please:
1. Add a scraper module or function with clear normalization logic.
2. Update the README and `debug/` examples if needed.
3. Open a PR with a brief description and sample output.

## License
This project is licensed under the MIT License — see the `LICENSE` file for details.

---

