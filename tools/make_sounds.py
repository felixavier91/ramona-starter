"""Makes funny sound effects and little tunes (all synthesized here, nothing copied) into
~/robot/audio/fx/*.wav, 44.1 kHz stereo. Run once on the Pi:
    python3 ~/robot/tools/make_sounds.py
then play one from a routine with r.play(".../audio/fx/ta_da.wav").
Tunes are public-domain melodies only (classical, folk, Happy Birthday) - no modern songs.
"""
import os, wave
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio", "fx")
SR = 44100
LEAD = 0.35                     # silence first: Bluetooth speakers swallow the first moment
rng = np.random.default_rng(5)


def t_(d): return np.arange(int(round(SR * d))) / SR      # every length rounds the same way
def hz(midi): return 440.0 * 2 ** ((midi - 69) / 12)


def env(n, a=0.01, r=0.08):
    e = np.ones(n); a, r = int(SR * a), int(SR * r)
    if a: e[:a] = np.linspace(0, 1, a)
    if r and r < n: e[-r:] *= np.linspace(1, 0, r)
    return e


def osc(freq, d, kind="sine"):
    """freq may be a number or an array (a sweep)."""
    f = np.full(len(t_(d)), freq, float) if np.isscalar(freq) else np.asarray(freq, float)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if kind == "sine": return np.sin(ph)
    if kind == "square": return np.sign(np.sin(ph)) * 0.6
    if kind == "saw": return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if kind == "tri": return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1


def noise(d): return rng.standard_normal(len(t_(d)))


def lowpass(x, k=8): return np.convolve(x, np.ones(k) / k, mode="same")


def mix(*parts):
    """parts: (start_seconds, signal)"""
    end = max(s + len(x) / SR for s, x in parts)
    out = np.zeros(int(SR * end) + 2)
    for s, x in parts:
        i = int(SR * s); out[i:i + len(x)] += x
    return out


def tune(notes, bpm=120, kind="square", vib=0.0):
    """notes: (midi or None for a rest, beats). A little chiptune voice."""
    parts, at, beat = [], 0.0, 60 / bpm
    for m, b in notes:
        d = b * beat
        if m is not None:
            n = len(t_(d * 0.95))
            f = hz(m) * (1 + vib * np.sin(2 * np.pi * 5.5 * t_(d * 0.95)))
            parts.append((at, osc(f, d * 0.95, kind)[:n] * env(n, 0.005, min(0.05, d * 0.3))))
        at += d
    return mix(*parts)


# ---------- sound effects ----------

def airhorn():
    d = 1.3
    x = sum(osc(f * (1 + 0.004 * np.sin(2 * np.pi * 6 * t_(d))), d, "saw") for f in (233, 349, 466, 587))
    x = np.tanh(lowpass(x, 3) * 1.5) * env(len(x), 0.02, 0.15)
    return mix((0, x[:int(SR * 0.25)] * env(len(t_(0.25)), 0.01, 0.03)), (0.33, x))


def sad_trombone():
    parts, at = [], 0.0
    for m, d in ((58, 0.45), (57, 0.45), (56, 0.45), (55, 1.4)):
        vib = 0.012 * np.sin(2 * np.pi * 6 * t_(d)) * (1 if d > 1 else 0.3)
        f = hz(m) * (1 + vib)
        x = (osc(f, d, "saw") + 0.4 * osc(f * 2, d, "saw")) * env(len(t_(d)), 0.03, 0.12)
        parts.append((at, lowpass(x, 10))); at += d * 0.97
    return mix(*parts)


def boing():
    d = 0.9; t = t_(d)
    f = 180 + 260 * np.exp(-t * 4) * (1 + 0.5 * np.sin(2 * np.pi * 14 * t))
    return osc(f, d, "sine") * np.exp(-t * 3.5)


def slide_whistle():
    up = 500 + 1300 * (t_(0.6) / 0.6) ** 1.3
    down = 1800 - 1400 * (t_(0.7) / 0.7) ** 0.8
    f = np.concatenate([up, down]); f = f * (1 + 0.01 * np.sin(2 * np.pi * 7 * np.arange(len(f)) / SR))
    x = osc(f, len(f) / SR, "sine")
    return x * env(len(x), 0.03, 0.1)


