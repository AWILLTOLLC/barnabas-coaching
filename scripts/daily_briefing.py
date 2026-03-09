#!/usr/bin/env python3
"""
daily_briefing.py — Aaron's 7am morning briefing
Sends via Telegram. Sections: Weather | Amazon | Email | Events
"""

import imaplib, json, email, requests, subprocess, re, sys
from email.header import decode_header
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
import caldav, sys
from caldav.elements import dav

CREDS_PATH        = Path("/root/.openclaw/credentials/email.json")
ICLOUD_CREDS_PATH = Path("/root/.openclaw/credentials/icloud.json")
AARON_TG          = "5161266419"
SEATTLE_LAT       = 47.652
SEATTLE_LON       = -122.352

# ── upcoming deadlines ────────────────────────────────────────────────────────
# Add time-sensitive reminders here. Format: (date(Y,M,D), days_before, "message")
DEADLINES = [
    (date(2026, 3, 31), 7,  "🎟️ ANJUNADEEP MALTA presale opens TODAY at 12pm GMT — buy immediately, boat parties sell out first. malta.anjunadeep.com"),
    (date(2026, 3, 31), 3,  "🎟️ Anjunadeep Malta presale opens in 3 days (March 31, 12pm GMT). Be ready at your computer."),
    (date(2026, 10, 2), 14, "✈️ MALTA TRIP in 2 weeks — confirm: Alaska SEA→Rome booked, Donna Camilla Savelli booked, FCO→MLA booked, ETIAS done."),
    (date(2026, 10, 2), 7,  "✈️ MALTA TRIP in 1 week — pack, check ETIAS, pre-book Colosseum + Vatican tickets if not done."),
]

def get_deadlines():
    today = datetime.now(timezone(timedelta(hours=-8))).date()
    alerts = []
    for deadline_date, days_before, message in DEADLINES:
        days_until = (deadline_date - today).days
        if days_until == days_before or (days_until == 0 and days_before == 0):
            alerts.append(message)
        elif days_until == 0:
            alerts.append(message)
    return alerts

LIKED_GENRES    = {'edm', 'electronic', 'house', 'techno', 'deep house', 'melodic techno',
                   'melodic house', 'organic', 'ambient', 'electronica', 'downtempo',
                   'reggae', 'dub', 'dancehall', 'indie', 'funk', 'soul', 'r&b', 'jazz',
                   'disco', 'dance', 'bass', 'drum', 'dnb', 'dubstep', 'tribute',
                   'anjunadeep', 'progressive', 'trance', 'afro'}
DISLIKED_GENRES = {'metal', 'hardcore', 'rap', 'hip hop', 'hip-hop', 'country', 'bluegrass',
                   'emo', 'punk', 'death metal', 'black metal'}

# Artists Aaron specifically loves — always flagged with ⭐ regardless of genre match
LIKED_ARTISTS = {
    # Confirmed by Aaron
    'christian löffler', 'christian loffler',
    # Anjunadeep / melodic-electronic orbit
    'above & beyond', 'above and beyond', 'lane 8', 'yotto', 'dosem',
    'anjunadeep', 'anjuna', 'elderbrook', 'ólafur arnalds', 'olafur arnalds',
    'monolink', 'ben böhm', 'ben bohm', 'bonobo', 'jon hopkins',
    'rufus du sol', 'rüfüs du sol', 'rufus',
    # Deep/melodic techno artists
    'tale of us', 'patrice bäumel', 'patrice baumel', 'stephan bodzin',
    '&me', 'pachanga boys', 'innervisions', 'âme', 'ame',
    # Deep house / organic
    'disclosure', 'four tet', '4 tet', 'floating points',
    # Rave/festival crossover artists Aaron likely knows
    'pretty lights', 'odesza', 'griz', 'tycho',
}

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Light showers", 81: "Showers", 82: "Heavy showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ heavy hail",
}


# ── helpers ───────────────────────────────────────────────────────────────────

