#!/usr/bin/env python3
"""
test_imessage_route.py — regression test for the cross-channel announce-reply routing bug.

Bug: a subagent-completion announce delivered into the *webchat* main session
(agent:main:main, session 9138659a-...) caused that session's final reply to be
delivered to iMessage (chat_id:1) instead of webchat, and bound the webchat
session to the iMessage conversation.

Assertion under test (crisp):
    A final reply from agent:main:main on the webchat surface must route to
    webchat — never to imessage.

The test reimplements the two OpenClaw routing decisions from the installed
source (openclaw 2026.9.2, /opt/homebrew/lib/node_modules/openclaw/dist):

  1. bound-delivery-router.resolveDestination
     (dist/subagent-announce-delivery-CB6b5kft.js, region
      src/infra/outbound/bound-delivery-router.ts)
  2. resolveEffectiveReplyRoute
     (dist/effective-reply-route-BeVh8uZJ.js, region
      src/auto-reply/reply/effective-reply-route.ts) — including the
      isSessionsSendInterSessionHandoff branch that inherits the persisted
      external delivery route on webchat.

It reads the *live* binding/delivery state from a fresh copy of the agent DB
(copy-on-read; never touches the original) and evaluates the routing decision
for the exact conditions observed in the incident.

Expected result:
  - Before fix: FAIL (reply routes to imessage — bug reproduced in isolation)
  - After fix:  PASS (reply routes to webchat)

Usage: python3 scripts/test_imessage_route.py
Exit code 0 = PASS, 1 = FAIL (bug present), 2 = environment error.
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile

MAIN_SESSION_KEY = "agent:main:main"
MAIN_SESSION_ID = "9138659a-5c6a-4128-a6da-0b887221e6d8"
BUG_CONVERSATION_ID = "conv_47a66cd72dbdb37dc81275ca910ab6cc"
DB_SOURCE = os.path.expanduser("~/.openclaw/agents/main/agent/openclaw-agent.sqlite")


def load_state():
    """Copy the agent DB and extract (bindings, persisted delivery context)."""
    if not os.path.exists(DB_SOURCE):
        print(f"ENV-ERROR: agent DB not found at {DB_SOURCE}", file=sys.stderr)
        sys.exit(2)
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        tmp_path = tmp.name
    shutil.copy2(DB_SOURCE, tmp_path)
    try:
        conn = sqlite3.connect(tmp_path)  # writable copy; source never touched
        conn.row_factory = sqlite3.Row
        bindings = [
            dict(r)
            for r in conn.execute(
                """
                SELECT sc.session_id, sc.role, c.channel, c.conversation_id,
                       c.delivery_target
                  FROM session_conversations sc
                  JOIN conversations c USING (conversation_id)
                """
            )
        ]
        row = conn.execute(
            "SELECT entry_json FROM session_nodes WHERE session_key = ?",
            (MAIN_SESSION_KEY,),
        ).fetchone()
        entry = json.loads(row["entry_json"]) if row else {}
    finally:
        os.unlink(tmp_path)

    # Persisted external delivery context on the session entry
    # (dist/delivery-context.shared-CXmRgetN.js: deliveryContextFromSession)
    delivery = entry.get("delivery") or {}
    persisted = (
        delivery.get("context") if delivery.get("kind") == "external" else None
    )
    return bindings, persisted


def resolve_effective_reply_route(persisted_delivery_context, *,
                                  input_provenance_kind="inter_session",
                                  source_tool="sessions_send",
                                  current_surface="webchat",
                                  originating_channel=None,
                                  originating_to=None):
    """
    Reimplementation of resolveEffectiveReplyRoute
    (dist/effective-reply-route-BeVh8uZJ.js).

    Only the branches exercised by the incident are modeled:
      - the sessions_send inter-session handoff branch (inherits persisted
        external route on webchat), and
      - the internal-turn-source fallback (uses live originating channel).
    """
    persisted_channel = (persisted_delivery_context or {}).get("channel")
    persisted_to = (persisted_delivery_context or {}).get("to")

    # isSessionsSendInterSessionHandoff(ctx.InputProvenance)
    handoff = (
        input_provenance_kind == "inter_session"
        and (source_tool or "").lower() == "sessions_send"
    )
    if (
        handoff
        and current_surface == "webchat"
        and persisted_channel
        and persisted_channel != "webchat"
        and persisted_to
    ):
        return {
            "channel": persisted_channel,
            "to": persisted_to,
            "inheritedExternalRoute": True,
        }
    if originating_channel is None:  # ctx.InternalTurnSource === undefined
        return {"channel": originating_channel, "to": originating_to}
    # canInheritPersistedTuple
    can_inherit = originating_channel == persisted_channel
    return {
        "channel": originating_channel,
        "to": originating_to
        or (persisted_to if can_inherit else None),
    }


def main():
    bindings, persisted = load_state()

    print("== State under test ==")
    print(f"session entry ({MAIN_SESSION_KEY}) persisted delivery context: "
          f"{json.dumps(persisted)}")
    my_bindings = [b for b in bindings if b["session_id"] == MAIN_SESSION_ID]
    for b in my_bindings:
        print(f"binding: role={b['role']} channel={b['channel']} "
              f"conversation={b['conversation_id']} target={b['delivery_target']}")

    print("\n== Routing decision ==")
    # Exact incident conditions: announce turn lands in the webchat main
    # session as a sessions_send inter-session handoff.
    route = resolve_effective_reply_route(persisted)
    channel = route.get("channel")
    print(f"resolved reply route: channel={channel} to={route.get('to')} "
          f"inheritedExternalRoute={route.get('inheritedExternalRoute', False)}")

    print("\n== Assertion ==")
    print("REQUIREMENT: reply from agent:main:main must route to webchat, "
          "not imessage.")

    failures = []
    if channel != "webchat":
        failures.append(
            f"reply from {MAIN_SESSION_KEY} routes to channel={channel!r} "
            f"(to={route.get('to')!r}); expected webchat"
        )
    stale = [b for b in my_bindings if b["channel"] != "webchat"]
    for b in stale:
        failures.append(
            f"webchat session bound to non-webchat conversation: "
            f"role={b['role']} channel={b['channel']} "
            f"conversation={b['conversation_id']}"
        )

    if failures:
        print("FAIL — cross-channel routing bug present:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print("PASS — reply from agent:main:main routes to webchat; no "
          "cross-channel bindings present.")
    sys.exit(0)


if __name__ == "__main__":
    main()
