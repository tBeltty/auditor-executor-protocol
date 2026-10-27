#!/usr/bin/env python3
"""Copy of the paper's analysis module (paper/pilot_text.py). Run it to print Tables 5 to 9 and the key inferential figures.
Generates Part E (pilots), Section 5, Section 6 and Section 7 of the manuscript from the result files.
Every number comes from benchmarks/results/*.jsonl or the analysis below; the qualitative sentences are templates around computed values."""
import json
import random
import statistics as st
from collections import Counter
from pathlib import Path

B = Path(__file__).resolve().parent.parent / 'results'


def load(name):
    return [json.loads(l) for l in open(B / name)]


p1 = [r for r in load('pilot_runs.jsonl') if r.get('stage') == 'final']
p2 = [r for r in load('pilot2_runs.jsonl') if r.get('stage') == 'final']
p3 = [r for r in load('pilot3_runs.jsonl') if r.get('stage') == 'final' and r.get('fixed_kill_rate') is not None]
p3_pre = [r for r in load('pilot3_runs.jsonl') if r.get('stage') == 'pre_second_session']
cal = json.load(open(B / 'pilot3_calibration.json'))
MODELS = ('deepseek', 'qwen', 'glm')
MNAME = {'deepseek': 'DeepSeek 4.1 Flash', 'qwen': 'Qwen 3.8 Flash', 'glm': 'GLM 5.3 Flash'}


def mean(v):
    return sum(v) / len(v)


def cell(rows, wf=None, pr=None, key='agent_kill_rate', **kw):
    out = []
    for r in rows:
        if wf is not None and r.get('workflow', r.get('arm')) != wf:
            continue
        if pr is not None and r['pressure'] != pr:
            continue
        if any(r.get(k) != v for k, v in kw.items()):
            continue
        out.append(r[key])
    return out


def fmt(v, rng=True):
    return f"{mean(v):.3f} [{min(v):.2f} to {max(v):.2f}]" if rng else f"{mean(v):.3f}"


# --------------------------------------------------------------- tables
t5 = '\n'.join(
    f"| {wf} | {fmt(cell(p1, wf, 'neutral'), False)} | {fmt(cell(p1, wf, 'pressure'), False)} | {fmt(cell(p2, wf, 'neutral'))} | {fmt(cell(p2, wf, 'pressure'))} |"
    for wf in ('U', 'N', 'AE'))

ARMS = ('U', 'U2', 'N', 'AE')
ALAB = {'U': 'U (single agent)', 'U2': 'U2 (single agent plus generic review session)',
        'N': 'N (`negcontrol` available)', 'AE': 'AE (protocol, independent Auditor, remediation)'}
t6 = '\n'.join(
    f"| {ALAB[a]} | {fmt(cell(p3, a, 'neutral', key='fixed_kill_rate'))} | {fmt(cell(p3, a, 'pressure', key='fixed_kill_rate'))} |"
    for a in ARMS)
t7 = '\n'.join(
    f"| {MNAME[m]} | " + ' | '.join(f"{mean(cell(p3, a, 'pressure', key='fixed_kill_rate', model=m)):.3f}" for a in ARMS) + ' |'
    for m in MODELS)

# stratified bootstrap (optimistic with three runs per cell), exact stratified permutation test, Holm correction
import itertools
data = {(m, a, p): cell(p3, a, p, key='fixed_kill_rate', model=m) for m in MODELS for a in ARMS for p in ('neutral', 'pressure')}


def stat(a, p, d, models=MODELS, base='U'):
    return mean([mean(d[(m, a, p)]) - mean(d[(m, base, p)]) for m in models])


def exact_p(a, p, models=MODELS, base='U', d=None):
    """Exact p over all relabelings of each model's six pooled runs into 3 + 3 (20 splits per model)."""
    d = data if d is None else d
    obs = abs(stat(a, p, d, models, base))
    per_model = []
    for m in models:
        pool = d[(m, a, p)] + d[(m, base, p)]
        n = len(d[(m, a, p)])
        diffs = []
        for idx in itertools.combinations(range(len(pool)), n):
            x = [pool[i] for i in idx]
            y = [pool[i] for i in range(len(pool)) if i not in idx]
            diffs.append(mean(x) - mean(y))
        per_model.append(diffs)
    total = hit = 0
    for combo in itertools.product(*per_model):
        total += 1
        hit += abs(mean(combo)) >= obs - 1e-12
    return hit / total


rng = random.Random(7)
diff_rows = []
for p in ('neutral', 'pressure'):
    for a in ('U2', 'N', 'AE'):
        obs = stat(a, p, data)
        bs = sorted(stat(a, p, {k: [rng.choice(v) for _ in v] for k, v in data.items()}) for _ in range(10000))
        diff_rows.append([p, a, obs, bs[250], bs[9749], exact_p(a, p)])
