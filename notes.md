# MHD protocol reverse engineering

first off i'd like to say that this is my first reverse engineering protocol project so bare with me

second of all i'm not a notes kind of guy so these notes WILL be all over the place and jumbled up

# CANBUS
## byte order
- uint16 little endian (LSB)

## CAN frame 0x612 (data response)
|byte0 |byte1    | byte2|byte3 | byte4|byte5 | byte6|byte7 |
|------|---------|------|------|------|------|------|------|
|`0xf1`|Register |Data  |Data  |Data  |Data  |Data  |Data  |

`0xf1` seems to be "this is a response"

*bytes are merged together*, so byte2 could be for one thing, while byte4 and byte5 could be for something else

(protobuf)

## CAN frame 0x6f1 (request data)
|byte0 |byte1            |byte2            |byte3            |byte4 |byte5 |byte6 |byte7 |
|------|-----------------|-----------------|-----------------|------|------|------|------|
|`0x12`|Identifier Byte 1|Identifier Byte 2|Identifier Byte 3|`0xff`|`0xff`|`0xff`|`0xff`|

- `12 02 1a 86` triggers VIN request
- `12 21 00 40` triggers flashed file request
- `12 30 00 02 FF_FF_FF_FF` triggers some sort of send frame idk

## special frames
- `0x6f1` `f1 02 6c f0`
    - some sort of "ACK" frame

- `0x6f1` `12 XX XX XX` (change register request)
    - changes register to read from the DME maybe?
    - `02 1A 80` = ???
    - `02 1A 91` = ???
    - `02 1A 86` = VIN, spec, DME version (e.g. I8A0S)
    - `02 31 0A` = zero clue, this responds with a completely different frame than normal
    - `06 23 00 00 00 07 40` = VIN, spec, DME version
    - `21 00 40 FF FF FF FF` = Recently flashed map name

- `0x6f1` `12 30 00 02 FF FF FF FF`
    - actually read DME register
    - DME responds with data response(s) after this
    - the trailing `FF`s are needed

- `0x612` `10 1F 5A XX YY ZZ WW 07`
    - DME ACK, where `XX YY ZZ` is selected register, response after a **change register request**

## registers
|frame (int)| description                                                                       |
|-----------|-----------------------------------------------------------------------------------|
|16         | ?                                                                                 |
|33-43      | multi-frame register, if data must be truncated, it's continued on the next index |

## multi-frame
all data is transmitted from 33-43, which gives 80 bytes of data possible, or 40 uint16s (sounds about right)

so:  
`if 'register (byte1)' >= 33 and 'register (byte1)' <= 43` then it is a data frame from the DME


## values

### scaling
each value has it's own scale (factor + offset), but some share the same scale  
e.g. timing cyl 1-6 share the same scale, while rail pressure and LPFP pressure don't

use `spamZeros.py` to figure out where `0x0000` lands on in MHD's app, then `0xFFFF`  
<sub>(needs CANBUS tap into PT-CAN)

## request DME data frame order

this is gonna be long


*****************************************************
1. MHD: `12 02 0A 80` <sub>(4 bytes)
2. Vehicle: `DME ACK`
3. MHD: `12 30 00 02` <sub>(request data frame)
4. Vehicle: updates data registers 0x21 - 0x25
5. do it again..?
*****************************************************
6. MHD: `12 02 1A 91` <sub>(4 bytes)
7. Vehicle: `DME ACK`
8. MHD: `12 30 00 02` <sub>(request data frame)
9. Vehicle: updates data registers 0x21 - 0x23
*****************************************************
10. MHD: `12 02 1A 86`
11. Vehicle: `DME ACK`
12. MHD: `12 30 00 02` <sub>(request data frame)
13. Vehicle: updates data registers 0x21 - 0x2b with ASCII decodable data (VIN and DME revision)
*****************************************************
14. MHD: `12 02 31 0A`
15. Vehicle: `DME ACK`, but shorter (4 bytes) for some reason
16. MHD: weird ass request
17. Vehicle: `DME ACK`
18. MHD: `12 30 00 02` <sub>(request data frame)
19. Vehicle: updates data registers 0x21 - 0x2A
*****************************************************
20. MHD: `12 03 30 1B 01`
21. Vehicle: `DME ACK`
22. MHD: `12 30 00 02` <sub>(request data frame)
23. Vehicle: updates data register 0x21
*****************************************************

# telnet adapter reverse engineering

the last byte is always checksum BTW!!!

the MHD adapter is not a direct passthrough of the PT-CAN bus, but could be with a special register change (?)  

