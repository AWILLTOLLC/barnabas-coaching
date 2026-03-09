#!/usr/bin/env python3
"""
One-shot Spotify OAuth helper.
Run on your local machine (Mac), NOT on the server.
Starts a local server, opens the auth URL, captures the code, exchanges for tokens.
Prints the refresh token at the end — paste that to Dru.
"""

import http.server, threading, webbrowser, urllib.parse, requests, base64, json, sys

CLIENT_ID     = "49b531f29fbc4bde9823b17c10f724a3"
CLIENT_SECRET = "96b602feadfa40a084d6de7d64858fb9"
REDIRECT_URI  = "http://127.0.0.1:8888/callback"
SCOPES        = "user-top-read user-read-recently-played user-follow-read"

auth_code = None

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2>Got it! You can close this tab.</h2>")
        threading.Thread(target=self.server.shutdown).start()

    def log_message(self, *args): pass  # silence logs

server = http.server.HTTPServer(("localhost", 8888), Handler)

auth_url = (
    "https://accounts.spotify.com/authorize?"
    + urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": "dru_auth_2026",
    })
)

print("Opening Spotify auth in your browser...")
webbrowser.open(auth_url)
print("Waiting for callback on localhost:8888 ...")
server.serve_forever()

if not auth_code:
    print("ERROR: No auth code received.")
    sys.exit(1)

# Exchange code for tokens
creds_b64 = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
r = requests.post(
    "https://accounts.spotify.com/api/token",
    headers={"Authorization": f"Basic {creds_b64}",
             "Content-Type": "application/x-www-form-urlencoded"},
    data={"grant_type": "authorization_code",
          "code": auth_code,
          "redirect_uri": REDIRECT_URI},
)
tokens = r.json()

if "refresh_token" not in tokens:
    print("ERROR:", tokens)
    sys.exit(1)

print("\n✅ Success! Paste this refresh token to Dru:\n")
print(tokens["refresh_token"])
print()
