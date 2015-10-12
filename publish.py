#!/usr/bin/env python

import socket                           # hostname
import paho.mqtt.publish as publish     # mosquitto
from w1thermsensor import W1ThermSensor # w1 temp
import RPi.GPIO as GPIO                 # gpio setup
GPIO.setmode(GPIO.BCM)

verbose=True
hostname=socket.gethostname()
mosquittoserver="test.mosquitto.org"
messages=[]

#w1 devices, gpio must be set in /boot/config.txt
#TODO: check if we need a physical pullup
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#pir devices listed as gpio ports
pir_gpios=(18, 27)

#send pir
if verbose:
  print pir_gpios

for count, pir in enumerate(pir_gpios):
  if verbose:
    print 'PIR', pir, 'count', count

  result=None
  input=None
  GPIO.setup(pir, GPIO.IN)
  input=GPIO.input(pir)
  if 0 == input:
    result='none'
  else:
    result='motion'

  messages.append({
    'topic': hostname + 'pir' + str(count),
    'payload': result})

#send temp
for count, sensor in enumerate(W1ThermSensor.get_available_sensors()):
  if verbose:
    print("Sensor %s has temperature %.1f" % (sensor.id, sensor.get_temperature()))
  messages.append({
    'topic': hostname + 'temp' + str(count),
    'payload': "%.1f" % sensor.get_temperature()})

# Send all
publish.multiple(messages, hostname=mosquittoserver, port=1883, client_id="", keepalive=60)

#TODO: rewrite to send more often if important changes
