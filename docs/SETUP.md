# Setup: from a blank SD card to the first test

The reference robot is a Raspberry Pi 4 with Raspberry Pi OS (64-bit, desktop, Debian 13) and
Python 3.13. A Pi 5 should work but is untested here (see the note at the end).

## 1. Build the car

Follow Freenove's own tutorial PDF. It is in their repo:
https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi
(`Tutorial(ordinary_wheels).pdf`, or the mecanum one if you have those wheels. This kit assumes
ordinary wheels.) Read `About_Battery.pdf` before buying cells: the car takes two 18650 Li-ion
cells and is picky about them.

While building: put the servos at their centre position before you screw the head on (the
tutorial says how), and tighten the head screws properly. Ours worked loose.

## 2. Pi OS and SSH

1. Flash **Raspberry Pi OS (64-bit)** with Raspberry Pi Imager. In the Imager's settings set a
   hostname (say `ramona`), your user name and password, your Wi-Fi, and turn on SSH.
2. Boot the Pi, then from your computer: `ssh YOURUSER@ramona.local`
3. Make logins password-free and give the robot a short name. On your computer:

   ```
   ssh-keygen -t ed25519          # only if you have no key yet; press Enter three times
   ssh-copy-id YOURUSER@ramona.local
   ```

   and add to `~/.ssh/config`:

   ```
   Host robot
       HostName ramona.local
       User YOURUSER
       ServerAliveInterval 30
   ```

   From now on `ssh robot` works, and `deploy.sh` / `run.sh` use that name. If `ramona.local`
   stops resolving one day, put the Pi's IP address in `HostName` (and reserve that address for
   it in your router).

`run.sh` uses `sudo` on the Pi without a password. That is the default for the first user on
Raspberry Pi OS; nothing to do.

## 3. Freenove's setup (once)

On the Pi:

```
cd ~
git clone --depth 1 https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi.git
cd Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code
sudo python3 setup.py
```

It installs their libraries, turns on I2C and the camera in `/boot/firmware/config.txt`, and
asks which camera you have (`ov5647` is the one that comes with most kits; it is printed on the
camera board). Reboot when it finishes.

Then run their test once, so it asks for your board versions and writes `params.json`:

```
cd ~/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server
sudo python3 test.py Led
```

It asks for **Connect version** and **PCB version** (both printed on the boards; the tutorial
shows where). Those answers decide how the LEDs and motors are driven, so get them right. To
change them later, delete `params.json` in that folder and run the test again.

## 4. This kit

On your computer, in this folder:

```
./deploy.sh                 # copies everything to ~/robot on the Pi
ssh robot bash robot/setup.sh
```

`setup.sh` makes a Python venv in `~/robot/venv` and installs Piper (the voice) into it.
Nothing else is installed system-wide apart from three small apt packages.

Now edit `robot/config.py` (name, speaker, voice), run `./deploy.sh` again, and go to
[TESTING.md](TESTING.md).

## 5. Sound

The Pi has no speaker. Pick one:

- **USB or 3.5 mm speaker**: plug it in, leave `SPEAKER = None` in `config.py`. If the sound
  comes out of the wrong output, choose the right one once with `wpctl status` (find its number
  under Sinks) and `wpctl set-default NUMBER`.
- **Bluetooth speaker** (what we use, strapped to the car): pair it once on the Pi:

  ```
  bluetoothctl
    scan on            # wait for your speaker to appear, note its address
    pair AA:BB:CC:DD:EE:FF
    trust AA:BB:CC:DD:EE:FF
    connect AA:BB:CC:DD:EE:FF
    quit
  ```

  and put that address in `config.py` as `SPEAKER`. Routines will then reconnect it when needed
  and tell you plainly if it is switched off.

## 6. Power

- The Pi can run from a USB-C supply on your desk while you program. The **wheels, servos and
  LEDs need the battery pack and the car-board switches on**.
- `r.battery()` reads the pack: 8.4 V is full, charge at about 7.0 V. Under about 6.6 V the
  wheels get weak and the Pi may brown out.
- Shut down properly (`ssh robot sudo poweroff`) before switching off. Pulling power has
  corrupted files on our SD card more than once, which is why `deploy.sh` ends with `sync`.

## Pi 5 note

Untested by us. Freenove supports it (their code drives the LEDs over SPI on a Pi 5 instead of
`rpi_ws281x`, which is what needs `sudo` on a Pi 4), and `body.py` only uses their classes, so
the LEDs should work. The ultrasonic code opens `gpiochip 0`; on some Pi 5 systems the header
is `gpiochip 4`. If `check.py distance` errors on a Pi 5, that line in `body.py` is the place.
