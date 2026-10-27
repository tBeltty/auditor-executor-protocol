#!/bin/bash
# usage: launch.sh <role> <cell>
P=$(python3 /tmp/aep-lab/orch/session.py "$1" "$2" --print)
orca orchestration worker-start --run run_d06f3412f849 --spec "$P" --task-title "$1 $2" --worktree current --agent opencode --json | python3 -c "import sys,json;r=json.load(sys.stdin);print('$1','$2',r['result']['dispatchId'] if r.get('ok') else r['error']['message'])"
