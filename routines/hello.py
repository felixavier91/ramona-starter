"""Say hello without moving the wheels: lights, a look to one side, a nod, and a sound if you give one.

On the Pi:  sudo python3 ~/robot/routines/hello.py [wav] [left|right|center]
(sudo turns on the LEDs; without it everything else still works.)
Make a wav first with tools/say.py, e.g.  tools/say.py "Hi, I'm Ramona!" audio/hi.wav
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "robot"))
import body

args = sys.argv[1:]
side = args.pop() if args and args[-1] in body.PAN_SIDE else "center"
wav = body.path(args[0]) if args else None

r = body.Robot()
try:
    r.lights("heartbeat")
    player = r.play(wav) if wav else None
    r.look(body.PAN_SIDE[side], 98)        # turn toward the person and look up a little
    r.nod(2)
    while player and player.poll() is None:
        time.sleep(0.1)
    time.sleep(1)
finally:
    r.shutdown()
