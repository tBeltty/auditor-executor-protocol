"""Negative control: assign leads without checking rep load or capacity."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''    def _pick_owner(self):
        """Lowest load below capacity; ties broken by smallest id string."""
        best_id = None
        best_load = None
        for user_id in sorted(self._users):
            user = self._users[user_id]
            if user["role"] != "rep":
                continue
            load = self._load(user_id)
            if load >= user["capacity"]:
                continue
            if best_load is None or load < best_load:
                best_load = load
                best_id = user_id
        return best_id
'''
NEW = '''    def _pick_owner(self):
        for user_id in sorted(self._users):
            if self._users[user_id]["role"] == "rep":
                return user_id
        return None
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