def rimshot():
    def drum(f0, d): t = t_(d); return osc(f0 * (1 + np.exp(-t * 30)), d) * np.exp(-t * 18)
    def snare(d): return lowpass(noise(d), 2) * np.exp(-t_(d) * 25) * 0.5 + osc(200, d) * np.exp(-t_(d) * 30) * 0.4
    def cymbal(d): return np.diff(noise(d + 1 / SR)) * np.exp(-t_(d) * 3) * 0.25
    return mix((0, snare(0.2)), (0.22, drum(110, 0.25)), (0.42, snare(0.15)), (0.45, cymbal(1.4)))


def pew_pew():
    def pew():
        t = t_(0.22); f = 1800 * np.exp(-t * 9) + 250
        return osc(f, 0.22, "square") * np.exp(-t * 8)
    return mix((0, pew()), (0.25, pew()), (0.5, pew()))


def drumroll():
    hits = [(i * 0.045, lowpass(noise(0.06), 2) * np.exp(-t_(0.06) * 40) * (0.3 + 0.5 * i / 40)) for i in range(40)]
    crash = np.diff(noise(1.6 + 1 / SR)) * np.exp(-t_(1.6) * 2.2) * 0.5
    boom = osc(60 * (1 + np.exp(-t_(0.5) * 20)), 0.5) * np.exp(-t_(0.5) * 6)
    return mix(*hits, (1.85, crash), (1.85, boom))


def applause():
    d = 3.0; out = np.zeros(int(SR * d))
    for _ in range(900):                              # lots of people clapping
        s = rng.uniform(0, d - 0.05); n = int(SR * 0.012); i = int(SR * s)
        out[i:i + n] += np.diff(noise(0.012 + 1 / SR))[:n] * rng.uniform(0.2, 1) * np.exp(-np.arange(n) / 120)
    return out * env(len(out), 0.3, 0.9)


def ta_da():
    def chord(ms, d): return sum(osc(hz(m), d, "saw") for m in ms) * env(len(t_(d)), 0.01, 0.2)
    return lowpass(mix((0, chord([60, 64, 67], 0.16)), (0.2, chord([65, 69, 72, 77], 1.2))), 5)


def fart():
    d = 1.0; t = t_(d)
    f = 95 + 25 * np.sin(2 * np.pi * 3 * t) + 10 * rng.standard_normal(len(t)).cumsum() / 300
    x = osc(f, d, "square") * (0.7 + 0.3 * np.sign(np.sin(2 * np.pi * 23 * t)))
    return lowpass(x, 14) * env(len(x), 0.02, 0.25) * np.linspace(1, 0.6, len(x))


def siren():
    d = 2.6; t = t_(d)
    f = 650 + 350 * (0.5 - 0.5 * np.cos(2 * np.pi * t / 1.3))
    return osc(f, d, "tri") * env(len(t), 0.05, 0.2)


def cuckoo():
    def coo(m, d): return osc(hz(m), d) * env(len(t_(d)), 0.02, 0.12)
    return mix(*[(i * 0.75 + o, coo(m, 0.28)) for i in range(2) for o, m in ((0, 79), (0.3, 75))])


def crickets():
    parts = []
    for i in range(6):
        for j in range(3):
            parts.append((i * 0.5 + j * 0.05, osc(4500, 0.03) * env(len(t_(0.03)), 0.005, 0.01) * 0.5))
    return mix(*parts)


def dun_dun_dun():
    def hit(m, d):
        x = sum(osc(hz(m + o), d, "saw") for o in (0, 12, -12)) * env(len(t_(d)), 0.01, 0.4 if d > 1 else 0.05)
        return lowpass(x, 6)
    return mix((0, hit(50, 0.3)), (0.4, hit(49, 0.3)), (0.8, hit(45, 1.8)))


def record_scratch():
    t = t_(0.5); f = 300 + 900 * np.abs(np.sin(2 * np.pi * 3 * t))
    return lowpass(noise(0.5), 3) * 0.3 * np.abs(osc(f, 0.5, "saw")) * env(len(t), 0.005, 0.1)


# ---------- public-domain tunes ----------
C, D, E, F, G, A, B = 60, 62, 64, 65, 67, 69, 71

