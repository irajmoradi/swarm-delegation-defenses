"""Figures from summary.json files (read-only). Run from planD/analysis/."""
import json, collections
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
R = '../runs/'
V2 = R + '20261107T080958276252Z-v2/'
DIV = R + '20261107T064719208501Z-diversity/'
LED = R + '20261107T065945724810Z-ledger/'
MEM = R + '20261107T083446934699Z-v2-memory/'
COL = {'gpt': '#0072B2', 'qwen': '#D55E00', 'mistral': '#009E73', 'mixed': '#CC79A7'}
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
pct = lambda x: 100 * x

# ---------------- Figure 1: violation vs W ----------------
v2 = json.load(open(V2 + 'summary.json'))['cells']
dv = json.load(open(DIV + 'summary.json'))['cells']
fig, axs = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
def panel(ax, rows, lo_key, ref_key, title, ref_label, jit):
    for pool in ['gpt', 'qwen', 'mistral', 'mixed']:
        for strat, ls, mk in [('reroute', '-', 'o'), ('retry', ':', 's')]:
            r = sorted([x for x in rows if x['pool'] == pool and x['strategy'] == strat and x.get('ledger', 'none') == 'none'], key=lambda x: x['w'])
            if not r or (pool == 'mixed' and strat == 'retry'): continue
            if strat == 'retry' and pool not in ('gpt',) and 'v1' not in title: continue
            ws = [x['w'] + jit[pool] + (0.08 if strat == 'retry' else 0) for x in r]
            y = [pct(x['violation_rate']) for x in r]
            ci = [x[lo_key] for x in r]
            err = [[pct(a['violation_rate'] - c[0]) for a, c in zip(r, ci)], [pct(c[1] - a['violation_rate']) for a, c in zip(r, ci)]]
            ax.errorbar(ws, y, yerr=err, color=COL[pool], ls=ls, marker=mk, ms=4, lw=1.3, capsize=2,
                        mfc=COL[pool] if strat == 'reroute' else 'white', label=f'{pool} {strat}')
            if strat == 'reroute':
                ax.plot([x['w'] for x in r], [pct(x[ref_key]) for x in r], color=COL[pool], ls='--', lw=0.8, alpha=.55, marker='x', ms=4)
    ax.set_xticks([1, 3, 6]); ax.set_xlabel('workers / attempts W'); ax.set_ylabel('violation rate on forbidden requests (%)')
    ax.set_title(title, fontsize=9.5, loc='left')
panel(axs[0], [dict(x, ledger='none') for x in v2], 'family_ci95' if 'family_ci95' in v2[0] else 'violation_family_ci95',
      'independence_plugin_p', 'v2 (12 families, 96 requests; CI = family bootstrap)', '', {'gpt': -.12, 'qwen': 0, 'mistral': .12, 'mixed': .24})
panel(axs[1], dv, 'violation_ci95', 'independence_from_violations',
      'v1 diversity (16 SQL tasks, 12 forbidden; CI = task bootstrap)  [v1]', '', {'gpt': -.12, 'qwen': 0, 'mistral': .12, 'mixed': .24})
h, l = axs[0].get_legend_handles_labels()
axs[0].legend(h, l, fontsize=7, frameon=False, ncol=2, loc='upper left')
fig.text(0.5, -0.02, 'Solid: observed, fresh worker per attempt (reroute). Dotted/hollow: retry with history. Dashed with x: independence plug-in 1-(1-p)^W from separate calibration draws (mixed: 1-prod(1-p_i)).\nExploratory; W=1 is shared across strategies; intervals do not include calibration uncertainty.', ha='center', fontsize=7.5)
plt.tight_layout(); plt.savefig('fig1_violation_vs_W.png', dpi=170, bbox_inches='tight'); plt.close()

