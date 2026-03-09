#!/usr/bin/env python3
"""
Apply Voice DNA rules to barnabas-coaching site copy.
Fixes: em dashes, spelled-out numbers, banned words, FATAL patterns.
"""

import re, os

PAGES_DIR = "/root/.openclaw/workspace/projects/barnabas-coaching/src/pages"

# --- index.astro fixes ---
INDEX = os.path.join(PAGES_DIR, "index.astro")

index_replacements = [
    # Description meta
    ("AI strategy coaching for Seattle small businesses — audits, retainers, and hands-on implementation guidance.",
     "AI strategy coaching for Seattle small businesses: audits, retainers, and hands-on implementation guidance."),
    ("Led by Aaron Williams — technologist, operator, and AI strategist.",
     "Led by Aaron Williams: technologist, operator, and AI strategist."),
    # Pillar: He doesn't chase
    ("He doesn't chase what's new — he evaluates what's proven, what's ready, and what fits your specific business.",
     "He doesn't chase what's new. He evaluates what's proven, what's ready, and what fits your specific business."),
    # Pillar: Aaron's job
    ("Aaron's job is to tell you the truth — including when the right answer is \"not yet\" or \"this one's not worth your time.\"",
     "Aaron's job is to tell you the truth, including when the right answer is \"not yet\" or \"this one's not worth your time.\""),
    # Pillar: over eight years
    ("Aaron has run his own businesses for over eight years.",
     "Aaron has run his own businesses for over 8 years."),
    # Pillar: not advising from a PowerPoint — FATAL: "He's not X — he's Y"
    ("He's not advising from a PowerPoint — he's been there.",
     "He's advised from experience, not a presentation deck."),
    # Hero description
    ("Barnabas Coaching helps Seattle small businesses move past the hype and build real AI workflows —\n          led by Aaron Williams, a technologist who has been at the bleeding edge before.",
     "Barnabas Coaching helps Seattle small businesses move past the hype and build real AI workflows. Led by Aaron Williams, a technologist who has been at the bleeding edge before."),
    # Aaron teaser: MSN Messenger
    ("working on MSN Messenger —\n          one of the first products",
     "working on MSN Messenger, one of the first products"),
    # Aaron teaser: wave hits
    ("He's seen what it looks like when a wave hits — the confusion, the urgency, the organizations that",
     "He's seen what it looks like when a wave hits: the confusion, the urgency, the organizations that"),
    # Timeline card
    ("'Writing VoIP routing code — pre-Skype'",
     "'Writing VoIP routing code, pre-Skype'"),
    # Final CTA — FATAL: "No pitch, no pressure — just..."
    ("Start with a free 30-minute discovery call. No pitch, no pressure — just an honest conversation\n        about where you are and where AI can take you.",
     "Start with a free 30-minute discovery call. A genuine conversation about where your business is and where AI can take you."),
]

# --- about.astro fixes ---
ABOUT = os.path.join(PAGES_DIR, "about.astro")

about_replacements = [
    # Meta description
    ("25+ year career at the leading edge of technology — from early VoIP to Microsoft, Accenture, and 16 years of senior advisory work in Seattle.",
     "25+ year career at the leading edge of technology: early VoIP, Microsoft, Accenture, and 16 years of senior advisory work in Seattle."),
    ("from writing early VoIP code in the 1990s to Technical Program Manager at Microsoft to AI strategy coaching for Seattle businesses.",
     "from writing early VoIP code in the 1990s to Technical Program Manager at Microsoft to founding Barnabas Coaching."),
    # Body: not because it was cool
    ("Not because it was cool — it wasn't yet — but because it was the most\n            interesting thing he could find.",
     "Not because it was cool (it wasn't). Because it was the most interesting thing he could find."),
    # Body: MSN Messenger — later Windows Live
    ("as a Technical Program Manager on MSN Messenger — later Windows Live\n            Messenger.",
     "as a Technical Program Manager on MSN Messenger (later Windows Live Messenger)."),
    # Body: for Microsoft consultants — translating
    ("for Microsoft consultants — translating technical complexity into learning that actually landed for",
     "for Microsoft consultants, translating technical complexity into learning that actually landed for"),
    # Body: Sections headers with "Eight years"
    ("<h2 class=\"font-serif text-2xl font-bold text-slate-900 pt-4\">Eight years in the biotech trenches.</h2>",
     "<h2 class=\"font-serif text-2xl font-bold text-slate-900 pt-4\">8 years in the biotech trenches.</h2>"),
    # Body: "After Accenture, Aaron served for eight years"
    ("Aaron served for eight years as the trusted technology advisor",
     "Aaron served for 8 years as the trusted technology advisor"),
    # Body: "a relationship conducted under NDA"
    ("a prominent\n            Seattle-area executive — a relationship conducted under NDA.",
     "a prominent Seattle-area executive (under NDA)."),
    # Body: "last eight years"
    ("Aaron has spent the last eight years running",
     "Aaron has spent the last 8 years running"),
    # Body: Biotechs are demanding clients — high stakes
    ("Biotechs are demanding clients — high stakes,\n            fast-moving, deeply technical, and operating under regulatory pressure",
     "Biotechs are demanding clients: high stakes, fast-moving, deeply technical, operating under regulatory pressure"),
    # Body: development process — not as a novelty
    ("the development process — not as a novelty, but as a genuine accelerant.",
     "the development process, as a genuine accelerant."),
    # Body: and it worked — FATAL check: "and it worked — not perfectly..."
    ("and it worked — not perfectly, not magically, but practically.",
     "and it worked. Practically, concretely, measurably."),
    # Body: The pattern — in VoIP in '99, in AI now —
    ("The pattern Aaron has seen twice — in VoIP in '99, in AI now — is the same",
     "The pattern Aaron has seen twice (in VoIP in '99, in AI now) is the same"),
    # Body: time to become AI experts — and shouldn't have to
    ("time to become AI experts — and shouldn't have to.",
     "time to become AI experts, and shouldn't have to."),
    # Timeline: Writing VoIP routing code — years before Skype
    ("'Writing VoIP routing code — years before Skype.'",
     "'Writing VoIP routing code. Years before Skype.'"),
    # Timeline: Management Consultant, Accenture — built
    ("'Management Consultant, Accenture — built training solutions for Microsoft consultants.'",
     "'Management Consultant, Accenture. Built training solutions for Microsoft consultants.'"),
    # Timeline: Barnabas Coaching — AI strategy
    ("'Barnabas Coaching — AI strategy for Seattle SMBs.'",
     "'Barnabas Coaching: AI strategy for Seattle SMBs.'"),
]