things to note:  
- only one device can be talking to the DME at a time
- connection randomly drops for some reason ~~(is this a me problem?)~~ (yes, you need to heartbeat every 30s)
- communication can be MITM'd through PT-CAN bus
    - how tf it talks to the PT-CAN bus through the OBD port is beyond me
- is pretty fast
- always located at `192.168.4.1:23`
- when MHD app stops monitoring parameters, they're not cleared; maybe i could use that to set parameters instead of doing it through the script
- MHD app does authentication for license, the DME doesn't do anything
    - meaning you could monitor for free, without having to pay for the monitoring license
    - hmmmmmmmm....
- MHD autheticates via the CAS VIN


## Response frames
| byte[0] | byte[1] | byte[2] | bytes[3:-1] | byte[-1] |
|---------|---------|---------|-------------|----------|
| `0x80`  |   n/a   |   n/a   |  Req. Data  | Checksum |

`bytes[1:3]` is always `0xf1 0x12` for some reason, no clue what it is
<sub>as of 9/30/25 idk if that's accurate anymore</sub>

## Request frames
|  byte[0]  | bytes[1:-1] | byte[-1] |
|-----------|-------------|----------|
| pkt-len?? | Packet data | Checksum |

byte[0] fluctuates a lot, i assume it's some sort of length parameter

the absolute closest i've gotten to calculating right is this lambda function:

```python
calc_first_byte = lambda data: (0x80 | ((len(data) - 1) & 0x7F))-1
```

maybe i'm on the right track, maybe i'm not, not sure - `0x80` works fine for the first byte anyways

## checksum calculation
raw sum (mod 256)

```python
def checksum_sum_mod256(data: bytes) -> int:
    """
    Compute checksum as sum of all bytes modulo 256.
    
    Args:
        data (bytes): Byte sequence (e.g., b'\x82\x12\xf1\x21\xf0')
    
    Returns:
        int: Checksum value (0–255)
    """
    return sum(data) % 256

# Example usage:
data = bytes([0x82, 0x12, 0xF1, 0x21, 0xF0])
print(hex(checksum_sum_mod256(data)))  # 0x96
```
the entire request is used as the checksum, so including the `0x82`

## packet hexdumps

### DME VIN response
```
[redacted]
```
grabbing vin: `data[57:67] + data[7:14]`  
DME revision: `data[52:57]`

-------------------------------------------------------------------------

### DME VIN response 2
```
[redacted]
```

-------------------------------------------------------------------------

### Recently flashed bin response
```
0000   80 f1 12 41 63 76 31 30 2e 30 20 73 74 67 20 31   ...Acv10.0 stg 1
0010   2b 20 39 33 5f 39 38 20 2d 20 39 33 20 31 30 30   + 93_98 - 93 100
0020   20 2d 20 39 33 20 36 30 20 2d 20 39 31 20 31 30    - 93 60 - 91 10
0030   30 41 54 5f 78 48 50 00 00 00 00 00 00 00 00 00   0AT_xHP.........
0040   00 00 00 00 00 17                                 ......
```
grab filename: `data[5:-2]`

-------------------------------------------------------------------------

### idk what this is
Request
```
0000   87 12 f1 23 d0 00 00 00 00 40 bd                  ...#.....@.
```
Response
```
0000   80 f1 12 41 63 41 00 83 82 07 80 b4 f3 82 06 00   ...AcA..........
0010   10 24 06 e0 00 e0 d3 de 3f ff d0 6f 79 ae 22 1b   .$......?..oy.".
0020   3a 14 c4 8a 60 55 91 7d 95 65 17 4b 56 a9 6b a8   :...`U.}.e.KV.k.
0030   ab 08 b3 9e aa 95 47 11 7e 5e 5b d5 c7 a3 90 aa   ......G.~^[.....
0040   a9 dc be a8 9f 51                                 .....Q
```

------------------

### bytes subscribing to whatever this is
```
0000   80 12 f1 e2 2c f0 03 01 02 c0 00 08 08 00 03 03   ....,...........
0010   02 c0 00 08 0c 00 03 05 02 d0 00 c6 b2 00 03 07   ................
0020   02 d0 00 cd ec 00 03 09 01 d0 00 76 aa 00 03 0a   ...........v....
0030   01 d0 00 81 a2 00 03 0b 01 d0 00 81 a3 00 03 0c   ................
0040   01 d0 00 81 a4 00 03 0d 01 d0 00 81 a5 00 03 0e   ................
0050   01 d0 00 81 a6 00 03 0f 01 d0 00 81 a7 00 03 10   ................
0060   02 d0 00 ab 02 00 03 12 01 d0 00 8a 46 00 03 13   ............F...
0070   01 d0 00 80 ec 00 03 14 02 d0 00 5a 74 00 03 16   ...........Zt...
0080   02 d0 00 5d d4 00 03 18 02 d0 00 d2 1a 00 03 1a   ...]............
0090   02 d0 00 cd e8 00 03 1c 02 c0 00 0d 78 00 03 1e   ............x...
00a0   02 d0 00 91 98 00 03 20 02 d0 00 71 22 00 03 22   ....... ...q".."
00b0   02 d0 00 63 76 00 03 24 02 d0 00 65 56 00 03 26   ...cv..$...eV..&
00c0   02 d0 00 96 1a 00 03 28 01 d0 00 8e 90 00 03 29   .......(.......)
00d0   02 d0 00 98 ba 00 03 2b 04 d0 00 d3 0c 00 03 2f   .......+......./
00e0   01 d0 00 8f 98 00 d4                              .......
```

```
                               ┌──────────────────────────────┐
           ID |    Request     |   Sep                        |
