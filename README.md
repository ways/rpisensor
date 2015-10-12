# rpisensor
Read sensors and publish via mqtt with the least amount of config

Some inspiration from https://github.com/sushack/pi_sensor_mqtt

For use with http://home-assistant.io/, http://openhab.org/ and the like.

Hardware:
GPIO connections:
http://pi.gadgetoid.com/pinout


1 3v3, for ds18b202 5V pir01
34 5v pir02
56 Gnd
78
9 Gnd10
11 sig ds18b20, WiringPi pin012 sig pir01, bcm18, WiringPi pin 1
13 	sig pir02, WiringPi pin214 Gnd
	
