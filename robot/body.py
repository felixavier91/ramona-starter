"""The robot's body: head, wheels, LEDs, sound, sensors. Runs on the Pi.

A thin, careful layer over Freenove's own code (motor.py, servo.py, led.py, adc.py, buzzer.py).
Every routine goes through this file, so the safety rules live in one place:

  - Head moves are always ramped (1 degree per step, ~30 deg/s) and never snap on startup.
    Freenove's Servo() jumps to centre the instant it starts, which shakes the head screws loose.
  - The ultrasonic sensor is always on. A guard thread reads it ~5x/s, and every wheel command
    goes through SafeMotor:
      * forward with something closer than STOP_CM (or with the head, and so the sensor, turned
        away from straight ahead) -> turn on the spot instead of going forward;
      * reverse only as far as it just drove forward (the sensor can't see behind);
      * while the wheels turn, the head pans at most PAN_DRIVING degrees off centre.
  - LEDs need root on a Connect v1 board (rpi_ws281x). Without root they are silently
    skipped, so every routine still runs without sudo. (Connect v2 drives them over SPI.)
  - Sound always plays in the normal user's PipeWire session, even when run with sudo.

All the numbers below are starting points measured on one car. Tune them for yours.
"""
import os, sys, pwd, time, threading, subprocess, wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

# The owner of this file is the robot's normal user. Using that (not ~) keeps paths right under sudo.
_owner = pwd.getpwuid(os.stat(os.path.abspath(__file__)).st_uid)
HOME, USER, UID = _owner.pw_dir, _owner.pw_name, _owner.pw_uid

FREENOVE = config.FREENOVE or HOME + "/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server"
if not os.path.isdir(FREENOVE):
    sys.exit(f"Freenove code not found at {FREENOVE} - see docs/SETUP.md")
sys.path.insert(0, FREENOVE)
# Freenove code reads params.json from the current directory (even lazily, e.g. ADC/LEDs),
# so we always run from there. Routines turn file arguments into full paths with body.path().
_START_DIR = os.getcwd()
os.chdir(FREENOVE)


def path(p):
    """A file argument as typed by the user -> full path (relative to where the routine was started)."""
    return os.path.normpath(os.path.join(_START_DIR, os.path.expanduser(p)))


from motor import Ordinary_Car
from servo import Servo
from pca9685 import PCA9685
try:
    from led import Led
except Exception:
    Led = None

# ---- head ----
PAN, TILT = "0", "1"                 # servo channels
TILT_MIN, TILT_MAX = 75, 105         # cautious: widen once you trust your head assembly
PAN_MIN, PAN_MAX = 40, 140
PAN_SIDE = {"left": 60, "center": 90, "right": 120}   # higher pan angle = the robot's own right
PAN_DRIVING = 15                     # head pan limit (deg off centre) while the wheels turn
HEAD_STATE = HOME + "/.robot_head"   # last head pose, so the next start ramps from there

# ---- wheels ----
STOP_CM = 35          # nothing closer than this ahead while going forward
CLEAR_CM = 45         # once blocked, the way counts as clear again only past this (no flip-flopping)
# Turning on the spot drags all four wheels sideways: below this duty the motors stall and grind.
MIN_TURN = 1400
KICK, KICK_S = 3500, 0.06   # a wheel starting (or reversing) gets a short strong push to break it loose
# Safety lock: while this file exists the wheels never turn (e.g. the robot is sitting on a desk).
#   lock:   touch ~/.robot_no_wheels        unlock:   rm ~/.robot_no_wheels
NO_WHEELS_FLAG = HOME + "/.robot_no_wheels"

# ---- colours ----
# On these WS2812s green is much brighter than red: a real yellow needs little green.
RED, GREEN, BLUE, WHITE, OFF = (255, 0, 0), (0, 255, 0), (0, 0, 255), (200, 200, 200), (0, 0, 0)
YELLOW, ORANGE, PURPLE, PINK = (255, 90, 0), (255, 35, 0), (120, 0, 200), (255, 20, 80)


