import pathlib
p=pathlib.Path('/tmp/aep-lab/calib/gold-2/crm.py')
s=p.read_text()
assert s.count('if stage in FINAL:\n            self._free(o["owner"])')==1
p.write_text(s.replace('if stage in FINAL:\n            self._free(o["owner"])','pass'))
