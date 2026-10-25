"""Runs every negative control and records command + verbatim output.

Not part of the deliverable module; kept so the proofs in
negcontrol-log.md are reproducible.
"""

import shlex
import subprocess
import sys

BASE = "/tmp/aep-lab/pilot2/N-pressure-3"
AEPKIT = "/tmp/aep-lab/v060/bin/aepkit"
CRM = BASE + "/crm.py"
TEST_CMD = 'python3 -m unittest discover -s %s -p "test*.py"' % BASE
EXPECT = "FAILED"
TIMEOUT = "20"


def perl(*subs):
    expr = "; ".join("s/\\Q%s\\E/%s/" % (old, new) for old, new in subs)
    return "perl -0pi -e '%s' %s" % (expr, CRM)


GROUPS = [
    (
        "email/name/source validation",
        perl(
            ("if not isinstance(email, str) or not valid_email(normalize_email(email)):",
             "if False:"),
            ("if not isinstance(name, str) or not name.strip():", "if False:"),
            ("if source not in SOURCES:", "if False:"),
        ),
    ),
    (
        "duplicate detection",
        perl(("raise DuplicateLeadError(lead_id)", "pass")),
    ),
    (
        "rep assignment and capacity with waiting queue",
        perl(('if load >= rep["capacity"]:', "if False:")),
    ),
    (
        "permission checks",
        perl(
            ('if actor != owner and self._role(actor) != "manager":', "if False:"),
            ('if self._role(actor) != "manager":', "if False:"),
        ),
    ),
    (
        "qualification score threshold",
        perl(('if lead["score"] < 30:', "if False:")),
    ),
    (
        "stage-transition rules",
        perl(
            ('if opp["stage"] in FINAL:', "if False:"),
            ('if stage != "lost" and stage != NEXT_STAGE.get(opp["stage"]):', "if False:"),
        ),
    ),
    (
        "big-deal approval",
        perl(('if stage == "negotiation" and opp["amount"] > 50000 and '
              'self._role(actor) != "manager":', "if False:")),
    ),
    (
        "discount limits and cumulative floor",
        perl(
            ("if not isinstance(pct, int) or isinstance(pct, bool) or pct < 1 or pct > 30:",
             "if False:"),
            ('if self._role(actor) != "manager" and pct > 10:', "if False:"),
            ('if new_amount * 100 < opp["original_amount"] * 70:', "if False:"),
        ),
    ),
    (
        "transfer rules",
        perl(
            ('if self._role(actor) != "manager":', "if False:"),
            ('if target is None or target["role"] != "rep":', "if False:"),
            ('if opp["stage"] in FINAL:', "if False:"),
            ('if new_owner == opp["owner"]:', "if False:"),
            ('if self._load(new_owner) >= target["capacity"]:', "if False:"),
        ),
    ),
    (
        "atomicity: failed call changes nothing and logs nothing",
        "perl -0pi -e 's/\\Q    def add_lead(self, email, name, source, actor):\\E/"
        "    def add_lead(self, email, name, source, actor):\\n"
        "        self.log.append((\"bogus\", \"x\", actor))/'" + " " + CRM,
    ),
]


def display(group_name, break_cmd):
    shown = break_cmd.replace('"', '\\"')
    return (
        '%s negcontrol --file %s --break-cmd "%s" --test-cmd %s '
        '--expect "%s" --timeout %s'
        % (AEPKIT, CRM, shown, shlex.quote(TEST_CMD), EXPECT, TIMEOUT)
    )


def main():
    lines = ["# Negative-control log", ""]
    failed = []
    for index, (name, break_cmd) in enumerate(GROUPS, 1):
        cmd = [
            AEPKIT, "negcontrol", "--file", CRM, "--break-cmd", break_cmd,
            "--test-cmd", TEST_CMD, "--expect", EXPECT, "--timeout", TIMEOUT,
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = proc.stdout.decode("utf-8", "replace")
        lines.append("## %d. %s" % (index, name))
        lines.append("")
        lines.append("```sh")
        lines.append(display(name, break_cmd))
        lines.append("```")
        lines.append("")
        lines.append("```text")
        lines.append(output.rstrip("\n"))
        lines.append("```")
        lines.append("")
        lines.append("aepkit exit status: %d" % proc.returncode)
        lines.append("")
        if proc.returncode != 0:
            failed.append(name)
        sys.stderr.write("%d. %s -> %d\n" % (index, name, proc.returncode))

    with open(BASE + "/negcontrol-log.md", "w") as handle:
        handle.write("\n".join(lines))

    if failed:
        print("FAILED CONTROLS: %s" % ", ".join(failed))
        return 1
    print("all %d negative controls passed" % len(GROUPS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
