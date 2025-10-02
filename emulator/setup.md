# setup MHD adapter emulator

1. install dnsmasq and hostapd
    - `sudo apt install dnsmasq hostapd`
2. disable and stop their services
    - ```
      sudo systemctl stop hostapd
      sudo systemctl stop dnsmasq
      sudo systemctl disable hostapd
      sudo systemctl disable dnsmasq
        ```
3. setup IP addressing
    - ```
      sudo ip addr add 192.168.4.1/24 dev wlan0
      sudo ip link set wlan0 up
      ```
4. connect phone to your AP
5. run emulator.py and open MHD, do stuff