SONGS = {
    "happy_birthday": tune([(G, .75), (G, .25), (A, 1), (G, 1), (C + 12, 1), (B, 2),
                            (G, .75), (G, .25), (A, 1), (G, 1), (D + 12, 1), (C + 12, 2),
                            (G, .75), (G, .25), (G + 12, 1), (E + 12, 1), (C + 12, 1), (B, 1), (A, 1),
                            (F + 12, .75), (F + 12, .25), (E + 12, 1), (C + 12, 1), (D + 12, 1), (C + 12, 3)], 150, "tri"),
    "fur_elise": tune([(E + 12, .5), (D + 13, .5), (E + 12, .5), (D + 13, .5), (E + 12, .5), (B, .5), (D + 12, .5), (C + 12, .5),
                       (A, 1.5), (None, .5), (C, .5), (E, .5), (A, .5), (B, 1.5), (None, .5), (E, .5), (G + 1, .5), (B, .5),
                       (C + 12, 1.5)], 150, "tri"),
    "william_tell": tune([(E, .25), (E, .25), (E, .5), (E, .25), (E, .25), (E, .5), (E, .25), (E, .25), (A, .5), (B, .5), (C + 13, .5),
                          (E, .25), (E, .25), (E, .5), (E, .25), (E, .25), (A, .5), (C + 13, .25), (C + 13, .25), (B, .5), (G + 1, .5),
                          (E, .25), (E, .25), (E, .5), (E, .25), (E, .25), (E, .5), (E, .25), (E, .25), (A, .5), (B, .5), (C + 13, .5),
                          (A, .5), (C + 13, .5), (E + 12, 1.5)], 160, "square"),
    "ode_to_joy": tune([(E, 1), (E, 1), (F, 1), (G, 1), (G, 1), (F, 1), (E, 1), (D, 1), (C, 1), (C, 1), (D, 1), (E, 1),
                        (E, 1.5), (D, .5), (D, 2)], 140, "tri"),
    "the_entertainer": tune([(D, .5), (D + 1, .5), (E, .5), (C + 12, 1), (E, .5), (C + 12, 1), (E, .5), (C + 12, 2.5), (None, .5),
                             (C + 12, .5), (D + 12, .5), (D + 13, .5), (E + 12, .5), (C + 12, .5), (D + 12, .5), (E + 12, 1),
                             (B, .5), (D + 12, 1), (C + 12, 2.5)], 170, "square"),
    "funeral_march": tune([(46, 1), (46, .75), (46, .25), (46, 1), (49, .75), (48, .25), (48, .75), (46, .25), (46, .75), (45, .25),
                           (46, 2)], 70, "saw", vib=0.006),
    "charge": tune([(G, .5), (C + 12, .5), (E + 12, .5), (G + 12, 1), (E + 12, .5), (G + 12, 2)], 150, "square"),
    "la_cucaracha": tune([(C, .5), (C, .5), (C, .5), (F, 1.5), (A, 1), (None, .5), (C, .5), (C, .5), (C, .5), (F, 1.5), (A, 1),
                          (None, .5), (F, .5), (F, .5), (E, .5), (E, .5), (D, .5), (D, .5), (C, 2)], 180, "square"),
    "twinkle_twinkle": tune([(C, 1), (C, 1), (G, 1), (G, 1), (A, 1), (A, 1), (G, 2), (F, 1), (F, 1), (E, 1), (E, 1),
                             (D, 1), (D, 1), (C, 2)], 150, "tri"),
    "jingle_bells": tune([(E, 1), (E, 1), (E, 2), (E, 1), (E, 1), (E, 2), (E, 1), (G, 1), (C, 1.5), (D, .5), (E, 4)], 200, "square"),
}

FX = {"airhorn": airhorn, "sad_trombone": sad_trombone, "boing": boing, "slide_whistle": slide_whistle,
      "rimshot": rimshot, "pew_pew": pew_pew, "drumroll": drumroll, "applause": applause, "ta_da": ta_da,
      "fart": fart, "siren": siren, "cuckoo": cuckoo, "crickets": crickets, "dun_dun_dun": dun_dun_dun,
      "record_scratch": record_scratch}


def save(name, x):
    x = np.concatenate([np.zeros(int(SR * LEAD)), x])
    x = x / (np.abs(x).max() + 1e-9) * 0.9
    st = np.repeat((x * 32767).astype(np.int16)[:, None], 2, axis=1)
    with wave.open(f"{OUT}/{name}.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, f in FX.items(): save(name, f())
    for name, x in SONGS.items(): save(name, x)
    print(len(FX), "effects,", len(SONGS), "tunes in", OUT)