class SafeMotor:
    """Wraps the Freenove car so no routine can drive into things (see the rules at the top).
    Routines call set_motor_model() as usual; the guard re-checks the last command on every reading."""
    def __init__(self, car, body):
        self.car, self.b = car, body
        self.lock = threading.Lock()
        self.req, self.out = (0, 0), (0, 0)
        self.credit, self.t = 0.0, time.time()     # forward travel (speed x s) it may retrace in reverse
        self.blind_ok = False   # set True only for a human driving by remote: allows reversing blind

    def moving(self):
        return self.out != (0, 0)

    def set_motor_model(self, a, b, c, d):
        with self.lock:
            self.req = ((a + b) / 2, (c + d) / 2)
            self._apply()

    def tick(self):
        with self.lock:
            if self.req != (0, 0): self._apply()

    def _apply(self):
        now = time.time()
        self.credit = max(0.0, self.credit + (self.out[0] + self.out[1]) / 2 * (now - self.t))
        self.t = now
        L, R = self.req
        go = (L + R) / 2
        if go > 0 and (self.b.blocked or abs(self.b.pos[PAN] - 90) > PAN_DRIVING):
            s = max(abs(L), abs(R)); L, R = (s, -s) if L >= R else (-s, s)      # dodge: turn on the spot
        elif go < 0 and self.credit <= 0 and not self.blind_ok:
            # nothing to retrace: hold still, or keep only a turn that is strong enough to really turn
            L, R = (0, 0) if abs(L - R) < 2 * MIN_TURN else ((L - R) / 2, (R - L) / 2)
        if L * R < 0:                                                           # on the spot: enough to really turn
            L, R = (max(abs(v), MIN_TURN) * (1 if v > 0 else -1) for v in (L, R))
        kick = [KICK * (1 if new > 0 else -1) if new and (old * new <= 0) and abs(new) < KICK else new
                for old, new in zip(self.out, (L, R))]
        if kick != [L, R]:                                                      # starting / reversing: push, then settle
            self.car.set_motor_model(int(kick[0]), int(kick[0]), int(kick[1]), int(kick[1])); time.sleep(KICK_S)
        self.out = (L, R)
        self.car.set_motor_model(int(L), int(L), int(R), int(R))

    def __getattr__(self, name):
        return getattr(self.car, name)


