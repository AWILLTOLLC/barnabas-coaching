#!/usr/bin/env python3
"""
Ahrefs CSV Intake Processor — Maven Marketing Agent

Drop any Ahrefs export CSV into:
  /root/.openclaw/workspace/channels/marketing/ahrefs-exports/

Supported export types (auto-detected):
  - Keyword Explorer: keyword ideas, matching terms, related terms
  - Site Explorer > Organic Keywords: ranking keywords for a domain
  - Content Gap: keywords competitors rank for that you don't
  - SERP Overview: who ranks for a specific keyword

Output: Markdown brief saved alongside the CSV, printed to stdout.

Usage:
  python3 ahrefs_process.py <path/to/export.csv> [--business barnabas|glimmer|morse|blackraven]
  python3 ahrefs_process.py --latest   # process most recent file in ahrefs-exports/
  python3 ahrefs_process.py --all      # process all unprocessed files
"""

import sys
import csv
import json
import re
from pathlib import Path
from datetime import datetime

EXPORTS_DIR = Path("/root/.openclaw/workspace/channels/marketing/ahrefs-exports")

BUSINESS_CONTEXT = {
    "barnabas": {
        "name": "Barnabas Coaching",
        "audience": "Seattle SMB owners",
        "goal": "Discovery call bookings, thought leadership, SEO for 'AI consultant Seattle'",
        "priority_intent": ["informational", "commercial"],
    },
    "glimmer": {
        "name": "Glimmer Cards",
        "audience": "Festival-goers, ravers, EDM community",
        "goal": "Product discovery, affiliate traffic, festival/rave search terms",
        "priority_intent": ["informational", "transactional"],
    },
    "morse": {
        "name": "Morse Command",
        "audience": "Ham radio operators, preppers, survivalists",
        "goal": "App Store organic discovery, content that drives installs",
        "priority_intent": ["informational", "navigational"],
    },
    "blackraven": {
        "name": "Black Raven Company",
        "audience": "Bushcrafters, green woodworkers, premium tool collectors",
        "goal": "Community embedding, product discovery, 'scotch eye auger' search authority",
        "priority_intent": ["informational", "transactional"],
    },
}

def detect_export_type(headers):
    h = [x.lower().strip() for x in headers]
    if "keyword difficulty" in h or "kd" in h:
        if any("position" in x for x in h):
            return "organic_keywords"  # Site Explorer > Organic Keywords
        elif any("intersection" in x or "competitor" in x for x in h):
            return "content_gap"
        else:
            return "keyword_explorer"  # Keyword Explorer ideas
    if "url" in h and "traffic" in h and "referring domains" in h:
        return "backlinks"
    if "position" in h and "url" in h:
        return "organic_keywords"
    return "unknown"

def parse_number(val):
    """Parse Ahrefs number strings like '1,200' or '1.2K' or '12M'"""
    if not val or val.strip() in ("-", "", "N/A", "n/a"):
        return 0
    val = val.strip().replace(",", "")
    try:
        if val.endswith("K") or val.endswith("k"):
            return int(float(val[:-1]) * 1000)
        if val.endswith("M") or val.endswith("m"):
            return int(float(val[:-1]) * 1_000_000)
        return int(float(val))
    except:
        return 0

def score_keyword(row, headers):
    """Score a keyword by opportunity: high volume, low difficulty."""
    h = [x.lower().strip() for x in headers]
    
    vol_col = next((headers[i] for i, x in enumerate(h) if x in ("volume", "search volume", "vol")), None)
    kd_col  = next((headers[i] for i, x in enumerate(h) if x in ("kd", "keyword difficulty", "difficulty")), None)
    tp_col  = next((headers[i] for i, x in enumerate(h) if "traffic potential" in x.lower() or x.lower() == "tp"), None)
    
    volume = parse_number(row.get(vol_col, "0")) if vol_col else 0
    kd     = parse_number(row.get(kd_col, "100")) if kd_col else 100
    tp     = parse_number(row.get(tp_col, "0")) if tp_col else 0
    
    # Opportunity score: penalize high KD, reward volume + traffic potential
    if volume == 0 and tp == 0:
        return 0
    effective_volume = max(volume, tp)
    kd_penalty = max(0, kd - 20) / 80  # 0 if KD<=20, scales to 1.0 at KD=100
    score = effective_volume * (1 - kd_penalty * 0.7)
    return int(score)

