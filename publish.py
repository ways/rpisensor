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
stream.close()

mosquittoserver=config['mqtt']['broker']
verbose=config['verbose']
idle_delay=config['delay']['max_idle_time']
activity_delay=config['delay']['check_every']
delay=activity_delay

# initialize
for sensor in config['sensors']:
  if 'ds18b20' == config['sensors'][sensor]:
    #TODO: may need a physical pullup
    GPIO.setup(config['sensors'][sensor]['gpio'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
  else:
    GPIO.setup(config['sensors'][sensor]['gpio'], GPIO.IN)

state={}
last_report_time=0
changed=False

while True:
  messages=[]
  if verbose:
    print "time since prev update", time.time()-last_report_time
  
  for sensor in config['sensors']:

    if 'ds18b20' == config['sensors'][sensor]['type']:
      for count, sensor in enumerate(W1ThermSensor.get_available_sensors()):
        input = "%.1f" % sensor.get_temperature()

        if verbose:
          print "Sensor %s temp %s." % (sensor.id, input)

        if (sensor.id not in state) or (input != state[sensor.id]):
          changed=True

          if verbose:
            print "Changed", sensor.id
          state[sensor.id] = input
          messages.append({
            'topic': hostname + config['sensors'][sensor]['type'] + '_' + str(count),
            'payload': input})

    else: # 'pir' == config['sensors'][sensor]['gpio']:
      input=GPIO.input(config['sensors'][sensor]['gpio'])
      if config['sensors'][sensor]['gpio'] not in state \
        or input != state[config['sensors'][sensor]['gpio']]:
        changed=True
        if verbose:
          print "Changed", config['sensors'][sensor]['gpio'], input
        state[config['sensors'][sensor]['gpio']]=input
        messages.append({
	  'topic': hostname + config['sensors'][sensor]['type'] + str(config['sensors'][sensor]['gpio']),
          'payload': 'motion' if 1 == state[config['sensors'][sensor]['gpio']] else 'none' })

  # Send all
  if changed or (time.time()-last_report_time) > idle_delay:
    if verbose:
      print messages

    try:
      publish.multiple(messages, hostname=mosquittoserver, port=1883, client_id="", keepalive=60)
      changed=False
      last_report_time=time.time()  
    except:
      pass

  time.sleep(activity_delay)