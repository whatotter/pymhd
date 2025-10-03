# BMW MHD Python API
a python API for communicating to the MHD adapter, mainly for logging vehicle data

doesn't require licenses btw
<sub>MHD plz don't sue me</sub>

# features
- [x] logging
- [x] code reading
- [ ] flashing (still needs to undergo testing)

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