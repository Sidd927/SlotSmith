"""Probe: which RuleSet toggles change the engine output? Run from the repo root with the project venv."""
import sys, copy
sys.path.insert(0,'src')
from slotsmith.rules import RuleSet
from slotsmith import rules as R
from slotsmith.generator import generate
from slotsmith.pipeline import run
base=[n for n in dir(R) if 'default' in n.lower()]
rs=getattr(R,base[0])() if base else None
g=generate(600,seed=7,inject_errors=0,groups=6); import tempfile,pathlib; P=pathlib.Path(tempfile.mkdtemp())/'a.xlsx'; g.df.to_excel(P,index=False)
def sig(rules):
    r=run([P],rules,verify_from_file=False)
    return (r.metrics.get('cabinets'),r.metrics.get('ciocs'),r.metrics.get('baseplates') if 'baseplates' in r.metrics else None, len(r.tqs), tuple(sorted({row.get('CIOC','') for row in r.rows}))[:3], sum(1 for c in r.check if c['Result']!='PASS'), hash(tuple(str(row.get('CHARM Address')) for row in r.rows)))
b=sig(rs); print('base',b)
for t in rs.toggles:
    r2=copy.deepcopy(rs)
    for x in r2.toggles:
        if x.id==t.id: x.enabled=False
    s=sig(r2); print(t.id,'CHANGED' if s!=b else 'identical', s[:4], s[5])
