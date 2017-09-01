#!/usr/bin/env python

import os                               # os.sys.exit
import RPi.GPIO as GPIO                 # gpio setup
GPIO.setmode(GPIO.BCM)
import w1thermsensor

max_reading=80
min_reading=-70
verbose=True
pin=17

# Functions


# Initialize sensor setups

GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for count, w1 in enumerate(w1thermsensor.W1ThermSensor.get_available_sensors()):
  input = None
  try:
    input = float("%.1f" % w1.get_temperature())
  except ValueError:
    continue
  except w1thermsensor.core.SensorNotReadyError:
    continue

  if input and min_reading < input and max_reading > input:
    print ('ds18b20_' + str(w1.id) + ':' + str(input))

