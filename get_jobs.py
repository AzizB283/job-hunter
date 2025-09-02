import feedparser
import requests
import json
from datetime import datetime, timezone, timedelta
import time
import os

from dotenv import load_dotenv
load_dotenv()


# Keywords to match frontend roles
my_tags = ['frontend developer', 'frontend', 'front end', 'front-end', 'frontend engineer', 'front-end-engineer']

# Max age in seconds (25 hours)
MAX_AGE = 25 * 3600

# Telegram setup (if using)
USE_TELEGRAM = True
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Use a simple HTTP helper to send Telegram messages. This avoids compatibility issues
# with python-telegram-bot versions (sync vs async) and surfaces HTTP errors.
def safe_send(text):
    if not USE_TELEGRAM:
        return
    if not TOKEN or not CHAT_ID:
        print("Telegram not configured (TOKEN or CHAT_ID missing).")
        return
    try:
        resp = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                             data={"chat_id": CHAT_ID, "text": text})
        if not resp.ok:
            print("Telegram send failed:", resp.status_code, resp.text)
        else:
            print("Telegram send OK")
    except Exception as e:
        print("Telegram send exception:", e)

# Utility: checks if job text contains keywords
def contains_keywords(text):
    if not text:
        return False
    txt = str(text).lower()
    return any(tag in txt for tag in my_tags)

# Format for sending or printing
def format_entry(title, link):
    return f"{title}\n{link}"

def save_debug_data(source_name, data):
    os.makedirs("debug", exist_ok=True)
    with open(f'debug/{source_name}.json', 'w') as f:
        json.dump(data, f, indent=2)

# --- Job Source: Remote OK ---
def remoteok():
    print("🔍 Checking Remote OK...")
    jobs = []
    try:
        res = requests.get("https://remoteok.com/api")
        data = res.json()
        save_debug_data("remoteok", data)
        data = [d for d in data if isinstance(d, dict)]  # skip metadata
        print(f" → Total jobs fetched: {len(data)}")
        for job in data:
            date_str = job.get('date')
            if not date_str:
                continue
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
            # if (datetime.now(timezone.utc) - dt).total_seconds() < MAX_AGE:
            if True:  # For testing, always check
                if contains_keywords(job.get("description", "") + job.get("position", "")):
                    jobs.append(format_entry(job.get("position", "No Title"), job.get("url", "")))
        print(f" → Frontend jobs found: {len(jobs)}")
    except Exception as e:
        print("Remote OK failed:", e)
    return jobs

# --- Job Source: Remote.io ---
def remoteio():
    print("🔍 Checking Remote.io...")
    jobs = []
    try:
        rss = feedparser.parse('https://s3.remote.io/feed/rss.xml')
        entries = rss.entries
        save_debug_data("remoteio", [e for e in entries])
        print(f" → Total jobs fetched: {len(entries)}")
        for entry in entries:
            published = entry.get("published")
            if not published:
                continue
            dt = datetime.strptime(published, "%Y-%m-%d %H:%M:%S")
            # if (datetime.now() - dt).total_seconds() < MAX_AGE:
            if True:
                summary = entry.get("summary", "")
                if contains_keywords(summary + entry.get("title", "")):
                    jobs.append(format_entry(entry.get("title", "No Title"), entry.get("link", "")))
        print(f" → Frontend jobs found: {len(jobs)}")
    except Exception as e:
        print("Remote.io failed:", e)
    return jobs

# --- Job Source: Working Nomads ---
def working_nomads():
    print("🔍 Checking Working Nomads...")
    jobs = []
    try:
        url = "https://www.workingnomads.co/api/exposed_jobs/"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = res.json()
        save_debug_data("workingnomads", data)
        print(f" → Total jobs fetched: {len(data)}")
        for job in data:
            pub_date = job.get("pub_date")
            if not pub_date:
                continue
            try:
                dt = datetime.fromisoformat(pub_date)
            except ValueError:
                dt = datetime.strptime(pub_date.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                dt = dt.replace(tzinfo=timezone.utc)
            # if (datetime.now(timezone.utc) - dt).total_seconds() < MAX_AGE:
            if True:
                if contains_keywords(job.get("description", "") + job.get("title", "")):
                    jobs.append(format_entry(job.get("title", "No Title"), job.get("url", "")))
        print(f" → Frontend jobs found: {len(jobs)}")
    except Exception as e:
        print("Working Nomads failed:", e)
    return jobs

# --- Job Source: GitHub Jobs (deprecated but mocked example) ---
def github_jobs():
    print("🔍 Checking GitHub Jobs (mock)...")
    # GitHub Jobs is no longer active, so return dummy or skip
    return []

# --- Job Source: We Work Remotely ---
def weworkremotely():
    print("🔍 Checking We Work Remotely...")
    jobs = []
    try:
        rss = feedparser.parse("https://weworkremotely.com/categories/remote-programming-jobs.rss")
        entries = rss.entries
        save_debug_data("weworkremotely", [e for e in entries])
        print(f" → Total jobs fetched: {len(entries)}")
        for entry in entries:
            published = entry.get("published")
            if not published:
                continue
            dt = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
            # if (datetime.now(timezone.utc) - dt).total_seconds() < MAX_AGE:
            if True:
                summary = entry.get("summary", "")
                if contains_keywords(summary + entry.get("title", "")):
                    jobs.append(format_entry(entry.get("title", "No Title"), entry.get("link", "")))
        print(f" → Frontend jobs found: {len(jobs)}")
    except Exception as e:
        print("We Work Remotely failed:", e)
    return jobs

# --- Job Source: Wellfound (AngelList) - Placeholder only ---
def wellfound():
    print("🔍 Checking Wellfound (not yet implemented)...")
    return []

# --- Main ---
if __name__ == "__main__":
    all_jobs = []
    sources = {
        "Remote OK": remoteok,
        "Remote.io": remoteio,
        "Working Nomads": working_nomads,
        "We Work Remotely": weworkremotely,
        "GitHub Jobs": github_jobs,
        "Wellfound": wellfound,
    }

    for name, func in sources.items():
        jobs = func()
        print(f"[{name}] → {len(jobs)} frontend jobs found.\n")
        all_jobs.extend(jobs)

    if not all_jobs:
        print("❌ No new frontend jobs found in the last 24 hours.")
        if USE_TELEGRAM:
            safe_send("No new frontend jobs found today.")
    else:
        print(f"✅ Found {len(all_jobs)} total frontend jobs.")
        for job in all_jobs:
            print("\n" + job)
            if USE_TELEGRAM:
                safe_send(job)
                time.sleep(3)