def ds(s):
    if not s: return ""
    parts = decode_header(s)
    out = []
    for p, enc in parts:
        if isinstance(p, bytes):
            out.append(p.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(str(p))
    return "".join(out)

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                return part.get_payload(decode=True).decode("utf-8", errors="replace").strip()
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode("utf-8", errors="replace").strip()
    return ""

def send_telegram(text):
    result = subprocess.run(
        ["python3", "/root/.openclaw/workspace/scripts/send_telegram.py", AARON_TG, text],
        capture_output=True, text=True
    )
    return result.returncode == 0

def send_email(subject, text):
    result = subprocess.run(
        ["python3", "/root/.openclaw/workspace/scripts/send_email.py",
         "a@kaw.cc", subject, text],
        capture_output=True, text=True
    )
    return result.returncode == 0


# ── weather ───────────────────────────────────────────────────────────────────

def get_weather():
    # Primary: Open-Meteo (retry up to 3 times)
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={SEATTLE_LAT}&longitude={SEATTLE_LON}"
        f"&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        f"&current_weather=true"
        f"&temperature_unit=fahrenheit"
        f"&timezone=America%2FLos_Angeles"
        f"&forecast_days=1"
    )
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=15)
            d = r.json()
            cur = d["current_weather"]
            day = d["daily"]
            code   = int(cur["weathercode"])
            desc   = WMO_CODES.get(code, f"Code {code}")
            temp   = cur["temperature"]
            hi     = day["temperature_2m_max"][0]
            lo     = day["temperature_2m_min"][0]
            rain   = day["precipitation_probability_max"][0]
            wind   = cur["windspeed"]
            return (
                f"Fremont/Seattle: {desc}, {temp:.0f}°F now\n"
                f"High {hi:.0f}° / Low {lo:.0f}° | Rain {rain:.0f}% | Wind {wind:.0f} km/h"
            )
        except Exception:
            if attempt < 2:
                import time; time.sleep(3)
            continue

    # Fallback: wttr.in (no SSL, simpler)
    try:
        r = requests.get(
            f"https://wttr.in/Seattle?format=%C+%t+Hi:%h+Lo:%l+Rain:%p",
            timeout=10, headers={"User-Agent": "curl/7.68.0"}
        )
        if r.status_code == 200 and r.text.strip():
            return f"Fremont/Seattle: {r.text.strip()} (via wttr.in)"
    except Exception:
        pass

    return "Weather unavailable (both sources failed)"


# ── market prices ────────────────────────────────────────────────────────────