def process_keyword_explorer(rows, headers, business=None):
    """Process Keyword Explorer export — find content opportunities."""
    h_lower = [x.lower().strip() for x in headers]
    kw_col  = next((headers[i] for i, x in enumerate(h_lower) if x in ("keyword", "query", "term")), headers[0] if headers else "keyword")
    kd_col  = next((headers[i] for i, x in enumerate(h_lower) if x in ("kd", "keyword difficulty", "difficulty")), None)
    vol_col = next((headers[i] for i, x in enumerate(h_lower) if x in ("volume", "search volume", "vol")), None)
    tp_col  = next((headers[i] for i, x in enumerate(h_lower) if "traffic potential" in x.lower() or x.lower() == "tp"), None)
    parent_col = next((headers[i] for i, x in enumerate(h_lower) if "parent topic" in x.lower()), None)

    scored = []
    for row in rows:
        kw = row.get(kw_col, "").strip()
        if not kw:
            continue
        score = score_keyword(row, headers)
        vol  = parse_number(row.get(vol_col, "0")) if vol_col else 0
        kd   = parse_number(row.get(kd_col, "?")) if kd_col else "?"
        tp   = parse_number(row.get(tp_col, "0")) if tp_col else 0
        parent = row.get(parent_col, "").strip() if parent_col else ""
        scored.append((score, kw, vol, kd, tp, parent, row))

    scored.sort(reverse=True)

    # Tier keywords
    quick_wins   = [(s,k,v,d,t,p,r) for s,k,v,d,t,p,r in scored if isinstance(d,int) and d <= 20 and v >= 100]
    medium_term  = [(s,k,v,d,t,p,r) for s,k,v,d,t,p,r in scored if isinstance(d,int) and 20 < d <= 50]
    long_game    = [(s,k,v,d,t,p,r) for s,k,v,d,t,p,r in scored if isinstance(d,int) and d > 50]

    return quick_wins, medium_term, long_game, scored

def process_organic_keywords(rows, headers):
    """Process Site Explorer organic keywords — what's already ranking."""
    h_lower = [x.lower().strip() for x in headers]
    kw_col  = next((headers[i] for i, x in enumerate(h_lower) if x in ("keyword", "query")), headers[0])
    pos_col = next((headers[i] for i, x in enumerate(h_lower) if x in ("position", "pos", "rank")), None)
    vol_col = next((headers[i] for i, x in enumerate(h_lower) if x in ("volume", "vol", "search volume")), None)
    url_col = next((headers[i] for i, x in enumerate(h_lower) if x == "url" or "landing" in x.lower()), None)

    results = []
    for row in rows:
        kw  = row.get(kw_col, "").strip()
        pos = parse_number(row.get(pos_col, "0")) if pos_col else 0
        vol = parse_number(row.get(vol_col, "0")) if vol_col else 0
        url = row.get(url_col, "").strip() if url_col else ""
        if kw:
            results.append((pos, kw, vol, url, row))

    results.sort()  # by position ascending (rank 1 first)
    return results

def process_content_gap(rows, headers):
    """Process Content Gap — keywords competitors rank for that we don't."""
    h_lower = [x.lower().strip() for x in headers]
    kw_col  = next((headers[i] for i, x in enumerate(h_lower) if x in ("keyword", "query")), headers[0])
    vol_col = next((headers[i] for i, x in enumerate(h_lower) if x in ("volume", "vol", "search volume")), None)
    kd_col  = next((headers[i] for i, x in enumerate(h_lower) if x in ("kd", "keyword difficulty")), None)

    scored = []
    for row in rows:
        kw = row.get(kw_col, "").strip()
        if not kw:
            continue
        score = score_keyword(row, headers)
        vol = parse_number(row.get(vol_col, "0")) if vol_col else 0
        kd  = parse_number(row.get(kd_col, "?")) if kd_col else "?"
        scored.append((score, kw, vol, kd, row))

    scored.sort(reverse=True)
    return scored

