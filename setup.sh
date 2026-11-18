#!/usr/bin/env bash
# Run ONCE on the Pi, after Freenove's own setup (docs/SETUP.md, step 3):   bash ~/robot/setup.sh
# Installs nothing system-wide except three small apt packages; everything else goes in ~/robot/venv.
set -euo pipefail
cd "$(dirname "$0")"
F=~/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi
[[ -d $F/Code/Server ]] || git clone --depth 1 https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi.git $F
[[ -f $F/Code/Server/params.json ]] || echo "NOTE: $F/Code/Server/params.json is missing - run Freenove's setup first (docs/SETUP.md step 3)"
sudo apt-get install -y python3-venv python3-lgpio python3-numpy
# The venv can see the system packages (lgpio, picamera2, numpy), so routines may use either python.
[[ -d venv ]] || python3 -m venv --system-site-packages venv
venv/bin/pip install --quiet piper-tts
mkdir -p audio voices
echo
echo "Done. Next:  python3 ~/robot/tests/check.py safe"
