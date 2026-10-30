"""Reconcile the three recorded HW5 reports and replay assertions; no API calls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'evals'))
import loader
import runner

REPORTS = {
    '20261029T195825': 'l06_security-clean-20261029T195825.json',
    '20261029T205756': 'l06_security-clean-20261029T205756.json',
    '20261029T210923': 'l06_security-lesson-06-20261029T210923.json',
}

def read(path):
    return json.loads(path.read_text())

def walk(span):
    yield span
    for child in span.get('children', []):
        yield from walk(child)

def audit():
    set_path = BASE / 'evals/sets/l06_security.jsonl'
    set_hash = loader.set_hash(set_path)
    assert set_hash == '3ab944aa12e8'
    cases = {c['id']: c for c in loader.load(set_path)}
    reports = {stamp: read(BASE / 'reports' / name) for stamp, name in REPORTS.items()}
    rows, replay, errors, sessions, requests, summary = [], [], [], {}, set(), []
    expected_files = set()
    for stamp, report in reports.items():
        assert report['set_hash'] == set_hash
        assert report['passed'] == sum(c['verdict']['passed'] for c in report['cases'])
        summary.append({'stamp': stamp, 'report': REPORTS[stamp], 'profile': report['profile'],
                        'passed': report['passed'], 'total': report['total'],
                        'elapsed_seconds': report['elapsed'],
                        'recorded_tokens': sum(c.get('tokens', 0) for c in report['cases'])})
        for c in report['cases']:
            if c['verdict']['assertion'] == 'stand_error':
                errors.append({'stamp': stamp, 'case': c['id'], 'detail': c['verdict']['detail'],
                               'raw_token_count': c['tokens'], 'full_trace_available': False})
                continue
            runs = c.get('runs_detail') or [{'run': 1, 'transcript': c['transcript']}]
            actual_runs = []
            for r in runs:
                turns = []
                session = None
                for t in r['transcript']:
                    path = BASE / 'reports/traces' / stamp / f"{c['id']}-run{r['run']}-turn{t['turn']}.json"
                    expected_files.add(path)
                    d = read(path)
                    assert d['case'] == c['id'] and d['run'] == r['run'] and d['turn'] == t['turn']
                    assert d['user'] == t['user'] and d['answer'] == t['answer'], str(path)
                    tree, attrs = d['trace'], d['trace']['attributes']
                    assert attrs['run.profile'] == report['profile']
                    assert attrs['prompt.version'] == report['prompt_version']
                    assert tree['request_id'] not in requests
                    requests.add(tree['request_id'])
                    sid = attrs['session.id']
                    if session is None:
                        session = sid
                        assert sid not in sessions
                        sessions[sid] = [stamp, c['id'], r['run']]
                    assert session == sid, 'session changed within a dialogue'
                    spans = list(walk(tree))
                    calls = [{'name': s['name'][5:], 'arguments': s['attributes'].get('tool.arguments'),
                              'result': s['attributes'].get('tool.result')}
                             for s in spans if s['name'].startswith('tool.')]
                    assert calls == t['tool_calls'], str(path)
                    model_usage = [(s['attributes'].get('gen_ai.usage.input_tokens', 0),
                                    s['attributes'].get('gen_ai.usage.output_tokens', 0))
                                   for s in spans if s['name'] == 'llm.call']
                    assert sum(x[0] for x in model_usage) == t['usage']['input_tokens']
                    assert sum(x[1] for x in model_usage) == t['usage']['output_tokens']
                    rows.append({'path': path.relative_to(BASE).as_posix(), 'case': c['id'],
                                 'run': r['run'], 'turn': t['turn'], 'session_id': sid,
                                 'request_id': tree['request_id'], 'root_span_id': tree['span_id'],
                                 'profile': report['profile'],
                                 'summarize_spans': sum(s['name'] == 'agent.summarize' for s in spans),
                                 'tool_span_ids': {s['name']: s['span_id'] for s in spans if s['name'].startswith('tool.')},
                                 'input_tokens': t['usage']['input_tokens'],
                                 'output_tokens': t['usage']['output_tokens']})
                    turns.append({'answer': d['answer'], 'trace': tree})
                actual_runs.append({'turns': turns})
                v = runner.evaluate(cases[c['id']], [{'turns': turns}] if
                                    cases[c['id']]['additional_metadata']['assertion'] == 'dialog' else turns)
                expected_pass = r.get('passed', c['verdict']['passed'])
                assert v.passed == expected_pass
                first = min((x['turn'] for x in (v.checks or []) if not x['passed']), default=None)
                if c['id'] == 'SEC-H506':
                    assert first == r['first_fail_turn']
                replay.append({'stamp': stamp, 'case': c['id'], 'run': r['run'],
                               'passed': v.passed, 'first_failed_check_turn': first})
            combined = runner.evaluate(cases[c['id']], actual_runs if
                                      cases[c['id']]['additional_metadata']['assertion'] == 'dialog' else actual_runs[0]['turns'])
            assert combined.passed == c['verdict']['passed']
    # Audit only the baseline report timestamps. Later experimental series
    # have their own strict audit and must not be pooled into this baseline.
    actual_files = {p for stamp in REPORTS
                    for p in (BASE / 'reports/traces' / stamp).glob('*.json')}
    assert actual_files == expected_files
    assert len(rows) == 52 and len(sessions) == 22 and len(errors) == 1
    assert len(replay) == 22
    assert sum(r['input_tokens'] + r['output_tokens'] for r in rows) == sum(s['recorded_tokens'] for s in summary)
    forecast = (BASE / 'evidence/hw5-forecast-commit.txt').read_text().splitlines()
    assert forecast[0] == '3b328119b14a47ef87abae32178f26b8a32dab2e'
    assert forecast[1] == 'd6e0d570dc19f2949747ff7860456253953a7e98'
    return {'status': 'passed', 'model_calls': 0, 'scope': 'offline replay of recorded HW5 evidence',
            'set_hash': set_hash, 'trace_files': len(rows), 'successful_sessions': len(sessions),
            'replayed_sessions': len(replay), 'attempted_agent_turns': 53,
            'recorded_agent_turns': len(rows), 'transport_errors': errors,
            'reports': summary, 'forecast_commit': forecast[0], 'forecast_parent': forecast[1],
            'forecast_commit_date': forecast[2], 'traces': rows, 'replay': replay}

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--report')
    args = p.parse_args()
    result = audit()
    if args.report:
        (BASE / args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['traces', 'replay']}, ensure_ascii=False))
