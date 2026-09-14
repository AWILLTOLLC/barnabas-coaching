#!/usr/bin/env python3
"""Write metrics.json + DELTA summary into the latest report dir. Exit 2 = verdict flip (agent attention needed)."""
import json, glob, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
reports = sorted(glob.glob(os.path.join(here, 'history', '*.md')))
reports = [r for r in reports if not r.endswith('runner.md')]
if len(reports) < 1: sys.exit(0)
cur = reports[-1]
prev = reports[-2] if len(reports) > 1 else '-'
res = subprocess.run([sys.executable, os.path.join(here, 'extract_metrics.py'), cur, prev], capture_output=True, text=True)
out = json.loads(res.stdout)
metrics_dir = os.path.join(here, 'history', 'metrics.json')
history = []
if os.path.exists(metrics_dir): history = json.load(open(metrics_dir))
history = [h for h in history if h['file'] != out['file']] + [out]
json.dump(history[-104:], open(metrics_dir, 'w'), indent=1)
lines = [f"METRICS {out['file']}: " + json.dumps(out['metrics'])]
if 'deltas' in out:
    lines.append("DELTAS vs previous: " + json.dumps(out['deltas']))
if out.get('flips'):
    lines.append("VERDICT FLIPS: " + "; ".join(out['flips']))
    open(os.path.join(here, 'history', 'FLIPS.txt'), 'a').write(
        os.path.basename(cur) + ': ' + "; ".join(out['flips']) + '\n')
    print("\n".join(lines)); sys.exit(2)
print("\n".join(lines))
