"""
the first script ever trying to decode MHD frames via CANBUS

only kept for historical reasons
"""

import can
import mhd.canbus.decodeMHD as decodeMHD

bus = can.interface.Bus(
    interface='socketcan', 
    channel="vcan0"
    )

def byteArrayToHex(bytear):
    hexa = []

    for byte in bytear:
        hexa.append(hex(byte))

    return hexa

def decode_boost(byte_low: int, byte_high: int) -> float:
    """
    Decode boost value from two CAN bytes.

    Args:
        byte_low (int): Least significant byte (0–255).
        byte_high (int): Most significant byte (0–255).

    Returns:
        float: Boost value in psi (gauge).
    """
    # Combine bytes (little-endian unsigned 16-bit)
    raw = (byte_high << 8) | byte_low

    print("rawDdecodeBoost = {}".format(raw))

    # Apply scale (factor) and offset
    factor = 0.0005664809100538849
    offset = -14.62257173122093

    return raw * factor + offset

def decode(raw: int, factor: float, offset: float) -> float:
    return raw * factor + offset

def mergeBytes(one,two):
    return (two << 8) | one

mhdIds = {
    6: {"name": "throttle position", "bytes": -2, "factor": 1, "offset": 0},
}

# per each numero in mhd
# they have a pair, and are added to the frame
# if the frame would be >8, they are sent in an additional frame

# so one request (0x6f1) could trigger three responses (0x612)

# b1  b2 b3  b4 b5  b6 b7  b8 b9 ...
# id  pair!  pair!  pair!  pair!

# 0xf1 = data frame

# arb id 0x612 is dme -> mhd
# arb id 0x6f1 is mhd -> dme

# 0x641 and len() == 8
#

recentRequestFrame = None
while True:
    frame = bus.recv()

    #\x12\x08 @ maf req @ 17.9

    if frame.arbitration_id == 0x612: # data frame

        if recentRequestFrame == None: continue

        decodedRequest = decodeMHD.decodeRequestFrame(recentRequestFrame)

        frameData = decodeMHD.decodeResponseFrame(frame)
    
        decodedResponse = decodeMHD.attemptDecode(frameData["id"], frameData["data"])

        if decodedResponse == None:
            continue

        print("----- {} -----".format(frame.timestamp))
        print("Request frame = {}".format(decodedRequest))
        print("Response frame data = {}".format(byteArrayToHex(frame.data)))
        print("Decoded response frame = {}".format(decodedResponse))
        print("-" * len("----- {} -----".format(frame.timestamp)))
        print('')

        decodeMHD.dumpRegisters()
        continue

    # ['0x12', '0x2', '0x21', '0xf0'] for two parameters
    elif frame.arbitration_id == 0x6f1:
        recentRequestFrame = frame
        continue

        pass