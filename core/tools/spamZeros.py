"""
meant to reply to the MHD adapter before the DME can, which can cause you to send arbitrary values to the MHD app

i used this to determine scaling for MHD values, then started using `spamZerosTelnet.py` w/ emulator instead
"""

import threading
import time
import can
import sys

byteToSpam = int(sys.argv[1])

assert byteToSpam >= 0 and byteToSpam <= 255

bus = can.interface.Bus(
    interface='socketcan', 
    channel="can0"
    )


forAllRegisters = []
def buildRegisters(byte):
    global forAllRegisters

    forAllRegisters = []
    for x in [33,34,35,36,37,38,39,40,41,42,43]:
        msg = can.Message(arbitration_id=0x612, is_extended_id=False)
        arr = bytearray()

        arr += b'\xf1'
        arr += bytes([x])
        arr += bytes([byte]) * 6

        msg.data = arr
        forAllRegisters.append(msg)

    return forAllRegisters

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
        actValueAtZero = float(input("Actual value (@ 0x00): "))

        print("[+] Spamming \\xFF")
        buildRegisters(255)
        actValueAt255 = float(input("Actual value (@ 0xFF): "))

        bytesLength = int(input("Length of bytes: "))

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
        input("......")

        disableMTPrints = False

buildRegisters(0)
threading.Thread(target=solveThread, daemon=True).start()
register10Packet = None
while True:
    pkt = bus.recv()

    if register10Packet != None:
        if pkt.arbitration_id == 0x6f1:
            if not disableMTPrints: print("[+] Recieved 0x6f1 packet")

            if len(pkt.data) == 4:
                bus.send(
                    can.Message(
                        arbitration_id=0x612,
                        is_extended_id=False,
                        #data=b'\xf1\x10\x19\x61\xf0\xd5\x64\xf0'
                        #data=b'\xf1\x10\x23\x61\xf0\xd5\x64\x00'
                        data=register10Packet
                    )
                )
                if not disableMTPrints: print("Sent checksum packet")
            elif len(pkt.data) == 8:
                for msg in forAllRegisters:
                    bus.send(msg)
                if not disableMTPrints: print("Sent data packets")
    else:
        if pkt.data[1] == 0x10:
            register10Packet = pkt.data
            print("Found Reg10 packet")

    ## this is to test registers.py
    ## sends mock request frame
    #tx = can.Message(arbitration_id=0x6f1)
    #tx.data = b"\x00\x00\x00\x00\xFF\xFF\xFF\xFF"
    #bus.send(tx)
    #time.sleep(0.01)