def format_report_keyword_explorer(quick_wins, medium_term, long_game, total, business_ctx, source_file):
    ctx = business_ctx or {}
    biz = ctx.get("name", "Unknown Business")
    goal = ctx.get("goal", "")
    now = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# Ahrefs Keyword Explorer Report — {biz}",
        f"_Generated {now} from `{source_file}`_",
        f"_Total keywords analyzed: {total}_",
        "",
    ]
    if goal:
        lines += [f"**Marketing goal:** {goal}", ""]

    lines += [
        "---",
        "",
        "## 🟢 Quick Wins (KD ≤ 20, Volume ≥ 100)",
        "_Low competition, real search volume. Write these first._",
        "",
        "| Keyword | Volume | KD | Traffic Potential | Action |",
        "|---|---|---|---|---|",
    ]
    for _, kw, vol, kd, tp, parent, _ in quick_wins[:20]:
        lines.append(f"| {kw} | {vol:,} | {kd} | {tp:,} | Write post |")

    lines += [
        "",
        "## 🟡 Medium Term (KD 21–50)",
        "_Worth targeting once you have some domain authority. Plan 3-6 months out._",
        "",
        "| Keyword | Volume | KD | Traffic Potential |",
        "|---|---|---|---|",
    ]
    for _, kw, vol, kd, tp, parent, _ in medium_term[:20]:
        lines.append(f"| {kw} | {vol:,} | {kd} | {tp:,} |")

    lines += [
        "",
        "## 🔴 Long Game (KD > 50)",
        "_High competition. Only worth targeting if you have significant domain authority or budget._",
        "",
        "| Keyword | Volume | KD |",
        "|---|---|---|",
    ]
    for _, kw, vol, kd, tp, parent, _ in long_game[:10]:
        lines.append(f"| {kw} | {vol:,} | {kd} |")

    lines += [
        "",
        "---",
        "",
        "## Next Steps",
        "",
        "1. **Start with Quick Wins** — pick the top 3-5 by Traffic Potential, not just volume",
        "2. **Check SERP intent** for each before writing — search it, see if top results are articles, products, or comparisons",
        "3. **One keyword = one post** — don't try to stuff multiple Quick Wins into one article",
        "4. **Publish, then build internal links** from existing content to the new post",
    ]

    return "\n".join(lines)

def format_report_organic_keywords(results, business_ctx, source_file, domain=""):
    ctx = business_ctx or {}
    biz = ctx.get("name", "Unknown Business")
    now = datetime.now().strftime("%Y-%m-%d")

    top10    = [(p,k,v,u,r) for p,k,v,u,r in results if 1 <= p <= 10]
    pos11_20 = [(p,k,v,u,r) for p,k,v,u,r in results if 11 <= p <= 20]

    lines = [
        f"# Ahrefs Organic Keywords Report — {biz}",
        f"_Generated {now} from `{source_file}`_",
        f"_Total ranking keywords: {len(results)}_",
        "",
        "---",
        "",
        "## 🏆 Top 10 Rankings",
        "",
        "| Pos | Keyword | Monthly Volume | URL |",
        "|---|---|---|---|",
    ]
    for pos, kw, vol, url, _ in top10[:30]:
        short_url = url.replace("https://", "").replace("http://", "")[:60]
        lines.append(f"| {pos} | {kw} | {vol:,} | {short_url} |")

    lines += [
        "",
        "## 📈 Positions 11–20 (Low-Hanging Fruit to Push into Top 10)",
        "_These are close. A refresh + internal links could move them up._",
        "",
        "| Pos | Keyword | Monthly Volume | URL |",
        "|---|---|---|---|",
    ]
    for pos, kw, vol, url, _ in pos11_20[:20]:
        short_url = url.replace("https://", "").replace("http://", "")[:60]
        lines.append(f"| {pos} | {kw} | {vol:,} | {short_url} |")

    lines += [
        "",
        "---",
        "",
        "## Next Steps",
        "",
        "1. **Positions 11–20 are the priority** — update those pages, add internal links, tighten the title tag",
        "2. **Review top 10** — are there featured snippet opportunities? Add a clean answer block near the top of each post",
        "3. **Find keyword clusters** — group related keywords by URL to see which pages cover multiple terms",
    ]

    return "\n".join(lines)

