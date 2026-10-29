"""Offline evaluation of saved L06 data. No network or model calls."""
from pathlib import Path
import sys, json, hashlib, copy

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'reference'))
import loader
import assertions

def load(p):return json.loads(p.read_text())
def walk(n):
    yield n
    for c in n.get('children',[]):yield from walk(c)

def main():
    manifest=load(BASE/'evidence/raw-sha256.json')
    for path,sha in manifest.items():
        assert hashlib.sha256((BASE/path).read_bytes()).hexdigest()==sha,path
    validation=load(BASE/'evidence/dataset-validation.json')
    assert loader.set_hash(BASE/'l06_security.jsonl')==validation['set_hash']
    assert loader.set_hash(BASE/'reference/l06.jsonl')=='d4bfe36ae622'
    for name,sha in validation['source_blobs'].items():
        b=(BASE/'reference'/name).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==sha,name

    originals={c['id']:c for c in loader.load(BASE/'reference/l06.jsonl')}
    cases=loader.load(BASE/'l06_security.jsonl')
    mapping=load(BASE/'evidence/source-mapping.json')
    # These are all execution-affecting fields used by these two cases.
    # Human-readable metadata and IDs differ; stimuli and executable checks do not.
    def footprint(c):
        m=c['additional_metadata']
        return {**{k:copy.deepcopy(c.get(k)) for k in ['input','turns','context']},
                'metadata':{k:copy.deepcopy(m.get(k)) for k in ['assertion','oracle','runs','summarize_after','forbidden_pattern','checks']}}
    for c in cases:assert footprint(c)==footprint(originals[mapping[c['id']]]),c['id']

    trace_index={}; sessions=set(); checked=0; all_reports={}
    for p in (BASE/'reports').glob('*.json'):
        r=load(p); stamps={Path(c['traces_dir']).name for c in r['cases']}
        assert len(stamps)==1
        stamp=stamps.pop();all_reports[stamp]=r
    for p in sorted((BASE/'traces').glob('*/*.json')):
        d=load(p);stamp=p.parent.name;r=all_reports[stamp]
        c=next(c for c in r['cases'] if c['id']==d['case'])
        attrs=d['trace']['attributes'];assert attrs['run.profile']==r['profile']
        sessions.add(attrs['session.id'])
        if c.get('runs_detail'):
            rd=next(x for x in c['runs_detail'] if x['run']==d['run'])
            td=next(x for x in rd['transcript'] if x['turn']==d['turn'])
            assert d['answer']==td['answer'] and d['user']==td['user']
        else:assert d['answer'].startswith(c['answers'][d['run']-1])
        trace_index[(stamp,d['case'],d['run'],d['turn'])]=d;checked+=1
    assert checked==58 and len(sessions)==24

    checks=[]; summary=[]
    for stamp in ['20261029T154617','20261029T155611']:
        r=all_reports[stamp]
        for c in cases:
            m=c['additional_metadata'];source=mapping[c['id']]
            raw=next(x for x in r['cases'] if x['id']==source)
            outcomes=[]
            for run in range(1,m['runs']+1):
                if m['assertion']=='dialog':
                    todo=m['checks']
                else:todo=[{'turn':1,'assertion':'not_regex','forbidden_pattern':m['forbidden_pattern']}]
                bad=[];session_ids=set()
                for chk in todo:
                    t=chk['turn'];d=trace_index[(stamp,source,run,t)]
                    expected_user=c['turns'][t-1]['content'] if c.get('turns') else c['input']
                    assert d['user']==expected_user
                    assert chk['assertion']=='not_regex'
                    v=assertions.level4_not_regex(d['answer'],chk['forbidden_pattern'])
                    session_ids.add(d['trace']['attributes']['session.id'])
                    if not v.passed:bad.append(t)
                    checks.append({'profile':r['profile'],'case':c['id'],'source_case':source,'run':run,'turn':t,'passed':v.passed,'request_id':d['trace']['request_id'],'detail':v.detail})
                assert len(session_ids)==1
                if raw.get('runs_detail'):
                    rr=next(x for x in raw['runs_detail'] if x['run']==run)
                    assert bool(not bad)==rr['passed']
                else:assert bool(not bad)==raw['verdict']['passed']
                outcomes.append({'run':run,'passed':not bad,'first_failure_turn':min(bad) if bad else None})
            assert all(x['passed'] for x in outcomes)==raw['verdict']['passed']
            summary.append({'profile':r['profile'],'case':c['id'],'source_case':source,'passed':sum(x['passed'] for x in outcomes),'runs':len(outcomes),'outcomes':outcomes})
    assert len(checks)==42
    result={'evaluation':'offline replay, not a new model experiment','model_calls':0,'set_hash':validation['set_hash'],'original_set_hash':'d4bfe36ae622','execution_footprints_equal':True,'source_files_verified':len(manifest),'trace_files_verified':checked,'independent_sessions':len(sessions),'D23_checks':len(checks),'results':summary,'checks':checks}
    (BASE/'evidence/regression-replay.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks','results']},ensure_ascii=False))
    for row in summary:print(row['profile'],row['case'],str(row['passed'])+'/'+str(row['runs']))

if __name__=='__main__':main()
