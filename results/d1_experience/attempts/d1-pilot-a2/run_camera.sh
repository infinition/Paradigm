#!/bin/bash
# Camera block of D1 pilot attempt d1-pilot-a2, missions 13 to 24.
# Must run under Terminal.app: AVFoundation needs an event loop the desktop-app
# shell lacks, and the camera permission belongs to the hosting application.
# The Paradigm service must already be listening on 8765 with the a2 state.
set -u

ATTEMPT_DIR=/Users/infinition/Coding/paradigm/results/d1_experience/attempts/d1-pilot-a2
VENV=/Users/infinition/Coding/paradigm/.venv/bin

cd /Users/infinition/Coding/laruche/laruche || exit 1
export PATH="$VENV:$PATH"
# Read at runtime, never written to disk or echoed.
LARUCHE_API_KEY="$("$VENV/python" -c "import json,pathlib;print(json.loads((pathlib.Path.home()/'Library/Application Support/LaRuche/provider-profiles.json').read_text())['profiles']['Deepseek']['api_key'])")"
export LARUCHE_API_KEY

export LARUCHE_PARADIGM_URL=http://127.0.0.1:8765
export LARUCHE_PARADIGM_CLOSE=external
export LARUCHE_PROVIDER=openai
export LARUCHE_API_BASE=https://api.deepseek.com
export LARUCHE_MODEL=deepseek-v4-flash
export D1_ATTEMPT_ID=d1-pilot-a2

./target/debug/examples/paradigm_d1_pilot camera 2>&1 | tee "$ATTEMPT_DIR/camera_missions_13-24.log"
echo
echo "camera block finished with status ${PIPESTATUS[0]}"
