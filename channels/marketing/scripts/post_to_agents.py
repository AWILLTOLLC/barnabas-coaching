#!/usr/bin/env python3
"""
Post a message to the agents channel (Clubhouse) via gateway WebSocket RPC.

Usage: python3 post_to_agents.py "Your message here"

Notes:
- Uses vantage.message RPC directly — the `message` tool can't target 
  agents channel by slug because it has no bound agent session.
- To fan out to specific agents, @mention them: @Eagle @Spark etc.
- Empty @mentions = broadcast to all. @Aaron only = no fan-out.
"""

import asyncio
import json
import sys
import uuid
import os

CONFIG_PATH = os.path.expanduser('~/.openclaw/openclaw.json')

def get_token():
    with open(CONFIG_PATH) as f:
        return json.load(f)['gateway']['auth']['token']

async def post_to_agents(message: str, channel: str = 'clubhouse') -> dict:
    try:
        import websockets
    except ImportError:
        raise RuntimeError("websockets not installed. Run: pip3 install websockets --break-system-packages")
    
    token = get_token()
    
    async with websockets.connect('ws://127.0.0.1:18789') as ws:
        # Wait for challenge
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('event') == 'connect.challenge':
                break
        
        # Authenticate
        conn_id = str(uuid.uuid4())
        await ws.send(json.dumps({
            'type': 'req', 'id': conn_id, 'method': 'connect',
            'params': {
                'minProtocol': 1, 'maxProtocol': 5,
                'client': {'id': 'gateway-client', 'version': '1.0.0', 'platform': 'linux', 'mode': 'backend'},
                'caps': [], 'auth': {'token': token},
                'role': 'operator', 'scopes': ['operator.admin']
            }
        }))
        while True:
            resp = json.loads(await ws.recv())
            if resp.get('id') == conn_id:
                if not resp.get('ok'):
                    raise RuntimeError(f"Auth failed: {resp}")
                break
        
        # Post message
        call_id = str(uuid.uuid4())
        await ws.send(json.dumps({
            'type': 'req', 'id': call_id, 'method': 'vantage.message',
            'params': {
                'channel': channel,
                'content': message,
                'authorName': 'Maven',
                'agentSlug': 'marketing'
            }
        }))
        while True:
            resp = json.loads(await ws.recv())
            if resp.get('id') == call_id:
                return resp
    
    return {}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: post_to_agents.py <message>", file=sys.stderr)
        sys.exit(1)
    
    message = sys.argv[1]
    result = asyncio.run(post_to_agents(message))
    
    if result.get('ok'):
        print(f"✅ Posted to agents channel. Fanned out to {result.get('payload', {}).get('fanned', 0)} agents.")
    else:
        print(f"❌ Failed: {result}", file=sys.stderr)
        sys.exit(1)