# --- services.astro fixes ---
SERVICES = os.path.join(PAGES_DIR, "services.astro")

services_replacements = [
    # leverage
    ("genuine leverage, and delivers a written report you can act on immediately — or hand to your team.",
     "real returns, and delivers a written report you can act on immediately, or hand to your team."),
    # written report — written for an owner
    ("'A clear, jargon-free document covering findings, opportunities, and risks — written for an owner, not a CTO.'",
     "'A clear, jargon-free document covering findings, opportunities, and risks. Written for an owner, not a CTO.'"),
    # You want an objective view — not a vendor pitch
    ("'You want an objective view — not a vendor pitch'",
     "'You want an objective view, with no vendor pitch attached'"),
    # isn't a one-time event — it's an ongoing process — FATAL: "isn't X — it's Y"
    ("Building AI into a business isn't a one-time event — it's an ongoing process of testing, adjusting,",
     "Building AI into a business is an ongoing process of testing, adjusting,"),
    # Structured working sessions — progress review
    ("'Structured working sessions focused on your current priorities — progress review, problem-solving, and next steps.'",
     "'Structured working sessions focused on your current priorities: progress review, problem-solving, and next steps.'"),
    # Each month is shaped — not a fixed curriculum
    ("'Each month is shaped by what matters most to your business right now — not a fixed curriculum.'",
     "'Each month is shaped by what matters most to your business right now, with no fixed curriculum.'"),
    # AI strategy translates across industries — the workflow
    ("AI strategy translates across industries — the workflow assessment approach",
     "AI strategy translates across industries. The workflow assessment approach"),
    # tell you honestly which option makes sense — or whether
    ("tell you honestly which option makes sense — or whether the timing isn't right yet.",
     "tell you honestly which option makes sense, or whether the timing isn't right yet."),
]

# --- blog/index.astro fixes ---
BLOG = os.path.join(PAGES_DIR, "blog/index.astro")

blog_replacements = [
    # wrong first question — and what to ask
    ("\"Why asking 'what AI tools should I use?' is the wrong first question — and what to ask instead.\"",
     "\"Why asking 'what AI tools should I use?' is the wrong first question. And what to ask instead.\""),
    # actually look like — and what it means
    ("\"Aaron's firsthand perspective on what the early days of a transformative technology actually look like — and what it means for where we are now.\"",
     "\"Aaron's firsthand perspective on what the early days of a transformative technology actually look like, and what it means for where we are now.\""),
    # Not the flashiest — the ones — FATAL: "Not X. Y."
    ("'Not the flashiest applications — the ones that pay back their cost fastest and build the internal muscle for more.'",
     "'The 3 applications that pay back their cost fastest and build the internal muscle for more, even if they're not the flashiest.'"),
    # landscape -> scene
    ("'Seattle business landscape',",
     "'Seattle business scene',"),
    # technology — from early VoIP
    ("technology — from early VoIP to Microsoft to biotech IT consulting to AI-assisted",
     "technology: early VoIP, Microsoft, biotech IT consulting, and AI-assisted"),
]

# --- contact.astro fixes ---
CONTACT = os.path.join(PAGES_DIR, "contact.astro")

contact_replacements = [
    # no pitch, no pressure — FATAL
    ("Find out what AI can actually do for your Seattle business — no pitch, no pressure.",
     "Find out what AI can actually do for your Seattle business."),
    # genuinely useful — regardless
    ("The discovery call is free, 30 minutes, and genuinely useful — regardless of whether\n        you end up working with Aaron.",
     "The discovery call is free, 30 minutes, and genuinely useful regardless of whether you end up working with Aaron."),
    # where AI fits — and doesn't — for your situation
    ("\"You'll hear an honest take on where AI fits — and doesn't — for your situation. No vague answers. No upselling.\"",
     "\"You'll hear an honest take on where AI fits for your situation, and where it doesn't. No upselling.\""),
]

def apply_replacements(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changes = 0
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            changes += 1
        else:
            print(f"  ⚠️  NOT FOUND: {old[:60]}...")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✓ {filepath.split('/')[-1]}: {changes}/{len(replacements)} replacements applied")

print("Applying Voice DNA fixes...")
apply_replacements(INDEX, index_replacements)
apply_replacements(ABOUT, about_replacements)
apply_replacements(SERVICES, services_replacements)
apply_replacements(BLOG, blog_replacements)
apply_replacements(CONTACT, contact_replacements)

# Final check: any remaining em dashes?
print("\nChecking for remaining em dashes...")
for root, dirs, files in os.walk(PAGES_DIR):
    for fname in files:
        if fname.endswith('.astro'):
            fpath = os.path.join(root, fname)
            with open(fpath) as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if ' — ' in line or '—' in line:
                    if not line.strip().startswith('//') and not line.strip().startswith('#'):
                        print(f"  [{fname}:{i}] {line.strip()[:80]}")
