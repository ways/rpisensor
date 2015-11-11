#!/usr/bin/env python

import time                             # Time calculations
import os                               # os.sys.exit
import socket                           # hostname
try:
  import yaml                             # config
  import paho.mqtt.publish as publish     # mosquitto
  import logging                          # logging
  import RPi.GPIO as GPIO                 # gpio setup
  GPIO.setmode(GPIO.BCM)
except ImportError as e:
  print "Error importing modules: %s. Please check README for requirements." % e
  os.sys.exit(1)
except RuntimeError as e:
  print "Error importing modules:", e


#Hostname is used in topic
hostname=socket.gethostname()

# Load config
try:
  stream = open("config.yml", 'r')
except IOError:
  print "Error opening config file config.yml. Please create one from the example file."
  os.sys.exit(1)

config = yaml.load(stream)
stream.close()

mosquittoserver=config['mqtt']['broker']
max_idle_time=config['delay']['max_idle_time']
activity_delay=1
delay=activity_delay

# Logging
logger = logging.getLogger(__name__)
handler = logging.FileHandler('/tmp/rpisensor.log')
if config['verbose']:
  handler.setLevel(logging.DEBUG)
  logging.basicConfig(level=logging.DEBUG)
  logger.debug("Logger set to DEBUG")
else:
  handler.setLevel(logging.INFO)
  logging.basicConfig(level=logging.INFO)

logger.addHandler(handler)

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
  error = 'No sensors configured!'
  logger.error(error)
  os.sys.exit(1)

for sensor in config['sensors']:
  if 'ds18b20' == config['sensors'][sensor]['type']:
    logger.info ("Initializing %s with pullup." % config['sensors'][sensor]['type'])
    GPIO.setup(config['sensors'][sensor]['gpio'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    from w1thermsensor import W1ThermSensor # w1 temp

  elif 'xloborg' == config['sensors'][sensor]['type']:
    logger.info ("Initializing %s. Hope you've activated i2c." % config['sensors'][sensor]['type'])
    import XLoBorg
    XLoBorg.printFunction = XLoBorg.NoPrint
    XLoBorg.Init()

  elif 'pir' == config['sensors'][sensor]['type'] or 'reed' == config['sensors'][sensor]['type']:
    logger.info ("Initializing %s on gpio %s." % (config['sensors'][sensor]['type'], config['sensors'][sensor]['gpio']))
    GPIO.setup(config['sensors'][sensor]['gpio'], GPIO.IN)
  
  elif 'dummy' == config['sensors'][sensor]['type']:
    logger.info ("Initializing %s on gpio %s." % (config['sensors'][sensor]['type'], config['sensors'][sensor]['gpio']))

  else:
    logger.error("Error: wrong type of sensor in config? <%s>" % type)
    os.sys.exit(1)

   
state={}           # Keep track of states of sensors: state[gpio]=input
last_change={}     # When a certain sensor change was last sent: last_change[gpio]=time
last_report_time=0 # When any change was sent
changed=False

# Main loop

while True:
  messages=[]
  logger.debug ("time since prev update %.0f" % (time.time()-last_report_time))
  
  for sensor in config['sensors']:
    input=None
    type=config['sensors'][sensor]['type']
    gpio=config['sensors'][sensor]['gpio']
    delay=config['sensors'][sensor]['delay']
    try:
      offset=config['sensors'][sensor]['offset']
    except KeyError:
      offset=0

    # Set a default value just to fill last_change
    if gpio not in last_change:
      last_change[gpio]=99999

    if 'ds18b20' == type:
      for count, w1 in enumerate(W1ThermSensor.get_available_sensors()):
        if w1.id not in last_change:
          last_change[w1.id]=99999
        #try:
        input = float("%.1f" % w1.get_temperature()) + offset
        #except:
        #  pass
        if (w1.id not in state) or (input != state[w1.id]):
          changed=True
          logger.debug ("Changed sensor %s, %s." % (w1.id, input))
          if (time.time()-last_change[w1.id] > delay):
            state[w1.id] = input
            last_change[w1.id] = time.time()
            messages.append({
              'topic': hostname + '/' + type + '_' + str(count),
              'payload': input,
              'retain': False})
          else:
            changed=False
            logger.debug (
              "Not time to send changed %s %s yet. Delay: %s. Since last update: %.0f."
              % (w1.id, input, delay, (time.time()-last_change[w1.id])))

    elif 'pir' == type or 'reed' == type:
      if 'pir' == type:
	input=GPIO.input(gpio)
      else: # Reed
        input='closed' if 0 == GPIO.input(gpio) else 'open'

      if gpio not in state or input != state[gpio]:
        changed=True
        logger.debug("%s changed to %s" % (gpio, input))

    elif 'xloborg' == type:
      product = updateProduct ()
      input = float( '%01.2f' % (product + offset) )
      
      if ('xloborg' not in state) or (input != state['xloborg']):
        changed=True

    elif 'dummy' == type:
      input='dummy test value'
      changed=True

    # Common for all sensors except ds18b20
    if 'ds18b20' != type:
      # Check if changed and above delay for the sensor, or above max_idle_time
      if (changed and (time.time()-last_change[gpio] > delay) ) \
        or (time.time()-last_change[gpio] > max_idle_time):
        logger.info("Changed (or max_idle_time hit) for %s: %s" % (gpio, input))
        state[gpio] = input
        last_change[gpio] = time.time()
        messages.append({
          'topic': (hostname + '/' + type + str(gpio)),
          'payload': input,
          'retain': False})
      else:
        logger.debug("Changed: %s, or not time to send %s: %s yet. Delay: %s. Since last update: %.0f." \
            % (changed, gpio, input, delay, (time.time()-last_change[gpio])))
        changed=False
    
  # Send all
  if changed:
    logger.debug(messages)

    try:
      publish.multiple(messages, hostname=mosquittoserver, port=1883, client_id="", keepalive=60)
      changed=False
      last_report_time=time.time()
    except Exception as err:
      logger.error("*** Error sending message *** %s." % err)

  time.sleep(activity_delay)