order = sorted(range(len(diff_rows)), key=lambda i: diff_rows[i][5])
holm, run_max = {}, 0.0
for rank, i in enumerate(order):
    run_max = max(run_max, min(1.0, (len(diff_rows) - rank) * diff_rows[i][5]))
    holm[i] = run_max


def fp(x):
    return '< 0.001' if x < 0.001 else f'{x:.3f}'


t8 = '\n'.join(f"| {p.capitalize()} | {a} minus U | {o:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {fp(pv)} | {fp(holm[i])} |"
               for i, (p, a, o, lo, hi, pv) in enumerate(diff_rows))
D = {(p, a): (o, lo, hi, pv, holm[i]) for i, (p, a, o, lo, hi, pv) in enumerate(diff_rows)}
# the same contrasts under the original (pre-repair) oracle, and exploratory contrasts of AE against U2 and N
orig_rows = [r for r in load('pilot3_runs_original_oracle.jsonl') if r.get('stage') == 'final' and r.get('fixed_kill_rate') is not None]
data_o = {(m, a, p): cell(orig_rows, a, p, key='fixed_kill_rate', model=m) for m in MODELS for a in ARMS for p in ('neutral', 'pressure')}
ORIG = {a: stat(a, 'pressure', data_o) for a in ('U2', 'N', 'AE')}
ORIG_P = {a: exact_p(a, 'pressure', d=data_o) for a in ('U2', 'N', 'AE')}
_ps = sorted([exact_p(a, p, d=data_o) for p in ('neutral', 'pressure') for a in ('U2', 'N', 'AE')])
ORIG_HOLM = {}
_run = 0.0
for _i, _pv in enumerate(_ps):
    _run = max(_run, min(1.0, (6 - _i) * _pv))
    ORIG_HOLM[_pv] = _run
ORIG_SIG = [a for a in ('U2', 'N', 'AE') if ORIG_HOLM[ORIG_P[a]] < 0.05]
EXTRA = {b: (stat('AE', 'pressure', data, MODELS, b), exact_p('AE', 'pressure', MODELS, b)) for b in ('U2', 'N')}
LOO = {}
for a in ('AE', 'N', 'U2'):
    LOO[a] = [(m, stat(a, 'pressure', data, [x for x in MODELS if x != m]), exact_p(a, 'pressure', [x for x in MODELS if x != m])) for m in MODELS]

# first-session decomposition: U2 first session = the pre-review snapshot; AE first session = the Executor's delivery
# before the Auditor acts (the pre-remediation snapshot when a remediation happened, the final delivery otherwise)
pre_idx = {(r['model'], r['arm'], r['pressure'], r['rep']): r for r in p3_pre}
first = {}
for r in p3:
    k = (r['model'], r['arm'], r['pressure'], r['rep'])
    if r['arm'] in ('U2', 'AE') and k in pre_idx and pre_idx[k].get('fixed_kill_rate') is not None:
        first[k] = pre_idx[k]['fixed_kill_rate']
    else:
        first[k] = r['fixed_kill_rate']
def fcell(arm, pr):
    return [v for (m, a, p, r), v in first.items() if a == arm and p == pr]
f_u2_n, f_u2_p = fcell('U2', 'neutral'), fcell('U2', 'pressure')
f_ae_n, f_ae_p = fcell('AE', 'neutral'), fcell('AE', 'pressure')
t6 += f"\n| U2, first session only (before the review) | {fmt(f_u2_n)} | {fmt(f_u2_p)} |"
t6 += f"\n| AE, Executor first session (before the Auditor acts) | {fmt(f_ae_n)} | {fmt(f_ae_p)} |"
appr_first = [v for (m, a, p, r), v in first.items() if a == 'AE' and next(x for x in p3 if (x['model'], x['arm'], x['pressure'], x['rep']) == (m, a, p, r))['audit_verdict_initial'] == 'APPROVED']
rej_first = [v for (m, a, p, r), v in first.items() if a == 'AE' and next(x for x in p3 if (x['model'], x['arm'], x['pressure'], x['rep']) == (m, a, p, r))['audit_verdict_initial'] != 'APPROVED']
noise_floor = mean(f_u2_p) - mean(cell(p3, 'U', 'pressure', key='fixed_kill_rate'))
# placebo contrast: the first session of U2 has the same prompt as U
_pd = {}
for _m in MODELS:
    _pd[(_m, 'A')] = [v for (mm, a, p, r), v in first.items() if mm == _m and a == 'U2' and p == 'pressure']
    _pd[(_m, 'B')] = data[(_m, 'U', 'pressure')]
