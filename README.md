# rpisensors to mqtt

Read sensors and publish via mqtt with the least amount of config

For use with http://home-assistant.io/, http://openhab.org/ and the like.


## Software requirements:

Install any debian based distro (raspbian, dietpi) and run:

sudo apt-get install python-pip python-yaml python-rpi.gpio
sudo pip install w1thermsensor paho-mqtt

## Types of sensors:

### ds18b20 temperature sensor

I.e. connect + to GPIO pin 1, - to GPIO pin 6, data to GPIO pin 12 (see example setup). No pull-up restistor required. 
Note that the ds18b20 / w1 needs special care. All sensors are connected to the same pin. This must be in your /boot/config.txt:

```
dtoverlay=w1-gpio,gpiopin=17
```

And in config.yml below "sensors:"

```
  s1:
    gpio: 17
    type: ds18b20
```

### Passive InfraRed or reed switch

I.e. connect + to GPIO pin 2, - to GPIO pin 6, data to GPIO pin 12.

And in config.yml below "sensors:"

```
  s1:
    gpio: 12
    type: pir
```

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

