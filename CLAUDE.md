# Ramona

Ramona is a Freenove 4WD Smart Car robot (Raspberry Pi). This folder on the computer is the
source of truth; the Pi gets a copy in `~/robot` via `./deploy.sh`. The Pi is reachable as
`ssh robot`.

## How to work

- Edit here, then `./run.sh ROUTINE [args]` (deploys, then runs with sudo on the Pi).
- Everything physical goes through `robot/body.py`. Do not call Freenove's motor or servo
  classes directly from a routine: the safety rules live in `body.py`.
- Every routine: `r = body.Robot()`, work inside `try:`, `finally: r.shutdown()`.
- Check a part with `ssh -t robot 'python3 ~/robot/tests/check.py NAME'` (see `docs/TESTING.md`).
- Commit after each change that works.

## Safety rules

- Before running anything that moves the wheels, ask where she is, unless I already said.
  If she is on furniture: `ssh robot touch ~/.robot_no_wheels` first, and remove it after.
- Head moves stay ramped and inside the limits in `body.py`.
- Never bypass `SafeMotor` or switch the ultrasonic guard off.
- Check `r.battery()` when something physical misbehaves, before changing code.

## Known facts about this robot

(fill in as you learn them: Pi model, board versions, speaker, head centre, floor type,
tuned numbers and why)

## My preferences

(yours to write: her voice, her colours, how loud, what she may and may not do)