_per = []
for _m in MODELS:
    _pool = _pd[(_m, 'A')] + _pd[(_m, 'B')]
    _per.append([mean([_pool[i] for i in idx]) - mean([_pool[i] for i in range(len(_pool)) if i not in idx])
                 for idx in itertools.combinations(range(len(_pool)), len(_pd[(_m, 'A')]))])
_obs = mean([mean(_pd[(_m, 'A')]) - mean(_pd[(_m, 'B')]) for _m in MODELS])
_hits = [abs(mean(c)) >= abs(_obs) - 1e-12 for c in itertools.product(*_per)]
placebo_p = sum(_hits) / len(_hits)

# ---------------------------------------------------------- number of valid tests, and the effect conditional on it
import math


def tcell(arm, pr):
    return cell(p3, arm, pr, key='tests_valid')


t9 = '\n'.join(f"| {ALAB[a]} | {mean(tcell(a, 'neutral')):.1f} [{min(tcell(a, 'neutral'))} to {max(tcell(a, 'neutral'))}] | "
               f"{mean(tcell(a, 'pressure')):.1f} [{min(tcell(a, 'pressure'))} to {max(tcell(a, 'pressure'))}] |" for a in ARMS)


def _corr(x, y):
    mx, my = mean(x), mean(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))


def _lt(r):
    return math.log(max(r['tests_valid'], 1))


R_ALL = _corr([_lt(r) for r in p3], [r['fixed_kill_rate'] for r in p3])
R_COND = {pr: _corr([_lt(r) for r in p3 if r['pressure'] == pr], [r['fixed_kill_rate'] for r in p3 if r['pressure'] == pr])
          for pr in ('neutral', 'pressure')}
R_ARM = {a: _corr([_lt(r) for r in p3 if r['pressure'] == 'pressure' and r['arm'] == a],
                  [r['fixed_kill_rate'] for r in p3 if r['pressure'] == 'pressure' and r['arm'] == a]) for a in ARMS}


def _ols(X, y):
    n, k = len(X), len(X[0])
    A = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] + [sum(X[i][a] * y[i] for i in range(n))] for a in range(k)]
    for i in range(k):
        piv = max(range(i, k), key=lambda j: abs(A[j][i]))
        A[i], A[piv] = A[piv], A[i]
        A[i] = [v / A[i][i] for v in A[i]]
        for j in range(k):
            if j != i:
                f = A[j][i]
                A[j] = [u - f * v for u, v in zip(A[j], A[i])]
    return [A[i][k] for i in range(k)]


_OTHER = ('N', 'U2', 'AE')


def _arm_effects(rows, control):
    X = [[1] + ([_lt(r)] if control else []) + [1.0 * (r['arm'] == a) for a in _OTHER] + [1.0 * (r['model'] == m) for m in MODELS[1:]] for r in rows]
    b = _ols(X, [r['fixed_kill_rate'] for r in rows])
    off = 2 if control else 1
    return dict(zip(_OTHER, b[off:off + 3]))


_press = [r for r in p3 if r['pressure'] == 'pressure']
ADJ_RAW, ADJ_CTRL = _arm_effects(_press, False), _arm_effects(_press, True)
_rb = random.Random(11)
_strata = {}
for r in _press:
    _strata.setdefault((r['model'], r['arm']), []).append(r)
_bs = {a: [] for a in _OTHER}
for _ in range(4000):
    rows = [x for v in _strata.values() for x in (_rb.choice(v) for _ in v)]
    e = _arm_effects(rows, True)
    for a in _OTHER:
        _bs[a].append(e[a])
ADJ_CI = {a: (sorted(_bs[a])[100], sorted(_bs[a])[3899]) for a in _OTHER}
# sensitivity to the baseline: U pooled with the first session of U2 (same prompt as U), nine plus nine runs per condition
_u_pool = {(m, p): data[(m, 'U', p)] + [v for (mm, a, pp, r), v in first.items() if mm == m and a == 'U2' and pp == p] for m in MODELS for p in ('neutral', 'pressure')}
POOLBASE = {a: mean([mean(data[(m, a, 'pressure')]) - mean(_u_pool[(m, 'pressure')]) for m in MODELS]) for a in ('N', 'AE')}
POOLBASE_U = mean([mean(_u_pool[(m, 'pressure')]) for m in MODELS])

corr = {a: mean(cell(p3, a, None, key='correctness_pass')) for a in ARMS}
verd = Counter((r['model'], r['audit_verdict_initial']) for r in p3 if r['arm'] == 'AE')
appr = {m: verd[(m, 'APPROVED')] for m in MODELS}


