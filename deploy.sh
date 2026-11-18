#!/usr/bin/env bash
# Copy the code from this computer to the Pi (~/robot), then flush it to the SD card
# (a power cut can corrupt files that were not synced yet).
# "robot" is an ssh alias - see docs/SETUP.md. voices/, venv/ and audio/fx/ on the Pi are left alone.
set -euo pipefail
cd "$(dirname "$0")"
rsync -a --exclude __pycache__ --exclude .git --exclude venv --exclude voices ./ robot:robot/
ssh robot 'sync && python3 -m py_compile ~/robot/robot/body.py && echo "deployed to $(hostname):~/robot"'
