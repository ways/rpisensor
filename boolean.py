#!/usr/bin/env python

# sudo apt install python-pip; sudo pip install paho-mqtt

import os                               # os.sys.exit
import time
import RPi.GPIO as GPIO

pins={
  14: "moisture_tank|not detected|detected",
  15: "moisture_floor|not detected|detected"
}

verbose=False

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(pins.keys(), GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

for pin, settings in pins.iteritems():
  value=GPIO.input(pin)

  description, iszero, isone = settings.split('|')
  if verbose:
    print "Pin %s which is %s: value %s (%s)." % (pin, description, value, iszero if 0 == value else isone)
  
  print(description + '/status', iszero if 0 == value else isone)

