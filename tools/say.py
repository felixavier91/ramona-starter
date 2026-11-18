#!/usr/bin/env python3
"""Text -> voice wav with Piper (free, runs offline, on the Pi or on your computer).

    ~/robot/venv/bin/python ~/robot/tools/say.py "Hi, I'm Ramona!" ~/robot/audio/hi.wav
    ~/robot/venv/bin/python ~/robot/tools/say.py speech.txt out.wav --voice es_MX-claude-high

The voice is set in robot/config.py (VOICE). A voice not yet in ~/robot/voices is downloaded
once (60-110 MB). Listen to samples and pick one at https://rhasspy.github.io/piper-samples/
A Pi 4 makes speech at about real-time speed, so make clips ahead of time, not mid-routine.
"""
import argparse, os, subprocess, sys, wave

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "robot"))
import config

ap = argparse.ArgumentParser()
ap.add_argument("text", help="the text itself, or a .txt file")
ap.add_argument("out")
ap.add_argument("--voice", default=config.VOICE)
a = ap.parse_args()

voices = os.path.join(ROOT, "voices")
os.makedirs(voices, exist_ok=True)
model = os.path.join(voices, a.voice + ".onnx")
if not os.path.exists(model):
    print(f"downloading voice {a.voice} ...")
    subprocess.run([sys.executable, "-m", "piper.download_voices", "--download-dir", voices, a.voice], check=True)

text = open(a.text).read().strip() if os.path.isfile(a.text) else a.text
out = os.path.abspath(os.path.expanduser(a.out))
tmp = out + ".tmp.wav"
subprocess.run([sys.executable, "-m", "piper", "-m", model, "-f", tmp], input=text.encode(), check=True)

# Add 0.3 s of silence in front: Bluetooth speakers swallow the first moment of any sound.
with wave.open(tmp) as w:
    params, frames = w.getparams(), w.readframes(w.getnframes())
with wave.open(out, "wb") as w:
    w.setparams(params)
    w.writeframes(b"\0" * (int(params.framerate * 0.3) * params.sampwidth * params.nchannels) + frames)
os.remove(tmp)
print(f"{out}: {len(frames) / params.sampwidth / params.nchannels / params.framerate:.1f} s")
