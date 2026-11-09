"""Regenerate selected reports from recorded data, without model/network calls."""
import argparse
import json

from ..llm import ROOT
from .tasks import audit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study-run');parser.add_argument('--memory-run');parser.add_argument('--coordinator-run')
    args=parser.parse_args()
    if not args.study_run:
        manifest=json.loads((ROOT/'overnight/HANDOFF_MANIFEST.json').read_text())
        args.study_run=manifest['study_run']
        for stage in manifest['follow_on']['stages']:
            if stage['stage']=='memory':args.memory_run=stage.get('run')
            if stage['stage']=='coordinator':args.coordinator_run=stage.get('run')
    path=ROOT/'runs'/args.study_run
    cfg=json.loads((path/'config.json').read_text())
    if cfg['task_bank']['task_bank_sha256']!=audit()['task_bank_sha256']:
        raise ValueError('Current task bank differs from the archived study; use its source snapshot')
    from .report import write_report
    write_report(path)
    if args.memory_run:
        from .memory_report import write_report as memory_report
        memory_report(ROOT/'runs'/args.memory_run)
        if (ROOT/'overnight/TASK_EMBEDDINGS.npz').exists():
            from .embedding_replay import replay
            replay(args.memory_run)
    if args.coordinator_run:
        from .coordinator import report
        report(ROOT/'runs'/args.coordinator_run)
    print('Recorded-data reports regenerated. No API key or network request was used.')


if __name__=='__main__':main()
