from mhd.core.packets import MHDPacket, MHDPackets
from mhd.core.parameters import MHDParameter, MHDParameters
from mhd.core.decode import MHDDecode

import socket
import threading
import time

class MHDAdapter():
    def __init__(self, 
                 parameters:list[MHDParameter],
                   dryRun:bool=False,
                   timeout:float=0.5, # quite aggressive timeout huh
                   heartbeatInterval:float=25
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

        if not dryRun:
            self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp.connect(("192.168.4.1", 23))
            self.tcp.settimeout(timeout)
        else:
            self.tcp = False

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

        self.heartbeatInterval = heartbeatInterval
        self.hbStallTime       = 0.025
        self.hbPacketsSent     = 0
        threading.Thread(target=self.__heartBeat__, daemon=True).start()
        self.sendingKA = False
        
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
    
    def sendData(self, packet:bytes, prepend:bool=True):
        """
        send data to adapter, no recieve, no reflection check

        prefixes data with `0x82` if `prepend == True`, suffixes with checksum

        Args:
            packet (bytes): Packet bytes to send to the adapter
            prepend (bool): Whether or not to prepend packet bytes with `b'\\x82'` (typically needed, set to `False` if you know what your doing)
        """

        # compile packet
        if prepend:
            staging = b'\x82' + packet
        else:
            staging = packet
        
        # calculate and add checksum
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


    def xfer(self, data:bytes, prepend:bool=True, expectedSize:int=0) -> MHDPacket:
        """
        Transfer data to the adapter for the DME to respond

        Args:
            data (bytes): Packet bytes to send to the DME
            prepend (bool): Whether or not to prepend packet bytes with `b'\\x82'` (typically needed, set to `False` if you know what your doing)
            expectedSize (int): Filter for only a packet of `len() >= expectedSize`, default=0

        Returns:
            MHDPacket: Data packet response from the DME
        """

        self.sendData(data, prepend=prepend)

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
    
    def requestData(self) -> dict:
        """
        request data from DME
        
        Returns:
            dict: Dictionary with DME response in structure `{"name": {"value": int}, ...}`
        """

        if self.sendingKA:
            print("Halted due to keep alive thread sending it's packet")
            while self.sendingKA:
                time.sleep(0) # wait for keep alive to finish sending and recieving

        timedout = 0
        while True:
            try:
                packet = self.xfer(
                    MHDPackets.RequestRegisters
                )
            except TimeoutError:
                timedout += 1
                print("[MHD] Timed out waiting for DME parameters packet ({} times)".format(timedout))
                continue

            return self.decoder.attemptDecode(packet.data)

