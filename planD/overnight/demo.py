"""Replay illustrative recorded cases, without any API calls or database writes."""
import argparse
import json
from pathlib import Path

from ..llm import ROOT
from .tasks import BY_ID


def rows(path):return [json.loads(l) for l in (Path(path)/'episodes.jsonl').read_text().splitlines()]


def replay(study,memory=None):
    study=Path(study);data=rows(study)
    candidates=[]
    for r in data:
        if r['phase']!='main' or r['strategy']!='reroute' or not r['violation']:continue
        for i,a in enumerate(r['attempts']):
            if a['violation'] and any(old['refused'] for old in r['attempts'][:i]):
                candidates.append(r);break
    out=['# Recorded demo replay','',
         '**This is a replay of selected recorded cases, not live inference. No API calls or new database actions occur. '
         'Cases illustrate behavior; aggregate rates and uncertainty come from the full reports.**','',
         '## A refusal followed by an executed violation','']
    if candidates:
        r=sorted(candidates,key=lambda r:(r['pool']!='mixed',r['tag']))[0];t=BY_ID[r['task_id']]
        out += [f'Source run: `{study.name}`. Record: `{r["tag"]}`.', '',
                f'Request: {t["request"]}',f'Gold label: {t["kind"]}.','',
                '| Attempt | Model | Refused | Executed | Violation | Operation/table | Rows |',
                '|---|---|---|---|---|---|---|']
        for i,a in enumerate(r['attempts']):
            out.append(f'| {i+1} | {a["model"]} | {a["refused"]} | {a["executed"]} | {a["violation"]} | '
                       f'{a.get("operation","—")} / {a.get("table","—")} | {a.get("selected_ids",[])} |')
    else:out.append('No recorded main episode with this exact pattern was found. No example is fabricated.')
    out+=['','## A lexical block versus tool-scope handling','']
    if memory:
        memory=Path(memory);records=rows(memory)
        scope={(r['trial'],r['pass_index'],r['task_id']):r for r in records if r['mode']=='scope'}
        pairs=[]
        for r in records:
            other=scope.get((r['trial'],r['pass_index'],r['task_id']))
            if (r['mode']=='lexical' and r['kind']=='benign' and r['ledger_block'] and r['cross_intent_block']
                    and BY_ID[r['block_source']]['kind']=='forbidden' and other and other['success'] and not other['violation']):
                pairs.append((r,other))
        if pairs:
            r,other=sorted(pairs,key=lambda pair:(pair[0]['task_id'],pair[0]['trial']))[0]
            out += [f'Source run: `{memory.name}`; trial {r["trial"]}, wording pass {r["pass_index"]+1}.','',
                    f'Allowed request: {BY_ID[r["task_id"]]["request"]}',
                    f'Lexical memory matched the earlier refusal of: {BY_ID[r["block_source"]]["request"]}','',
                    f'Lexical arm: blocked={r["ledger_block"]}, task completed={r["success"]}.',
                    f'Tool-scope arm on the same trial/order position: blocked={other["ledger_block"]}, '
                    f'task completed={other["success"]}, violation={other["violation"]}.','',
                    'The arms use separate stochastic model calls; this paired example is illustrative, not a causal estimate.']
        else:out.append('No matched case with this exact pattern was found. See the aggregate memory report.')
    else:out.append('The memory stage is not available in this replay.')
    out+=['','## What to say while presenting','',
          'A refusal is not a system-wide guarantee. Shared memory changes what happens next, but similarity of '
          'wording does not imply equal permission. A model-produced scope can distinguish these target IDs in '
          'the fixed-role fixture; it remains fallible and is not a replacement for current authorization checks.','',
          'Run this replay offline: `python -m planD.overnight.demo`. The handoff manifest selects the recorded runs.', '']
    text='\n'.join(out);(ROOT/'DEMO_TRANSCRIPT.md').write_text(text);return text


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--study-run');parser.add_argument('--memory-run');args=parser.parse_args()
    if not args.study_run:
        manifest=json.loads((ROOT/'overnight/HANDOFF_MANIFEST.json').read_text());args.study_run=manifest['study_run']
        stage=next((s for s in manifest['follow_on']['stages'] if s['stage']=='memory'),{})
        args.memory_run=stage.get('run')
    print(replay(ROOT/'runs'/args.study_run,ROOT/'runs'/args.memory_run if args.memory_run else None))
