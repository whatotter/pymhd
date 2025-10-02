"""
Decoding for recieved MHD packets
"""

import json
from core.parameters import MHDParameter

def loadJsonFile(file):
    with open(file, "r") as f:
        return json.loads(f.read())

def byteArrayToHex(bytear:bytes):
    #return bytear.hex()

    hexa = []

    for byte in bytear:
        hexa.append(hex(byte))

    return hexa

class MHDDecode():
    def __init__(self, parametersList:list[MHDParameter]):
        """
        MHD DME data decoder

        Arguments:
            parametersList: List of parameters, by name
        """
        self.parameters = parametersList
        self.parameterNames = [prm.name for prm in self.parameters]

        self.scales = loadJsonFile("./core/scalars.json")
        pass

    def uint16(self, _bytes:list):
        """Turn two bytes into a uint16 (LSB)"""
        return (_bytes[1] << 8) | _bytes[0]

    def byteArrayToHex(self, bytear):
        hexa = []

        for byte in bytear:
            hexa.append(hex(byte))

        return hexa

    def factorAndOffset(self, raw: int, factor: float, offset: float) -> float:
        """do a factor and offset on a value"""
        return raw * factor + offset

    def DecodeBytes(self, _bytes:list, opt:MHDParameter):
        """
        Decode a single parameter with it's uint16 bytes and it's MHDParameter object

        Args:
            _bytes (list): Bytes of it's value (len()==1 or ==2)
            opt (MHDParameter): MHDParameter of the value, this will be used for scale, name, etc.
        """
        # Grab factors, offset for parameter
        factor = self.scales[opt.name]["factor"]
        offset = self.scales[opt.name]["offset"]

        # Check if `_bytes` should be a uint16 by checking len
        if len(_bytes) >= 2:
            a = self.uint16(_bytes) # Turn `_bytes` into a uint16
            return round(
                self.factorAndOffset(a, factor, offset), 2
                )
        
        else: # Is a regular, single integer byte (0-255)
            return self.factorAndOffset(
                int(_bytes[0]), factor, offset
                )

    def attemptDecode(self, frameData, debug=False, onFailure=None) -> dict:
        """
        Attempt to decode a full DME response frame
        
        If there's an error decoding a specific parameter, the value will become `onFailure` (defaults to `None`)

        Args:
            frameData (bytes): data of frame
            debug (bool): whether or not to return bytes and it's raw uint16 value alongside the decoded value
            onFailure (any): returns this when there's been a failure in decoding a parameter
        """
        ptr = 0

        optDict = {}
        for opt in self.parameters:
            byteLen = opt.bytesLength
            _bytes = frameData[ptr:ptr+byteLen]

            if debug:
                optDict[opt.name] = {
                    "value": self.DecodeBytes(_bytes, opt), 
                    "bytes": byteArrayToHex(_bytes),
                    "uint16": int(_bytes[0]) if len(_bytes) == 1 else self.uint16(_bytes)
                }
            else:
                try:
                    optDict[opt.name] = {"value": round(self.DecodeBytes(_bytes, opt), 4)}
                except (UnicodeDecodeError, IndexError):
                    optDict[opt.name] = {"value": onFailure}
                    #raise KeyError("failed to decode the frame you fed me - are you sure this is right?")

            ptr += byteLen

        #print(optDict)
        #print(frameData[ptr:])
        return optDict
        #return {"decoded": optDict, "leftovers": frameData[ptr:]}