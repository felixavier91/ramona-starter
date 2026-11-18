# Lessons from the sister robot

Each of these cost an evening. Most are already handled in `robot/body.py`; this is the why,
so you know what you are changing if you change it.

## Head

- **Freenove's `Servo()` snaps the head to centre the instant it is created.** Every routine
  start jerked the head, and after a day a head screw had worked loose. `body.py` builds the
  servo object without that snap, remembers the last pose in `~/.robot_head`, and ramps from
  there.
- **Always ramp.** One degree per step, about 30 degrees a second, slower for wide turns. It
  also looks far more alive than a snap.

## Wheels

- **Spinning on the spot needs real power.** All four wheels get dragged sideways. Below about
  1400 the motors stall and grind instead of turning (`MIN_TURN`).
- **A stopped wheel needs a kick.** A 60 ms strong pulse before settling to the asked speed
  makes slow starts reliable (`KICK`).
- **Keep the ultrasonic sensor always on, in one place.** We first added obstacle checks to
  individual routines, and the one routine without them drove into a wall. Now every wheel
  command goes through `SafeMotor` and no routine can forget.
- **The sensor sits on the head.** If the head looks sideways, "ahead" is not being watched. So
  while the wheels turn, the head may pan only 15 degrees, and forward with the head turned
  becomes a turn on the spot.
- **She can't see behind her.** Reversing is allowed only as far as she just drove forward.
  (A person with a remote can be trusted more: that is what `blind_ok` is for.)
- **Have a wheel lock.** `touch ~/.robot_no_wheels` whenever she is on a table. You will be
  testing a head move at midnight and forget the routine also drives.

## Sensors

- **Freenove's `Ultrasonic` class (gpiozero) gave junk readings** on our Pi. Raw `lgpio`
  timing on pins 27/22 with a median of three is solid.
- **No echo means "far", not "error".** Open space returns nothing; treat it as clear.
- **The battery reading dips while the motors run.** Read it at rest, or keep the highest
  reading of the last minute.

## LEDs

- **On a Pi 4 the LEDs need root** (`rpi_ws281x`). `body.py` skips them silently without sudo,
  so the same routine runs either way.
- **Green is much brighter than red on these LEDs.** `(255, 200, 0)` looks green, not yellow.
  A yellow that looks yellow is about `(255, 90, 0)`. Check any colour you care about by eye.

## Sound

- **Run with sudo, play as the user.** Sound belongs to the logged-in user's PipeWire session;
  root has none. `body.py` plays through `sudo -u YOU` with `XDG_RUNTIME_DIR` set.
- **`pw-play` can hang forever when there is no working output** (speaker off). `play()` starts
  a watchdog that kills it a few seconds after the clip should have ended.
- **Bluetooth speakers swallow the first quarter second.** Put 0.3 s of silence at the start of
  every clip (`say.py` does).
- **A Bluetooth speaker sometimes connects in "phone call" mode** (tinny, mono). Disconnecting
  and reconnecting fixes it. Pair, then `trust`, so it reconnects by itself.
- **Make speech ahead of time.** Piper on a Pi 4 is about real time; nicer voices (Kokoro) are
  several times slower. Rendering inside a routine means a long awkward pause.
- **Speech engines mispronounce names.** Keep the real spelling in your text and a small
  "written -> said" table in your script.

## The Pi

- **Freenove's code reads `params.json` from the current directory.** Run from another folder
  and things fail in odd ways. `body.py` changes into their folder on import, which is why
  routines turn file arguments into full paths with `body.path()`.
- **Under sudo, `~` is root's home.** `body.py` works out the real user from who owns the file.
- **`sync` after copying code, and shut down properly.** Power cuts corrupted files twice.
- **One program at a time on the motors.** Two routines at once fight over the same PWM chip.
  If you later add an always-running app (a web remote, say), let it be the one thing that
  launches routines.
- **Commit before and after every session** (`git init` in this folder). When a change makes
  her worse, `git diff` tells you what you did.
