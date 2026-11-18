"""The few things that differ from one robot to the next. Edit freely."""

NAME = "Ramona"

# Bluetooth speaker MAC address ("AA:BB:CC:DD:EE:FF"), or None to play through whatever the
# Pi's default sound output is (USB speaker, headphone jack, HDMI).
# Find the MAC with:  bluetoothctl devices
SPEAKER = None

# Where the Freenove kit code lives on the Pi. None = ~/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server
FREENOVE = None

# Piper voice used by tools/say.py (any name from https://huggingface.co/rhasspy/piper-voices).
VOICE = "en_US-amy-medium"
