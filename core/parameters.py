class MHDParameter():
    def __init__(self, name, _bytes, byteLength):
        """
        Quick ref parameter class

        Args:
            name: Name of parameter
            _bytes: Bytes to request parameter (6 bytes long)
            byteLength: Length of parameter response
        """
        self.name:str = name
        """Name of parameter"""
        self.bytes:bytes = _bytes
        """Bytes to request parameter"""
        self.bytesLength:int = byteLength
        """Length of response bytes"""

    def __str__(self):
        return "<MHDParameter name={}>".format(self.name)


class MHDParameters():
    Unknown1       = MHDParameter("Unknown1", b"", 2) # doesn't have bytes (?)
    """Unknown what this is for, but for some reason needed (coconut.jpg)"""

    Unknown2      = MHDParameter("Unknown2", b"\x02\xc0\x00\x08\x08\x00", 2)
    """Unknown what this is for, but for some reason needed (coconut.jpg)"""

    AccelPedalPos = MHDParameter("Accel Ped. Pos", b"\x02\xc0\x00\x08\x0c\x00", 2)
    """Accelerator Pedal Position (0-100%)"""

    AntilagActive = MHDParameter("Antilag active", b"\x01\xd0\x00\x39\x1f\x00", 1)
    """Antilag active (0-1)"""

    BoostActual   = MHDParameter("Boost", b"\x02\xd0\x00\xc6\xb2\x00", 2)
    """Actual boost (PSI)"""

    BoostMean = MHDParameter("Boost Mean", b"\x02\xd0\x00\xdb\x1e\x00", 2)
    """Boost mean (PSI)"""

    BoostSetLimit = MHDParameter("Boost Set Limit", b"\x02\xd0\x00\xcb\x0a\x00", 2)
    """Boost set limit"""

    BoostSetPoint = MHDParameter("Boost Set Point", b"\x02\xd0\x00\xcd\xe4\x00", 2)
    """Boost set point"""

    BoostTarget = MHDParameter("Boost target", b"\x02\xd0\x00\xcd\xec\x00", 2)
    """Boost target"""

    CoolantTemp = MHDParameter("Coolant", b"\x01\xd0\x00\x76\xaa\x00", 1)
    """Coolant temp"""

    CurrentMap = MHDParameter("Current Map", b"\x01\xc0\x00\x42\xff\x00", 1)
    """Current map"""

    LPFP = MHDParameter("Fuel low pressure sensor", b"\x02\xd0\x00\x0c\xd0\x00", 2)
    """Fuel LPFP pressure"""

    IAT = MHDParameter("IAT", b"\x01\xd0\x00\x80\xec\x00", 1)
    """Intake air temperature"""

    LoadAct = MHDParameter("Actual Load", b"\x02\xd0\x00\xd3\x9c\x00", 2)
    """Load actual"""
    LoadReq = MHDParameter("Load Requested", b"\x02\xd0\x00\xc3\x64\x00", 2)
    """Load req."""

    LTFT1 = MHDParameter("LTFT 1", b"\x01\xd0\x00\x8d\x0a\x00", 1)
    """LTFT 1"""
    LTFT2 = MHDParameter("LTFT 2", b"\x01\xd0\x00\x8d\x0b\x00", 1)
    """LTFT 2"""

    MafAct = MHDParameter("MAF value", b"\x02\xd0\x00\x96\x8c\x00", 2)
    """MAF value (g/s)"""
    MafReq = MHDParameter("MAF Req", b"\x02\xd0\x00\xd2\x1a\x00", 2)
    """MAF requested value (g/s)"""

    OilTemp = MHDParameter("Oil temp", b"\x02\xc0\x00\x0d\x78\x00", 2)
    """Oil temperature"""

    RailPressure = MHDParameter("Rail pressure", b"\x02\xd0\x00\x91\x98\x00", 2)
    """Rail pressure"""

    RPM = MHDParameter("RPM", b"\x02\xd0\x00\x71\x22\x00", 2)
    """RPM"""

    STFT1 = MHDParameter("STFT 1", b"\x02\xd0\x00\x63\x76\x00", 2)
    """STFT 1"""
    STFT2 = MHDParameter("STFT 2", b"\x02\xd0\x00\x65\x56\x00", 2)
    """STFT 2"""

    TimingCyl1 = MHDParameter("Timing Cyl. 1", b"\x01\xd0\x00\x8e\x90\x00", 1)
    """Timing cyl. 1"""
    TimingCyl2 = MHDParameter("Timing Cyl. 2", b"\x01\xd0\x00\x8e\x91\x00", 1)
    """Timing cyl. 2"""
    TimingCyl3 = MHDParameter("Timing Cyl. 3", b"\x01\xd0\x00\x8e\x92\x00", 1)
    """Timing cyl. 3"""
    TimingCyl4 = MHDParameter("Timing Cyl. 4", b"\x01\xd0\x00\x8e\x93\x00", 1)
    """Timing cyl. 4"""
    TimingCyl5 = MHDParameter("Timing Cyl. 5", b"\x01\xd0\x00\x8e\x94\x00", 1)
    """Timing cyl. 5"""
    TimingCyl6 = MHDParameter("Timing Cyl. 6", b"\x01\xd0\x00\x8e\x95\x00", 1)
    """Timing cyl. 6"""

    TransTemp = MHDParameter("Transmission temp", b"\x01\xd0\x00\x8f\x98\x00", 1)
    """Transmission temp"""

    Gear = MHDParameter("Gear", b"\x01\xd0\x00\x8a\x46\x00", 1)
    """Transmission gear"""

    LambdaBank1 = MHDParameter("Lambda bank 1", b"\x02\xd0\x00\x5a\x74\x00", 2)
    """AFRs"""

    LambdaBank2 = MHDParameter("Lambda bank 2", b"\x02\xd0\x00\x5d\xd4\x00", 2)
    """AFRs"""

    Speed = MHDParameter("Speed", b"\x01\xd0\x00\x8b\x5b\x00", 1)
    """Speed (mph)"""

    TorqueActual = MHDParameter("Torque actual value", b"\x02\xd0\x00\x98\xba\x00", 1)
    """Torque actual value (guessed from dme, i think)"""

    TorqueLimActive = MHDParameter("Torque Lim. active", b"\x04\xd0\x00\xd3\x0c\x00", 2)
    """Torque limiter active (e.g. DTC/DSC intervention)"""

    WGDCBank1 = MHDParameter("WGDC Bank 1", b"\x02\xd0\x00\x95\x24\x00", 1)
    """Wastegate opening value (bank 1)"""

    WGDCBank2 = MHDParameter("WGDC Bank 2", b"\x02\xd0\x00\x95\x26\x00", 2)
    """Wastegate opening value (bank 2)"""