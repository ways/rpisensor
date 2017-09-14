#!/usr/bin/env python3
 
# sudo apt install python3-pip; sudo pip3 install paho-mqtt 
 
import os                               # os.sys.exit 
import socket                           # hostname 
import paho.mqtt.publish as publish     # mosquitto 
import RPi.GPIO as GPIO                 # gpio setup 
GPIO.setmode(GPIO.BCM) 
 
mosquittoserver='192.168.1.11' 
mosquittoport=1883 
verbose=True 
 
# Functions 
 
def append_message(messages, topic, payload): 
  messages.append({ 
    'topic': topic, 
    'payload': payload}) 
  changed=True 
pins={ 
  14: "moisture_tank|not detected|detected", 
  15: "moisture_floor|not detected|detected" 
} 
 
#Hostname is used in topic 
hostname=socket.gethostname() 
 
GPIO.setmode(GPIO.BCM) 
GPIO.setwarnings(False) 
messages=[] 
 
for pin, settings in pins.items(): 
  GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
  value=GPIO.input(pin) 
 
  description, iszero, isone = settings.split('|') 
  if verbose: 
    print("Pin %s which is %s: value %s (%s)." % (pin, description, value, iszero if 0 == value else isone)) 
    #print(description + '/status', iszero if 0 == value else isone) 
 
  append_message(messages, hostname + '/' + description, iszero if 0 == value else isone) 
 
if 0 < len(messages): 
  if verbose: print (messages) 
  try:
    publish.multiple(messages, hostname=mosquittoserver, port=mosquittoport, client_id="", keepalive=60)
  except Exception as err:
    print("*** Error sending message *** %s." % err)
