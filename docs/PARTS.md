# The robot's parts

What each part is, where it sits, what it is good for, and how to use it from this kit. For
photos and the exact position of every connector, see Freenove's tutorial PDF (in
[their repo](https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi)); this
page is the plain-language version.

In the code below, `r` is `body.Robot()`.

## At a glance

| Part | Where | What it gives you | In this kit | Check |
|---|---|---|---|---|
| Raspberry Pi | on top, plugged into the car board | the brain: runs your Python, Wi-Fi, Bluetooth | everything runs here | `ssh robot` |
| Car board | the big board the Pi sits on | power, motor drivers, and the chips that talk to everything else | used through `body.py` | `check.py battery` |
| 4 motors + wheels | one at each corner | driving and turning (it steers like a tank: left side vs right side) | `r.drive()`, `r.go()`, `r.stop()` | `check.py wheels` |
| Head (2 servos) | front, on a pan/tilt mount | turns the "eyes" and camera left/right and up/down | `r.look()`, `r.head()`, `r.nod()` | `check.py head` |
| Ultrasonic sensor | on the head: the two round "eyes" | distance to whatever is straight ahead of the head | `r.distance()`, `r.blocked` | `check.py distance` |
| Camera | on the head, between or above the "eyes" | photos and video of where the head points | `r.photo(path)` | `check.py camera` |
| Light sensors (2) | front of the car board, one left, one right | how bright it is on each side | `r.light()` | `check.py light` |
| Line sensors (3) | underneath, at the front, facing the floor | light floor vs dark line under each sensor | not used yet (see below) | see below |
| LEDs (8) | on the car board | colour and animation | `r.lights()` | `check.py leds` |
| Buzzer | on the car board | one fixed beep tone | `r.beep()` | `check.py buzzer` |
| Battery pack | two 18650 cells in the holder | power for wheels, head and lights | `r.battery()` | `check.py battery` |
| Speaker | **not in the kit**: add your own | voice, music, effects | `r.play(wav)` | `check.py sound` |

## Each part in a little more detail

### Raspberry Pi and the car board

The Pi is an ordinary small computer. It has no way to drive a motor or read a voltage by
itself, so it sits on Freenove's car board, which adds:

- a **PWM chip** (PCA9685) that sets the power of the four motors and the angle of the servos;
- an **ADC chip** (ADS7830) that measures voltages: the two light sensors and the battery;
- the **motor drivers**, the **LEDs**, the **buzzer**, the **power switches** and the battery
  input.

The Pi talks to the two chips over I2C, which is why "I2C not enabled" breaks half the robot
at once. `i2cdetect -y 1` on the Pi should show `40` (PWM chip) and `48` (ADC chip).

### Wheels

Four small geared motors, one per wheel. There is no steering: she turns by running the left
and right sides at different speeds, and spins on the spot by running them in opposite
directions. Power goes from -4095 (full reverse) to 4095 (full forward); roughly 1200 to 3000
is the useful range.

```python
r.drive(1500, 1500, 1.0)     # left power, right power, seconds: straight ahead for 1 s
r.drive(2000, -2000, 0.5)    # spin right
r.go(1400, 1400)             # start rolling and return at once ...
r.stop()                     # ... until you stop
```

There are no wheel encoders, so she cannot measure how far she went or how much she turned.
"Drive 1 second" is all you can say, and the result changes with battery level and floor.
Every wheel command passes through the safety guard in `body.py`.

### Head

Two hobby servos stacked into a pan/tilt mount: one turns the head left/right (pan), the other
up/down (tilt). 90 is straight ahead for both. A higher pan angle is the robot's own right.
The head carries the ultrasonic sensor and the camera, so where the head points is where she
measures and sees.

```python
r.look(90, 90)                        # pan, tilt: straight ahead
r.head(body.PAN, body.PAN_SIDE["left"])
r.nod(2)
```

The servos are the most fragile part of the robot. `body.py` always moves them slowly and
keeps them inside safe limits.

### Ultrasonic sensor (distance)

The two metal cylinders that look like eyes. One sends a click of sound too high to hear, the
other listens for the echo; the delay gives the distance. Useful range is about 2 cm to 3 or
4 m, and no echo means nothing is in range.

```python
d = r.distance()     # cm, or None when nothing is in range
r.blocked            # True while something is closer than STOP_CM (35 cm) ahead
```

What it misses, and why it matters:

- **It sees a narrow cone straight ahead of the head**, not the whole front of the car. A
  chair leg off to one side, or anything lower than the head, is invisible.
- **Soft or slanted things** (curtains, cushions, a wall met at a shallow angle) swallow or
  deflect the sound and can read as "nothing there".
