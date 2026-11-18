# Where it can go

None of this is in the kit, on purpose: each one is full of choices that should be yours. This
is what the sister robot grew into over a few weeks, what each part is built from, and roughly
how hard it was. Everything runs on the Pi itself, with no cloud service.

| Idea | Built from | Effort | Notes |
|---|---|---|---|
| **Wander without bumping** | `body.py`: `r.go()`, `r.blocked`, `r.distance()`, the head | an evening or two on the floor | A good first project, and deliberately not in the kit: we never got one we were happy with. Roll forward; when `r.blocked`, stop, look left and right, turn toward the side with more room; back out if cornered. The guard in `body.py` keeps mistakes harmless. The sensor does not see table edges, stairs, thin chair legs or soft things. |
| **Phone / tablet remote** | Python's built-in `http.server`, one HTML page | a weekend | Buttons that launch routines, a joystick, a volume slider. Add it to the home screen and it feels like an app. Let this server be the only thing that starts routines. |
| **Live camera in the remote** | `picamera2` MJPEG stream | an evening | Switching to the camera view whenever the wheels move is a nice touch. |
| **Start at boot** | a `systemd` service | an hour | `Restart=always`, log to a file. |
| **Choreographed shows** | `body.py` + a wav + a list of (time, move) | an evening each | Speech or music with moves and lights timed to it. By far the most fun per hour. |
| **Lights that follow her voice** | already in `play()` | done | Pick her colour: `r.play(wav, color=body.PURPLE)`. |
| **Better voice** | `kokoro-onnx` | an evening | More natural than Piper, about 4x slower than real time on a Pi 4, so pre-render. |
| **Voice commands** | `vosk` (small English model) + a USB microphone | a weekend | Works offline. Give it a short fixed list of phrases; open-ended listening is poor. |
| **Seeing people and things** | OpenCV YuNet (faces), SFace (who), YOLO11n in NCNN format (objects, body pose) | a week | About 2 to 5 frames a second on a Pi 4. Turning the head toward a face is a great first use. MediaPipe does not run on a Pi 4. |
| **Gestures** | body pose from YOLO11n-pose | after the above | Hands up, pointing, waving. Finger gestures need a Pi 5. |
| **A face** | a small SPI/I2C OLED or LCD + Pillow | a weekend | Eyes that blink and a mouth that moves with speech. Needs an extra display; the kit has none. |
| **Battery card / weather** | `r.battery()`, Open-Meteo (free, no key) | an evening | Something for her to say or show when idle. |

## Working on her with Claude Code

Most of the sister robot was written by describing what we wanted to Claude Code on a computer
and letting it edit the files, deploy and run them over `ssh robot`. If you do the same:

- Keep `CLAUDE.md` (in this folder) up to date. It is read at the start of every session, so
  put your rules there once instead of repeating them.
- Say where she is ("on the desk", "on the floor, 2 m clear") before asking for anything that
  moves. Lock the wheels when she is on furniture.
- Ask for one change at a time and watch it run. A robot's bugs are physical; you are the
  only one who can see them.
- Write your preferences down as rules the moment you notice them ("never louder than 60%",
  "no wheel moves after 9 pm"). That is how a personality accumulates.
