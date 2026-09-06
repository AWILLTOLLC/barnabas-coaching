#!/usr/bin/env python3
"""Morse Command subscribe endpoint — proxies email signups to Mailchimp."""

import json
import hashlib
import base64
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

MAILCHIMP_API_KEY = "55d54d9d57ca55ff494432766167aa6f-us19"
MAILCHIMP_DC = "us19"
AUDIENCE_ID = "2b76ea924c"
TAG = "morse-command-waitlist"
BASE_URL = f"https://{MAILCHIMP_DC}.api.mailchimp.com/3.0"
AUTH = base64.b64encode(f"mc:{MAILCHIMP_API_KEY}".encode()).decode()


def mc_request(url, method, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        method=method,
        headers={
            "Authorization": f"Basic {AUTH}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read()


def add_subscriber(email):
    email = email.strip().lower()
    email_hash = hashlib.md5(email.encode()).hexdigest()

    # Add or update member (status_if_new preserves existing subscribers)
    mc_request(
        f"{BASE_URL}/lists/{AUDIENCE_ID}/members/{email_hash}",
        "PUT",
        {"email_address": email, "status_if_new": "subscribed"},
    )

    # Tag as morse-command-waitlist
    mc_request(
        f"{BASE_URL}/lists/{AUDIENCE_ID}/members/{email_hash}/tags",
        "POST",
        {"tags": [{"name": TAG, "status": "active"}]},
    )


class SubscribeHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress default stdout log

    def send_json(self, code, body):
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self.path != "/subscribe":
            self.send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()

        try:
            ct = self.headers.get("Content-Type", "")
            if "application/json" in ct:
                email = json.loads(body).get("email", "")
            else:
                email = urllib.parse.parse_qs(body).get("email", [""])[0]
        except Exception:
            email = ""

        if not email or "@" not in email:
            self.send_json(400, {"error": "invalid email"})
            return

        try:
            add_subscriber(email)
            self.send_json(200, {"ok": True})
        except Exception as e:
            self.send_json(500, {"error": str(e)})


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 3731), SubscribeHandler)
    print("Subscribe server listening on 127.0.0.1:3731")
    server.serve_forever()
