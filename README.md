# BMW MHD Python API
a python API for communicating to the MHD adapter, mainly for logging vehicle data

doesn't require licenses btw
<sub>MHD plz don't sue me</sub>

# features
- [x] logging
- [x] code reading
- [ ] flashing (still needs to undergo testing)

# usage
```
usage: mhd.py [-h] [--target TARGET] [--vdata] [--codes] [--monitor]

MHD adapter toolset

options:
  -h, --help       show this help message and exit
  --target TARGET  IP to connect to (default: 192.168.4.1)
  --vdata          Print out vehicle data (VIN, DME version, flashed file)
  --codes          Read DME codes
  --monitor        Monitor vehicle data (parameters r hardcoded, for now)
```

p.s. you can run multiple arguments at once (e.g. `--vdata --codes --monitor`)

## Read DME codes
```shell
$ python3 mhd.py --target 192.168.4.1 --codes
```
```shell
-*-*-*-*-* Active *-*-*-*-*-
29cc: Misfire, multiple cylinders
29cd: Misfire, cylinder 1
29ce: Misfire, cylinder 2
29cf: Misfire, cylinder 3
<.....>

-*-*-*-*-* Shadow *-*-*-*-*-
29f4: Catalyst temperature too high, bank 2
29f5: Oxygen sensor heater bank 1 sensor 1, circuit fault
2a2b: Valvetronic system, minimum lift not reached
<.....>
```

## Read DME info
```shell
$ python3 mhd.py --target 192.168.4.1 --vdata
```
```shell
[*] VIN           = otterwrks.co
[*] DME ROM       = I8A0S
[*] Flashed file  = v10.0 stg 1+ 93_98 - 93 60 - e30 100 - 91 100AT_xHP
```

## Stream DME parameters
```shell
$ python3 mhd.py --target 192.168.4.1 --monitor
```
```shell
Unknown1 = {'value': 61537}          
Unknown2 = {'value': 65535}          
Accel Ped. Pos = {'value': 1606.25}          
Boost = {'value': 22.5}          
Boost target = {'value': 22.5}          
Coolant = {'value': 289.0}          
Current Map = {'value': 256}           
Fuel low pressure sensor = {'value': 2522.0}          
IAT = {'value': 289.0}          
Lambda bank 1 = {'value': 939.8}          
Lambda bank 2 = {'value': 939.8}          
Oil temp = {'value': 8806.0}          
Rail pressure = {'value': 5045.28}          
RPM = {'value': 65535}          
Transmission temp = {'value': 419.0}
```

# examples
```python
"""
read out data parameters, print them to console
"""
from mhd import MHDAdapter, MHDParameters
import time

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
])

while True:
    data = adapter.requestData()
    
    print("\033[2J") # clear the console

    # print out all values recieved
    for key, values in data.items():
        print("{} = {}".format(key, values["value"]))

    # 50hz / sleep a little to not overload the adapter (not needed, make as many requests as you want, this is just a demo)
    time.sleep(0.02)
```

<sub>i really should fill this readme out more huh</sub>