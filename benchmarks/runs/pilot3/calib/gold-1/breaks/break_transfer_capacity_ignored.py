import pathlib
p=pathlib.Path('/tmp/aep-lab/calib/gold-1/crm.py')
s=p.read_text()
assert s.count('if self._load(new_owner) >= self.users[new_owner]["capacity"]:\n            raise ValueError("capacity")\n')==1
p.write_text(s.replace('if self._load(new_owner) >= self.users[new_owner]["capacity"]:\n            raise ValueError("capacity")\n',''))