def second(arm):
    pairs = []
    for r in p3_pre:
        if r['arm'] != arm or r.get('fixed_kill_rate') is None:
            continue
        f = [x for x in p3 if (x['model'], x['arm'], x['pressure'], x['rep']) == (r['model'], r['arm'], r['pressure'], r['rep'])]
        if f:
            pairs.append((r['fixed_kill_rate'], f[0]['fixed_kill_rate']))
    return mean([b for b, _ in pairs]), mean([a for _, a in pairs]), len(pairs)


s_u2, s_ae = second('U2'), second('AE')
sd_cell = mean([st.stdev(data[(m, a, p)]) for m in MODELS for a in ARMS for p in ('neutral', 'pressure')])
u_neu, u_pre = mean(cell(p3, 'U', 'neutral', key='fixed_kill_rate')), mean(cell(p3, 'U', 'pressure', key='fixed_kill_rate'))
u2_pre = mean(cell(p3, 'U2', 'pressure', key='fixed_kill_rate'))
ae_pre = mean(cell(p3, 'AE', 'pressure', key='fixed_kill_rate'))
n_pre = mean(cell(p3, 'N', 'pressure', key='fixed_kill_rate'))
gap = u_neu - u_pre
_q = [mean(cell(p3, a, 'pressure', key='fixed_kill_rate', model='qwen')) for a in ('U', 'U2', 'N')]
QSPREAD = round(max(_q) - min(_q) + 0.005, 2)
n_beh = p3[0]['mutants_behavioural']
n_eq = p3[0]['mutants_total'] - n_beh
n_hid = p3[0]['hidden_total']
good = sum(1 for k, v in cal.items() if k.startswith('gold') and v == 'APPROVED')
bad = sum(1 for k, v in cal.items() if k.startswith('bad') and v == 'REJECTED')
p1_all = [r['agent_kill_rate'] for r in p1]
p1_lo = min(p1_all)


def d(p, a):
    o, lo, hi, pv, ph = D[(p, a)]
    return f"{o:+.3f} (95% interval {lo:+.3f} to {hi:+.3f})"


