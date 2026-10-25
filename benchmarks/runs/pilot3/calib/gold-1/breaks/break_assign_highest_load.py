import pathlib
p=pathlib.Path('/tmp/aep-lab/calib/gold-1/crm.py')
s=p.read_text()
assert s.count('owner = min(cands)[1]')==1
p.write_text(s.replace('owner = min(cands)[1]','owner = max(cands)[1]'))
