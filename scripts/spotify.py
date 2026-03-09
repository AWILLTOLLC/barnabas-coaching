#!/usr/bin/env python3
"""
spotify.py — Spotify API helper for Dru
Fetches Aaron's top artists, recently played, and followed artists.
Auto-refreshes access token using stored refresh token.
"""

import json, requests, base64, time
from pathlib import Path

CREDS_PATH = Path("/root/.openclaw/credentials/spotify.json")


def _load_creds():
    return json.loads(CREDS_PATH.read_text())

def _save_creds(creds):
    CREDS_PATH.write_text(json.dumps(creds, indent=2))

def get_access_token():
    creds = _load_creds()
    client_id     = creds["client_id"]
    client_secret = creds["client_secret"]
    refresh_token = creds["refresh_token"]

    b64 = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {b64}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()

    # Spotify may issue a new refresh token
    if "refresh_token" in data:
        creds["refresh_token"] = data["refresh_token"]
        _save_creds(creds)

    return data["access_token"]


def _get(path, params=None):
    token = get_access_token()
    r = requests.get(
        f"https://api.spotify.com/v1{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def get_top_artists(time_range="short_term", limit=50):
    """
    time_range: short_term (~4 weeks), medium_term (~6 months), long_term (years)
    Returns list of artist name strings.
    """
    data = _get("/me/top/artists", {"time_range": time_range, "limit": limit})
    return [a["name"] for a in data.get("items", [])]


def get_recently_played(limit=50):
    """Returns list of unique artist name strings from recently played tracks."""
    data = _get("/me/player/recently-played", {"limit": limit})
    seen = set()
    artists = []
    for item in data.get("items", []):
        for artist in item["track"]["artists"]:
            name = artist["name"]
            if name not in seen:
                seen.add(name)
                artists.append(name)
    return artists


def get_followed_artists(limit=50):
    """Returns list of artist name strings Aaron follows."""
    data = _get("/me/following", {"type": "artist", "limit": limit})
    return [a["name"] for a in data.get("artists", {}).get("items", [])]


def get_all_liked_artists():
    """
    Combines top artists (short + medium term), recently played, and followed artists.
    Returns a deduplicated lowercase set for fast matching.
    """
    names = set()
    try:
        for a in get_top_artists("short_term"):
            names.add(a.lower())
        for a in get_top_artists("medium_term"):
            names.add(a.lower())
        for a in get_recently_played():
            names.add(a.lower())
        for a in get_followed_artists():
            names.add(a.lower())
    except Exception as e:
        print(f"[spotify] Warning: {e}")
    return names


if __name__ == "__main__":
    print("=== Top Artists (last 4 weeks) ===")
    for a in get_top_artists("short_term"):
        print(f"  {a}")

    print("\n=== Top Artists (last 6 months) ===")
    for a in get_top_artists("medium_term"):
        print(f"  {a}")

    print("\n=== Recently Played ===")
    for a in get_recently_played(20):
        print(f"  {a}")

    print("\n=== Followed Artists ===")
    for a in get_followed_artists():
        print(f"  {a}")
