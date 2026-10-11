#!/usr/bin/env bash
# LINKER-MM3 end to end with headless Claude agents: prep -> agent (claude -p) -> gate, one stage at a time.
# A failed gate stops the run (e2e.py exits 1 and writes FLAG.md). Stage 3a gets one retry with its rerun prompt.
# Gates 3a and 3b read hand grades (grade3a.json, grade3b.json): the script pauses so you can write them.
# Untested as a whole: written to work in theory, never run end to end.
#   usage: ./run_all.sh            MODEL=claude-opus-5-5 ./run_all.sh
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$PWD R=runs/linker-mm3 MODEL=${MODEL:-claude-opus-5-5}

WEB="Read,Write,Edit,Glob,Grep,Bash(python3:*),Bash(curl:*),WebFetch,WebSearch"
LOCAL="Read,Write,Edit,Glob,Grep,Bash(python3:*)"
# agents must never see answer keys or gate results (the prompts say so; this enforces it)
DENY="Read($ROOT/site_data/key.md),Read($ROOT/site_data/SPEC.md),Read($ROOT/$R/gate*.json),Read($ROOT/$R/grade*.json),Read($ROOT/$R/gates.json)"

agent() {   # agent <stage folder> <prompt file> <tools> <log name>
  local prompt; prompt=$(cat "prompts/$2")
  echo "== $2 in $R/$1"
  (cd "$R/$1" && claude -p "$prompt" --model "$MODEL" --allowedTools "$3" --disallowedTools "$DENY" --output-format json) > "$R/agent_$4.json"
}
grade() {   # hand-grade pause for gates that need it
  read -rp "Write $R/$1 from the agent's output, then press Enter to run the gate. "
}

python3 e2e.py prep1;  agent stage1 stage1_sites.md "$WEB" s1;          python3 e2e.py gate1
python3 e2e.py prep2;  agent stage2 stage2_contacts.md "$WEB" s2;       python3 e2e.py gate2
python3 e2e.py prep3a; agent stage3a stage3a_questionnaire.md "$WEB" s3a; grade grade3a.json
if ! python3 e2e.py gate3a; then
  agent stage3a stage3a_rerun.md "$WEB" s3a_rerun; grade grade3a.json; python3 e2e.py gate3a
fi
python3 e2e.py prep3b
agent stage3b_public stage3b_public_prefill.md "$WEB" s3b_public
agent stage3b_riverside stage3b_riverside.md "$LOCAL" s3b_riverside   # site agent: its own files only, no web
grade grade3b.json;    python3 e2e.py gate3b
python3 e2e.py prep4;  agent stage4 stage4_decisions.md "$LOCAL" s4;    python3 e2e.py gate4
python3 e2e.py build
echo "Done. Agent logs (duration, tokens) are in $R/agent_*.json; serve app/ to view."
