# 4dpi-24-hat Python lib

A simple driver for the 4D Systems 4DPI-24-HAT (ILI9341 based).
This library doesn't use spidev, and I haven't tested if it continues to work when the Raspberry Pi SPI driver is enabled. If in doubt run `sudo raspi-config` and select `Interface Options -> SPI -> Disable`, then reboot.

Running the example:
```
sudo apt install pigpio python3-pigpio python3-numpy
pip3 install -r requirements.txt
sudo pigpiod
python3 example.py
```
