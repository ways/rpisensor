#!/usr/bin/env python

import time
import socket                           # hostname
import yaml				# config
import paho.mqtt.publish as publish     # mosquitto
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
act_led=16

# Functions

def getReading ():
  x,y,z = XLoBorg.ReadAccelerometer()
  product = abs(x) + abs(y) + abs(z)
  #if verbose:
  #  print "Raw %s %s %s, abs %s, summed %s." % (x, y, z, product, x+y+z)
  return product

def updateProduct ():
  # Read several times to get a precise value.
  reading1 = getReading ()
  time.sleep (0.2)
  reading2 = getReading ()
  time.sleep (0.2)
  reading3 = getReading ()
  time.sleep (0.2)
  reading4 = getReading ()
  time.sleep (0.2)
  reading5 = getReading ()
  time.sleep (0.2)
  reading6 = getReading ()
  time.sleep (0.2)
  reading7 = getReading ()
  time.sleep (0.2)
  reading8 = getReading ()
  time.sleep (0.2)
  reading9 = getReading ()

  product = ( reading1 + reading2 + reading3 + reading4 + \
    reading5 + reading6 + reading7 + reading8 + reading9) / 9
  return product


# initialize
if 1 > len(config['sensors']):
  print "No sensors configured!"
  sys.exit(1)

for sensor in config['sensors']:
  if 'ds18b20' == config['sensors'][sensor]['type']:
    if verbose:
      print "Initializing %s with pullup." % config['sensors'][sensor]['type']
    GPIO.setup(config['sensors'][sensor]['gpio'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    from w1thermsensor import W1ThermSensor # w1 temp

  if 'xloborg' == config['sensors'][sensor]['type']:
    if verbose:
      print "Initializing %s. Hope you've activated i2c." % config['sensors'][sensor]['type']
    import XLoBorg
    XLoBorg.printFunction = XLoBorg.NoPrint
    XLoBorg.Init()

  if 'pir' == config['sensors'][sensor]['type'] or 'reed' == config['sensors'][sensor]['type']:
    if verbose:
      print "Initializing %s." % config['sensors'][sensor]['type']
    GPIO.setup(config['sensors'][sensor]['gpio'], GPIO.IN)

# Set ACT light blink every time we post an update
if config['actled']:
  import os
  os.system("echo none >/sys/class/leds/led0/trigger")
  GPIO.setup(act_led, GPIO.OUT)

state={}
last_report_time=0
changed=False

while True:
  messages=[]
  if verbose:
    print "time since prev update", time.time()-last_report_time
  
  for sensor in config['sensors']:

    if 'ds18b20' == config['sensors'][sensor]['type']:
      for count, w1 in enumerate(W1ThermSensor.get_available_sensors()):
        input = "%.1f" % w1.get_temperature()

        if verbose:
          print "Sensor %s temp %s." % (w1.id, input)

        if (w1.id not in state) or (input != state[w1.id]):
          changed=True

          if verbose:
            print "Changed", w1.id
          state[w1.id] = input
          messages.append({
            'topic': hostname + config['sensors'][sensor]['type'] + '_' + str(count),
            'payload': input})

    if 'xloborg' == config['sensors'][sensor]['type']:
      product = updateProduct ()
      input = '%01.0f' % (100*abs(product-previous))
      
      #cut-off
      if 2 > int(input):
        input=0

      if ('xloborg' not in state) or (input != state['xloborg']):
        changed=True

        if verbose:
          print "Changed", w1.id
          state[w1.id] = input
        messages.append({
          'topic': hostname + config['sensors'][sensor]['type'] + '_' + str(count),
          'payload': input})

    if 'pir' == config['sensors'][sensor]['type'] or 'reed' == config['sensors'][sensor]['type']:
      input=GPIO.input(config['sensors'][sensor]['gpio'])
      if config['sensors'][sensor]['gpio'] not in state \
        or input != state[config['sensors'][sensor]['gpio']]:
        changed=True
        if verbose:
          print "Changed", config['sensors'][sensor]['gpio'], input
        state[config['sensors'][sensor]['gpio']]=input
        messages.append({
	  'topic': hostname + config['sensors'][sensor]['type'] + str(config['sensors'][sensor]['gpio']),
          'payload': '1' if 1 == state[config['sensors'][sensor]['gpio']] else '0' })

    if 'dummy' == config['sensors'][sensor]['type']:
      changed=True
      if verbose:
        print "Changed", config['sensors'][sensor]['gpio']
        messages.append({
          'topic': hostname + config['sensors'][sensor]['type'] + str(config['sensors'][sensor]['gpio']),
          'payload': 'dummy test value' })

    else:
      print "Error: wrong type of sensor in config?"
      sys.exit(1)

  # Send all
  if changed or (time.time()-last_report_time) > idle_delay:
    if verbose:
      print messages

    try:
      if config['actled']:
        GPIO.output(act_led, GPIO.LOW)
      publish.multiple(messages, hostname=mosquittoserver, port=1883, client_id="", keepalive=60)
      changed=False
      last_report_time=time.time()
      if config['actled']:
        GPIO.output(act_led, GPIO.HIGH)
    except:
      pass

  time.sleep(activity_delay)
