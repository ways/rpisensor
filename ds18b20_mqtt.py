#!/usr/bin/env python3

import os                               # os.sys.exit
import socket                           # hostname
import paho.mqtt.publish as publish     # mosquitto
import RPi.GPIO as GPIO                 # gpio setup
GPIO.setmode(GPIO.BCM)
import w1thermsensor

# sudo pip3 install paho-mqtt w1thermsensor

mosquittoserver='192.168.1.11'
mosquittoport=1883
max_reading=100
min_reading=-70
verbose=True
pin=14

#Hostname is used in topic
hostname=socket.gethostname()

# Functions

def append_message(messages, topic, payload):
  messages.append({
    'topic': topic,
    'payload': payload})
  changed=True


# Initialize sensor setups

GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

messages=[]
  
for count, w1 in enumerate(w1thermsensor.W1ThermSensor.get_available_sensors()):
  input = None
  try:
    input = float("%.1f" % w1.get_temperature())
  except ValueError:
    continue
  except w1thermsensor.core.SensorNotReadyError:
    continue

  if input and min_reading < input and max_reading > input:
    append_message(messages, hostname + '/ds18b20_' + str(w1.id), input)

if 0 < len(messages):
  if verbose: print (messages)
  try:
    publish.multiple(messages, hostname=mosquittoserver, port=mosquittoport, client_id="", keepalive=60)
  except Exception as err:
    print("*** Error sending message *** %s." % err)