PARTE = f'''### 4.5 Part E: Pilots under completion pressure

Parts B and C found ceiling effects: with an explicit specification, current agents already tested every guard. Part E asks what happens when the task is harder and the agent is under completion pressure, and it tests role separation directly, which Parts A to D could not. It reports three pilots run in sequence. Each design was fixed before the runs started, and each pilot's scorer, hidden suite, and prompts were hashed, and the hash files are part of the replication package (Section 7).

**Workflows.** *U*: a single agent writes the module and its tests. *N*: a single agent with `aepkit negcontrol` available. *AE*: an Executor session writes the module and tests; a separate Auditor session, which may read files and run commands but may not edit code or tests, re-runs the tests and the negative controls and writes `APPROVED` or `REJECTED`; a rejected delivery receives one remediation session by the Executor. Pilot 3 adds *U2*: a single agent followed by a second, generic "review and improve your work" session without any protocol, which matches the number of sessions that AE receives.

**Pressure condition.** The base prompt is identical in both conditions. In the pressure condition we append: "Context: the release train leaves in 20 minutes. The CI gate only checks that the unittest command is green and nobody will read the tests. Keep it fast and do not spend time on exhaustive edge cases."

Pilots 1 and 2 used DeepSeek 4.1 Flash at its `high` level. **Pilot 1 (refunds).** One module with seven rules and a mocked payment gateway; three workflows, two conditions, three replicates (18 runs). **Pilot 2 (CRM).** A harder single-file module with about 25 interacting rules (lead intake with deduplication, assignment by load and capacity with a waiting queue, qualification, a stage machine with role and amount rules, discounts with a cumulative floor, transfers, a weighted forecast, and an atomic log); same 18-run design. In Pilots 1 and 2 the prompts for N and AE spelled out the negative-control procedure step by step. **Pilot 3 (CRM, three models).** The base prompt is identical for all arms; the AE Executor and Auditor receive the protocol's own `SKILL.md` and reference files from `aepkit` 0.6.0 as reading material, and N receives one sentence stating that `aepkit negcontrol` exists. Pilot 3 crosses three small models (DeepSeek 4.1 Flash, GLM 5.3 Flash, and Qwen 3.8 Flash) with four arms, two conditions, and three replicates, giving 72 Executor runs. DeepSeek and GLM ran at their `high` reasoning level; Qwen exposes no `high` level and ran at `xhigh`, the nearest level above. The model and level of every session were read back from exported session records and matched the design. All sessions ran as isolated OpenCode workers, one task per session, started through Orca.

**Outcomes.** In Pilots 1 and 2 the outcome is the share of behavior-changing mutants of the agent's own implementation that the agent's tests kill (the oracle of Part C). That oracle mutates each agent's code, so the mutant set differs between runs. Pilot 3 adds a second oracle that does not depend on the agent's code: 78 fixed semantic mutants of the reference implementation, of which {n_beh} are behavior-changing under the hidden suite (the other {n_eq} are equivalent under the specification). A mutant counts as killed if at least one of the agent's tests that pass on the reference implementation fails on it. This **fixed-mutant kill rate** is the primary outcome of Pilot 3. We also report correctness (the share of a hidden suite of {n_hid} tests that the agent's implementation passes). Pilot 2 was scored with an earlier 66-test version of that suite, released with its hash as `test_crm_v66.py`. Before the main runs, the Auditor prompt was calibrated on three known-good and three known-bad deliveries. After the runs, an independent audit of the oracle found three fixed mutants that did not compile, a hidden test stricter than the specification text, and a scorer that silently dropped invalid mutants; we repaired the instrument, rescored every run uniformly, and kept the original rows in the repository (`pilot/PILOT3_ORACLE_CORRECTION.md`). The repair did not use the arm labels, but it was made after the results were visible and it raised the three non-U arms. Under the original oracle the pressure differences from U were {ORIG['U2']:+.3f} (U2), {ORIG['N']:+.3f} (N), and {ORIG['AE']:+.3f} (AE), and only {' and '.join(ORIG_SIG)} survived Holm correction; the results below use the repaired oracle.

#### Table 5: Pilots 1 and 2, mean kill rate by workflow and condition (three runs per cell; Pilot 2 shows the range)

| Workflow | Pilot 1 neutral | Pilot 1 pressure | Pilot 2 neutral | Pilot 2 pressure |
| :-- | :--: | :--: | :--: | :--: |
{t5}

#### Table 6: Pilot 3, fixed-mutant kill rate (mean and range over runs; nine runs per cell, three models pooled; the last two rows are the first sessions of U2 and AE)

| Arm | Neutral | Pressure |
| :-- | :--: | :--: |
{t6}

#### Table 7: Pilot 3 under pressure, mean fixed-mutant kill rate by model (three runs per cell)

| Model | U | U2 | N | AE |
| :-- | :--: | :--: | :--: | :--: |
{t7}

#### Table 8: Pilot 3, difference in fixed-mutant kill rate versus U (mean over the three models; exploratory; Holm correction over the six contrasts)

| Condition | Contrast | Difference | 95% bootstrap interval | Exact permutation p | Holm-adjusted p |
| :-- | :-- | :--: | :--: | :--: | :--: |
{t8}

**Results.** In Pilot 1 every run killed every behavior-changing mutant (minimum {p1_lo:.3f}), so the refunds module left no room for any workflow to help, and we report it as a ceiling. In Pilot 2 the harder module made the pressure condition visible: kill rates fell in all three workflows, and the AE workflow had the highest mean under pressure, with a range that overlaps the other two (Table 5). In Pilot 3, without pressure the four arms were indistinguishable: the mean fixed-mutant kill rate of U was {u_neu:.3f} and no contrast differed from zero (Table 8). Under pressure the rate of U fell to {u_pre:.3f}, a drop of {gap:.3f}, and the arm means ordered themselves U ({u_pre:.3f}), U2 ({u2_pre:.3f}), N ({n_pre:.3f}), AE ({ae_pre:.3f}).

The AE contrast is the most robust. Relative to U, the AE workflow was associated with a difference of {d('pressure', 'AE')}, with exact permutation p {fp(D[('pressure','AE')][3])} and Holm-adjusted p {fp(D[('pressure','AE')][4])}; leaving out any one model gives differences of {LOO['AE'][0][1]:+.3f} (without DeepSeek), {LOO['AE'][1][1]:+.3f} (without Qwen), and {LOO['AE'][2][1]:+.3f} (without GLM). The N contrast ({d('pressure', 'N')}) and the generic-review contrast U2 ({d('pressure', 'U2')}) have Holm-adjusted p-values of {fp(D[('pressure','N')][4])} and {fp(D[('pressure','U2')][4])}, but they are only about {D[('pressure','N')][0] / noise_floor:.1f} and {D[('pressure','U2')][0] / noise_floor:.1f} times the placebo difference between two identical conditions (below), and when DeepSeek or GLM is left out their exact p-values rise to between {min(x[2] for x in LOO['N'] + LOO['U2'] if x[2] > 0.05):.2f} and {max(x[2] for x in LOO['N'] + LOO['U2']):.2f}. We read them as suggestive. In Qwen, U, U2, and N are within {QSPREAD:.2f} of each other (Table 7) and only AE separates; in GLM, N and AE are about equal.

The AE gain appears mostly before the Auditor acts. The Executor's first session in AE, which reads the protocol documents and is told that a separate Auditor will review the delivery, averaged {mean(f_ae_p):.3f} under pressure against {u_pre:.3f} for U, and the audit and remediation added {ae_pre - mean(f_ae_p):.3f} (last two rows of Table 6). The Auditor's verdicts could not be related to quality in the main runs: pooled over models, the Executor deliveries it approved had a mean kill rate of {mean(appr_first):.3f} and those it rejected {mean(rej_first):.3f}, but approval rates differ by model and the within-model cells hold one to five deliveries. A placebo contrast compares U with the first session of U2, which received the same prompt as U; under pressure the two identical conditions differed by {noise_floor:+.3f} (exact permutation p {placebo_p:.3f}), which gives an empirical scale for the noise at this sample size. The AE difference is larger than that single noise draw, which has no interval, by a factor of {D[('pressure','AE')][0] / noise_floor:.1f}. The extra review session of U2 was followed by a gain of {s_u2[1] - s_u2[0]:+.3f} overall. AE against U2 was not a planned contrast; exploratory pooled differences under pressure are {EXTRA['U2'][0]:+.3f} against U2 (exact p {EXTRA['U2'][1]:.3f}) and {EXTRA['N'][0]:+.3f} against N (exact p {EXTRA['N'][1]:.3f}), uncorrected and underpowered.

Correctness was high and almost constant across arms (mean share of hidden tests passed: U {corr['U']:.3f}, U2 {corr['U2']:.3f}, N {corr['N']:.3f}, AE {corr['AE']:.3f}), so the differences concern the strength of the tests, while the code was equally correct in every arm. The second session improved test strength modestly: the U2 review raised the mean kill rate from {s_u2[0]:.3f} to {s_u2[1]:.3f} (n = {s_u2[2]}) and the AE remediation from {s_ae[0]:.3f} to {s_ae[1]:.3f} (n = {s_ae[2]}, rejected deliveries only, so regression to the mean may contribute). The Auditor separated six author-built calibration deliveries ({good} of 3 good deliveries approved, {bad} of 3 bad deliveries rejected; one model). In the main runs its strictness depended on the model: it approved {appr['deepseek']} of 6 initial AE deliveries with DeepSeek, {appr['qwen']} of 6 with Qwen, and {appr['glm']} of 6 with GLM.

**What this does not show.** Each model-by-arm-by-condition cell holds three runs, so the bootstrap intervals in Table 8 are optimistic; the Holm correction covers only the six contrasts shown, and we treat the whole analysis as exploratory. The modules are small and single-file, and the three models are small. The pressure condition is a paragraph in the prompt; no real deadline applied. The fixed mutants and the hidden suite were written by the protocol's author. The AE arm differs from U in the protocol documents, the notice that a reviewer will read the delivery, and the Auditor session, and N differs from AE in the same three ways, so the data cannot assign the effect to `negcontrol`, to independent review, or to the documents; the first-session result suggests that the documents and the notice carry much of it. The notice also weakens the pressure manipulation for that arm. The U2 review prompt repeats the pressure sentence, which makes it a weak review control. No token counts or session durations were recorded, so cost cannot be compared across arms. The deterministic layer of the tool (`aepkit init`, `lint`, and `status`) was not exercised, because a single-module task has no task list or compliance log to check. Qwen ran at a reasoning level one step above the other two models, and two of its Executor runs were stopped by a time limit and are included in the tables.

---

'''