def format_report_content_gap(scored, business_ctx, source_file):
    ctx = business_ctx or {}
    biz = ctx.get("name", "Unknown Business")
    now = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# Ahrefs Content Gap Report — {biz}",
        f"_Generated {now} from `{source_file}`_",
        f"_Keywords competitors rank for that you don't: {len(scored)}_",
        "",
        "---",
        "",
        "## Top Gap Opportunities (by Volume × Opportunity Score)",
        "",
        "| Keyword | Volume | KD |",
        "|---|---|---|",
    ]
    for score, kw, vol, kd, _ in scored[:40]:
        lines.append(f"| {kw} | {vol:,} | {kd} |")

    lines += [
        "",
        "---",
        "",
        "## Next Steps",
        "",
        "1. **Filter by intent** — which of these map to informational posts vs product pages?",
        "2. **Cluster by topic** — group similar keywords; each cluster = one article",
        "3. **Prioritize by KD** — under 30 first, build authority before going after the hard ones",
    ]

    return "\n".join(lines)

def process_file(filepath, business=None):
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    print(f"Processing: {filepath.name}")

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)

    if not rows:
        print("ERROR: Empty CSV")
        sys.exit(1)

    print(f"  Rows: {len(rows)}")
    print(f"  Columns: {', '.join(headers[:8])}{'...' if len(headers) > 8 else ''}")

    export_type = detect_export_type(headers)
    print(f"  Detected type: {export_type}")

    business_ctx = BUSINESS_CONTEXT.get(business) if business else None

    if export_type == "keyword_explorer":
        quick, medium, long, all_scored = process_keyword_explorer(rows, headers, business_ctx)
        print(f"  Quick wins (KD≤20, vol≥100): {len(quick)}")
        print(f"  Medium term (KD 21-50): {len(medium)}")
        print(f"  Long game (KD>50): {len(long)}")
        report = format_report_keyword_explorer(quick, medium, long, len(all_scored), business_ctx, filepath.name)

    elif export_type == "organic_keywords":
        results = process_organic_keywords(rows, headers)
        report = format_report_organic_keywords(results, business_ctx, filepath.name)

    elif export_type == "content_gap":
        scored = process_content_gap(rows, headers)
        report = format_report_content_gap(scored, business_ctx, filepath.name)

    else:
        # Generic: just show column summary and top rows
        print(f"  Unknown export type — generating raw summary")
        lines = [
            f"# Ahrefs Export Summary",
            f"_File: {filepath.name}_",
            f"_Rows: {len(rows)} | Columns: {', '.join(headers)}_",
            "",
            "## Raw Data (first 50 rows)",
            "",
            "| " + " | ".join(headers[:6]) + " |",
            "|" + "|".join(["---"] * min(6, len(headers))) + "|",
        ]
        for row in rows[:50]:
            lines.append("| " + " | ".join(str(row.get(h, ""))[:40] for h in headers[:6]) + " |")
        report = "\n".join(lines)

    # Save report
    out_path = filepath.with_suffix(".report.md")
    with open(out_path, "w") as f:
        f.write(report)

    print(f"\n✅ Report saved: {out_path.name}")
    print("=" * 60)
    print(report[:3000])
    if len(report) > 3000:
        print(f"\n... (truncated — full report at {out_path})")

    return out_path

def main():
    args = sys.argv[1:]
    business = None

    if "--business" in args:
        idx = args.index("--business")
        business = args[idx + 1].lower()
        args = [a for i, a in enumerate(args) if i != idx and i != idx + 1]

    if "--latest" in args:
        csvs = sorted(EXPORTS_DIR.glob("*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not csvs:
            print(f"No CSV files in {EXPORTS_DIR}")
            sys.exit(1)
        process_file(csvs[0], business)

    elif "--all" in args:
        csvs = sorted(EXPORTS_DIR.glob("*.csv"), key=lambda f: f.stat().st_mtime)
        unprocessed = [f for f in csvs if not f.with_suffix(".report.md").exists()]
        if not unprocessed:
            print("No unprocessed CSV files found.")
        for f in unprocessed:
            process_file(f, business)

    elif args:
        process_file(args[0], business)

    else:
        print(__doc__)

if __name__ == "__main__":
    main()
