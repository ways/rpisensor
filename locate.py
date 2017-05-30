#!/usr/bin/env python
# sudo pip install paho-mqtt; sudo pip install git+https://github.com/bshillingford/wifi-locate

import paho.mqtt.publish as publish     # mosquitto
from wifilocate import locate, linux_scan
import time

mosquittoserver='example.com'
mosquittoport=1883
mosquittousername='name'
mosquittopassword='password'
verbose=True

# Functions

def append_message(messages, topic, payload):
  messages.append({
    'topic': topic,
    'payload': payload})
  changed=True


messages=[]

accuracy, latlng = locate(linux_scan(device="wlan0"))
if verbose: print(accuracy, latlng)  # e.g. 25, (50.1234567, -1.234567)

append_message(messages, 'owntracks/sensor/piow', '{"_type":"location","tid":"Pi","acc":' + str(accuracy) + ',"lat":' + str(latlng[0]) + ',"lon":' + str(latlng[1]) + ',"tst":' + str(int(time.time())) + '}' )

# Publish

if 0 < len(messages):
  if verbose: print (messages)

  try:
    publish.multiple(messages, hostname=mosquittoserver, port=mosquittoport, client_id="", keepalive=60, auth={ 'username':mosquittousername, 'password': mosquittopassword })
  except Exception as err:
    print("*** Error sending message *** %s." % err)
else:
  if verbose: print ('No message to send')

# owntracks/lars/fp2 {"_type":"location","tid":"L","acc":24,"batt":60,"conn":"m","doze":false,"lat":59.9497678,"lon":10.7677667,"tst":1490013093}
# (517, (59.9492182, 10.7683369))