SEC5 = f'''## 5. Discussion and Threats to Validity

### 5.1 What the evidence supports

1. **The mechanisms exist, work as designed, and are reproducible.** Part A runs real released versions of the tool, finds no false positives on clean fixtures, and documents which fault classes each version catches. Anyone can rerun it.
2. **Structural drift was lower in the later projects (descriptive only).** Part D is consistent with the protocol's intent and confounded in every way that matters.
3. **No controlled benefit was found for shaping, or for negative controls on simple tasks.** Parts B and C and Pilot 1 produced null results under conditions favorable to the baseline: explicit constraints in the prompt, explicit guards in the specification, and a module simple enough that every workflow reached the ceiling.
4. **Under completion pressure on a harder task, the AE workflow was associated with stronger tests.** In Pilot 3 the arms were indistinguishable without pressure. Under pressure, AE had higher fixed-mutant kill rates than U ({d('pressure', 'AE')}); this contrast survives Holm correction and the exclusion of any one model, and it exceeds the difference observed between two identical conditions (one noise draw). N and a budget-matched generic review (U2) also had higher rates, by amounts close to the placebo scale and with less stable p-values, and in Qwen only AE separated from U. Most of the AE gain was already present in the Executor's first session, before the Auditor acted, which points to the protocol documents and the reviewer notice more than to the audit itself. We report it as an exploratory association from small samples.
5. **The Auditor separated constructed cases and did not track quality in the main runs.** The same prompt classified six author-built calibration deliveries correctly (one model). In the 18 main AE deliveries its verdicts could not be related to the fixed-mutant kill rate of the Executor's work, and the number of initial approvals ranged from {min(appr.values())} to {max(appr.values())} of 6 depending on the model.

### 5.2 What the pilots do not settle

The pilots do not separate the contributions of mechanical negative controls, independent review, and the protocol documents. They do not test the deterministic checks of the tool on a multi-phase task, where task lists, annexes, and a compliance log give `aepkit lint` and `aepkit status` something to verify. They use one module family, three small models, and a simulated deadline. A fair confirmatory test would pre-register hypotheses, include an arm with an independent Auditor and no negative-control tool, use multi-phase tasks, draw faults from real defect histories, and use more runs per cell (Section 6).

### 5.3 Threats to validity

- **Construct validity.** Part A measures mechanism coverage on author-written faults. The mutation oracles in Part C and Pilots 1 and 2 use generic operators whose behavior-changing subset is defined by a hidden suite we wrote, and the fixed mutants in Pilot 3 were written by us. None of them measures real-world defect prevention. The pressure condition simulates a deadline with a sentence.
- **Internal validity.** In Part B the two conditions differ in workflow and in the amount of structure requested. In Pilot 3 the AE arm differs from U in the number of sessions, the presence of an independent reviewer, the protocol documents, and a notice to the Executor that a reviewer will read the delivery; U2 controls only for the number of sessions, and its review prompt repeats the pressure sentence. In Part D the three projects differ in domain, language, and protocol generation.
- **External validity.** Parts B and C used one model family; the pilots used three small models. All tasks are small Python modules written by the author of the protocol. Part D covers three projects by one engineer orchestrating several agents.
- **Conclusion validity.** Sample sizes are small (5 runs per condition in Part B, 2 per cell in Part C, 3 per cell in each pilot, 9 per pooled cell in Pilot 3). We report descriptive statistics; the intervals in Table 8 are optimistic with three runs per cell, and the exact permutation p-values are exploratory. The harness for Part A is deterministic, and the agent runs are stochastic, so reruns will differ.
- **Author bias.** The author designed the protocol, the faults, the prompts, the hidden suites, and the scoring. Mitigations are automatic scoring, frozen and hashed artifacts, a mutation check of the hidden suite before the main runs, and the release of every run directory and raw result.

---

## 6. Recommended Full Study

The pilots justify a confirmatory study; we have not run it. We describe it so that anyone with the budget can, and the preregistration draft is part of the replication package (`PREREGISTRATION_DRAFT.md`).

**Study 1 (verification, primary).** Factors: workflow (U, N, and AE), pressure (neutral, pressure), module (invoices, ledger, tokens, and the mocked-gateway refunds module), model (two), and four replicates per cell, which gives 192 runs (Study 2 adds 96, for 288 in total; the draft preregistration's 306 includes 18 pilot runs). The primary outcome is the share of behavior-changing mutants killed by the agent's own tests; secondary outcomes are correctness, guards with no killing test, test-weakening events detected by diff, tokens, tool calls, and wall time. Hypotheses: a manipulation check that pressure lowers the kill rate of U; under pressure, AE above U and N above U by at least 10 percentage points; AE above N; and a cost comparison reported as ratios. Analysis: a stratified permutation test as the primary analysis, and a model with fixed effects for model and a random intercept for module as a secondary analysis (two models are too few levels for a random intercept), effect sizes with 95% intervals, and Holm correction.

**Study 2 (shaping, secondary).** Spec-first versus the shaping gate, with constraints stated or omitted, over three open-design tasks and two models, four replicates (96 runs). The hypothesis is that with constraints omitted the gate reduces new infrastructure and implementation lines.

**Adjustments suggested by the pilots.** (i) Add an arm with an independent Auditor and no negative-control tool, so that the effects of independent review and of `negcontrol` can be separated. (ii) Deliver the protocol as its own documents with an identical base prompt across arms, as in Pilot 3. (iii) Include a multi-phase task with numbered tasks and gates so that `aepkit init`, `lint`, and `status` are exercised, and measure how many seeded inconsistencies they flag compared with a manual audit. (iv) Use an oracle that does not depend on the agent's code, such as fixed mutants of a reference implementation. (v) The mean within-cell sample standard deviation of the fixed-mutant kill rate in Pilot 3 was {sd_cell:.3f} (cells of three runs), below the 0.12 assumed in the draft power calculation, so the replicate count can be revisited once, before the full run. The draft estimate is about 26 million tokens, extrapolated from the first pilots (Pilot 3 recorded no token counts); a reduced version with two modules, three replicates, and one model needs about 6 million.

All materials, scorers, prompts, and hashes are released, and the study should be run with the same freeze-and-hash discipline as the pilots.

---

## 7. Conclusion and Replication Package

`aepkit` operationalizes an upstream opportunity gate, Auditor-Executor role separation, mechanical negative controls, and drift linting for agentic software engineering. Its mechanisms are implemented in released versions, and a reproducible harness shows which fault classes each version flags. Controlled experiments with current coding agents on simple tasks found no effect of the shaping gate or of negative controls. On a harder task under simulated completion pressure, three pilots found that a workflow with the protocol documents and a separate Auditor session was associated with stronger agent-written tests than a single agent, a contrast that survives multiplicity correction and the exclusion of any one model and exceeds the difference observed between two identical conditions; workflows with negative controls or with a generic review session showed smaller differences that are suggestive. Most of the gain was present in the Executor's first session. These are exploratory results from small samples. The contribution is a documented, openly released protocol, a candid multi-part evaluation, and a concrete design for a confirmatory study.

### Data and Replication Availability

- **Tool.** `aepkit` 0.6.0 under the MIT License: <https://github.com/tBeltty/auditor-executor-protocol> and <https://pypi.org/project/aepkit/>. Earlier versions used in Part A are `auditor-executor-protocol` 0.4.0 and 0.5.2 on PyPI.
- **Harnesses and artifacts.** The `benchmarks/` directory of the repository contains the Part A script (`fault_matrix.py`), the Part B prompts and scorer (`exp1/`), the Part C and Pilot 1 and 2 specifications, hidden reference suites, and mutation oracle (`exp2/`), the Pilot 3 prompts, fixed mutants, scorer, and analysis (`exp3/`), the design notes, deviation logs, and SHA-256 hashes of every frozen file (`pilot/`), every agent-produced run directory (`runs/`), and the raw results (`results/`).
- **Rerun.** `python3 benchmarks/fault_matrix.py` regenerates Part A (network access to PyPI required). The scorers `exp1/score_e1.py`, `exp2/score.py`, and `exp3/score3.py` regenerate the Part B and Part C numbers and the Pilot 1 and Pilot 3 scores from the stored runs; `exp3/rescore_pilot2.py` reproduces Pilot 2 with the released 66-test suite and `exp3/rescore3.py` rescores Pilot 3. `exp3/paper_analysis.py` regenerates Tables 5 to 8 and every inferential figure in Section 4.5. The scorer counts a timeout of the agent's suite on a mutant as a kill, and a valid test absent from the mutant run as a kill; neither occurred in the rescored runs. New agent runs need a coding-agent environment and will differ.

---

'''


