"""
opens a parameters packet file, reads it, \
then decodes it to detect parameters by their 7 bytes, \
then chop off the incrementing byte to get the request bytes aswell as the bytes length
"""

import base64

b64Packet = open("./parameterPacket.txt", "r").read()

# fill this out with the parameters set in the MHD app
# only used for pretty naming
strNames = [
    "unknown1",
    "Accel Ped. Pos.",
    "Gear",
    "Lambda bank 1",
    "Lambda bank 2",
    "Speed",
    "Torque actual value",
    "Torque Lim. active",
    "Torque Output req",
    "WGDC Bank 1",
    "WGDC Bank 2"
]

packetData = base64.b64decode(b64Packet) # turn base64 packet into bytes
parameters = [] # bytes found by iter
parameterLengths = [] # byte lengths
parameterAbsLengths = []

def byteArrayToHex(bytear):
    hexa = []

    for byte in bytear:
        hexa.append(hex(byte))

    return hexa

def makePythonCopy(dictionary):
    print("{} = MHDParameter(\"{}\", b\"{}\", {})".format(
        dictionary["name"].replace(" ", "").replace(".", ""),
        dictionary["name"],
        dictionary["bytes"],
        dictionary["length"],
    ))


currentParameterBytes = b""
recordingParameter = False
howBallsDeepAreWe = 0

for integer in packetData:
    byte = bytes([integer])

    if recordingParameter:
        currentParameterBytes += byte # record to byte

        if len(currentParameterBytes) == 7: # we got all 7 bytes we need
            lengthByte               = currentParameterBytes[0]     # get the length byte
            try:
                prevParamLength  = parameterLengths[-1]             # get the previously recorded parameter's length byte
            except:
                prevParamLength  = 0                                # default to zero if we can't get the previous one

            currentParameterBytes    = currentParameterBytes[1:]    # get last 6 bytes - this is the request itself
            responseLength           = lengthByte-prevParamLength   # calculate length of parameter data response
            parameterAbsLengths.append(responseLength)

            print("[!] Parameter saved: {} | Byte: {} | Incremental: {} | Len: {}".format(
                ''.join(f'\\x{b:02x}' for b in currentParameterBytes), howBallsDeepAreWe, lengthByte, responseLength)
                )
            
            recordingParameter = False                               # we're not recording bytes anymore
            parameters.append(                                       # to be interpreted
                {
                    "bytes": ''.join(f'\\x{b:02x}' for b in currentParameterBytes),
                    "name": strNames[len(parameters)]
                }
            )
            parameterLengths.append(lengthByte)                      # for easy ref

            currentParameterBytes = b""                              # clear the bytes buffer once we finish

    if byte == b"\x03" and recordingParameter == False:
        #print('[+] Sep detected @ byte {}'.format(howBallsDeepAreWe))
        recordingParameter = True

    howBallsDeepAreWe += 1

# idk how tf this works but it does
index = 0
parameterAbsLengths.insert(1, 2)
for parameterLenIndex in parameterAbsLengths:
    parameters[index-2]["length"] = parameterLenIndex
    index += 1
    #print(parameters[index])

print("-*"*50 + "-")
print('')

for x in parameters:
    try:
        friendlyName = strNames[parameters.index(x)]
    except:
        friendlyName = "No friendly name found"

    print("{} = {}".format(friendlyName, x))

print('')
print("-*"*50 + "-")
print('')
for x in parameters:
    makePythonCopy(x)