def get_market_prices():
    lines = []
    try:
        # Crypto: CoinGecko (no key)
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum", "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10
        )
        c = r.json()
        btc = c["bitcoin"]["usd"]
        btc_chg = c["bitcoin"]["usd_24h_change"]
        eth = c["ethereum"]["usd"]
        eth_chg = c["ethereum"]["usd_24h_change"]
        lines.append(f"  BTC  ${btc:,.0f}  ({btc_chg:+.1f}%)")
        lines.append(f"  ETH  ${eth:,.0f}  ({eth_chg:+.1f}%)")
    except Exception as e:
        lines.append(f"  Crypto unavailable ({e})")

    try:
        # Stocks: Yahoo Finance (no key)
        for label, ticker in [("S&P 500", "^GSPC"), ("DOW", "^DJI")]:
            r = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                params={"interval": "1d", "range": "1d"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            meta = r.json()["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice") or meta.get("previousClose")
            prev  = meta.get("chartPreviousClose") or meta.get("previousClose")
            chg   = ((price - prev) / prev * 100) if prev else 0
            lines.append(f"  {label}  {price:,.2f}  ({chg:+.2f}%)")
    except Exception as e:
        lines.append(f"  Stocks unavailable ({e})")

    return "\n".join(lines)


# ── icloud calendar ───────────────────────────────────────────────────────────

SKIP_CALENDARS = {'Reminders ⚠️', 'Other ⚠️'}

def get_calendar_events():
    try:
        creds = json.load(open(ICLOUD_CREDS_PATH))
        client = caldav.DAVClient(
            url='https://caldav.icloud.com',
            username=creds['apple_id'],
            password=creds['app_password']
        )
        principal = client.principal()
        calendars = principal.calendars()

        pst = timezone(timedelta(hours=-8))
        today_start = datetime.now(pst).replace(hour=0,  minute=0,  second=0,  microsecond=0)
        today_end   = datetime.now(pst).replace(hour=23, minute=59, second=59, microsecond=0)

        events = []
        for cal in calendars:
            name = cal.get_display_name() or "Unknown"
            if name in SKIP_CALENDARS:
                continue
            try:
                results = cal.date_search(start=today_start, end=today_end, expand=True)
                for ev in results:
                    ev.load()
                    comp = ev.vobject_instance.vevent
                    summary = str(comp.summary.value) if hasattr(comp, 'summary') else "(no title)"
                    dtstart = comp.dtstart.value if hasattr(comp, 'dtstart') else None

                    # Format time
                    if dtstart:
                        if hasattr(dtstart, 'hour'):
                            # datetime object
                            if hasattr(dtstart, 'tzinfo') and dtstart.tzinfo:
                                dtstart = dtstart.astimezone(pst)
                            time_s = dtstart.strftime("%-I:%M %p")
                        else:
                            # date-only (all-day)
                            time_s = "All day"
                    else:
                        time_s = ""

                    events.append((dtstart, time_s, summary, name))
            except Exception:
                continue

        if not events:
            return "Nothing on the calendar today."

        # Sort by start time
        events.sort(key=lambda x: (x[0] is None, str(x[0])))
        lines = []
        for _, time_s, summary, cal_name in events:
            lines.append(f"  • {time_s}  {summary}  [{cal_name}]")
        return "\n".join(lines)

    except Exception as e:
        return f"Calendar unavailable ({e})"


# ── youtube search ────────────────────────────────────────────────────────────

def get_youtube_link(artist):
    """Search for a recent YouTube live set via Brave Search API, return URL or None."""
    try:
        cfg = json.load(open("/root/.openclaw/openclaw.json"))
        brave_key = cfg.get("memorySearch", {}).get("search", {}).get("apiKey", "")
        if not brave_key:
            return None
        query = re.sub(r"[^\w\s]", "", artist).strip() + " live set site:youtube.com"
        r = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": 5},
            headers={"Accept": "application/json", "X-Subscription-Token": brave_key},
            timeout=10
        )
        for result in r.json().get("web", {}).get("results", []):
            url = result.get("url", "")
            m = re.search(r"watch\?v=([a-zA-Z0-9_-]{11})", url)
            if m:
                return f"https://youtube.com/watch?v={m.group(1)}"
    except Exception:
        pass
    return None


# ── nectar events ─────────────────────────────────────────────────────────────

