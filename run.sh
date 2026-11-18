#!/usr/bin/env bash
# Deploy, then run a routine on the Pi from this computer:
#   ./run.sh hello
#   ./run.sh hello ~/robot/audio/hi.wav left
#   ./run.sh dance 20
# Ctrl+C stops it (the routine's "finally" stops the wheels and centres the head).
set -euo pipefail
cd "$(dirname "$0")"
routine="${1:?usage: run.sh ROUTINE [args...]}"; shift
[[ -f "routines/$routine.py" ]] || { echo "no such routine: routines/$routine.py" >&2; exit 1; }
./deploy.sh >/dev/null
args=$(printf ' %q' "$@")
ssh -t robot "sudo python3 ~/robot/routines/$routine.py$args"