- **It cannot see the floor ending.** Table edges and stairs are invisible to it.
- **It looks where the head looks.** That is why `body.py` limits the head while driving.

### Camera

A small Pi camera on the head (usually the `ov5647`, 5 megapixels). It takes about a second
to grab a photo.

```python
r.photo("/tmp/look.jpg")     # 640x480 jpg of whatever the head is facing
```

Everything beyond snapshots (live video, finding faces or objects) is yours to add; see
[IDEAS.md](IDEAS.md).

### Light sensors

Two photoresistors at the front of the car board, left and right. Each gives a voltage that
changes with how much light falls on it, so comparing the two tells her which side is
brighter. Good for "turn toward the lamp", "it just got dark", or noticing a hand's shadow.

```python
left, right = r.light()      # volts; cover one with a finger and watch it change
```

The numbers depend on your room, so compare the two with each other, or against a reading
you took a moment ago, not against fixed values.

### Line sensors

A strip of three infrared sensors under the front of the car, a few millimetres above the
floor. Each one shines infrared light down and reports whether the floor reflects it (light
surface) or not (dark line, or no floor at all). Freenove uses them to follow a black tape
line.

This kit does not use them yet, because the sister robot never needed them. Freenove's own
class reads them:

```python
from infrared import Infrared        # works after "import body", which adds their folder
ir = Infrared()
print(ir.read_one_infrared(1), ir.read_one_infrared(2), ir.read_one_infrared(3))
ir.close()
```

Worth trying: because they also report "nothing under me", they are the only sensors on the
car that could notice a table edge. That would need testing at very low speed before you
trust it.

### LEDs

Eight RGB LEDs on the car board, each settable to any colour.

```python
r.lights("rainbow")                  # also "heartbeat", "alarm", "off"
r.lights(body.BLUE)                  # one colour
r.lights(lambda strip, n, k: ...)    # your own animation: called about 30 times a second
```

While a sound plays, the LEDs pulse with its loudness (in the colour you pass to `r.play`),
which makes her look like she is the one talking. On these LEDs green is much stronger than
red, so mix colours by eye. Depending on your board they may need `sudo` (see board versions
below).

### Buzzer

A small buzzer on the car board with one fixed tone: on or off, nothing else. Good for a honk
or an alarm. For anything musical use the speaker.

```python
r.beep(2)                    # two short beeps
r.beep(1, on=0.5)            # one long one
```

### Battery

Two 18650 lithium cells in series: 8.4 V full, about 7.0 V time to charge, about 6.6 V and
the wheels get weak. The pack powers the wheels, head and LEDs. The Pi can run from the pack
too, or from a USB-C supply on your desk while you program.

```python
r.battery()                  # volts. Read it while standing still: motors pull it down.
```

Low cells are behind most "random" problems (jerky head, weak turns, reboots), so check this
first.

### Speaker (bring your own)

The kit has no speaker and no microphone. For a voice, add a small Bluetooth or USB speaker;
[SETUP.md](SETUP.md) step 5 covers both. For her to hear you, add a USB microphone
([IDEAS.md](IDEAS.md)).

```python
p = r.play("/home/you/robot/audio/hi.wav")   # returns at once; p.wait() to wait for the end
```

## What she cannot sense

Worth knowing before you plan a behaviour:

- **How far she has driven or turned** (no wheel encoders, no compass, no gyroscope).
- **Anything behind or beside her** (one distance sensor, facing where the head faces).
- **Being picked up, tilted or bumped** (no accelerometer, no bump switches).
- **Edges and stairs** (unless you put the line sensors to work).
- **Sound** (no microphone).

## Board versions

Freenove has shipped two versions each of the car board ("PCB") and the small board that
connects it to the Pi ("Connect"). The version is printed on each board, and Freenove's setup
asks for both ([SETUP.md](SETUP.md) step 3). What changes:

| | Connect v1 | Connect v2 |
|---|---|---|
| LEDs driven by | the `rpi_ws281x` library: **needs `sudo`**, Pi 4 and older only | SPI: works on a Pi 4 and a Pi 5 |
| Pi 5 | LEDs not supported | supported |

The PCB version changes how the battery and light-sensor voltages are scaled; `body.py` and
Freenove's code read the version from `params.json` and adjust.

This kit was developed and tested on **Connect v1 + PCB v1 on a Pi 4**. On v2 boards the same
code should work, because it goes through Freenove's own classes for everything that differs,
but nobody has run it there yet. If something is off on a v2 board, the LEDs and the battery
reading are the first places to look.
