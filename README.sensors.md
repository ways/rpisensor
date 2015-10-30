# Supported sensors

Warning: There are different ways of numbering pins, all numbers here will be in "Physical pin" number, unless you see BCM mentioned.

Get to know the pins and pin numbering at http://pi.gadgetoid.com/pinout

### ds18b20 temperature sensor

I.e. connect V to physical pin 1, GND to physical pin 6, DATA to physical pin 12/BCM pin 18. No pull-up restistor required. Note that the ds18b20 / w1 needs special care. All sensors are connected to the same pin. This must be in your /boot/config.txt (BCM pin numbering):

```
dtoverlay=w1-gpio,gpiopin=18
```

And in config.yml below "sensors:"

```
  s1:
    gpio: 18
    type: ds18b20
```


### Passive InfraRed or reed switch

I.e. connect V to physical pin 2, GND to physical pin 6, data to physical pin 11/BCM pin 17.

And in config.yml below "sensors:"

```
  s1:
    gpio: 17
    type: pir
```

### XLoBorg Accelerometer

* Activate i2c via raspi-config / dietpi-config
* Fetch library from https://www.piborg.org/xloborg/install into same folder as rpisensors.
* The library uses i2c, witch runs via BCM ports 2 and 3, so the gpio value in our config doesn't matter much. Just don't crash with one of the other sensors you're using.

In config.yml below "sensors:"

```
  s1:
    gpio: 2
    type: pir
```

