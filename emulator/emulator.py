"""
emulate the MHD adapter itself for use with the MHD app

not full emulation, only enough for data logging and grabbing parameters
"""
import base64
import socket
import time

# setup socket
a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
a.bind(("0.0.0.0", 23))
a.listen(1)

def byteArrayToHex(bytear:bytes):
    return bytear.hex()

def checksum(data:bytes) -> bytes:
    """
    calculate checksum using sum+mod256
    """

    return bytes([sum(data) % 256])

def buildShadowCodes() -> bytes:
    """
    build shadow codes from `shadowCodes.txt`
    """

    codes = open("shadowCodes.txt").read().split("\n")[:20] # only 20 codes can be sent

    calc_first_byte = lambda data: (0x80+1) | ((len(data) - 1) & 0x7F)

    totalPacket = b''

    totalPacket += b"\xf1\x12\x62\x20\x00" # shadow+active codes request
    totalPacket += int.to_bytes(len(codes)) # amount of codes stored

    # add all codes we want
    for code in codes:
        if len(code) == 4:
            totalPacket += bytes.fromhex(code)
            totalPacket += b"\x01" # TODO: figure out how this works

    # calc first byte
    firstByte = bytes([calc_first_byte(totalPacket)-1])
    print('first byte: {}'.format(firstByte))
    totalPacket = firstByte + totalPacket

    # finally, calc checksum
    totalPacket += checksum(totalPacket)

    return totalPacket

def buildActiveCodes() -> bytes:
    """
    build active codes from `activeCodes.txt`
    """

    codes = open("activeCodes.txt").read().split("\n")[:20] # only 20 codes can be sent

    calc_first_byte = lambda data: (0x80+1) | ((len(data) - 1) & 0x7F)

    totalPacket = b''

    totalPacket += b"\xf1\x12\x58" # active codes request
    totalPacket += int.to_bytes(len(codes)) # amount of codes stored

    # add all codes we want
    for code in codes:
        if len(code) == 4:
            totalPacket += bytes.fromhex(code)
            totalPacket += b"\x48" # TODO: figure out how this works

    # calc first byte
    firstByte = bytes([calc_first_byte(totalPacket)-1])

    print('first byte: {}'.format(firstByte))

    totalPacket = firstByte + totalPacket

    # finally, calc checksum
    totalPacket += checksum(totalPacket)

    return totalPacket

def replaceVin(b64):
    packet = base64.b64decode(b64)

    vinFile = open("dme_vin.txt", "r").read().strip()
    vinOne = vinFile[:10].encode()
    vinTwo = vinFile[10:17].encode()

    # padding
    while len(vinOne) != 10:
        vinOne += b" "
    # padding
    while len(vinTwo) != 7:
        vinTwo += b" "

    packet = packet.replace(b"OTTRWUZHRE", vinOne)
    packet = packet.replace(b"HIOTTER", vinTwo)

    return base64.b64encode(packet).decode()

paramaterPacketFileObject = open("parameterPacket.txt", "w")

qwe = base64.b64decode # i used this cuz it's quick to type `qwe`
responses = { # every single request and response MHD looks for
    # Request                   ->          Response
    qwe("ghLxGoAf"): "n/ESWoAAAAdhE5cAFwAAMzMgCAIHBAAAAAAAAAAAAP///z0=",
    qwe("gvHx/f1e"): "hfHx/QAQAQ2C",
    qwe("ghLxGpEw"): "RQAAQAAAQABABr42wKgEAQrXrQEAF7kud+t4Uy9SAstQGAgALjwAAJTxElqRAAAHYROXAAAHYROXAAAHYROXuA==",
    qwe("ghLxMQrA"): "g/EScQoBAg==",

    # vin requests
    qwe("ghLxGoYl"): replaceVin("gPESQlqGAUhJT1RURVIgFAQIAAAHYmFmAAAHYmFlAAAAAAAAAAJATkZTMDEAMDA0NERDMEk4QTBTT1RUUldVWkhSRf///5A="), # VIN request # redact this
    qwe("hhLxIwAAAAdA8w=="): replaceVin("gPESQWNASElPVFRFUiAIAiMAAAdYMzQAAAdYMzUAAAAAAAABERExMjM0NQAwMDQ0REMwSTg2MFNPVFRSV1VaSFJF////GQ=="), # VIN request, two # redact this
    qwe("g0DxIhAQ9g=="): open("vin.txt", "r").read().strip(), # also vin, this is what MHD checks for licensing
    #qwe("g0DxIhAQ9g=="): "lPFAYhAQT1RUVFRUVFRUVFRUVFRUVEVS", # vin "OTTTTTTTTTTTTTTTTTER"

    qwe("gxLxMBsB0g=="): "h/EScBsBAasBq24=", # ts: 57-61
    qwe("g2DxIjEDKg=="): "mvFgYjEDoCIBRwDxB5sPGhvvHgAAgwQHCcwPDhIB", # ts: 63-67
    qwe("hxLxI4AH5gAAECo="): "kfESY01IRDKBCAAAAAAAILr/XJlZ", # ts: 69-72
    qwe("hxLxI4AAwwQABPg="): "hfESY+gP/mJC", # ts 74-77
    qwe("hxLxI4AAw0QABDg="): "hfESY46c1dS+", # ts 79-82
    qwe("hxLxI4AIAwQABEA="): "hfESYxPCWO4G", # ts 84-87
    qwe("hxLxI9AAAAAAQL0="): "gPESQWNBAIOCB4C084IGABAkBuAAv7raP//Rbv1VOTs4VMQKUOqrfZVnF2tW1VWoqwiznquutDFuXlvXx11cqqncvqifKQ==", # ts 89-93
    qwe("hxLxI4AH5iAAQHo="): "gPESQWN2MTAuMCBzdGcgMSsgOTNfOTggLSA5MyA2MCAtIGUzMCAxMDAgLSA5MSAxMDBBVF94SFAAAAAAAAAAAAAAAAAAcw==", # ts 95-99
    qwe("hxLxI4AH9wIADDk="): "jfESYwAAAAAAAAAAAAAAAPM=",
    qwe("gxLxLPAEpg=="): "gvESbPDh",
    qwe("ghLxIfCW"): "datareq",

    # code reading portions
    qwe("hxLxI9AAOKQABF0="): "hfESYwAAAADr", # not sure..
    qwe("hxLxI9AAOKAABFk="): "hfESYwAAAADr", # ts 106-109, also not sure..

    #qwe("hBLxGAL//58="): "i/ESWAMt7Ugsd4QseISa", # ts 111-114 - returns active codes
    qwe("hBLxGAL//58="): base64.b64encode(
        buildActiveCodes()
        ).decode(),

    #qwe("gxLxIiAAyA=="): "lvESYiAABi3tSC9sJCqvATD/CCx3hCx4hKI=", # ts 116-119, shadow+active codes
    qwe("gxLxIiAAyA=="): base64.b64encode(
        buildShadowCodes()
        ).decode(),

    qwe("ghLxIQWr"): "hfESYQUHYWW7" # ts 121-124, some sort of 'finish' request
}