def get_spotify_artists():
    """Fetch Aaron's current liked artists from Spotify. Falls back to empty set on error."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from spotify import get_all_liked_artists
        return get_all_liked_artists()
    except Exception as e:
        return set()


def _parse_artist_entry(artist, chunk, spotify_artists):
    """Given an artist name and event chunk text, return (is_fave, genre_match, star, yt)."""
    chunk_lower  = chunk.lower()
    artist_lower = artist.lower()
    is_fave = (any(a in artist_lower for a in LIKED_ARTISTS)
               or any(artist_lower in a or a in artist_lower for a in spotify_artists))
    genre_match = any(g in chunk_lower for g in LIKED_GENRES)
    star = "⭐ " if is_fave else ("✅ " if genre_match else "")
    yt   = get_youtube_link(artist) if (is_fave or genre_match) else None
    return is_fave, genre_match, star, yt


def get_nectar_events(spotify_artists=None):
    """Scrape Nectar Lounge calendar — full 7-day lookahead, grouped by day."""
    if not spotify_artists:
        spotify_artists = get_spotify_artists()
    try:
        result = subprocess.run(
            ["mcporter", "call", "scrapling.stealthy_fetch",
             "url=https://nectarlounge.com/calendar/",
             "extraction_type=text", "--output", "json"],
            capture_output=True, text=True, timeout=90
        )
        raw = json.loads(result.stdout)
        content = raw.get("content", "")
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)

        pst       = timezone(timedelta(hours=-8))
        today_dt  = datetime.now(pst)
        month_map = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
                     "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

        chunks = re.split(r'(?:TICKETS|More Info)', content)
        # events_by_day: list of (days_ahead, day_label, entry)
        events = []

        for chunk in chunks:
            m = re.search(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(\d{4})', chunk)
            if not m:
                continue
            mon_s, day_s, yr_s = m.group(2), int(m.group(3)), int(m.group(4))
            event_dt   = datetime(yr_s, month_map[mon_s], day_s, tzinfo=pst)
            days_ahead = (event_dt.date() - today_dt.date()).days
            if days_ahead < 0 or days_ahead > 6:
                continue

            venue = "Nectar Lounge" if "Nectar Lounge" in chunk else "Hidden Hall"

            chunk_lines = [l.strip() for l in chunk.splitlines() if l.strip()]
            artist = ""
            for i, line in enumerate(chunk_lines):
                if "presents" in line.lower() or "present:" in line.lower():
                    if i + 1 < len(chunk_lines):
                        artist = chunk_lines[i + 1]
                    break
            if not artist:
                for line in chunk_lines:
                    if line.isupper() and len(line) > 3:
                        artist = line
                        break

            chunk_lower = chunk.lower()
            if any(g in chunk_lower for g in DISLIKED_GENRES):
                continue

            time_m = re.search(r'(\d+:\d+\s*[AP]M)', chunk)
            time_s = time_m.group(1) if time_m else ""

            _, _, star, yt = _parse_artist_entry(artist, chunk, spotify_artists)
            entry = f"  {star}• {artist} @ {venue} {time_s}".strip()
            if yt:
                entry += f"\n    {yt}"

            if days_ahead == 0:
                day_label = "Tonight"
            elif days_ahead == 1:
                day_label = "Tomorrow"
            else:
                day_label = event_dt.strftime("%A, %b %-d")

            events.append((days_ahead, day_label, entry))

        events.sort(key=lambda x: x[0])
        lines = []
        current_label = None
        for _, day_label, entry in events:
            if day_label != current_label:
                lines.append(f"{day_label}:")
                current_label = day_label
            lines.append(entry)

        if not lines:
            lines.append("Nothing at Nectar this week.")

        return "\n".join(lines)

    except Exception as e:
        return f"Nectar unavailable ({e})"


def _scrape_venue(url, stealthy=False):
    """Scrape a venue URL, return text content or empty string on failure."""
    tool = "scrapling.stealthy_fetch" if stealthy else "scrapling.fetch"
    try:
        result = subprocess.run(
            ["mcporter", "call", tool, f"url={url}", "extraction_type=text",
             "--output", "json", "--timeout", "90000"],
            capture_output=True, text=True, timeout=95
        )
        raw = json.loads(result.stdout)
        content = raw.get("content", "")
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        if raw.get("status", 200) >= 400:
            return ""
        return content
    except Exception:
        return ""


def _parse_neumos(content, today_dt, pst):
    """
    Parse Neumos events page.
    Format: 'Neumos Presents\nARTIST\n...\nMar\n7\nDoors: ...'
    Returns list of (days_ahead, date_label, artist, venue).
    """
    events = []
    month_map = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
                 "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    # Split on event separators
    chunks = re.split(r'Neumos Presents|The Crocodile.*?Presents', content)
    for chunk in chunks:
        # Find month + day: "Mar\n7" or "Mar 7"
        m = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})', chunk)
        if not m:
            continue
        try:
            month_num  = month_map[m.group(1)]
            day_num    = int(m.group(2))
            year       = today_dt.year
            event_date = datetime(year, month_num, day_num, tzinfo=pst)
            # Handle year rollover
            if (event_date.date() - today_dt.date()).days < -30:
                event_date = datetime(year + 1, month_num, day_num, tzinfo=pst)
        except Exception:
            continue

        days_ahead = (event_date.date() - today_dt.date()).days
        if days_ahead < 0 or days_ahead > 13:
            continue

        # Artist is first non-empty, non-boilerplate line
        chunk_lines = [l.strip() for l in chunk.splitlines()
                       if l.strip() and not re.match(r'^(Doors:|Buy Tickets|All Ages|21 &|with\s)', l.strip(), re.I)]
        artist = chunk_lines[0] if chunk_lines else ""
        if not artist or len(artist) < 2:
            continue

        if days_ahead == 0: date_label = "Tonight"
        elif days_ahead == 1: date_label = "Tomorrow"
        else: date_label = event_date.strftime("%A, %b %-d")

        events.append((days_ahead, date_label, artist, "Neumos", False))
    return events


def _parse_kremwerk(content, today_dt, pst):
    """
    Parse Kremwerk events page (calendar grid format).
    Looks for 'Sat\n7' / 'Sun\n8' day markers, extracts events in following detail cards.
    Returns list of (days_ahead, date_label, artist, venue).
    """
    events = []
    # Find current month/year from header
    month_map = {"January":1,"February":2,"March":3,"April":4,"May":5,"June":6,
                 "July":7,"August":8,"September":9,"October":10,"November":11,"December":12}
    month_m = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', content)
    if not month_m:
        return events
    cal_month = month_map[month_m.group(1)]
    cal_year  = int(month_m.group(2))

    # Find all day markers: "(Mon|Tue|...) (\d{1,2})" — they appear as separate lines
    day_pattern = re.compile(r'\b(Sun|Mon|Tue|Wed|Thu|Fri|Sat)\s+(\d{1,2})\b')
    day_matches = list(day_pattern.finditer(content))

    for idx, dm in enumerate(day_matches):
        day_num = int(dm.group(2))
        try:
            event_date = datetime(cal_year, cal_month, day_num, tzinfo=pst)
        except Exception:
            continue
        days_ahead = (event_date.date() - today_dt.date()).days
        if days_ahead < 0 or days_ahead > 13:
            continue

        # Text block between this day marker and the next
        start = dm.end()
        end   = day_matches[idx + 1].start() if idx + 1 < len(day_matches) else len(content)
        block = content[start:end]

        # Extract event detail cards: EVENT_NAME followed by TIME – TIME, then ROOM
        # Pattern: name line, then "H:MM PM – H:MM AM" time range
        detail_pattern = re.compile(
            r'^(.+?)\n\d+:\d+\s*[AP]M\s*[–-]\s*\d+:\d+\s*[AP]M',
            re.MULTILINE
        )
        for em in detail_pattern.finditer(block):
            artist = em.group(1).strip()
            # Skip duplicated 24h time format lines, address lines, skip words
            if re.match(r'^\d+:\d+|^1809|^Seattle|^United', artist):
                continue
            if len(artist) < 3:
                continue

            if days_ahead == 0: date_label = "Tonight"
            elif days_ahead == 1: date_label = "Tomorrow"
            else: date_label = event_date.strftime("%A, %b %-d")

            events.append((days_ahead, date_label, artist, "Kremwerk", True))  # always_show=True (all-electronic venue)

    return events


def get_seattle_upcoming(spotify_artists=None):
    """
    Scrape Kremwerk + Neumos for the next 2 weeks.
    Only surfaces events matching Spotify artists or liked genres.
    Groups output by date.
    """
    if not spotify_artists:
        spotify_artists = get_spotify_artists()

    pst      = timezone(timedelta(hours=-8))
    today_dt = datetime.now(pst)

    # Scrape venues in parallel via subprocess (already fastest we can do)
    kremwerk_content = _scrape_venue("https://kremwerk.com/events", stealthy=True)
    neumos_content   = _scrape_venue("https://www.neumos.com/events", stealthy=False)

    raw_events = []
    if kremwerk_content:
        raw_events.extend(_parse_kremwerk(kremwerk_content, today_dt, pst))
    if neumos_content:
        raw_events.extend(_parse_neumos(neumos_content, today_dt, pst))

    # Filter, deduplicate, flag
    seen   = set()
    events = []
    for days_ahead, date_label, artist, venue, always_show in raw_events:
        artist_lower = artist.lower()
        if any(g in artist_lower for g in DISLIKED_GENRES):
            continue
        is_fave     = (any(a in artist_lower for a in LIKED_ARTISTS)
                       or any(artist_lower in a or a in artist_lower for a in spotify_artists))
        genre_match = any(g in artist_lower for g in LIKED_GENRES)

        if not (always_show or is_fave or genre_match):
            continue

        key = (days_ahead, artist_lower)
        if key in seen:
            continue
        seen.add(key)

        star = "⭐ " if is_fave else "✅ "
        yt   = get_youtube_link(artist) if is_fave else None
        events.append((days_ahead, date_label, star, artist, venue, yt))

    events.sort(key=lambda x: x[0])

    lines         = []
    current_label = None
    for days_ahead, date_label, star, artist, venue, yt in events:
        if date_label != current_label:
            lines.append(f"{date_label}:")
            current_label = date_label
        entry = f"  {star}• {artist} @ {venue}"
        if yt:
            entry += f"\n    {yt}"
        lines.append(entry)

    if not lines:
        return "  Nothing at Kremwerk or Neumos in the next 2 weeks (or scraping failed)."

    return "\n".join(lines)


# ── email + amazon ────────────────────────────────────────────────────────────

def is_glimmer_order(frm, subj, body):
    """Detect forwarded Glimmer Cards / Shopify order notifications."""
    indicators = ['glimmer', 'shopify', 'new order', 'you have a new order',
                  'order confirmed', 'order #', 'order notification']
    text = (frm + " " + subj + " " + body[:500]).lower()
    return any(ind in text for ind in indicators)

def parse_glimmer_order(subj, body):
    """Extract order number and total from a Shopify order email."""
    order_m = re.search(r'[Oo]rder\s*#?\s*(\d+)', subj + " " + body[:1000])
    total_m = re.search(r'\$\s*([\d,]+\.\d{2})', body[:1000])
    order_num = f"#{order_m.group(1)}" if order_m else "new order"
    total     = f"${total_m.group(1)}" if total_m else ""
    return order_num, total

def is_amazon_email(frm, subj, body):
    """Heuristic: forwarded Amazon emails often keep the original subject/body."""
    indicators = ['amazon.com', 'amazon order', 'your order', 'shipment', 'delivery estimate',
                  'arriving', 'out for delivery', 'shipped', 'package']
    text = (frm + " " + subj + " " + body[:500]).lower()
    return sum(1 for ind in indicators if ind in text) >= 2

def parse_amazon_delivery(body, subj):
    """Try to extract a delivery date mention from an Amazon email."""
    # Patterns like "Arriving Tuesday, March 3" / "Estimated delivery March 3" / "by Tuesday, March 3"
    patterns = [
        r'[Aa]rriving\s+(?:by\s+)?(\w+day,?\s+\w+\s+\d{1,2})',
        r'[Ee]stimated\s+delivery[:\s]+(\w+day,?\s+\w+\s+\d{1,2})',
        r'[Ee]xpected\s+(?:delivery\s+)?by\s+(\w+day,?\s+\w+\s+\d{1,2})',
        r'[Dd]elivery\s+[Dd]ate[:\s]+(\w+day,?\s+\w+\s+\d{1,2})',
        r'[Dd]elivered\s+(?:on\s+)?(\w+day,?\s+\w+\s+\d{1,2})',
    ]
    for pat in patterns:
        m = re.search(pat, body)
        if m:
            return m.group(1).strip()
    return None

def check_email():
    creds = json.load(open(CREDS_PATH))
    mail  = imaplib.IMAP4_SSL("posteo.de", 993)
    mail.login(creds["username"], creds["password"])
    mail.select("INBOX")

    # Emails since ~8pm last night (overnight window)
    since = (datetime.now(timezone.utc) - timedelta(hours=14)).strftime("%d-%b-%Y")
    _, messages = mail.search(None, f'SINCE "{since}"')
    ids = messages[0].split()

    glimmer_orders = []  # (order_num, total, subject)
    amazon_today  = []   # (subject, delivery_date, body_snippet)
    attention     = []   # (from, subject)
    skip_patterns = ["drubot@posteo", "mailer-daemon", "posteo.de", "noreply",
                     "no-reply", "do-not-reply", "notifications@", "notification@",
                     "amazon.com", "amazon marketplace", "@amazon"]

    for mid in ids:
        _, data = mail.fetch(mid, "(RFC822)")
        msg  = email.message_from_bytes(data[0][1])
        frm  = ds(msg["From"])
        subj = ds(msg["Subject"])
        body = get_body(msg)

        # skip noise
        if any(p in frm.lower() for p in skip_patterns):
            continue
        # skip RFQ blast bounces
        if "Undelivered Mail" in subj or "Undeliverable" in subj or "delivery failed" in subj.lower():
            continue
        # skip our own manufacturer outreach summaries
        if "Manufacturer Outreach Summary" in subj:
            continue
        # skip Amazon review/rating requests
        if any(p in subj.lower() for p in ["rate your", "leave a review", "write a review", "how was your", "share your feedback"]):
            continue

        if is_glimmer_order(frm, subj, body):
            order_num, total = parse_glimmer_order(subj, body)
            glimmer_orders.append((order_num, total, subj))
        elif is_amazon_email(frm, subj, body):
            today_str = datetime.now(timezone(timedelta(hours=-8))).strftime("%B %-d")
            today_str2 = datetime.now(timezone(timedelta(hours=-8))).strftime("%b %-d")
            today_day  = datetime.now(timezone(timedelta(hours=-8))).strftime("%A")
            delivery   = parse_amazon_delivery(body, subj)
            is_today   = delivery and (
                today_str in delivery or today_str2 in delivery or
                today_day in delivery or "Today" in delivery or "today" in delivery
            )
            if is_today or "Delivered" in subj or "out for delivery" in body.lower():
                amazon_today.append((subj, delivery or "today", body[:200]))
        else:
            attention.append((frm, subj))

    mail.logout()
    return glimmer_orders, amazon_today, attention


# ── assemble briefing ─────────────────────────────────────────────────────────

def build_briefing():
    now = datetime.now(timezone(timedelta(hours=-8)))
    date_str = now.strftime("%A, %B %-d")

    sections = [f"☀️ Good morning, Aaron — {date_str}\n"]

    # Deadlines
    deadlines = get_deadlines()
    if deadlines:
        sections.append("⚠️ ACTION REQUIRED")
        for d in deadlines:
            sections.append(f"  {d}")

    # Markets
    sections.append("\n📈 MARKETS")
    sections.append(get_market_prices())

    # Weather
    sections.append("\n🌤 WEATHER")
    sections.append(get_weather())

    # Calendar
    sections.append("\n📅 TODAY'S CALENDAR")
    sections.append(get_calendar_events())

    # Email
    glimmer_orders, amazon_today, attention = check_email()

    # Glimmer Cards orders — TOP PRIORITY
    if glimmer_orders:
        order_lines = []
        for order_num, total, subj in glimmer_orders:
            line = f"  🛒 {order_num}"
            if total:
                line += f"  {total}"
            order_lines.append(line)
        sections.insert(1, "💳 GLIMMER CARDS ORDERS — " + str(len(glimmer_orders)) + " NEW\n" + "\n".join(order_lines) + "\n")

    # Amazon
    sections.append("\n📦 AMAZON DELIVERIES TODAY")
    if amazon_today:
        for subj, delivery, _ in amazon_today:
            sections.append(f"  • {subj} — {delivery}")
    else:
        sections.append("  Nothing arriving today (or no shipping emails yet).")

    # Email attention
    sections.append("\n✉️ EMAILS NEEDING ATTENTION")
    if attention:
        for frm, subj in attention:
            # trim display name clutter
            frm_short = re.sub(r'<.*?>', '', frm).strip().strip('"') or frm
            sections.append(f"  • {frm_short}: {subj}")
    else:
        sections.append("  Inbox quiet overnight.")

    # Fetch Spotify artists once — shared by both event sections
    spotify_artists = get_spotify_artists()

    # Nectar — full week
    sections.append("\n🎵 NECTAR THIS WEEK")
    sections.append(get_nectar_events(spotify_artists))

    # Seattle upcoming — 2-week lookahead across all venues
    sections.append("\n🗺 UPCOMING IN SEATTLE (next 2 weeks)")
    sections.append(get_seattle_upcoming(spotify_artists))

    sections.append("\n— Dru 🧙")
    return "\n".join(sections)


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    briefing = build_briefing()
    print(briefing)
    if "--send" in sys.argv:
        ok_tg = send_telegram(briefing)
        print("Telegram: sent" if ok_tg else "Telegram: FAILED")
        now = datetime.now(timezone(timedelta(hours=-8)))
        subject = f"☀️ Morning Briefing — {now.strftime('%A, %B %-d')}"
        ok_email = send_email(subject, briefing)
        print("Email: sent" if ok_email else "Email: FAILED")
