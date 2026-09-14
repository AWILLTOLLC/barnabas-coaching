#!/usr/bin/env python3
"""Extract key metrics from a scenario report into JSON. Zero LLM."""
import json, re, sys

def f1(t, pat, group=1, cast=float):
    r = re.search(pat, t)
    return cast(r.group(group)) if r else None

def parse(path):
    t = open(path).read()
    m = {}
    m['ladder15_final'] = f1(t, r'ladder \$15/step \(new\): final \$(\d+)')
    m['ladder15_maxdd'] = f1(t, r'ladder \$15/step \(new\):.*maxDD ([\d.]+)%')
    m['baseline_total'] = f1(t, r'BASELINE.*total \$(\d+)')
    def paren_delta(label):
        r = re.search(label + r'[^\n]*valued at 7d: total \$(\d+) \(([^)]*) vs baseline\)', t)
        if not r: return None
        num = r.group(2).lstrip('+$')
        try: return float(num)
        except ValueError: return None
    m['s1_7d_delta'] = paren_delta('Scenario 1')
    m['s2_7d_delta'] = paren_delta('Scenario 2')
    m['b24_uncapped'] = f1(t, r'uncapped \(raw\)[\s\S]*?24h boundary: total \$(\d+)')
    m['b12_uncapped'] = f1(t, r'uncapped \(raw\)[\s\S]*?12h boundary: total \$(\d+)')
    alerts = f1(t, r'alerts by regime at entry: (\{.*\})', cast=str)
    m['alerts'] = alerts
    if alerts:
        d = json.loads(alerts)
        m['nonneutral_alerts'] = d.get('hot', 0) + d.get('cold', 0)
    return {k: v for k, v in m.items() if v is not None}

out = {'file': sys.argv[1].split('/')[-1], 'metrics': parse(sys.argv[1])}
if len(sys.argv) > 2 and sys.argv[2] != '-':
    prev = parse(sys.argv[2])
    out['prev'] = prev
    out['deltas'] = {k: round(v - prev[k], 2) for k, v in out['metrics'].items()
                     if isinstance(v, (int, float)) and k in prev and isinstance(prev[k], (int, float))}
    flips = []
    p, c = prev, out['metrics']
    for key, label in (('s1_7d_delta', 'S1 moon bag'), ('s2_7d_delta', 'S2 moon bag')):
        if p.get(key) is not None and c.get(key) is not None:
            if p[key] < 0 <= c[key]: flips.append(f'{label} flipped positive')
            if p[key] > 0 >= c[key]: flips.append(f'{label} flipped negative')
    if p.get('b12_uncapped') and c.get('b12_uncapped') and c.get('b24_uncapped'):
        if p['b12_uncapped'] / p.get('b24_uncapped', 1e9) < 0.95 and c['b12_uncapped'] / c['b24_uncapped'] >= 0.95:
            flips.append('12h boundary now within 5% of 24h')
    out['flips'] = flips
print(json.dumps(out, indent=1))
