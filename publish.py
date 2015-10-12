#!/usr/bin/env python

import time
import socket                           # hostname
import yaml				# config
import paho.mqtt.publish as publish     # mosquitto
from w1thermsensor import W1ThermSensor # w1 temp
import RPi.GPIO as GPIO                 # gpio setup
GPIO.setmode(GPIO.BCM)

hostname=socket.gethostname()

# Load config
stream = open("config.yml", 'r')
config = yaml.load(stream)

mosquittoserver=config['mqtt']['broker']
verbose=config['verbose']

#w1 devices gpio must be set in /boot/config.txt

# Change these to match your hardware
sensors={
  17: 'ds18b20',
  18: 'pir',
  27: 'pir'
}

# initialize
for gpio in sensors:
  if 'ds18b20' == sensors[gpio]:
    #TODO: may need a physical pullup
    GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  else:
    GPIO.setup(gpio, GPIO.IN)

idle_delay=600
activity_delay=10
delay=activity_delay
state={}
last_report_time=0
changed=False

while True:
  messages=[]
  if verbose:
    print "time since prev update", time.time()-last_report_time
  
  for gpio in sensors:
    #if verbose:
    #  print gpio, ' - ', sensors[gpio]

    if 'ds18b20' == sensors[gpio]:
      for count, sensor in enumerate(W1ThermSensor.get_available_sensors()):
        input = "%.0f" % sensor.get_temperature()
        if str(gpio) + sensor.id not in state \
          or input != state[str(gpio) + sensor.id]:
          changed=True
          if verbose:
            print "Changed", str(gpio) + sensor.id, input
          state[str(gpio) + sensor.id] = input
          messages.append({
            'topic': hostname + sensors[gpio] + str(count),
            'payload': state[str(gpio) + sensor.id]})
        if verbose:
          print("Sensor %s temp %s" % (sensor.id, state[str(gpio) + sensor.id]))

    else: # 'pir' == sensors[gpio]:
      input=GPIO.input(gpio)
      if gpio not in state \
        or input != state[gpio]:
        changed=True
        if verbose:
          print "Changed", str(gpio), input
        state[gpio]=input
        messages.append({
	  'topic': hostname + sensors[gpio] + str(gpio),
          'payload': 'motion' if 1 == state[gpio] else 'none' })

  # Send all
  if changed or (time.time()-last_report_time) > idle_delay:
    if verbose:
      print messages

    try:
      publish.multiple(messages, hostname=mosquittoserver, port=1883, client_id="", keepalive=60)
    except:
      pass

    changed=False
    last_report_time=time.time()
  time.sleep(activity_delay)
