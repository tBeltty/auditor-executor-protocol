import pathlib
p=pathlib.Path('/tmp/aep-lab/calib/gold-1/crm.py')
s=p.read_text()
assert s.count('if l["score"] < 30:')==1
p.write_text(s.replace('if l["score"] < 30:','if l["score"] <= 30:'))
