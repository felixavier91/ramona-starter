"""A full show: the robot acts out an insurance ad. Safety scan, fender bender, claim photo,
dance, tagline, chant. About a minute, and it uses every part of the body, which makes it a
good end-to-end test once the single checks pass.

A fan-made skit for fun. Not affiliated with or endorsed by Liberty Mutual.

One time, on the Pi (makes the voice clips in your robot's name and voice):
    ~/robot/venv/bin/python ~/robot/tools/make_show.py liberty_ad
Then, on the floor with 1.5 m clear all round, wheels unlocked:
    sudo python3 ~/robot/routines/liberty_ad.py          (or from your computer: ./run.sh liberty_ad)

Uses: wheels, head, LEDs (gold/navy, alarm red, camera flash, pulsing while she talks),
ultrasonic distance (skips forward moves if something is close), light sensors, battery,
buzzer, camera (the claim photo lands in ~/robot/photos/).
Clip 8, the sung chant, ships ready-made in audio/liberty_ad/; the rest are spoken lines from
speeches/liberty_ad/, so change the words there and run make_show.py again.
"""
import os, sys, time
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "robot"))
import body

A = os.path.join(ROOT, "audio", "liberty_ad")
PHOTO = os.path.join(ROOT, "photos", "claim_photo.jpg")
CLIPS = ["1_intro", "2_scan", "3_clear", "4_bump", "5_photo", "6_dance", "7_tagline", "8_jingle"]
ROOM_CM = 50           # need this much room ahead before driving forward
NAVY = (0, 20, 120)

missing = [c for c in CLIPS if not os.path.exists(os.path.join(A, c + ".wav"))]
if missing:
    sys.exit(f"missing voice clips: {', '.join(missing)}\n"
             f"make them once with:  {ROOT}/venv/bin/python {ROOT}/tools/make_show.py liberty_ad")

r = body.Robot()

def brand(strip, n, k):
    """Gold and navy, swapping places four times a second."""
    for i in range(n): strip.set_led_rgb_data(i, body.YELLOW if (i + k // 8) % 2 else NAVY)
    strip.show()

FLASH = (255, 255, 255)

def say(name, during=None, color=body.WHITE):
    """Play a clip; run during() while it plays, then wait for it to finish."""
    p = r.play(os.path.join(A, name + ".wav"), color=color)
    if during: during()
    while p.poll() is None: time.sleep(0.05)

def room_ahead():
    d = r.distance()
    print(f"distance ahead: {d} cm", flush=True)
    return d is None or d > ROOM_CM

def chacha():
    r.head(body.PAN, 84); r.drive(1500, 1500, 0.25); r.drive(-1500, -1500, 0.25)
    r.head(body.PAN, 96); r.drive(1500, 1500, 0.25); r.drive(-1500, -1500, 0.25); r.head(body.PAN, 90)

try:
    os.makedirs(os.path.dirname(PHOTO), exist_ok=True)
    r.lights(brand)

    # 1. Intro, then a happy honk
    say("1_intro", lambda: (r.look(90, 98), r.nod(1)))
    if room_ahead(): body.strut(r)
    else: body.wiggle(r)
    r.beep(2)

    # 2. Safety scan: slow look left, right, then measure ahead
    def scan():
        r.head(body.PAN, body.PAN_SIDE["left"]); r.head(body.PAN, body.PAN_SIDE["right"]); r.head(body.PAN, 90)
    say("2_scan", scan)
    d = r.distance(); print(f"scan distance: {d} cm", flush=True)
    if d is not None and d < 30:                         # too close: back away first
        r.lights("alarm"); r.beep(2, 0.05, 0.05); r.drive(-1800, -1800, 0.6)
    left, right = r.light(); print(f"light sensors: {left} V / {right} V, battery {r.battery()} V", flush=True)

    # 3. All clear
    r.lights(brand)
    say("3_clear", chacha)

    # 4. Fender bender: quick lurch, alarm lights and beeps
    if room_ahead(): r.drive(2600, 2600, 0.35)
    r.lights("alarm"); r.beep(3, 0.06, 0.06)
    say("4_bump", lambda: r.drive(-1500, -1500, 0.3))

    # 5. Claim photo with a camera flash
    say("5_photo", lambda: r.look(90, 92))
    r.lights(FLASH); r.photo(PHOTO); r.beep(1, 0.05, 0)
    print(f"photo saved: {PHOTO}", flush=True)
    r.lights(brand)

    # 6. Back to dancing
    say("6_dance")
    for move in (body.spin_right, body.wiggle, body.circle, body.spin_left): move(r)

    # 7. Tagline, standing proud
    say("7_tagline", lambda: (r.look(90, 98), r.nod(1)))

    # 8. The chant in yellow, with a twirl and a big finish
    r.lights(body.YELLOW)
    say("8_jingle", lambda: body.figure8(r), color=body.YELLOW)
    body.spin_right(r); r.nod(2); r.beep(1, 0.3, 0)
    time.sleep(1)
finally:
    r.shutdown()
