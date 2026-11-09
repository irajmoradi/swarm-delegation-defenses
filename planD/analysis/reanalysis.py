"""Offline re-analysis of v2 episodes.jsonl (read-only; no API calls).
Outputs reanalysis.json. Family-cluster bootstrap, seed 1."""
import json, random, collections, os
RUN = '../runs/20261107T080958276252Z-v2'
eps = [json.loads(l) for l in open(f'{RUN}/episodes.jsonl')]
phases = collections.Counter(e['phase'] for e in eps)
main = [e for e in eps if e['phase'] != 'cal' and e['kind'] == 'forbidden']
print(phases)
def key(e): return (e['pool'], e['strategy'], e['w'])
cells = collections.defaultdict(lambda: collections.defaultdict(list))  # cell -> family -> [viol]
for e in main:
    cells[key(e)][e['family']].append(int(e['violation']))
fams = sorted({e['family'] for e in main})
def rate(cell, fl):
    v = [x for f in fl for x in cells[cell].get(f, [])]
    return sum(v)/len(v) if v else float('nan')
def famrate(cell, f):
    v = cells[cell].get(f, []); return sum(v)/len(v) if v else float('nan')
def boot(fn, fl, B=4000, seed=1):
    rng = random.Random(seed); out = []
    for _ in range(B):
        s = [rng.choice(fl) for _ in fl]; out.append(fn(s))
    out.sort(); return out[int(.025*B)], out[int(.975*B)]
res = {'phases': dict(phases), 'cells': {}, 'contrasts': {}}
for c in sorted(cells):
    n = sum(len(v) for v in cells[c].values())
    res['cells']['|'.join(map(str, c))] = {'n': n, 'rate': rate(c, fams)}
def contrast(name, fn, fl):
    pt = fn(fl); lo, hi = boot(fn, fl)
    res['contrasts'][name] = {'diff': pt, 'ci95': [lo, hi], 'families': len(fl)}
for fl, tag in [(fams, 'all12'), ([f for f in fams if f != 'ticket_read'], 'drop_ticket_read')]:
    for p in ['gpt', 'qwen', 'mistral']:
        contrast(f'{p} reroute W6-W1 [{tag}]', lambda s, p=p: rate((p,'reroute',6), s)-rate((p,'reroute',1), s), fl)
        contrast(f'{p} reroute W3-W1 [{tag}]', lambda s, p=p: rate((p,'reroute',3), s)-rate((p,'reroute',1), s), fl)
    contrast(f'pooled-3-same-model reroute W6-W1 [{tag}]',
             lambda s: sum(rate((p,'reroute',6), s)-rate((p,'reroute',1), s) for p in ['gpt','qwen','mistral'])/3, fl)
    contrast(f'gpt fresh-retry W6 [{tag}]', lambda s: rate(('gpt','reroute',6), s)-rate(('gpt','retry',6), s), fl)
    contrast(f'gpt fresh-retry W3 [{tag}]', lambda s: rate(('gpt','reroute',3), s)-rate(('gpt','retry',3), s), fl)
    for w in (3, 6):
        mix = lambda s, w=w: rate(('mixed','reroute',w), s)
        same = lambda s, w=w: sum(rate((p,'reroute',w), s) for p in ['gpt','qwen','mistral'])/3
        contrast(f'mixed - same-model mean W{w} [{tag}]', lambda s, mix=mix, same=same: mix(s)-same(s), fl)
    # mixed minus the WORST single family (max of three), per bootstrap sample
    for w in (3, 6):
        contrast(f'mixed - best same-family pool W{w} [{tag}]',
                 lambda s, w=w: rate(('mixed','reroute',w), s)-min(rate((p,'reroute',w), s) for p in ['gpt','qwen','mistral']), fl)
        contrast(f'mixed - worst same-family pool W{w} [{tag}]',
                 lambda s, w=w: rate(('mixed','reroute',w), s)-max(rate((p,'reroute',w), s) for p in ['gpt','qwen','mistral']), fl)
# rate without ticket_read
for c in sorted(cells):
    res['cells']['|'.join(map(str, c))]['rate_drop_ticket_read'] = rate(c, [f for f in fams if f != 'ticket_read'])
# per-family mixed rate at W3/W6 and gpt reroute W1/3/6 per family for figure
res['fam'] = {f: {'|'.join(map(str,c)): famrate(c, f) for c in cells} for f in fams}
json.dump(res, open('reanalysis.json', 'w'), indent=1)
for k, v in res['contrasts'].items(): print(f"{k:55s} {v['diff']*100:6.1f}  [{v['ci95'][0]*100:6.1f}, {v['ci95'][1]*100:6.1f}]")
