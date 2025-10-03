from core.packets import MHDPacket, MHDPackets
from core.parameters import MHDParameter, MHDParameters
from core.decode import MHDDecode

import socket
import threading
import time

class MHDAdapter():
    def __init__(self, 
                 parameters:list[MHDParameter],
                   dryRun:bool=False,
                   timeout:float=1,
                   heartbeatInterval:float=25,
                   ipAddr:str="192.168.4.1"
                ):
        """
        MHD adapter object

        Arguments:
            parameters: List of parameters, as `MHDParameter` objects
        """
        self.vin    = None
        """Vehicle VIN number"""
        self.dme    = None
        """DME Revision"""
        self.flash  = None
        """Name of recently flashed file to the DME"""

        if 12 > len(parameters): # TODO: figure out why this is
            raise KeyError("a minimum of 12 parameters is needed - you have {}".format(len(parameters)))

        #region Connection stuffs
        if not dryRun:
            self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp.connect((ipAddr, 23))
            self.tcp.settimeout(timeout)
            self.timeout = timeout
        else:
            self.tcp = False
        #endregion

        #region Retrieve vehicle info
        if self.tcp:
            dmePacket = self.xfer(MHDPackets.RequestDME, prepend=False)

            self.dme = (dmePacket.rawData[52:57]).decode().strip()
            self.vin = (dmePacket.rawData[57:67] + dmePacket.rawData[7:14]).decode().strip()
            self.flash = self.xfer(MHDPackets.RequestFlash, prepend=False).data[2:].decode().strip()
            
            pass
        #endregion

        #region Handle parameters
        parameters.insert(0, MHDParameters.Unknown1)
        parameters.insert(1, MHDParameters.Unknown2)

        self.parameters = parameters
        """Parameters given as MHDParameter objects"""

        self.parameterNames = [prm.name for prm in self.parameters]
        """String names of parameters given"""

        self.decoder = MHDDecode(self.parameters)
        """Decoder object"""

        self.sendParametersPacket()
        #endregion

        #region Heartbeat thread
        self.heartbeatInterval = heartbeatInterval
        self.hbStallTime       = 0.01
        self.hbPacketsSent     = 0
        self.sendingKA         = False
        threading.Thread(target=self.__heartBeat__, daemon=True).start()
        #endregion

        pass


    def __heartBeat__(self):
        """
        Heartbeat keep-alive thread
        """

        if self.tcp == False: return

        while True:
            time.sleep(self.heartbeatInterval)  # wait for our time to shine
            self.sendingKA = True               # no packets can send while this is True
            time.sleep(self.hbStallTime)        # wait for any packets to finish sending
            self.sendParametersPacket()         # send heartbeat packet!
            self.sendingKA = False              # put down the flag, other packets can send again
            self.hbPacketsSent += 1             # increment (just for logging/debugging purposes)

    def __calcChecksum__(self, data:bytes) -> bytes:
        """
        calculate checksum using sum+mod256
        """

        return bytes([sum(data) % 256])
    
    def sendData(self, packet:bytes, prepend:bool=True, calcChecksum:bool=True):
        """
        send data to adapter, no recieve, no reflection check

        prefixes data with `0x82` if `prepend == True`, suffixes with checksum

        Args:
            packet (bytes): Packet bytes to send to the adapter
            prepend (bool): Whether or not to prepend packet bytes with `b'\\x82'` (typically needed, set to `False` if you know what your doing)
            calcChecksum(bool): Whether or not to calculate the checksum
        """

        # compile packet
        if prepend:
            staging = b'\x82' + packet
        else:
            staging = packet
        
        # calculate and add checksum
        if calcChecksum:
            chksum  = self.__calcChecksum__(staging)
            packet = staging + chksum

        # send!
        if self.tcp != False:
            self.tcp.sendall(packet)

    def generateParametersPacket(self) -> bytes:
        """
        Generate parameters packet

        in no case would you have to use this but feel free
        """

        calc_first_byte = lambda data: 0x80 | ((len(data) - 1) & 0x7F)

        fullPacket = b"" # const
        #initialRequest = b"\x12\xf1\x2c\xf0" # const
        initialRequest = b"\x12\xf1\x72\x2c\xf0"
        packetsPointer = -1 # quick little hack
        seperator = b"\x03" # const

        # Do packet organizing
        fullPacket += initialRequest                    # Add initial request bytes
        for parameter in self.parameters:               # add each parameter
            if len(parameter.bytes) != 0:                   # if parameter is not a null parameter..
                fullPacket += seperator                         # add seperator
                fullPacket += bytes([packetsPointer])           # add pointer byte
                fullPacket += parameter.bytes                   # parameter bytes
            packetsPointer += parameter.bytesLength         # add parameter index after

        # Calc first byte
        #firstByte = calc_first_byte(fullPacket)-1
        firstByte = b"\x80"
        fullPacket = firstByte + fullPacket

        # Calc checksum
        chksum = self.__calcChecksum__(fullPacket)
        fullPacket += chksum

        return fullPacket
    
    def sendParametersPacket(self) -> None:
        """
        Generate and send parameters packet
        Also used for heartbeat (every 30s)
        """

        parametersPacket = self.generateParametersPacket()
        if self.tcp:
            try:
                self.tcp.sendall(parametersPacket)
                self.tcp.recv(512) # reflection
                self.tcp.recv(512) # ack
            except TimeoutError:
                pass


    def xfer(self, data:bytes, prepend:bool=True, useCRC:bool=True, expectedSize:int=0) -> MHDPacket:
        """
        Transfer data to the adapter for the DME to respond

        Args:
            data (bytes): Packet bytes to send to the DME
            prepend (bool): Whether or not to prepend packet bytes with `b'\\x82'` (typically needed, set to `False` if you know what your doing)
            expectedSize (int): Filter for only a packet of `len() >= expectedSize`, default=0

        Returns:
            MHDPacket: Data packet response from the DME
        """

        self.sendData(data, prepend=prepend, calcChecksum=useCRC)

        # honestly fuck the reflection idk what's wrong with it but \
        # it doesn't reflect correctly, it doesn't match with the data sent
        # am i stupid as fuck? probably
        reflection = self.tcp.recv(512)
        #print("[+] Packet = {}".format(data))
        #print("[+] Reflection = {}".format(reflection))
        #print("[+] Reflection matches data = {}".format(reflection == data))

        while True:
            DMEResponse = self.tcp.recv(2048)

            if len(DMEResponse) >= expectedSize:
                return MHDPacket(DMEResponse, "rx")
            else:
                print("[MHD] Packet recieved didn't pass expectedSize: {} < {}".format(
                    len(DMEResponse), expectedSize)
                    )
                
    def close(self) -> None:
        """
        close adapter connection
        """

        self.tcp.close()
    
    def requestData(self) -> dict:
        """
        request data from DME
        
        Returns:
            dict: Dictionary with DME response in structure `{"name": {"value": int}, ...}`
        """

        if self.sendingKA:
            #print("Halted due to keep alive packet in transit")
            while self.sendingKA:
                time.sleep(0) # wait for keep alive to finish sending and recieving

        timedout = 0
        while True:
            try:
                packet = self.xfer(
                    MHDPackets.RequestRegisters
                )

                return self.decoder.attemptDecode(packet.data)
            except TimeoutError:
                timedout += 1
                print("[MHD] Timed out waiting for DME parameters packet ({} times)".format(timedout))
                continue

    def readCodes(self) -> dict:
        """
        read shadow and active codes from the DME, returning them in hexadecimal format

        Returns:
            dict: Dictionary in structure of `{"active": ["30ff", "...."], "shadow": ["29f4", "...."]}`
        """

        # todo: make this cleaner

        self.tcp.settimeout(5) # increase timeout, make sure we get everything

        # get the data we need from the DME
        shadowPlusActive = self.xfer(
                    MHDPackets.RequestShadowActiveCodes,
                    prepend=False, useCRC=False
                )
        
        activeOnly = self.xfer(
                    MHDPackets.RequestActiveCodes,
                    prepend=False, useCRC=False
                )
        
        # get bytes we need from `activeOnly` packet
        activeCodesData   = activeOnly.data[2:]   # Active codes data
        activeCodes = []

        # get bytes we need from `shadowPlusActive` packet
        shadowActiveCodesData   = shadowPlusActive.data[4:] # Shadow+Active codes data
        shadowCodes = []

        # parse all active codes first
        for x in range(0, len(activeCodesData), 3):
            activeCodes.append(
                activeCodesData[x:x+2].hex()
            )

        # parse all shadow+active codes..
        for x in range(0, len(shadowActiveCodesData), 3):
            shadowCodes.append(
                shadowActiveCodesData[x:x+2].hex()
            )
        # then filter for shadow codes only
        shadowCodes = list(
            filter(
                lambda x: x not in activeCodes,
                shadowCodes,
            )
        )

        self.tcp.settimeout(self.timeout) # reset timeout back to whatever timeout set

        return {"active": activeCodes, "shadow": shadowCodes}

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="MHD adapter toolset")

    parser.add_argument("--target", help="IP to connect to (default: 192.168.4.1)", default="192.168.4.1")
    parser.add_argument("--vdata", action="store_true", help="Print out vehicle data (VIN, DME version, flashed file)")
    parser.add_argument("--codes", action="store_true", help="Read DME codes")
    parser.add_argument("--monitor", action="store_true", help="Monitor vehicle data (parameters r hardcoded, for now)")

    args = parser.parse_args()

    print("[+] Attempting to connect to adapter @ {}:23...".format(args.target))
    adapter = MHDAdapter([
        MHDParameters.AccelPedalPos,
        MHDParameters.BoostActual,
        MHDParameters.BoostTarget,
        MHDParameters.CoolantTemp,
        MHDParameters.CurrentMap,
        MHDParameters.LPFP,
        MHDParameters.IAT,
        MHDParameters.LambdaBank1,
        MHDParameters.LambdaBank2,
        MHDParameters.OilTemp,
        MHDParameters.RailPressure,
        MHDParameters.RPM,
        MHDParameters.TransTemp
    ], ipAddr=args.target)
    print("[!] Connected")

    print("")

    if args.vdata:
        print("[*] VIN           = {}".format(adapter.vin))
        print("[*] DME ROM       = {}".format(adapter.dme))
        print("[*] Flashed file  = {}".format(adapter.flash))

    if args.codes:
        codes = adapter.readCodes()

        # user friendly code decoder thingy
        friendlyCodes = json.loads(open("./core/codes.json", "r").read())
        defaultDescription = {"description": "No description found"}

        print("")
        print("-*-*-*-*-*-*-*-*-*-* Active codes *-*-*-*-*-*-*-*-*-*-")
        for activeCode in codes["active"]:
            print("{}: {}".format(
                activeCode,
                friendlyCodes.get(activeCode.upper(), defaultDescription)["description"]
            ))

        print("")

        print("-*-*-*-*-*-*-*-*-*-* Shadow codes *-*-*-*-*-*-*-*-*-*-")
        for shadowCode in codes["shadow"]:
            print("{}: {}".format(
                shadowCode,
                friendlyCodes.get(shadowCode.upper(), defaultDescription)["description"]
            ))
        print("")
        

    if args.monitor:
        print("\033[s") # save cursor position in console
        while True:
            try:
                data = adapter.requestData() # request data from DME

                print("\033[u") # put cursor position back up to where we started, to print over what we have

                # print out all DME data we recieved
                for parameterName, parameterValue in data.items():
                    print("{} = {}".format(parameterName, parameterValue) + (" "*10))

                time.sleep(0.1) # 10hz
            except KeyboardInterrupt:
                print("Ctrl + C")
                break

    adapter.close()
