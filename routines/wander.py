"""Wander around for a while without bumping into things.

On the Pi:  python3 ~/robot/routines/wander.py [seconds]      (default 30)
The routine only ever says "go forward". body.SafeMotor does the rest: when something is closer
than STOP_CM it turns the forward command into a turn on the spot until the way is clear.
A good first routine to read: it shows how little a routine has to care about safety.
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "robot"))
import body

secs = float(sys.argv[1]) if len(sys.argv) > 1 else 30
r = body.Robot()
try:
    end = time.time() + secs
    while time.time() < end:
        r.lights(body.RED if r.blocked else body.GREEN)
        r.drive(1500, 1500, 0.5)
finally:
    r.shutdown()
