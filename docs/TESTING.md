# Testing

Test one part at a time, in this order. Each step takes a minute and the order means a failure
points at one thing. All commands run on the Pi (`ssh robot` first), or from your computer as
`ssh -t robot '...'`.

**Before anything with wheels: put her on the floor.** Or lock the wheels:
`touch ~/.robot_no_wheels` (routines then keep their timing but the wheels stay still;
`rm ~/.robot_no_wheels` to unlock). Use the lock whenever she is on a desk.

## The checks

```
python3 ~/robot/tests/check.py safe        # everything except the wheels
sudo python3 ~/robot/tests/check.py leds   # LEDs need sudo on a Pi 4
python3 ~/robot/tests/check.py wheels      # asks before moving
```

or one at a time: `check.py battery`, `check.py head`, ...

| Check | You should see / hear | If not |
|---|---|---|
| `battery` | 7.0 to 8.4 V | Near 0: car-board power switch is off, or no cells. An I2C error: I2C is not enabled (`sudo raspi-config` > Interface Options), or the board is not seated on the Pi's pins. |
| `distance` | cm values that follow your hand; "nothing in range" for open space | Always "nothing in range": the ultrasonic module's plug, or the head cable pulled out. |
| `light` | two voltages that change when you cover a sensor | Stuck values: same I2C causes as `battery`. |
| `buzzer` | two beeps | Silent: board switch off. |
| `head` | left, right, centre, nod: slow and smooth | Jerky or buzzing: battery low. Moves the wrong way or off-centre: servo horn mounted off-centre, see below. Nothing: servo plugged into the wrong channel (pan = 0, tilt = 1). |
| `leds` | red, then green, then blue, then rainbow | "skipped": use `sudo` (Connect v1 boards). Wrong colours or nothing: wrong Connect/PCB version in `params.json` (SETUP step 3). |
| `camera` | "saved /tmp/check_photo.jpg" | Ribbon cable (blue side faces the USB ports on a Pi 4), or the wrong camera model in `/boot/firmware/config.txt`. Look at the photo with `scp robot:/tmp/check_photo.jpg .` |
| `sound` | three rising notes | See "Sound" in SETUP. With a Bluetooth speaker: is it on? |
| `wheels` | forward, back, spin right, spin left; all four wheels turn | One wheel backwards: swap that motor's plug around. Grinding on spins: raise `MIN_TURN` in `body.py`. Won't go forward and spins instead: something is within 35 cm, the guard is doing its job. |

## Then the examples

From your computer, in this folder:

```
./run.sh hello                      # no wheels
ssh robot '~/robot/venv/bin/python ~/robot/tools/say.py "Hello, I am Ramona." ~/robot/audio/hi.wav'
./run.sh hello ~/robot/audio/hi.wav left
./run.sh dance 15                   # on the floor, 1.5 m clear
```

## The full show (the real end-to-end test)

When every check passes and `dance` works, run the one-minute show. It uses the wheels, head,
LEDs, speaker, distance sensor, light sensors, battery reading, buzzer and camera in one go,
so if it runs start to finish, the whole robot works.

```
ssh robot '~/robot/venv/bin/python ~/robot/tools/make_show.py liberty_ad'    # once: makes the voice clips
./run.sh liberty_ad                                                          # on the floor, 1.5 m clear all round
```

She introduces herself, scans left and right, has a pretend fender bender, takes a "claim
photo" (saved in `~/robot/photos/` on the Pi), dances, and finishes with a sung chant in
yellow light. It is also the best file to read for how a longer show is put together: lines
of speech in `speeches/`, each played with a move running alongside it.

Ctrl+C stops a routine cleanly: the `finally: r.shutdown()` in each one stops the wheels and
centres the head.

## Tuning for your car

Every car is a little different. The numbers live at the top of `robot/body.py`:

- **Head centre.** If she looks slightly sideways at 90, the servo horn is a tooth off. Remount
  it, or just treat e.g. 86 as your centre.
- **`TILT_MIN/MAX`, `PAN_MIN/MAX`.** Ours are cautious. Widen them one step at a time and
  watch for the head touching the chassis or straining a cable.
- **`MIN_TURN`** (1400). The lowest power at which she still turns on the spot. On carpet it
  needs to be higher than on a hard floor.
- **`STOP_CM` / `CLEAR_CM`** (35 / 45). How close is too close. Faster driving needs more.
- **Drive power.** Useful range is roughly 1200 to 3000 out of 4095. Below about 1000 the
  motors hum without moving.
- **Does she drive straight?** `r.drive(1500, 1500, 3)` on a hard floor. A steady pull to one
  side is normal with these motors; give that side a little more power in your routines.

## When something that worked stops working

1. `check.py battery`. Low cells cause most "random" problems: weak wheels, jerky head, reboots.
2. Is another routine still running? `ssh robot pgrep -af routines/` (two programs driving the
   same motors fight each other). `sudo pkill -f routines/` stops them.
3. `ssh robot` not connecting: the Pi takes about 40 s to boot; after that, check your router
   for its address (see SETUP step 2).
