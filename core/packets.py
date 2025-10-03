"""
Packets for MHD
"""

import base64


def byteArrayToHex(bytear:bytes):
    #return bytear.hex()

    hexa = []

    for byte in bytear:
        hexa.append(hex(byte))

    return hexa

class MHDPacket():
    def __init__(self, data:bytes, src:str):
        self.rawData = data
        """Raw packet data, direct from socket"""

        self.length = len(data)
        """Packet length"""

        self.crc = data[-1] 
        """Data checksum byte (sum+mod256)"""

        self.id = data[0]
        """Byte ID"""

        self.data = data[3:-1]
        """Packet Data"""

        self.unknown = data[1:3]
        """no fucking clue"""

        self.src = src
        """Packet source"""

        pass

    def checkCRC(self) -> bool:
        """
        Check if CRC is valid for packet

        Returns:
            `True` if valid, `False` otherwise
        """

        checksum = bytes([sum(
            self.rawData[0:-1]
            ) % 256])

        return checksum == self.crc

    """
    def decode(self) -> dict:
        \"""
        Attempt to decode DME data packet

        Returns:
            `dict` of decoded packet
        \"""

        try:
            return decodeMHD.attemptDecode(self.data)
        except Exception as e:
            print("Errored trying to decode packet")
            print("Packet details: len = {}  data = {}  err = {}".format(self.length, self.data, e))
            return None
    """

    def __str__(self):
        return "<MHDPacket object len={} data={} crc={} src='{}'>".format(self.length, byteArrayToHex(self.data), self.crc, self.src)

class MHDPackets():
    RequestFlash = b"\x87\x12\xf1\x23\x80\x07\xe6\x20\x00\x40" # 12 f1 23 80 07 e6 20 00 40
    RequestDME = b"\x82\x12\xf1\x1a\x86" # 12 f1 1a 86
    RequestRegisters = b'\x12\xf1\x21\xf0'

    RequestShadowActiveCodes = b'\x83\x12\xf1\x22\x20\x00\xc8'
    RequestActiveCodes       = b'\x84\x12\xf1\x18\x02\xff\xff\x9f'