class Robot:
    def __init__(self):
        self.near, self.blocked = None, False
        self._sonar = threading.Lock()
        self.pos = _load_head()
        self.motor = SafeMotor(Ordinary_Car(), self)
        self._guard_on = True                   # ultrasonic always on
        self._guard = threading.Thread(target=self._guard_loop, daemon=True)
        self._guard.start()
        t0 = time.time()
        while self.near is None and time.time() - t0 < 1.0: time.sleep(0.05)   # first reading before the head moves
        # Start from where the head was left last time and ramp gently to centre.
        self.servo = _gentle_servo(self.pos)
        self.look(90, 90)
        self.strip = None
        if Led is not None:
            try:
                self.strip = Led().strip
            except Exception:
                self.strip = None               # not root -> no lights
        self.light_mode = "off"
        self._lights_on = False
        self._light_thread = None
        self._talk = None                       # (start time, frame secs, loudness per frame) while talking
        self._talk_color = WHITE

    def _guard_loop(self):
        while self._guard_on:
            try: d = self._measure()
            except Exception: d = None
            self.near = d if d is not None else 999.0          # no echo = nothing within ~4 m
            self.blocked = self.near < (CLEAR_CM if self.blocked else STOP_CM)
            self.motor.tick()
            time.sleep(0.02)

    # ---- head (gentle, always) ----
    def head(self, ch, target, step=1, dt=0.035):
        lo, hi = (PAN_MIN, PAN_MAX) if ch == PAN else (TILT_MIN, TILT_MAX)
        if ch == PAN and self.motor.moving():   # keep the sensor looking where it's going
            lo, hi = max(lo, 90 - PAN_DRIVING), min(hi, 90 + PAN_DRIVING)
        target = max(lo, min(hi, int(target)))
        if abs(target - 90) > 15: step, dt = 1, max(dt, 0.05)    # wide turns go extra slow
        while self.pos[ch] != target:
            self.pos[ch] += max(-step, min(step, target - self.pos[ch]))
            self.servo.set_servo_pwm(ch, self.pos[ch]); time.sleep(dt)
        _save_head(self.pos)

    def look(self, pan=90, tilt=90):
        self.head(PAN, pan); self.head(TILT, tilt)

    def nod(self, times=1):
        for _ in range(times):
            self.head(TILT, 98); self.head(TILT, 84)
        self.head(TILT, 90)

    # ---- wheels ----
    def wheels_locked(self):
        return os.path.exists(NO_WHEELS_FLAG)

    def drive(self, left, right, secs):
        """Left/right wheel power (-4095..4095, useful range ~1200-3000) for secs, then stop."""
        if self.wheels_locked():                # keep the timing, skip the motion
            time.sleep(secs); return
        self.motor.set_motor_model(left, left, right, right); time.sleep(secs)
        self.stop(); time.sleep(0.05)

    def go(self, left, right):
        """Start driving and return at once (drive() without the wait). Call stop() when done."""
        if not self.wheels_locked():
            self.motor.set_motor_model(left, left, right, right)

    def stop(self):
        self.motor.set_motor_model(0, 0, 0, 0)

    # ---- LEDs ----
    def _fill(self, c):
        n = self.strip.get_led_count()
        for i in range(n): self.strip.set_led_rgb_data(i, c)
        self.strip.show()

    @staticmethod
    def _wheel(p):
        p &= 255
        if p < 85: return (p * 3, 255 - p * 3, 0)
        if p < 170: p -= 85; return (255 - p * 3, 0, p * 3)
        p -= 170; return (0, p * 3, 255 - p * 3)

    def _light_loop(self):
        k = 0; n = self.strip.get_led_count()
        while self._lights_on:
            md = self.light_mode
            level = self._talk_level()
            if level is not None:                 # a sound is playing: pulse with it (always wins)
                self._fill(tuple(int(c * level) for c in self._talk_color)); time.sleep(0.03)
            elif callable(md):                    # a routine draws its own lights: md(strip, n, k)
                md(self.strip, n, k); time.sleep(0.03)
            elif isinstance(md, tuple):           # a plain colour, e.g. lights(BLUE)
                self._fill(md); time.sleep(0.1)
            elif md == "rainbow":
                for i in range(n): self.strip.set_led_rgb_data(i, self._wheel(i * 256 // n + k * 8))
                self.strip.show(); time.sleep(0.03)
            elif md == "heartbeat":
                for b in (0.2, 1.0, 0.4, 1.0, 0.2, 0.05):
                    self._fill(tuple(int(c * b) for c in PINK)); time.sleep(0.12)
            elif md == "alarm":
                self._fill(RED if k % 2 else OFF); time.sleep(0.1)
            else:
                self._fill(OFF); time.sleep(0.1)
            k += 1
        self._fill(OFF)

    def _talk_level(self):
        if self._talk is None: return None
        start, dt, env = self._talk
        i = int((time.time() - start) / dt)
        if i >= len(env): self._talk = None; return None
        return env[i]

    def lights(self, mode):
        """mode: "off", "rainbow", "heartbeat", "alarm", a colour tuple, or a function(strip, n, k)."""
        self.light_mode = mode
        if self.strip is not None and not self._lights_on:
            self._lights_on = True
            self._light_thread = threading.Thread(target=self._light_loop, daemon=True)
            self._light_thread.start()

    # ---- sound ----
    def _as_user(self, cmd):
        env = ["env", f"XDG_RUNTIME_DIR=/run/user/{UID}"]
        return ["sudo", "-u", USER] + env + cmd if os.geteuid() == 0 else cmd

    def speaker_ok(self):
        """With a Bluetooth speaker configured: make sure it is connected (try to reconnect once)."""
        mac = config.SPEAKER
        if not mac: return True
        info = lambda: subprocess.run(self._as_user(["bluetoothctl", "info", mac]), capture_output=True, text=True).stdout
        if "Connected: yes" not in info():
            subprocess.run(self._as_user(["bluetoothctl", "connect", mac]), capture_output=True, timeout=20)
            time.sleep(3)
        return "Connected: yes" in info()

    def play(self, wav, volume=0.7, color=WHITE, pulse=True):
        """Start playing a wav and return the player process (poll() it, or wait()).
        The LEDs pulse with the sound in `color` unless pulse=False."""
        if not self.speaker_ok():
            raise RuntimeError("Bluetooth speaker not connected - is it turned on?")
        subprocess.run(self._as_user(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", str(min(1.0, volume))]))
        env, dt = loudness(wav)
        secs = len(env) * dt
        p = subprocess.Popen(self._as_user(["pw-play", wav]), start_new_session=True)
        self._talk_color = color
        if pulse:
            self._talk = (time.time() + 0.15, dt, env)   # ~0.15 s output latency
        self.lights(self.light_mode)            # make sure the light thread is running
        # With no working output pw-play can hang forever: kill it shortly after the clip should end.
        # (Kill the whole group: under sudo, p is the sudo wrapper and pw-play is its child.)
        def stop_stuck():
            if p.poll() is None:
                try: os.killpg(p.pid, 9)
                except OSError: p.kill()
        t = threading.Timer(secs + 5, stop_stuck); t.daemon = True; t.start()
        return p

    # ---- senses ----
    def distance(self):
        """Latest ultrasonic distance in cm from the always-on guard (None if no echo)."""
        if self._guard_on and self.near is not None:
            return None if self.near >= 999 else self.near
        return self._measure()

    def _measure(self):
        """Ultrasonic distance in cm (median of 3), raw lgpio timing on trig 27 / echo 22.
        (Freenove's gpiozero-based Ultrasonic class gave junk readings.) None if no echo."""
        import lgpio
        with self._sonar:
            h = lgpio.gpiochip_open(0)
            try:
                lgpio.gpio_claim_output(h, 27, 0); lgpio.gpio_claim_input(h, 22)
                ds = []
                for _ in range(3):
                    lgpio.gpio_write(h, 27, 1); time.sleep(10e-6); lgpio.gpio_write(h, 27, 0)
                    t0 = time.time()
                    while lgpio.gpio_read(h, 22) == 0 and time.time() - t0 < 0.03: pass
                    s0 = time.time()
                    while lgpio.gpio_read(h, 22) == 1 and time.time() - s0 < 0.03: pass
                    d = (time.time() - s0) * 17150
                    if 2 < d < 400: ds.append(d)
                    time.sleep(0.03)
                return sorted(ds)[len(ds) // 2] if ds else None
            finally:
                lgpio.gpiochip_close(h)

    def light(self):
        """(left, right) photoresistor voltages."""
        from adc import ADC
        a = ADC(); v = (a.read_adc(0), a.read_adc(1)); a.close_i2c(); return v

    def battery(self):
        """Battery pack voltage (8.4 V full, about 6.6 V empty). ADC channel 2 through a divider:
        x3 on PCB v1, x2 on PCB v2, the same as Freenove's own code."""
        from adc import ADC
        a = ADC(); v = a.read_adc(2) * (3 if a.pcb_version == 1 else 2); a.close_i2c(); return round(v, 2)

    def beep(self, times=1, on=0.12, off=0.1):
        from buzzer import Buzzer
        b = Buzzer()
        for _ in range(times):
            b.set_state(True); time.sleep(on); b.set_state(False); time.sleep(off)
        b.close()

    def photo(self, path):
        subprocess.run(["rpicam-still", "-n", "-t", "600", "--width", "640", "--height", "480", "-o", path],
                       capture_output=True)
        return path

    # ---- cleanup (always call it: put your routine in try/finally) ----
    def shutdown(self):
        self._lights_on = False
        if self._light_thread: self._light_thread.join(timeout=2)
        self.stop(); self.look(90, 90)
        self._guard_on = False
        self._guard.join(timeout=1)


def _gentle_servo(pos):
    """Freenove's Servo() snaps every servo to 1500 us the instant it starts, which jerks the head
    on every routine. Build it without that snap and hold the head where it already is instead."""
    s = Servo.__new__(Servo)
    s.pwm_frequency, s.initial_pulse = 50, 1500
    s.pwm_channel_map = {str(i): 8 + i for i in range(8)}
    s.pwm_servo = PCA9685(0x40, debug=True)
    s.pwm_servo.set_pwm_freq(s.pwm_frequency)
    for ch in (PAN, TILT): s.set_servo_pwm(ch, pos[ch])
    return s

def _load_head():
    try:
        p, t = open(HEAD_STATE).read().split()
        return {PAN: int(p), TILT: int(t)}
    except Exception:
        return {PAN: 90, TILT: 90}

def _save_head(pos):
    try:
        with open(HEAD_STATE, "w") as f: f.write(f"{pos[PAN]} {pos[TILT]}")
        os.chmod(HEAD_STATE, 0o666)
    except Exception:
        pass


def loudness(wav, frame=0.03):
    """Per-frame loudness in 0.05..1, for pulsing the LEDs along with a sound (16-bit wav)."""
    import numpy as np
    with wave.open(wav) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    if ch > 1: a = a.reshape(-1, ch).mean(axis=1)
    n = int(sr * frame); a = a[:len(a) // n * n].reshape(-1, n)
    e = np.sqrt((a ** 2).mean(axis=1))
    lo, hi = np.percentile(e, 30), np.percentile(e, 97)
    lvl = np.clip((e - lo) / max(hi - lo, 1e-6), 0, 1) ** 0.7
    return list(0.05 + 0.95 * lvl), frame


# ---- moves (each returns roughly to where it started) ----
def wiggle(r):
    for _ in range(3): r.drive(2200, -2200, 0.25); r.drive(-2200, 2200, 0.25)

def strut(r):
    r.look(90, 90)
    r.drive(2000, 2000, 0.9); r.drive(2200, -2200, 0.35); r.drive(-2200, 2200, 0.35); r.drive(-2000, -2000, 0.9)

def spin_right(r):
    r.head(PAN, 96); r.drive(2600, -2600, 1.2)

def spin_left(r):
    r.head(PAN, 84); r.drive(-2600, 2600, 1.2)

def circle(r):
    r.drive(2600, 1000, 1.6); r.drive(-2600, -1000, 1.6)

def figure8(r):
    r.drive(2600, 1000, 1.0); r.drive(1000, 2600, 1.0); r.drive(-1000, -2600, 1.0); r.drive(-2600, -1000, 1.0)

def zigzag(r):
    for l, rt in ((2400, 1200), (1200, 2400), (2400, 1200)): r.drive(l, rt, 0.45)
    for l, rt in ((-2400, -1200), (-1200, -2400), (-2400, -1200)): r.drive(l, rt, 0.45)

def shimmy(r):
    for _ in range(4): r.drive(2000, 2000, 0.15); r.drive(-2000, -2000, 0.15)

MOVES = [strut, wiggle, circle, spin_right, zigzag, figure8, shimmy, spin_left]