# parameters the mhd app is using
# can be replaced with an integer if parameter isn't present in `MHDParameters`
# you can overshoot, but not by a lot
# adding 2 for a parameter that uses 1 is fine, FYI
"""
        2, MHDParameters.AccelPedalPos,
        2, MHDParameters.BoostActual,
        2, MHDParameters.BoostTarget,
        1, MHDParameters.CoolantTemp,
        1, MHDParameters.CurrentMap,
        2, MHDParameters.LPFP,
        1, MHDParameters.IAT,
        2, MHDParameters.LambdaBank1,
        2, MHDParameters.LambdaBank2,
        2, MHDParameters.OilTemp,
        2, MHDParameters.RailPressure,
        2, MHDParameters.RPM,
        1, MHDParameters.TransTemp
"""
parametersList = [
    2, #MHDParameters.Unknown2,

    2,
    2,
    2,
    1,
    1,
    2,
    1,
    2,
    2,
    2,
    2,
    2,
    1,
]
### or ###
parametersLen = (
      2 # unknown1 and unknown2
    ) + (
      6 # accelpedpos, lambda1, lambda2, etc.
    )
##########

parametersLen = None

def readFill():
    """reads fill.txt to get the byte to fill up parameters with"""
    with open("fill.txt", "r") as f:
        byte = f.read()
        return bytes.fromhex(byte)

fill = readFill()
def generateDataPacket():
    """
    remember: packet data = data[3:-1]
    """
    global fill

    # get fill byte
    fill = readFill()

    # data packet itself
    packet = b"\x98\xf1\x12\x61\xf0"

    # figure out how many bytes we need to add
    totalBytesNeeded = 0

    if parametersLen != None:
        print("| Using `parametersLen` for TBN")
        totalBytesNeeded = parametersLen * 2
    else:
        print("| Using `parametersList` iteration for TBN")
        for parameter in parametersList:
            if type(parameter) == int:
                totalBytesNeeded += parameter
            else:
                totalBytesNeeded += parameter.bytesLength

    # add those bytes
    print("| Filling {} bytes of {}".format(totalBytesNeeded, fill))
    for x in range(totalBytesNeeded):
        packet += fill

    # calc checksum
    packet += checksum(packet)

    return packet


packetsAutoReplied = 0 # how many auto replies we got
parameterPacket = None # set when a parameter packet is detected
while True:

    # wait for connection to come to us
    print("waiting..")
    conn, addr = a.accept()
    print("Got connection from {}".format(addr))

    while True:
        packet = conn.recv(2048) # recv packet

        if len(packet) == 0:
            break
        
        conn.sendall(packet) # reflect the packet back

        print()
        print('[+] packet <len={}> <b64={}> <raw={}>'.format(len(packet), base64.b64encode(packet), byteArrayToHex(packet)))

        if responses.get(packet, False): # if we have a set response for this packet
            if responses[packet] == "datareq": # data request
                data = generateDataPacket() # do our fill stuff
                print("| Device requested data ({})".format(time.time()))
                print("\\ Returning {}".format(byteArrayToHex(data)))

                for x in range(2): # send twice to speed up app
                    conn.sendall(data)
                    time.sleep(0.05)

                conn.sendall(data)
                time.sleep(0.05)

                continue
                
            # send the response
            print("| Response is available")
            conn.sendall(base64.b64decode(responses[packet]))
            print("\\ Sent response")
            packetsAutoReplied += 1

        else:
            if packet[1:4] == b"\x12\xf1\x72": # detect parameter packet
                # 12 f1 72 2c
                print("[!] this a parameter packet")
                parameterPacket = packet
                paramaterPacketFileObject.write(
                    base64.b64encode(packet).decode()
                )
                paramaterPacketFileObject.flush()
                conn.sendall(base64.b64decode("gvESbPDh")) # ack!
                continue

            print("\\ Auto-response unavailable")
            print("     Got to reply {} times".format(packetsAutoReplied))