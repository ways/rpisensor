# rpisensor
Read sensors and publish via mqtt with the least amount of config

For use with http://home-assistant.io/, http://openhab.org/ and the like.


Requirements:
apt-get install python-pip python-yaml python-rpi.gpio
pip install w1thermsensor paho-mqtt

Hardware:

See GPIO connections:
http://pi.gadgetoid.com/pinout

Example setup:
```
# Physical pin number, function
# So here we use 3,3 V for the temp sensors and 5 V from two different pins for PIR sensors. We have PIR at 12 and 13. Temp at 11.

1 3v3, for ds18b20			2 5V pir01
3					4 5v pir02
5					6 Gnd
7					8
9 Gnd					10
11 sig ds18b20, WiringPi pin0		12 sig pir01, bcm18, WiringPi pin 1
13 	sig pir02, WiringPi pin2	14 Gnd
```

Note that the ds18b20 / w1 needs special care. All sensors are connected to the same pin. This must be in your /boot/config.txt:

```
dtoverlay=w1-gpio,gpiopin=17
```

You can add this by running:

cat config.txt_values_for_ds18b20 >> /boot/config.txt


And in config.yml:

```
sensors:
  s1:
    gpio: 17
    type: ds18b20
```