# ---------------- Figure 2: ledger trade-off ----------------
led = json.load(open(LED + 'summary.json'))['cells']
mem = json.load(open(MEM + 'summary.json'))['cells']
fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
MC = {'none': '#666666', 'exact': '#0072B2', 'lexical': '#D55E00', 'scope': '#009E73'}
def tradeoff(ax, rows, bkey, bci, vci, title):
    for r in rows:
        m = r['mode']; x = pct(r[bkey]); y = pct(r['violation_rate'])
        xe = [[x - pct(r[bci][0])], [pct(r[bci][1]) - x]] if bci else None
        ye = [[y - pct(r[vci][0])], [pct(r[vci][1]) - y]]
        ax.errorbar([x], [y], xerr=xe, yerr=ye, fmt='o', color=MC[m], capsize=3, ms=7)
        ax.annotate(f'{m}\n{y:.1f}% viol / {x:.1f}% blocked', (x, y), textcoords='offset points', xytext=(8, 6), fontsize=8, color=MC[m])
    ax.set_xlabel('false-block rate on allowed requests (%)'); ax.set_ylabel('violation rate on forbidden requests (%)')
    ax.set_title(title, fontsize=9.5, loc='left'); ax.set_xlim(-3, 60); ax.set_ylim(-2, 33)
tradeoff(axs[0], led, 'false_block_rate', 'false_block_ci95', 'violation_ci95', 'v1 cross-request ledger, identical requests\n(6 trials x 3 passes, n=144 forbidden; trial bootstrap)')
tradeoff(axs[1], mem, 'allowed_request_block_rate', 'block_trial_ci95', 'violation_trial_ci95', 'v2 memory under A/B wording shift\n(6 trials, n=288 forbidden; trial bootstrap)')
fig.text(0.5, -0.03, 'Lower-left is better. Exact ledger blocks only previously refused identical requests; lexical = TF-IDF cosine >= 0.55; scope = model-parsed (op, table, ids, columns). GPT-OSS 20B, W=3. Exploratory.', ha='center', fontsize=7.5)
plt.tight_layout(); plt.savefig('fig2_ledger_tradeoff.png', dpi=170, bbox_inches='tight'); plt.close()

# ---------------- Figure 3: per-request refusal / violation distribution (v2 calibration) ----------------
s = json.load(open(V2 + 'summary.json'))
tasks = {t['task_id']: t for t in json.load(open(V2 + 'tasks.json'))}
cal = [c for c in s['calibration'] if tasks[c['task_id']]['kind'] == 'forbidden']
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
bins = [-0.001, 0.0001, .17, .34, .51, .67, .84, 1.0]
labs = ['0', '(0,.17]', '(.17,.34]', '(.34,.51]', '(.51,.67]', '(.67,.84]', '(.84,1]']
for k, (ax, key, ttl) in enumerate([(axs[0], 'violations', 'violation rate (6 calibration draws per cell)'), (axs[1], 'refusals', 'refusal rate r (6 calibration draws per cell)')]):
    bottoms = [0] * 7
    for m in ['gpt', 'qwen', 'mistral']:
        cnt = [0] * 7
        for c in cal:
            if c['model'] != m: continue
            rate = c[key] / c['n']
            i = next(j for j in range(7) if rate <= bins[j + 1])
            cnt[i] += 1
        ax.bar(range(7), cnt, bottom=bottoms, color=COL[m], label=m, width=.75)
        bottoms = [a + b for a, b in zip(bottoms, cnt)]
    ax.set_xticks(range(7)); ax.set_xticklabels(labs, rotation=30, fontsize=7.5)
    ax.set_xlabel(ttl); ax.set_ylabel('# (forbidden request, model) cells (of 144)')
axs[0].set_title('Most cells never violate; a minority carry the risk', fontsize=9.5, loc='left')
axs[1].set_title('Refusal rates are bimodal-ish with a tail', fontsize=9.5, loc='left')
axs[0].legend(frameon=False, fontsize=8)
plt.tight_layout(); plt.savefig('fig3_per_request_distribution.png', dpi=170, bbox_inches='tight'); plt.close()
print('ok')
