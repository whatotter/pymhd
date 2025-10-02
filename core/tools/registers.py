"""
read MHD frames via CANBUS in register fashion (this is how the MHD adapter works)

currently the best way to read MHD frames via CAN, still needs refining
"""

import can
import canbus.decodeMHD as decodeMHD

bus = can.interface.Bus(
    interface='socketcan', 
    channel="can0"
    )

recentRequestFrame = None
while True:
    frame = bus.recv()

    if frame.arbitration_id == 0x612: # rx frame
        decodeMHD.decodeResponseFrame(frame)

    if frame.arbitration_id == 0x6f1:
        registerData = decodeMHD.getDataRegisters()
        decodedDict = decodeMHD.attemptDecode(registerData)

        print("\033[2J")

        print("-" * 30)
        print("Decode:")
        for key, val in decodedDict["decoded"].items():
            print("{}: {}".format(key, val))
        print("-" * 30)

        if decodedDict["leftovers"][0] != 0:
            print("")
            print("[!] Leftover bytes detected")
            print(decodeMHD.byteArrayToHex(decodedDict["leftovers"]))
            ua = input("Append to optionsDictLength? ")
            
            if len(ua) >= 1:

                leftoverBytes = list(filter(
                    lambda x: x != 0,
                    decodedDict["leftovers"]
                ))
                bytesLength = len(leftoverBytes)

                kn = input("Key name: ")

                # set length of new parameter
                decodeMHD.optionsDictLength[kn] = bytesLength

                # add it to the parameter list
                decodeMHD.parameters.append(kn)

                # add it to the optionsScalars with a default factor and offset
                decodeMHD.optionsScalars[kn] = {"factor": 1, "offset": 0}

                # dump ODL, scalars, and options
                decodeMHD.dumpODL()
                decodeMHD.dumpScalars()
                decodeMHD.dumpOptions()