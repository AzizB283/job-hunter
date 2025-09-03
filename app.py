#!/usr/bin/env python3
# filepath: /var/www/html/job-hunter/app.py
from flask import Flask, render_template, request
import requests
import feedparser
from datetime import datetime, timezone, timedelta
import re
import logging

# Configure logging
logger = logging.getLogger('jobhunter')
logger.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(fmt)
logger.addHandler(ch)
# file handler
fh = logging.FileHandler('jobhunter.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(fmt)
logger.addHandler(fh)

app = Flask(__name__)

# Helpers
def normalize_keywords(text):
    # split by comma or newline and normalize
    parts = re.split(r"[,\n]+", text)
    tags = [p.strip().lower() for p in parts if p.strip()]
    logger.debug("Normalized keywords: %s -> %s", text, tags)
    return tags

def matches_keywords(text, keywords):
    """
    Match text against provided keywords; if none provided, fall back to original my_tags
    from get_jobs.py to behave exactly like the get_jobs script.
    """
    if not text:
        return False
    txt = str(text).lower()
    # First, if user-supplied keywords exist, check them
    if keywords:
        for k in keywords:
            if k and k in txt:
                logger.debug('matches_keywords: matched user keyword "%s" in text', k)
                return True
    # Fallback: use my_tags from get_jobs.py to preserve original behavior
    try:
        from get_jobs import my_tags as default_tags
        for tag in default_tags:
            if tag and tag in txt:
                logger.debug('matches_keywords: matched default tag "%s" in text', tag)
                return True
    except Exception as e:
        logger.debug('matches_keywords: could not import default tags: %s', e)
    return False

# Source: Remote OK
def fetch_remoteok(keywords, max_age_seconds):
    out = []
    logger.debug('fetch_remoteok start: keywords=%s max_age_seconds=%s', keywords, max_age_seconds)
    try:
        res = requests.get("https://remoteok.com/api", headers={"User-Agent": "job-hunter-ui/1.0"}, timeout=15)
        logger.debug('remoteok status_code=%s', getattr(res, 'status_code', None))
        data = res.json()
        data = [d for d in data if isinstance(d, dict)]
        logger.debug('remoteok total items=%d', len(data))
        now = datetime.now(timezone.utc)
        for job in data:
            date_str = job.get('date')
            if not date_str:
                continue
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
            except Exception:
                logger.debug('remoteok skipping job with invalid date: %s', date_str)
                continue
            age = (now - dt).total_seconds()
            if max_age_seconds is not None and age > max_age_seconds:
                continue
            combined = ' '.join(filter(None, [job.get('description',''), job.get('position',''), ' '.join(job.get('tags',[]))]))
            if matches_keywords(combined, keywords):
                out.append({
                    'title': job.get('position','No title'),
                    'link': job.get('url',''),
                    'source': 'Remote OK',
                    'published': dt.isoformat()
                })
        logger.debug('fetch_remoteok found=%d', len(out))
    except Exception as e:
        logger.exception('remoteok error')
    return out

# Source: Remote.io (RSS)
def fetch_remoteio(keywords, max_age_seconds):
    out = []
    logger.debug('fetch_remoteio start: keywords=%s max_age_seconds=%s', keywords, max_age_seconds)
    try:
        rss = feedparser.parse('https://s3.remote.io/feed/rss.xml')
        entries = getattr(rss, 'entries', [])
        logger.debug('remoteio total items=%d', len(entries))
        now = datetime.now(timezone.utc)
        for entry in entries:
            published = entry.get('published')
            if not published:
                continue
            try:
                dt = datetime.strptime(published, "%Y-%m-%d %H:%M:%S")
                dt = dt.replace(tzinfo=timezone.utc)
            except Exception:
                logger.debug('remoteio skipping entry with invalid published: %s', published)
                continue
            age = (now - dt).total_seconds()
            if max_age_seconds is not None and age > max_age_seconds:
                continue
            combined = ' '.join(filter(None, [entry.get('summary',''), entry.get('title','')]))
            if matches_keywords(combined, keywords):
                out.append({
                    'title': entry.get('title','No title'),
                    'link': entry.get('link',''),
                    'source': 'Remote.io',
                    'published': dt.isoformat()
                })
        logger.debug('fetch_remoteio found=%d', len(out))
    except Exception as e:
        logger.exception('remoteio error')
    return out

# Source: Working Nomads
def fetch_working_nomads(keywords, max_age_seconds):
    out = []
    logger.debug('fetch_working_nomads start: keywords=%s max_age_seconds=%s', keywords, max_age_seconds)
    try:
        url = "https://www.workingnomads.co/api/exposed_jobs/"
        res = requests.get(url, headers={"User-Agent": "job-hunter-ui/1.0"}, timeout=15)
        logger.debug('workingnomads status_code=%s', getattr(res, 'status_code', None))
        data = res.json()
        logger.debug('workingnomads total items=%d', len(data) if hasattr(data, '__len__') else 0)
        now = datetime.now(timezone.utc)
        for job in data:
            pub_date = job.get('pub_date')
            if not pub_date:
                continue
            try:
                dt = datetime.fromisoformat(pub_date)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except Exception:
                try:
                    dt = datetime.strptime(pub_date.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    dt = dt.replace(tzinfo=timezone.utc)
                except Exception:
                    logger.debug('workingnomads skipping job with invalid pub_date: %s', pub_date)
                    continue
            age = (now - dt).total_seconds()
            if max_age_seconds is not None and age > max_age_seconds:
                continue
            combined = ' '.join(filter(None, [job.get('description',''), job.get('title','')]))
            if matches_keywords(combined, keywords):
                out.append({
                    'title': job.get('title','No title'),
                    'link': job.get('url',''),
                    'source': 'Working Nomads',
                    'published': dt.isoformat()
                })
        logger.debug('fetch_working_nomads found=%d', len(out))
    except Exception as e:
        logger.exception('working_nomads error')
    return out

# Source: WeWorkRemotely
def fetch_weworkremotely(keywords, max_age_seconds):
    out = []
    logger.debug('fetch_weworkremotely start: keywords=%s max_age_seconds=%s', keywords, max_age_seconds)
    try:
        rss = feedparser.parse("https://weworkremotely.com/categories/remote-programming-jobs.rss")
        entries = getattr(rss, 'entries', [])
        logger.debug('weworkremotely total items=%d', len(entries))
        now = datetime.now(timezone.utc)
        for entry in entries:
            published = entry.get('published')
            if not published:
                continue
            try:
                dt = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
            except Exception:
                logger.debug('weworkremotely skipping entry with invalid published: %s', published)
                continue
            age = (now - dt).total_seconds()
            if max_age_seconds is not None and age > max_age_seconds:
                continue
            combined = ' '.join(filter(None, [entry.get('summary',''), entry.get('title','')]))
            if matches_keywords(combined, keywords):
                out.append({
                    'title': entry.get('title','No title'),
                    'link': entry.get('link',''),
                    'source': 'We Work Remotely',
                    'published': dt.isoformat()
                })
        logger.debug('fetch_weworkremotely found=%d', len(out))
    except Exception as e:
        logger.exception('weworkremotely error')
    return out

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    keywords_input = ', '.join([k for k in ["frontend developer", "frontend", "front end", "front-end", "frontend engineer"]])
    hours = 24
    logger.debug('Received %s request for /', request.method)
    if request.method == 'POST':
        keywords_input = request.form.get('keywords', '')
        hours_raw = request.form.get('hours', '24')
        logger.debug('Form raw inputs: keywords=%s hours=%s', keywords_input, hours_raw)
        try:
            hours = int(hours_raw or 24)
        except Exception:
            hours = 24
            logger.debug('Invalid hours value, defaulting to 24')
        tags = normalize_keywords(keywords_input)
        max_age_seconds = None
        if hours > 0:
            max_age_seconds = hours * 3600
        logger.info('Searching with tags=%s max_age_seconds=%s', tags, max_age_seconds)
        # Fetch from sources
        sources = [fetch_remoteok, fetch_remoteio, fetch_working_nomads, fetch_weworkremotely]
        for func in sources:
            try:
                logger.info('Calling source: %s', func.__name__)
                part = func(tags, max_age_seconds)
                logger.info('Source %s returned %d items', func.__name__, len(part))
                results.extend(part)
            except Exception as e:
                logger.exception('source fetch error for %s', func.__name__)
        # sort results by published desc when available
        def sort_key(item):
            try:
                return item.get('published','')
            except Exception:
                return ''
        results = sorted(results, key=sort_key, reverse=True)
        logger.info('Total results after aggregation: %d', len(results))
    return render_template('index.html', results=results, keywords_input=keywords_input, hours=hours)

if __name__ == '__main__':
    logger.info('Starting Flask app on 0.0.0.0:8000')
    app.run(host='0.0.0.0', port=8000, debug=True)
