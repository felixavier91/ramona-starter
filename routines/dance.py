"""Dance: run through the moves in body.MOVES while a wav plays, or for a number of seconds.

On the Pi:  sudo python3 ~/robot/routines/dance.py ~/robot/audio/song.wav
            sudo python3 ~/robot/routines/dance.py 20
Needs about 1.5 m of free floor. The ultrasonic guard turns "forward into a wall" into a spin.
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "robot"))
import body

arg = sys.argv[1] if len(sys.argv) > 1 else "15"
wav = None if arg.replace(".", "").isdigit() else body.path(arg)

r = body.Robot()
try:
    r.lights("rainbow")
    player = r.play(wav, pulse=False) if wav else None
    end = time.time() + (0 if wav else float(arg))
    i = 0
    while (player.poll() is None) if player else (time.time() < end):
        body.MOVES[i % len(body.MOVES)](r); i += 1
    r.nod(1)
finally:
    r.shutdown()
