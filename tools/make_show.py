#!/usr/bin/env python3
"""Render every line of a show into voice clips: speeches/SHOW/*.txt -> audio/SHOW/*.wav

    ~/robot/venv/bin/python ~/robot/tools/make_show.py liberty_ad

Uses the voice in robot/config.py, and replaces {name} in the texts with the robot's name.
Run it again after changing a text, the name or the voice (add --all to redo every clip).
"""
import glob, os, subprocess, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "robot"))
import config

args = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args: sys.exit(__doc__)
show = args[0]
texts = sorted(glob.glob(os.path.join(ROOT, "speeches", show, "*.txt")))
if not texts: sys.exit(f"no texts in speeches/{show}/")
out_dir = os.path.join(ROOT, "audio", show)
os.makedirs(out_dir, exist_ok=True)
for t in texts:
    wav = os.path.join(out_dir, os.path.basename(t)[:-4] + ".wav")
    if os.path.exists(wav) and os.path.getmtime(wav) > os.path.getmtime(t) and "--all" not in sys.argv:
        continue
    text = open(t).read().strip().replace("{name}", config.NAME)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "say.py"), text, wav], check=True)
