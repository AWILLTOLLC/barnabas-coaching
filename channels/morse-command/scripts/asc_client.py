#!/usr/bin/env python3
"""
App Store Connect API client for Morse Command.
Requires: PyJWT, cryptography (installed in /tmp/asc-venv)
Usage: /tmp/asc-venv/bin/python3 scripts/asc_client.py [command]
Commands: reviews, sales [YYYY-MM-DD], appinfo
"""

import jwt, time, json, gzip, sys, urllib.request
from datetime import datetime, timedelta, timezone

CREDS_PATH = "/Users/apollo/.openclaw/credentials/appstore_connect.json"
APP_ID = "6759479305"
VENDOR_NUMBER = "85612226"

def load_creds():
    with open(CREDS_PATH) as f:
        return json.load(f)

def make_token(creds):
    with open(creds["private_key_path"]) as f:
        private_key = f.read()
    payload = {
        "iss": creds["issuer_id"],
        "iat": int(time.time()),
        "exp": int(time.time()) + 1200,
        "aud": "appstoreconnect-v1"
    }
    return jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": creds["key_id"]})

def get(url, creds, accept="application/json"):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {make_token(creds)}",
        "Accept": accept
    })
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
        if accept == "application/a-gzip":
            return gzip.decompress(raw).decode("utf-8")
        return json.loads(raw)

def cmd_reviews(creds):
    data = get(
        f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/customerReviews"
        "?sort=-createdDate&limit=25",
        creds
    )
    reviews = data.get("data", [])
    print(f"Reviews: {len(reviews)}")
    for r in reviews:
        a = r["attributes"]
        print(f"  ⭐{a['rating']} [{a['createdDate'][:10]}] {a['title']!r} — {a['reviewerNickname']}")
        print(f"    {a['body'][:200]}")

def cmd_appinfo(creds):
    data = get(
        f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}"
        "?fields[apps]=name,bundleId,primaryLocale",
        creds
    )
    print(json.dumps(data["data"]["attributes"], indent=2))

def cmd_sales(creds, date=None):
    if not date:
        date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    url = (
        "https://api.appstoreconnect.apple.com/v1/salesReports"
        "?filter[frequency]=DAILY"
        "&filter[reportType]=SALES"
        "&filter[reportSubType]=SUMMARY"
        f"&filter[reportDate]={date}"
        f"&filter[vendorNumber]={VENDOR_NUMBER}"
    )
    text = get(url, creds, accept="application/a-gzip")
    lines = text.strip().split("\n")
    headers = lines[0].split("\t")
    print(f"Sales for {date}:")
    for l in lines[1:]:
        cols = dict(zip(headers, l.split("\t")))
        if APP_ID in cols.get("Apple Identifier", ""):
            print(f"  {cols.get('Title')} | Units: {cols.get('Units')} | Revenue: {cols.get('Developer Proceeds')} {cols.get('Currency of Proceeds')} | Country: {cols.get('Country Code')}")

if __name__ == "__main__":
    creds = load_creds()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "reviews"
    if cmd == "reviews":
        cmd_reviews(creds)
    elif cmd == "sales":
        date_arg = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_sales(creds, date_arg)
    elif cmd == "appinfo":
        cmd_appinfo(creds)
    else:
        print(f"Unknown command: {cmd}")
