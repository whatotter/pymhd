# MHD adapter emulator
these tools can emulate the MHD adapter to intercept packets from MHD's app

responses were learned from PCAPs of how the MHD app talks to the telnet adapter

# vin base64 packet
as long as you have a super license, and if you can replace the string "OTTTTTTTTTTTTTTER" in this base64 string with the vin assigned to that super license:

```
lPFAYhAQT1RUVFRUVFRUVFRUVFRUVEVS
```
then you can use the emulator with MHD!

once replaced with your actual 18 char vin (last character should be G if you have a 17char vin), place the base64 encoded string in `vin.txt` and run `emulator.py`

# file descriptions
### `fill.txt`
singular byte in `FF` format to fill stream packets with (no granular scaling becuz too lazy)

### `activeCodes.txt`
DME DTC codes to send when **active** codes are requested, max of 20, split by newlines (LF format)

### `shadowCodes.txt`
DME DTC codes to send when **shadow** codes are requested, max of 20, split by newlines (LF format)

### `vin.txt`
base64 encoded packet to reply with when MHD asks for CAS VIN (which is what it uses to check licenses) - this should be your actual vehicle VIN, or a VIN that is connected to your account

### `dme_vin.txt`
string to reply with when MHD asks for DME VIN - could be vanity, since MHD does not care about this field