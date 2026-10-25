import pathlib
p=pathlib.Path('/tmp/aep-lab/calib/gold-2/crm.py')
s=p.read_text()
assert s.count('o["amount"] > 50000 and')==1
p.write_text(s.replace('o["amount"] > 50000 and','o["amount"] >= 50000 and'))
