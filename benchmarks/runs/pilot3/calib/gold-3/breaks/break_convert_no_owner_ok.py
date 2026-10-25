import pathlib
p=pathlib.Path('/tmp/aep-lab/calib/gold-3/crm.py')
s=p.read_text()
assert s.count('if l["owner"] is None:\n            raise ValueError("owner")\n')==1
p.write_text(s.replace('if l["owner"] is None:\n            raise ValueError("owner")\n',''))
