#!/usr/bin/env python3
"""
Apple Search Ads daily report script.
Pulls prior day impressions, taps, and spend for the Morse Command campaign.
Sends a summary to Aaron via email.

Credentials: /Users/apollo/.openclaw/credentials/apple_search_ads.json
Private key:  /Users/apollo/.openclaw/agents/marketing/apple_ads_private.pem

Campaign: US Morse Command Campaign (ID: 2143622293)
Org ID: 21160890
"""

import jwt
import time
import json
import requests
from datetime import datetime, timedelta
import subprocess
import sys

CREDS_PATH = "/Users/apollo/.openclaw/credentials/apple_search_ads.json"
ORG_ID = 21160890
CAMPAIGN_ID = 2143622293
ADGROUP_ID = 2147335247
AARON_EMAIL = "a@kaw.cc"
SEND_SCRIPT = "/Users/apollo/.openclaw/workspace/scripts/send_email.py"


def get_access_token():
    with open(CREDS_PATH) as f:
        creds = json.load(f)
    with open(creds["private_key_path"]) as f:
        private_key = f.read()

    payload = {
        "sub": creds["client_id"],
        "aud": "https://appleid.apple.com",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "iss": creds["team_id"]
    }
    token = jwt.encode(payload, private_key, algorithm="ES256",
                       headers={"alg": "ES256", "kid": creds["key_id"]})

    resp = requests.post("https://appleid.apple.com/auth/oauth2/token", data={
        "grant_type": "client_credentials",
        "client_id": creds["client_id"],
        "client_secret": token,
        "scope": "searchadsorg"
    })
    return resp.json()["access_token"]


def get_campaign_report(access_token, date_str):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={ORG_ID}",
        "Content-Type": "application/json"
    }

    payload = {
        "startTime": date_str,
        "endTime": date_str,
        "granularity": "DAILY",
        "selector": {
            "orderBy": [{"field": "impressions", "sortOrder": "DESCENDING"}],
            "pagination": {"offset": 0, "limit": 10}
        },
        "returnRowTotals": True,
        "returnGrandTotals": True
    }

    r = requests.post(
        f"https://api.searchads.apple.com/api/v5/reports/campaigns",
        headers=headers,
        json=payload
    )
    return r.json()


def get_keyword_report(access_token, date_str):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={ORG_ID}",
        "Content-Type": "application/json"
    }

    payload = {
        "startTime": date_str,
        "endTime": date_str,
        "granularity": "DAILY",
        "selector": {
            "orderBy": [{"field": "impressions", "sortOrder": "DESCENDING"}],
            "pagination": {"offset": 0, "limit": 20}
        },
        "returnRowTotals": True,
        "returnGrandTotals": True
    }

    r = requests.post(
        f"https://api.searchads.apple.com/api/v5/reports/campaigns/{CAMPAIGN_ID}/adgroups/{ADGROUP_ID}/keywords",
        headers=headers,
        json=payload
    )
    return r.json()


def format_report(campaign_data, keyword_data, date_str):
    lines = [f"Apple Search Ads — Morse Command Daily Report ({date_str})", ""]

    try:
        # Campaign totals are in row[0].total (no grandTotals key in this endpoint)
        rows = campaign_data["data"]["reportingDataResponse"]["row"]
        totals = rows[0]["total"] if rows else {}
        impressions = totals.get("impressions", 0)
        taps = totals.get("taps", 0)
        installs = totals.get("totalInstalls", 0)
        spend = float(totals.get("localSpend", {}).get("amount", 0))
        avg_cpt = float(totals.get("avgCPT", {}).get("amount", 0))
        ctr = (taps / impressions * 100) if impressions > 0 else 0
        cpi = (spend / installs) if installs > 0 else 0

        lines += [
            "SUMMARY",
            f"  Impressions: {impressions:,}",
            f"  Taps:        {taps:,}",
            f"  Installs:    {installs:,}",
            f"  Spend:       ${spend:.2f}",
            f"  CTR:         {ctr:.1f}%",
            f"  Avg CPT:     ${avg_cpt:.2f}",
            f"  CPI:         ${cpi:.2f}" if installs > 0 else "  CPI:         n/a",
            ""
        ]

        if impressions == 0:
            lines.append("STATUS: Zero impressions. Bids may still need to be raised.")
        elif installs == 0 and taps > 0:
            lines.append("STATUS: Getting taps but no installs. Check App Store listing conversion.")
        elif installs > 0:
            lines.append("STATUS: Campaign converting. Monitor CPI vs target.")
        lines.append("")

    except Exception as e:
        lines += [f"Could not parse campaign totals: {e}", ""]

    # Keyword breakdown
    try:
        rows = keyword_data["data"].get("reportingDataResponse", {}).get("row", [])
        if rows:
            lines.append("TOP KEYWORDS")
            for row in rows[:10]:
                kw = row.get("metadata", {}).get("keyword", row.get("metadata", {}).get("keywordText", "unknown"))
                m = row.get("granularity", [{}])[0] if row.get("granularity") else {}
                imp = m.get("impressions", 0)
                tap = m.get("taps", 0)
                inst = m.get("newDownloads", 0)
                lines.append(f"  {kw:<30} imp={imp:>5}  taps={tap:>3}  installs={inst:>2}")
    except Exception as e:
        lines.append(f"Could not parse keyword data: {e}")

    lines += ["", "---", "Managed by Maven | marketing channel"]
    return "\n".join(lines)


def main():
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Fetching ASA report for {yesterday}...")
    token = get_access_token()
    campaign_data = get_campaign_report(token, yesterday)
    keyword_data = get_keyword_report(token, yesterday)

    report = format_report(campaign_data, keyword_data, yesterday)
    print(report)

    subject = f"Morse Command ASA Report — {yesterday}"
    result = subprocess.run(
        ["python3", SEND_SCRIPT, AARON_EMAIL, subject, report],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("Report emailed to Aaron.")
    else:
        print(f"Email failed: {result.stderr}")


if __name__ == "__main__":
    main()
