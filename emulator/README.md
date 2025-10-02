# MHD adapter emulator
these tools can emulate the MHD adapter to intercept packets from MHD's app

responses were learned from PCAPs of how the MHD app talks to the telnet adapter

# vin base64 packet
can this be used by the public? yes, if you can replace the string "OTTTTTTTTTTTTTTER" in this base64 string with your vehicle vin:

```
lPFAYhAQT1RUVFRUVFRUVFRUVFRUVEVS
```

once replaced with your actual 18 char vin (last character should be G if you have a 17char vin), place the string in `vin.txt` and run `emulator.py`