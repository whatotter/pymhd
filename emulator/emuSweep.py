"""
sweeps between 0-255 using math.sin, output it as hex to `fill.txt`

for use in tandem with `emulator.py`
"""

import math
import time

def bytesSin(x):
    return round((math.sin(x) + 1) * (255) / 2)

value = 0
direction = True
with open("fill.txt", "w") as f:
    while True:
        sineWave = bytesSin(value)

        f.seek(0)
        f.write(
            hex(sineWave)[2:]
        )
        f.flush()

        print(hex(sineWave)[2:])

        value += 0.05
        time.sleep(0.05)