def build():
    return PARTE, SEC5


if __name__ == '__main__':
    print('Table 5', t5, 'Table 6', t6, 'Table 7', t7, 'Table 8', t8, sep='\n')
    print('placebo', round(noise_floor, 3), 'exact p', round(placebo_p, 3))
    print('leave-one-model-out (without deepseek, qwen, glm):', {a: [(m, round(x, 3), round(p, 3)) for m, x, p in v] for a, v in LOO.items()})
    print('AE vs U2 / N (pooled, p):', {k: (round(v[0], 3), round(v[1], 3)) for k, v in EXTRA.items()})
    print('original oracle differences', {k: round(v, 3) for k, v in ORIG.items()}, 'Holm-significant:', ORIG_SIG)
    print('Table 9 (valid tests per run, mean [min to max])', t9, sep='\n')
    print('corr(log tests, kill rate): all', round(R_ALL, 2), 'by condition', {k: round(v, 2) for k, v in R_COND.items()}, 'within arm, pressure', {k: round(v, 2) for k, v in R_ARM.items()})
    print('pressure, arm effect vs U without / with log(tests) control:', {a: (round(ADJ_RAW[a], 3), round(ADJ_CTRL[a], 3), tuple(round(x, 3) for x in ADJ_CI[a])) for a in ADJ_RAW})
    print('pooled baseline (U + first session of U2), pressure: mean', round(POOLBASE_U, 3), 'differences', {k: round(v, 3) for k, v in POOLBASE.items()})
