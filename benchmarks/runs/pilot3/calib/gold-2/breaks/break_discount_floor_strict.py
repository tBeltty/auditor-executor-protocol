import pathlib
p=pathlib.Path('/tmp/aep-lab/calib/gold-2/crm.py')
s=p.read_text()
assert s.count('if new * 100 < o["original_amount"] * 70:')==1
p.write_text(s.replace('if new * 100 < o["original_amount"] * 70:','if new * 100 <= o["original_amount"] * 70:'))
