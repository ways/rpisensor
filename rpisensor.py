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

sys_version=0.6

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
activity_delay=2
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


def append_message(messages, topic, payload, changed):
  messages.append({
    'topic': topic,
    'payload': payload})
  changed=True


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

  elif config['sensors'][sensor]['type'] in ['digital', 'pir', 'reed']:
    logger.info ("Initializing %s on gpio %s." % (config['sensors'][sensor]['type'], config['sensors'][sensor]['gpio']))
    GPIO.setup(config['sensors'][sensor]['gpio'], GPIO.IN)
  
  elif 'dummy' == config['sensors'][sensor]['type']:
    pass

  else:
    logger.error("Error: wrong type of sensor in config? <%s>" % type)
    os.sys.exit(1)

   
state={}           # Keep track of states of sensors: state[gpio]=input
last_change={}     # When a certain sensor change was last sent: last_change[gpio]=time

# Main loop

while True:
  messages=[]
  changed=False
  
  for sensor in config['sensors']:
    # Gather settings
    input=None
    type=config['sensors'][sensor]['type']
    gpio=config['sensors'][sensor]['gpio']
    try:
      delay=config['sensors'][sensor]['delay']
    except KeyError:
      delay=1
    try:
      invert=config['sensors'][sensor]['invert']
    except KeyError:
      invert=False
    try:
      offset=config['sensors'][sensor]['offset']
    except KeyError:
      offset=0

    if 'ds18b20' == type:
      logger.debug("Reading %s" % type)
      for count, w1 in enumerate(W1ThermSensor.get_available_sensors()):
        # Make sure a new reading will be fetched
        if w1.id not in last_change:
          last_change[w1.id]=time.time()-delay

        # Read from sensor
        #try:
        input = float("%.1f" % w1.get_temperature()) + offset
        #except W1ThermSensorError:
        #  logger.error("Unable to read %s sensor on gpio %." % (type, gpio))
        #  continue

        if (input is None):
          logger.error("Sensor %s gave invalid data %s." % (w1.id, input))
          state[w1.id] = input
          continue

        # Store, but don't send first reading
        if (w1.id not in state):
          state[w1.id] = input
          continue

        # Check if value is different from last reading
        if (input != state[w1.id]):
          changed=True
          logger.debug ("Sensor %s changed from %s to %s." % (w1.id, state[w1.id], input))

          # Check if we're allowed to send yet ( sensor/delay )
          if changed and (time.time()-last_change[w1.id] > delay):
            state[w1.id] = input
            last_change[w1.id] = time.time()
            changed=True
            append_message(messages, hostname + '/' + type + '_' + str(count), input, changed)

        # Check if we should send anyway because prev value is older than max_idle_time
        elif (time.time()-last_change[w1.id] > max_idle_time):
            state[w1.id] = input
            last_change[w1.id] = time.time()
            changed=True
            append_message(messages, hostname + '/' + type + '_' + str(count), input, changed)

        # Do not send
        else:
          logger.debug (
            "(Not sending %s yet. Delay: %s. Max idle: %s. Since last update of last_change[%s]: %.0f.)"
            % (input, delay, max_idle_time, w1.id, (time.time()-last_change[w1.id])))

    elif type in ['digital', 'pir', 'reed']:
      logger.debug("Reading %s" % type)
      if 'digital' == type:
        if not invert:
	  input='1' if 1 == GPIO.input(gpio) else '0'
        else:
	  input='0' if 1 == GPIO.input(gpio) else '1'

      elif 'pir' == type:
        input='none' if 0 == GPIO.input(gpio) else 'motion'
      else: # Reed
        input='closed' if 0 == GPIO.input(gpio) else 'open'

      if gpio not in state or input != state[gpio]:
        changed=True
        logger.debug("%s changed to %s" % (gpio, input))

    elif 'xloborg' == type:
      logger.debug("Reading %s" % type)
      product = updateProduct ()
      input = float( '%01.2f' % (product + offset) )
      
      if ('xloborg' not in state) or (input != state['xloborg']):
        changed=True

    elif 'dummy' == type:
      logger.debug("Reading %s" % type)
      input=int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3
      #changed=True

    # Common for all sensors except ds18b20
    if 'ds18b20' != type:
      # Skip first reading:
      if gpio not in state:
        state[gpio] = input
        continue

      # Set a default value just to fill last_change
      if gpio not in last_change:
        last_change[gpio]=99999

      # Check if changed and above delay for the sensor
      if (changed and (time.time()-last_change[gpio] > delay) ):
        logger.info("Sending %s %s." % (gpio, input))
        state[gpio] = input
        last_change[gpio] = time.time()
        append_message(messages, hostname + '/' + type + str(gpio), input, changed)

      # Check if above max_idle_time
      if (time.time()-last_change[gpio] > max_idle_time):
        logger.info("Max_idle_time hit for %s: %s" % (gpio, input))
        state[gpio] = input
        last_change[gpio] = time.time()
        append_message(messages, hostname + '/' + type + str(gpio), input, changed)
        continue
      #else:
      #  logger.debug("Not time to send %s yet. Delay: %s. Max idle: %s. Since last update of last_change[%s]: %.0f." \
      #      % (input, delay, max_idle_time, gpio, (time.time()-last_change[gpio])))
  
  # Send all
  if changed:
    logger.debug(messages)

    try:
      publish.multiple(messages, hostname=mosquittoserver, port=1883, client_id="", keepalive=60)
      changed=False
    except Exception as err:
      logger.error("*** Error sending message *** %s." % err)

  time.sleep(activity_delay)
