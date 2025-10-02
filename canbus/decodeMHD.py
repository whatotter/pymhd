"""
this is for decoding MHD via canbus MITM
"""

from can import Message
import json

def loadJsonFile(file):
    with open(file, "r") as f:
        return json.loads(f.read())

responseRegisters = {}

parameters = [
    #"accel pedal pos",
    #"antilag active",
    #"boost", "boost error d-fact",
    #"boost error p-fact", "boost mean",
    #"boost set limit", "boost setpoint",
    #"boost target", "coolant", "current map",
    #"cyl1 timing cor", "cyl2 timing cor", "cyl3 timing cor",
    #"cyl4 timing cor", "cyl5 timing cor", "cyl6 timing cor",
    
    #"accel pedal pos", "boost", "current map", "load req",
    #"maf req", "oil temp", "rail pressure"

    "pad1", "pad2",
    "accel pedal pos",
    "boost",
    "boost target",
    "coolant",
    "current map",
    "fuel low pressure sensor",
    "IAT",
    "lambda bank 1",
    "lambda bank 2",
    "ltft 1",
    "ltft 2",
    "oil temp",
    "rail pressure",
    "RPM",
    "stft 1",
    "stft 2",
    #"timing cyl 1",
    #"timing cyl 2",
    #"timing cyl 3",
    #"timing cyl 4",
    #"timing cyl 5",
    #"timing cyl 6",
    "transmission temp"
]

optionsDictLength = loadJsonFile("./odl.json")

optionsScalars = loadJsonFile("./scalars.json")

for param in parameters:
    if param not in optionsDictLength:
        raise KeyError("MHD parameter not supported: {}".format(param))

#region Decoding
def uint16(_bytes:list):
    return (_bytes[1] << 8) | _bytes[0]

def byteArrayToHex(bytear):
    hexa = []

    for byte in bytear:
        hexa.append(hex(byte))

    return hexa

def factorAndOffset(raw: int, factor: float, offset: float) -> float:
    return raw * factor + offset

def stupidDecodeShit(_bytes:list, factor, offset):

    if len(_bytes) >= 2:
        a = uint16(_bytes)
        return round(factorAndOffset(a, factor, offset), 2)
    else:
        return factorAndOffset(int(_bytes[0]), factor, offset)
    
def attemptDecode(frameData):
    ptr = 0

    optDict = {}
    for opt in parameters:
        byteLen = optionsDictLength[opt]
        _bytes = frameData[ptr:ptr+byteLen]

        optDict[opt] = {
            "value": stupidDecodeShit(_bytes, optionsScalars[opt]["factor"], optionsScalars[opt]["offset"]), 
            "bytes": byteArrayToHex(_bytes),
            "uint16": int(_bytes[0]) if len(_bytes) == 1 else uint16(_bytes)
        }

        ptr += byteLen

    return {"decoded": optDict, "leftovers": frameData[ptr:]}
#endregion

#region CANBUS framing
def decodeRequestFrame(frame:Message):
    identifier = frame.data[0]
    identifierBytes = frame.data[1:5]

    #assert identifier == 0x12

    return identifierBytes

def decodeResponseFrame(frame:Message):
    identifier    = frame.data[0]
    responseID    = frame.data[1]
    frameData     = frame.data[2:]

    #return [dataOne, dataTwo, dataThree]
    responseRegisters[responseID] = {"id": responseID, "data": frameData}
    return {"id": responseID, "data": frameData}
#endregion

#region Registers
def getRegister(register:int):
    return responseRegisters.get(register, {"data": bytearray(8)})["data"]

def getDataRegisters():
    """33-43"""
    data = bytearray()
    #        Data registers (80 bytes, 40 pair)
    for x in [33,34,35,36,37,38,39,40,41,42,43]:
        data += responseRegisters.get(x, {"data": bytearray(8)})["data"]

    return data

def clearDataRegisters():
    global responseRegisters
    responseRegisters = {}
#endregion

#region IO
def dumpODL():
    with open("./mhd/odl.json", "w") as f:
        f.write(json.dumps(optionsDictLength, indent=4))
        f.flush()

def dumpScalars():
    with open('./mhd/scalars.json', "w") as f:
        f.write(json.dumps(optionsScalars, indent=4))
        f.flush()

def dumpOptions():
    with open("./mhd/parameters.json", "w") as f:
        f.write(json.dumps(parameters, indent=4))
        f.flush()
#endregion