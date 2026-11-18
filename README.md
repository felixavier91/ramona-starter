# Ramona starter kit

Working starter software for a **Freenove 4WD Smart Car Kit for Raspberry Pi** robot. Fork it,
name your robot, and start from code that already drives, looks, lights up, talks and tests
itself, instead of from the kit maker's raw examples.

## Why fork this

This comes out of several weeks of building up a sister robot of the same kit. The reusable
groundwork is here; her personality is not. What you get by starting from it:

- **You skip the trial and error.** Freenove's code snaps the head hard enough to loosen its
  screws, its distance sensor class gives junk readings, the wheels grind on slow spins, sound
  does not play under `sudo`, and a missing speaker hangs a routine forever. All of that is
  already solved in [`robot/body.py`](robot/body.py), and [docs/LESSONS.md](docs/LESSONS.md)
  explains each fix.
- **Your robot is hard to hurt.** Every wheel and head move goes through one safety layer:
  the head always ramps, the ultrasonic guard is always on, she won't drive forward into
  something or reverse blind, and one file locks the wheels while she sits on a table.
- **You can tell what is broken.** [`tests/check.py`](tests/check.py) tests one part at a
  time and says what you should see or hear; [docs/TESTING.md](docs/TESTING.md) lists what
  each failure usually means.
- **Writing a new behaviour is 15 lines.** `r.look()`, `r.nod()`, `r.drive()`, `r.lights()`,
  `r.play()`, `r.distance()`. Two example routines show the pattern.
- **It is set up for Claude Code.** [`CLAUDE.md`](CLAUDE.md) tells Claude how to deploy, run,
  test and stay safe with this robot, so you can describe what you want in plain words and
  let it write and run the code. Not required; everything works by hand too.
- **Nothing is decided for you.** No voice, colours, name, phrases or behaviours are baked
  in. The "My preferences" section of `CLAUDE.md` starts empty.

What it is not: a finished robot app. There is no remote control, no camera streaming, no
voice commands and no vision here. [docs/IDEAS.md](docs/IDEAS.md) describes how the sister
robot got each of those and what it took, as projects for you.

## How to use this repo

- **Fork** it if you are happy for your robot's code to be public, or click **Use this
  template** (green button, top right) to make your own copy that can be **private**. Your
  copy will collect personal things over time (your speaker's address, your preferences, voice
  clips), so private is a sensible default.
- Clone your copy to your computer. That folder is the source of truth for your robot: you
  edit there, `./deploy.sh` copies it to the Pi, `./run.sh` runs a routine.
- Rename things freely. Set the robot's name in `robot/config.py` and in `CLAUDE.md`.
- Commit after each change that works. When a change makes her worse, `git diff` shows what
  you did.

## Start here

You do not need to read every file. Do these four things in order.

1. **Get your own copy** (see above) and clone it on your computer (Mac or Linux; on Windows
   use WSL), e.g. to `~/ramona`.
2. **Set up the Pi** by following [docs/SETUP.md](docs/SETUP.md), steps 2 and 3 (step 1 is
   building the car; skip it if she is already assembled). This is the hands-on part, well
   under an hour, and nobody can do it for you. You are done when `ssh robot` logs you into
   the Pi.
3. **Let Claude Code take it from there** (or do step 4 of SETUP and
   [docs/TESTING.md](docs/TESTING.md) by hand if you don't use it). Open a terminal in this
   folder, run `claude`, and paste:

   > Read README.md, CLAUDE.md and the docs folder. Ramona is on the floor with 2 m clear
   > around her. Deploy the kit to the Pi, run setup.sh, then run the hardware checks one at
   > a time. Before each check tell me what I should see or hear, and wait for me to confirm.
   > Fix whatever fails.

4. **Make her yours.** Once the checks pass, just ask for things: "make her say hello in my
   voice of choice", "write a routine where she follows my hand", "make her dance to this
   song". Tell Claude your preferences as you notice them and ask it to save them in
   `CLAUDE.md`, so they stick.

**No batteries yet?** You can still do steps 1 to 3 with the Pi on a USB-C power supply.
Tell Claude "no batteries yet, Pi is on USB power" instead of the floor sentence. The camera,
the speaker, voice clips (`tools/say.py`) and sound effects all work that way. The wheels,
head and LEDs need the battery pack, so leave those checks for the day the cells arrive.

One rule from day one: **when she is on a table, lock the wheels** (`ssh robot touch
~/.robot_no_wheels`), and tell Claude where she is before asking for anything that moves.

The rest of this page is reference.

## What is in the box

```
robot/config.py     name, speaker, voice: the only file you must look at
robot/body.py       the body: head, wheels, LEDs, sound, sensors, with the safety rules built in
tests/check.py      test one part at a time (battery, distance, head, LEDs, camera, sound, wheels)
routines/           examples to copy from
  hello.py            lights + nod + a sound, no wheels
  dance.py            a set of wheel moves, to a wav or for N seconds
  liberty_ad.py       a full one-minute show (an insurance-ad skit) that uses every part of
                      the body: the end-to-end test once the single checks pass
speeches/           the show's spoken lines as text; {name} becomes your robot's name
tools/say.py        text -> voice wav (Piper, free, offline)
tools/make_show.py  render all of a show's lines into voice clips
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
4. Open `routines/hello.py` (20 lines), change something, run it again.

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
    r.drive(1500, 1500, 1.0)         # left power, right power, seconds (r.go / r.stop to drive without waiting)
    p = r.play(body.path("audio/hi.wav")); p.wait()
    print(r.distance(), r.battery(), r.light())
finally:
    r.shutdown()                     # always: stops the wheels, centres the head, lights off
```

Run it with `sudo python3` if you want the LEDs (on a Pi 4 they need root); everything else
works without sudo.

## What is tested and what is not

On 2026-11-18 this exact code ran on the sister robot (Pi 4, Raspberry Pi OS 13, Connect v1 /
PCB v1 board): every check in `check.py` except `wheels`, plus `hello` and `dance` with the
wheel lock on, `say.py` and `make_sounds.py`.

`routines/liberty_ad.py` is a port of the sister robot's best-tested show. In this form it
has only been run against fake hardware on a PC (it completes, 38 s, every body part called),
and its voice clips render. It has not yet run on a real robot.

Not run in this form: the wheels actually turning (the wheel code is copied unchanged from the
sister robot, where it has driven for weeks), `setup.sh` on a blank Pi, and anything on a
Pi 5 or a v2 board. Start with `check.py wheels` on the floor and expect to tune a number or
two in `body.py`.
