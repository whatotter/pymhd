"""
like CANBUS' spamZeros MITM, but for use with telnet emulator
"""

import json
import time

forAllRegisters = [
]

fillFile = open("fill.txt", "w")
scalars = json.loads(open("./core/scalars.json").read())

def dumpScalars():
    global scalars

    with open("./core/scalars.json", "w") as f:
        f.write(json.dumps(scalars, indent=4))
        f.flush()

def buildRegisters(byte):
    hexaByte = hex(byte)[2:]
    if len(hexaByte) == 1:
        hexaByte = "0" + hexaByte

    fillFile.seek(0)
    fillFile.write(
        hexaByte
    )
    fillFile.flush()

def solve_linear_mapping(raw1: int, phys1: float, raw2: int, phys2: float):
    """
    Solve for factor (scale) and offset in a linear CAN mapping:
        physical = raw * factor + offset

    Args:
        raw1 (int): First raw value (integer from CAN bytes).
        phys1 (float): Corresponding physical value.
        raw2 (int): Second raw value.
        phys2 (float): Corresponding physical value.

    Returns:
        tuple: (factor, offset)
    """
    if raw1 == raw2:
        raise ValueError("raw1 and raw2 must be different to solve mapping")

    factor = (phys2 - phys1) / (raw2 - raw1)
    offset = phys1 - factor * raw1
    return factor, offset

disableMTPrints = False
def solveThread():
    global disableMTPrints

    byteLengths = {
        1: 0xFF,
        2: 0xFFFF
    }

    while True:
        input("..")

        disableMTPrints = True
        time.sleep(0.1)

        print("[+] Spamming \\x00")
        buildRegisters(0)
        actValueAtZero = float(input("\nActual value (@ 0x00): "))

        print("[+] Spamming \\xFF")
        buildRegisters(255)
        actValueAt255 = float(input("\nActual value (@ 0xFF): "))

        bytesLength = int(input("Length of bytes (use `decodeParameters.py`): "))

        print("Values: {}@0x00, {}@0xFF".format(actValueAtZero, actValueAt255))

        factor, offset = solve_linear_mapping(
            0, actValueAtZero,
            byteLengths[bytesLength], actValueAt255
        )

        print(" ")
        print("---------------------------")
        print("Factor: {}".format(factor))
        print("Offset: {}".format(offset))
        print("---------------------------")
        print(" ")

        scalars[input("Name of value to put in scalars.json: ")] = {
            "factor": factor,
            "offset": offset,
            "unit": input("Unit: ")
        }
        dumpScalars()

        print("Done\n")

        disableMTPrints = False

buildRegisters(0)
#threading.Thread(target=solveThread, daemon=True).start()
register10Packet = None
while True:
    solveThread()