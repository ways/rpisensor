#!/usr/bin/env python3 
 
# Usage: 
# uRADMonitor.py http://192.168.1.10/j 
 
# example output from sensor 
# {"data":{ "id":"11000016","type":"1","detector":"SBM20","cpm":19,"temperature":15.88,"uptime": 98724}} 
 
# Requires pip3 install paho-mqtt 
 
import sys, json, requests, socket 
import paho.mqtt.publish as publish 
 
verbose = True 
mosquittoserver='192.168.1.11' 


def getDose(cpm):
    # https://github.com/radhoo/uradmonitor_kit1/blob/8928a7cf016745f7a456eeba948b0bd44821195b/code/geiger/detectors.cpp
    GEIGER_TUBE_SBM20 = 0.006315
    return GEIGER_TUBE_SBM20 * cpm


source = sys.argv[1] 
hostname=socket.gethostname() 
messages=[] 
 
if verbose: print("Will fetch data from %s." % source ) 
 
r = requests.get(source) 
if verbose: print ("Got %s" % r.content) 
 
jsondata = json.loads(r.content.decode('utf-8')) 
 
if verbose: print (jsondata) 
sensorid=jsondata['data']['id'] 
sensorcpm=jsondata['data']['cpm'] 
sensortemperature=jsondata['data']['temperature'] 
 
messages.append({'topic': hostname + '/uRADMonitor' + sensorid + '/cpm', 'payload': sensorcpm}) 
messages.append({'topic': hostname + '/uRADMonitor' + sensorid + '/dose', 'payload': getDose(sensorcpm)}) 
messages.append({'topic': hostname + '/uRADMonitor' + sensorid + '/temperature', 'payload': sensortemperature}) 
 
if verbose: print ("Publishing: " + hostname + '/uRADMonitor' + sensorid + '/cpm') 
  
try: 
      publish.multiple(messages, hostname=mosquittoserver, port=1883, client_id="", keepalive=60) 
except Exception as err: 
  print (err) 
 
