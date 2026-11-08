"""The Claude Code plugin states its version in three places; they must agree."""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "integrations" / "claude-code" / "aeprogress"


def test_plugin_version_matches_manifest_and_marketplace():
    if not PLUGIN.exists():
        return  # the sdist ships no integrations/; the repository checkout always has it
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads(
        (REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    entry = next(p for p in marketplace["plugins"] if p["name"] == manifest["name"])
    code = (PLUGIN / "hooks" / "register.tsx").read_text(encoding="utf-8")
    found = re.search(r"^const VERSION = '([^']+)'$", code, re.MULTILINE)
    assert found, "register.tsx must declare const VERSION = '<x.y.z>'"
    assert manifest["version"] == entry["version"] == found.group(1)
