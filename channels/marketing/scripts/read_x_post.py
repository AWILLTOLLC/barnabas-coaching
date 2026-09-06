#!/usr/bin/env python3
"""
read_x_post.py — Fetch a tweet + full thread via X API v2

Usage:
  python3 read_x_post.py <tweet_url_or_id>

Examples:
  python3 read_x_post.py https://x.com/DeRonin_/status/2032796569808830921
  python3 read_x_post.py 2032796569808830921

Output: human-readable thread dump to stdout
"""

import sys
import re
import json
import requests

CREDS_PATH = "/Users/apollo/.openclaw/credentials/x_api.json"

def load_bearer():
    with open(CREDS_PATH) as f:
        return json.load(f)["bearer_token"]

def extract_tweet_id(input_str):
    # Handle full URLs
    m = re.search(r"/status/(\d+)", input_str)
    if m:
        return m.group(1)
    # Handle raw IDs
    if re.match(r"^\d+$", input_str.strip()):
        return input_str.strip()
    raise ValueError(f"Cannot extract tweet ID from: {input_str}")

def fetch_tweet(tweet_id, bearer):
    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    params = {
        "tweet.fields": "text,author_id,created_at,conversation_id,referenced_tweets,entities",
        "expansions": "author_id,referenced_tweets.id",
        "user.fields": "name,username",
    }
    headers = {"Authorization": f"Bearer {bearer}"}
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json()

def fetch_thread(conversation_id, author_id, bearer):
    """Fetch all replies in thread from the original author."""
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": f"conversation_id:{conversation_id} from:{author_id}",
        "tweet.fields": "text,created_at,in_reply_to_user_id",
        "max_results": 100,
    }
    headers = {"Authorization": f"Bearer {bearer}"}
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    data = r.json()
    return data.get("data", [])

def clean_text(text):
    # Replace t.co links with placeholder note
    text = re.sub(r"https://t\.co/\S+", "[link]", text)
    return text

def main():
    if len(sys.argv) < 2:
        print("Usage: read_x_post.py <tweet_url_or_id>")
        sys.exit(1)

    tweet_id = extract_tweet_id(sys.argv[1])
    bearer = load_bearer()

    # Fetch root tweet
    data = fetch_tweet(tweet_id, bearer)
    tweet = data["data"]
    users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
    author = users.get(tweet["author_id"], {})
    author_name = author.get("name", "Unknown")
    author_handle = author.get("username", "unknown")

    print(f"=== @{author_handle} ({author_name}) ===")
    print(f"Posted: {tweet['created_at']}")
    print(f"ID: {tweet['id']}")
    print()
    print(clean_text(tweet["text"]))

    # Quoted tweet if present
    refs = tweet.get("referenced_tweets", [])
    included_tweets = {t["id"]: t for t in data.get("includes", {}).get("tweets", [])}
    for ref in refs:
        if ref["type"] == "quoted":
            qt = included_tweets.get(ref["id"])
            if qt:
                article = qt.get("article", {})
                print()
                print(f"--- Quoted tweet (ID: {ref['id']}) ---")
                if article.get("title"):
                    print(f"Article: {article['title']}")
                print(clean_text(qt.get("text", "")))

    # Fetch thread continuation (author's own replies)
    conversation_id = tweet.get("conversation_id", tweet_id)
    author_id = tweet["author_id"]
    thread_tweets = fetch_thread(conversation_id, author_id, bearer)

    if thread_tweets:
        # Filter out replies to others (pure @reply noise) — keep ones that read as thread continuations
        thread_tweets.sort(key=lambda t: t["created_at"])
        print()
        print(f"=== Thread replies by @{author_handle} ({len(thread_tweets)} found) ===")
        for t in thread_tweets:
            text = t["text"]
            # Skip pure @mention replies (they're Q&A noise, not thread content)
            if text.startswith("@") and text.count("\n") < 2:
                print(f"\n[Q&A reply] {clean_text(text)}")
            else:
                print(f"\n--- {t['created_at']} ---")
                print(clean_text(text))

if __name__ == "__main__":
    main()
