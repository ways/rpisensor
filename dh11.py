#!/usr/bin/env python

import os                               # os.sys.exit
import socket                           # hostname
import paho.mqtt.publish as publish     # mosquitto
import RPi.GPIO as GPIO                 # gpio setup
GPIO.setmode(GPIO.BCM)
import Adafruit_DHT # git clone https://github.com/adafruit/Adafruit_Python_DHT.git; sudo apt-get install build-essential python-dev; sudo python setup.py install; sudo apt install python-pip; sudo pip install paho-mqtt

mosquittoserver='192.168.1.11'
mosquittoport=1883
mosquittousername=''
mosquittopassword=''
mosquittotopic='sensor/basement/'

max_reading=100
min_reading=-70
verbose=False
pin=15

#Hostname is used in topic
hostname=socket.gethostname()

# Functions

def append_message(messages, topic, payload):
  messages.append({
    'topic': topic,
    'payload': payload})
  changed=True


messages=[]

sensor = Adafruit_DHT.DHT11
humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

if temperature and min_reading < temperature and max_reading > temperature:
  append_message(messages, mosquittotopic + 'temperature', temperature)

if humidity:
  append_message(messages, mosquittotopic + 'humidity', humidity)

if 0 < len(messages):
  if verbose: print (messages)
  try:
    publish.multiple(messages, hostname=mosquittoserver, port=mosquittoport, client_id="", keepalive=60, auth={ 'username':mosquittousername, 'password': mosquittopassword })
  except Exception as err:
    print("*** Error sending message *** %s." % err)
