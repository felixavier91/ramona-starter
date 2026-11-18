"""Check the robot one part at a time. Run on the Pi, from anywhere:

    python3 ~/robot/tests/check.py                 list the checks
    python3 ~/robot/tests/check.py battery         one check
    python3 ~/robot/tests/check.py safe            everything that does not turn the wheels
    sudo python3 ~/robot/tests/check.py leds       LEDs need sudo on a Pi 4
    python3 ~/robot/tests/check.py wheels          asks first; add --yes to skip the question

Each check prints what you should see or hear, so you can tell a pass from a fail yourself.
"""
import os, sys, time, wave, math, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "robot"))
import body


def battery(r):
    v = r.battery()
    print(f"  battery: {v} V   (8.4 full, below ~7.0 charge soon, below ~6.6 the wheels get weak)")
    if v < 5: print("  -> near zero usually means the car-board power switch is off (Pi on USB power only)")

def distance(r):
    print("  move your hand in front of the 'eyes' for 5 seconds:")
    for _ in range(10):
        d = r.distance()
        print("   ", "nothing in range" if d is None else f"{d:.0f} cm"); time.sleep(0.5)

def light(r):
    l, rt = r.light()
    print(f"  light sensors: left {l:.2f} V, right {rt:.2f} V   (cover one with a finger and run again: it should change)")

def buzzer(r):
    print("  two short beeps"); r.beep(2)

def head(r):
    print("  head: left, right, centre, then a nod. Slow and smooth, no jerks.")
    r.look(body.PAN_SIDE["left"], 90); r.look(body.PAN_SIDE["right"], 90); r.look(90, 90); r.nod(1)

def leds(r):
    if r.strip is None:
        print("  LEDs skipped: they need root. Run:  sudo python3", os.path.abspath(__file__), "leds"); return
    print("  LEDs: red, green, blue (check the colours are right), then rainbow")
    for c in (body.RED, body.GREEN, body.BLUE):
        r.lights(c); time.sleep(1)
    r.lights("rainbow"); time.sleep(3); r.lights("off"); time.sleep(0.3)

def camera(r):
    p = r.photo("/tmp/check_photo.jpg")
    ok = os.path.exists(p) and os.path.getsize(p) > 10000
    print(f"  camera: {'saved ' + p if ok else 'NO PICTURE - check the ribbon cable and the dtoverlay line in /boot/firmware/config.txt'}")

def sound(r):
    wav = "/tmp/check_tone.wav"
    sr = 22050
    with wave.open(wav, "wb") as w:                  # three rising notes, made right here
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"\0\0" * int(sr * 0.3))       # Bluetooth speakers swallow the first moment
        for f in (440, 554, 659):
            w.writeframes(b"".join(struct.pack("<h", int(12000 * math.sin(2 * math.pi * f * i / sr) * min(1, (sr * 0.3 - i) / 800)))
                                   for i in range(int(sr * 0.3))))
    os.chmod(wav, 0o644)
    print("  sound: three rising notes (LEDs pulse along if run with sudo)")
    r.play(wav, volume=0.6).wait(); time.sleep(0.5)

def wheels(r):
    if r.wheels_locked():
        print("  wheels are locked (~/.robot_no_wheels exists) - remove that file to test them"); return
    if "--yes" not in sys.argv:
        if input("  Wheels will turn. Robot on the floor with 1 m clear in front, or wheels off the ground? [y/N] ").lower() != "y":
            print("  skipped"); return
    d = r.distance()
    print(f"  ahead: {'clear' if d is None else f'{d:.0f} cm'}"
          + ("   (closer than %d cm: 'forward' will turn on the spot instead - that is the guard working)" % body.STOP_CM
             if d is not None and d < body.STOP_CM else ""))
    print("  forward 1 s"); r.drive(1500, 1500, 1.0); time.sleep(0.5)
    print("  back 1 s (allowed, because it just drove forward)"); r.drive(-1500, -1500, 1.0); time.sleep(0.5)
    print("  spin right, then left"); r.drive(2000, -2000, 0.6); time.sleep(0.3); r.drive(-2000, 2000, 0.6)
    print("  All four wheels should have turned. A wheel going the wrong way = its motor plug is reversed.")


CHECKS = {"battery": battery, "distance": distance, "light": light, "buzzer": buzzer, "head": head,
          "leds": leds, "camera": camera, "sound": sound, "wheels": wheels}
SAFE = [k for k in CHECKS if k != "wheels"]

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); print("checks:", ", ".join(CHECKS), "| safe | all"); sys.exit()
    names = SAFE if args == ["safe"] else list(CHECKS) if args == ["all"] else args
    bad = [n for n in names if n not in CHECKS]
    if bad: sys.exit(f"unknown check: {', '.join(bad)}")
    r = body.Robot()
    try:
        for n in names:
            print(f"[{n}]")
            try: CHECKS[n](r)
            except Exception as e: print(f"  FAILED: {type(e).__name__}: {e}")
    finally:
        r.shutdown()
