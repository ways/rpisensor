# rpisensors to mqtt

Read sensors connected to a Raspberry Pi (http://raspberrypi.org/), and publish the results via the Mosquito protocol (http://mosquitto.org/) with the least amount of config.

For use with http://home-assistant.io/, http://openhab.org/ and the like.


## Software requirements:

Install any debian based distro (raspbian, dietpi) and run:

sudo apt-get install python-pip python-yaml python-rpi.gpio
sudo pip install w1thermsensor paho-mqtt logger

## Types of sensors:

See README.sensors.md


## Example hardware setup:

See GPIO connections:
http://pi.gadgetoid.com/pinout

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

## Testing:

Results can be tested with i.e.:
mosquitto_sub -h test.mosquitto.org -t ${hostname_of_your_pi}pir01


## TODO:
* Use parasitic power (only need two wires): https://github.com/raspberrypi/firmware/issues/348
* Always discard first sensor read. Seems lots of sensors give bad data at first read.
