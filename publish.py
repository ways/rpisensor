#!/usr/bin/env python

import time                             # Time calculations
import os                               # os.sys.exit
import socket                           # hostname
import yaml                             # config
import paho.mqtt.publish as publish     # mosquitto
import RPi.GPIO as GPIO                 # gpio setup
GPIO.setmode(GPIO.BCM)

#Hostname is used in topic
hostname=socket.gethostname()

# Load config
stream = open("config.yml", 'r')
config = yaml.load(stream)
stream.close()

mosquittoserver=config['mqtt']['broker']
verbose=config['verbose']
max_idle_time=config['delay']['max_idle_time']
activity_delay=1
delay=activity_delay

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


# Initialize sensor setups

if 1 > len(config['sensors']):
  print "No sensors configured!"
  os.sys.exit(1)

for sensor in config['sensors']:
  if 'ds18b20' == config['sensors'][sensor]['type']:
    if verbose:
      print "Initializing %s with pullup." % config['sensors'][sensor]['type']
    GPIO.setup(config['sensors'][sensor]['gpio'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    from w1thermsensor import W1ThermSensor # w1 temp

  elif 'xloborg' == config['sensors'][sensor]['type']:
    if verbose:
      print "Initializing %s. Hope you've activated i2c." % config['sensors'][sensor]['type']
    import XLoBorg
    XLoBorg.printFunction = XLoBorg.NoPrint
    XLoBorg.Init()

  elif 'pir' == config['sensors'][sensor]['type'] or 'reed' == config['sensors'][sensor]['type']:
    if verbose:
      print "Initializing %s on gpio %s." % (config['sensors'][sensor]['type'], config['sensors'][sensor]['gpio'])
    GPIO.setup(config['sensors'][sensor]['gpio'], GPIO.IN)

  else:
    print "Error: wrong type of sensor in config? <%s>" % type
    os.sys.exit(1)

   
state={}           # Keep track of states of sensors: state[gpio]=input
last_change={}     # When a certain sensor change was last sent: last_change[gpio]=time
last_report_time=0 # When any change was sent
changed=False

# Main loop

while True:
  messages=[]
  if verbose:
    print "time since prev update %.0f" % (time.time()-last_report_time)
  
  for sensor in config['sensors']:
    input=None
    type=config['sensors'][sensor]['type']
    gpio=config['sensors'][sensor]['gpio']
    delay=config['sensors'][sensor]['delay']
    
    # Set a default value just to fill last_change
    if gpio not in last_change:
      last_change[gpio]=99999

    if 'ds18b20' == type:
      for count, w1 in enumerate(W1ThermSensor.get_available_sensors()):
        if w1.id not in last_change:
          last_change[w1.id]=99999
        input = "%.1f" % w1.get_temperature()
        if (w1.id not in state) or (input != state[w1.id]):
          changed=True
          if verbose:
            print "Changed sensor %s, %s." % (w1.id, input)
          if (time.time()-last_change[w1.id] > delay):
            state[w1.id] = input
            last_change[w1.id] = time.time()
            messages.append({
              'topic': hostname + '/' + type + '_' + str(count),
              'payload': input})
          else:
            changed=False
            if verbose:
              print "Not time to send changed %s %s yet. Delay: %s. Since last update: %.0f." \
                % (w1.id, input, delay, (time.time()-last_change[w1.id]))

    elif 'xloborg' == type:
      product = updateProduct ()
      input = '%01.0f' % (100*abs(product-previous))
      
      #HACK: cut-off
      if 2 > int(input):
        input=0

      if ('xloborg' not in state) or (input != state['xloborg']):
        changed=True

    elif 'pir' == type or 'reed' == type:
      input=GPIO.input(gpio)
      if gpio not in state or input != state[gpio]:
        changed=True

    elif 'dummy' == type:
      input='dummy test value'
      changed=True

#    else:
#      print "Error: wrong type of sensor in config? <%s>" % type
#      os.sys.exit(1)

    # Common for all sensors except ds18b20
    if 'ds18b20' != type:
      # Check if changed and above delay for the sensor, or above max_idle_time
      if changed and (time.time()-last_change[gpio] > delay) \
        or (time.time()-last_change[gpio] > max_idle_time):
        if verbose:
          print "Changed (or max_idle_time hit) for %s: %s" % (gpio, input)
        state[gpio] = input
        last_change[gpio] = time.time()
        messages.append({
          'topic': hostname + '/' + type + gpio,
          'payload': input})
      else:
        changed=False
        if verbose:
          print "Not time to send %s: %s yet. Delay: %s. Since last update: %.0f." \
            % (gpio, input, delay, (time.time()-last_change[gpio]))
    
  # Send all
  if changed:
    if verbose:
      print messages

    try:
      publish.multiple(messages, hostname=mosquittoserver, port=1883, client_id="", keepalive=60)
      changed=False
      last_report_time=time.time()
    except:
      pass

  time.sleep(activity_delay)
