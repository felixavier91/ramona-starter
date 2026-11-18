# Ramona starter kit

A small, plain starting point for a Freenove 4WD Smart Car (Raspberry Pi) robot. It comes out of
a few weeks of work on a sister robot of the same kit: the reusable parts are here, the
personality is not. Voice, name, colours, what she does and how she behaves are yours to decide.

## What is in the box

```
robot/config.py     name, speaker, voice: the only file you must look at
robot/body.py       the body: head, wheels, LEDs, sound, sensors, with the safety rules built in
tests/check.py      test one part at a time (battery, distance, head, LEDs, camera, sound, wheels)
routines/           three short examples to copy from
  hello.py            lights + nod + a sound, no wheels
  dance.py            a set of wheel moves, to a wav or for N seconds
  wander.py           drive around without bumping into things
tools/say.py        text -> voice wav (Piper, free, offline)
tools/make_sounds.py  25 synthesized sound effects and public-domain tunes
setup.sh            one-time install on the Pi
deploy.sh, run.sh   copy the code to the Pi / run a routine from your computer
CLAUDE.md           notes for Claude Code, if you use it to program her (optional)
docs/SETUP.md       from a blank SD card to the first test
docs/TESTING.md     how to test each part, and what a failure usually means
docs/LESSONS.md     things that cost us time, so they don't cost you any
docs/IDEAS.md       what the sister robot grew into, and what it took
```

## Quick start

1. Build the car and set up the Pi: [docs/SETUP.md](docs/SETUP.md).
2. On the Pi: `python3 ~/robot/tests/check.py safe`, then the rest of [docs/TESTING.md](docs/TESTING.md).
3. From your computer: `./run.sh hello`.
4. Open `routines/wander.py` (20 lines), change something, run it again.

## Writing a routine

```python
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "robot"))
import body

r = body.Robot()
try:
    r.lights("rainbow")              # "off", "rainbow", "heartbeat", "alarm", or a colour like body.BLUE
    r.look(body.PAN_SIDE["left"])    # head: always slow and smooth
    r.nod(2)
    r.drive(1500, 1500, 1.0)         # left power, right power, seconds
    p = r.play(body.path("audio/hi.wav")); p.wait()
    print(r.distance(), r.battery(), r.light())
finally:
    r.shutdown()                     # always: stops the wheels, centres the head, lights off
```

Run it with `sudo python3` if you want the LEDs (on a Pi 4 they need root); everything else
works without sudo.

## What is tested and what is not

On 2026-11-18 this exact code ran on the sister robot (Pi 4, Raspberry Pi OS 13, Connect v1 /
PCB v1 board): every check in `check.py` except `wheels`, plus `hello`, `dance` and `wander`
with the wheel lock on, `say.py` and `make_sounds.py`.

Not run in this form: the wheels actually turning (the wheel code is copied unchanged from the
sister robot, where it has driven for weeks), `setup.sh` on a blank Pi, the first-time voice
download in `say.py`, and anything on a Pi 5 or a v2 board. Start with `check.py wheels` on the
floor and expect to tune a number or two in `body.py`.