0000       80 | 12 f1 e2 2c f0 03 01 02 c0 00 08 08 00 03 03  │
0010         02 c0 00 08 0c 00 03 05 02 d0 00 c6 b2 00 03 07  │ P
0020         02 d0 00 cd ec 00 03 09 01 d0 00 76 aa 00 03 0a  │ a
0030         01 d0 00 81 a2 00 03 0b 01 d0 00 81 a3 00 03 0c  │ c
0040         01 d0 00 81 a4 00 03 0d 01 d0 00 81 a5 00 03 0e  │ k
0050         01 d0 00 81 a6 00 03 0f 01 d0 00 81 a7 00 03 10  │ e
0060         02 d0 00 ab 02 00 03 12 01 d0 00 8a 46 00 03 13  │ t
0070         01 d0 00 80 ec 00 03 14 02 d0 00 5a 74 00 03 16  │ 
0080         02 d0 00 5d d4 00 03 18 02 d0 00 d2 1a 00 03 1a  │ 
0090         02 d0 00 cd e8 00 03 1c 02 c0 00 0d 78 00 03 1e  │ D
00a0         02 d0 00 91 98 00 03 20 02 d0 00 71 22 00 03 22  │ a
00b0         02 d0 00 63 76 00 03 24 02 d0 00 65 56 00 03 26  │ t
00c0         02 d0 00 96 1a 00 03 28 01 d0 00 8e 90 00 03 29  │ a
00d0         02 d0 00 98 ba 00 03 2b 04 d0 00 d3 0c 00 03 2f  │
00e0         01 d0 00 8f 98 00 ┐  d4                          
             ──────────────────┘   
               Packet data
```

-------------------------------------------------------------------------

### bytes subscribing to `accel pedal pos + antilag + boost`
```
0000   a2 12 f1 2c f0 03 01 02 c0 00 08 08 00 03 03 02   ...,............
0010   c0 00 08 0c 00 03 05 01 d0 00 39 1f 00 03 06 02   ..........9.....
0020   d0 00 c6 b2 00 f7                                 ......
```

| Bytes description      | Actual bytes from packet  |
|------------------------|---------------------------|
| Initial request        | `a2 12 f1 2c f0`          |
| Sep                    | `03`                      |
| wtf is this bruh       | `01 02 c0 00 08 08 00`    |
| Sep                    | `03`                      |
| Accel pedal pos        | `03 02 c0 00 08 0c 00`    |
| Sep                    | `03`                      |
| Antilag active         | `05 01 d0 00 39 1f 00`    |
| Sep                    | `03`                      |
| Act. Boost             | `06 02 d0 00 c6 b2 00`    |
| Checksum               | `f7`                      |

### bytes subscribing to `accel pedal pos + antilag`
```
0000   9a 12 f1 2c f0 03 01 02 c0 00 08 08 00 03 03 02   ...,............
0010   c0 00 08 0c 00 03 05 01 d0 00 39 1f 00 9c         ..........9...
                            ^^ ^^ ^^ ^^ ^^ ^^
```

### bytes subscribing to `accel pedal pos + boost `
```
0000   9a 12 f1 2c f0 03 01 02 c0 00 08 08 00 03 03 02   ...,............
0010   c0 00 08 0c 00 03 05 02 d0 00 c6 b2 00 bd         ..............
                            ^^ ^^ ^^ ^^ ^^ ^^
