# rpisensor
Read sensors and publish via mqtt with the least amount of config

Currently broken.

For use with http://home-assistant.io/, http://openhab.org/ and the like.

Requirements:
python-yaml
pip install w1thermsensor

Hardware:
GPIO connections:
http://pi.gadgetoid.com/pinout

Example setup:
```
1 3v3, for ds18b20			2 5V pir01
3					4 5v pir02
5					6 Gnd
7					8
9 Gnd					10
11 sig ds18b20, WiringPi pin0		12 sig pir01, bcm18, WiringPi pin 1
13 	sig pir02, WiringPi pin2	14 Gnd
```