```

## setting parameter registers
| Name          | Bytes                  |
|---------------|------------------------|
| unknown2      | `01 02 c0 00 08 08 00` |
| AccelPedPos   | `03 02 c0 00 08 0c 00` |
| ALS active    | `05 01 d0 00 39 1f 00` |
| Boost         | `06 02 d0 00 c6 b2 00` |

Adding a parameter needs three things:
1. A seperator (always `0x03`)
2. The length of the parameter's hexadecimal data (1 or 2)
3. The parameter bytes itself

as you can see in the table above, the first byte of the 7 bytes is always incrementing, but never in a certain pattern

this is because the first byte is being incremented by the 2nd thing you need adding a parameter - the length of the parameter's data (2 or 1)

you add to that increment **AFTER** you add the request btw

tl;dr first byte is setting index of where the response message is gonna go

so, for example (these are not accurate btw):
- we start at 0x00
- add unknown1 (needs to be added anyways), then add +1
- we're now at 0x01
- unknown2 is also needed, and that's 2 bytes, so add that req. and then +2
- we're now at 0x03
- accelpedpos is 2 bytes, add that request, then +2
- we're now at 0x05
- iat/coolant/oil temp is 1 byte, add that request, then +1
- we're now at 0x06, add the request for iat/coolant/oil temp
- ...

```python
# Do packet organizing
fullPacket += initialRequest            # Add initial request bytes
for parameter in self.parameters:           # add each parameter
    if len(parameter.bytes) != 0:               # if parameter is not null..
        fullPacket += seperator                     # add seperator
        fullPacket += bytes([packetsPointer])       # add index byte
        fullPacket += parameter.bytes               # parameter bytes
    packetsPointer += parameter.bytesLength     # add parameter index after
```

## adapter emulation
at 12am i decided to emulate the MHD adapter from pcaps i've gathered over time from this project

it works pretty great actually, it supports parameter extraction and data emulation, but no code scanning or wtv; it only works with data logging

usage:
1. do hotspot with whatever software you like (hostapd+dnsmasq works)
2. assign emulation host the ip `192.168.4.1` with netmask `255.255.255.0`
3. connect phone to emulation host's AP
4. start `emulator.py` as sudo (since it uses port 23)
5. start datalogging on phone, it should say connected and work fully
6. adjust gauge values using `fill.txt` (1 byte hexadecimal), or `emuSweep.py`
7. profit

## reading codes
for the MHD adapter to read codes from the DME, it issues a request (full: `83 12 f1 22 20 c0 c8`), then gets a response



`83 12 f1 22 20 c0 c8` (get ALL codes, shadow and active):
```
              total amount of codes stored
                         vv
0000   96 f1 12 62 20 00 06  2d ed 48  2f 6c 24  2a af 01   ...b ..-.H/l$*..
                             ^^^^^^^^  ^^^^^^^^  ^^^^^^^^
0010   30 ff 08  2c 77 84  2c 78 84  a2                         0..,w.,x..
       ^^^^^^^^  ^^^^^^^^  ^^^^^^^^

0000   96 f1 12 62 20 00 06 2d ed 48 2f 6c 24 2a af 01   ...b ..-.H/l$*..
0010   30 ff 08 2c 77 84 2c 78 84 a2                     0..,w.,x..

```

`84 12 f1 18 02 ff ff 9f` (get only active codes):
```
       total amount of codes stored
                   vv
0000   8b f1 12 58 03 2d ed 48 2c 77 84 2c 78 84 9a      ...X.-.H,w.,x..
                      ^^^^^^^^ ^^^^^^^^ ^^^^^^^^
```

## special frames
- request data
    - `82 12 f1 21 f0` `<checksum>`
- response data
    - `0x80` `<2 bytes, no clue>` `<data>` `<checksum>`
- buttons data maybe? (response from MHD adapter)
    - `0x80` `0x71 0xc 0x4`
- request DME codes
    - `83 12 f1 22 20 c0 c8`

## request flow
1. initial request
    - typically suffixed by `0x82` (?) or `0x80`
    - data request is every byte after that
    - last byte is mod256 checksum
    - so, requesting data would be `0x82 0x12 0xf1 0x21 0xf0 0x96`
2. adapter ack
    - adapter returns exact same data as initial request
    - tbh idk what this is for but eeh
    - doesn't always return exact same data as initial request though..
3. response
    - adapter returns full response, no register fiddling needed
    - first two bytes seem unneeded
    - last byte is checksum
    - slice would be something like `msgData[3:-1]`

## DME data response notes
after using a data request packet (`0x82 0x12 0xf1 0x21 0xf0 0x96`), when reading DME parameter data, the first two bytes of the data correspond to something and the next two bytes after are for something else. as if the adapter is adding two parameters by itself..

these could be used as padding (likely not), but probably one of them is for battery voltage, and one for ignition status

not sure but so far they're used as padding so