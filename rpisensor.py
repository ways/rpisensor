#!/usr/bin/env python3

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
    print("Error importing modules: %s. Please check README for requirements." % e)
except RuntimeError as e:
    print("Error importing modules:", e)



# Functions


def enable_logging(verbose=True, logfile='/tmp/rpisensor.log'):
    """
    Enable logging
    """

    import logging
    if verbose:
        logging.basicConfig(filename=logfile,level=logging.DEBUG)
    else:
        logging.basicConfig(filename=logfile,level=logging.INFO)

    logging.debug("Logger set to %s." % ('debug' if verbose else 'info') )
    return logging


def load_config():
    """
    Load config from file
    """

    c = None

    try:
        stream = open("config.yml", 'r')
    except IOError:
        print("Error opening config file config.yml. Please create one from the example file.")
        os.sys.exit(1)

    c = yaml.load(stream)
    stream.close()
    return c


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

    product = ( reading1 + reading2 + reading3 + reading4 +
        reading5 + reading6 + reading7 + reading8 + reading9) / 9
    return product


def append_message(msg, topic, payload, changed):
    return msg + [{
        'topic': topic,
        'payload': payload}]


def add_sensor(state, gpio, type, value, last_value, check_every, last_check, last_upload):
    state[gpio] = [type, value, last_value, check_every, last_check, last_upload]
    return True


def init_sensors(state):
    """
       Initialize sensor setups
    """

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

        elif 'cputemp' == config['sensors'][sensor]['type']:
            logger.debug ("Adding sensor %s" % config['sensors'][sensor]['type'])

        else:
            logger.error("Error: wrong type of sensor in config? <%s>" % type)
            os.sys.exit(1)

        add_sensor(state=state,
            gpio=config['sensors'][sensor]['gpio'],
            type=config['sensors'][sensor]['type'],
            value=None,
            last_value=None,
            check_every=config['sensors'][sensor]['check_every'],
            last_check=None,
            last_upload=None)


# Main


sys_version = 1.1

state={}
"""
# Keep track of states of sensors: state[gpio]=input
# Main state table:
# { gpio:
#     [ type, value, last_value, check_every, last_check, last_upload ]
# }
"""

#Hostname is used in topic
hostname=socket.gethostname()

config = load_config()
logger = enable_logging(config['verbose'])

mosquitto_server=config['mqtt']['broker']
max_idle_time=config['delay']['max_idle_time']
loop_delay=2

init_sensors(state)


# Loop

while True:
    messages=[]
    changed=False

    print (state)
    print ("# { gpio: [ type, value, last_value, check_every, last_check, last_upload ]")
    for line in state:
      print (line)

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
                    messages = append_message(messages, hostname + '/' + type + '_' + str(count), input, changed)

            # Check if we should send anyway because prev value is older than max_idle_time
            elif (time.time()-last_change[w1.id] > max_idle_time):
                state[w1.id] = input
                last_change[w1.id] = time.time()
                changed=True
                messages = append_message(messages, hostname + '/' + type + '_' + str(count), input, changed)

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

        elif 'cputemp' == type:
            logger.debug("Reading %s" % type)
            input=int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3

        # Common for all sensors except ds18b20
        if 'ds18b20' != type:

            # Check if time since last check is above check_every for the sensor
            if (None == state[gpio][1] or (time.time()-int(state[gpio][4]) > state[gpio][3])):
                state[gpio][2] = state[gpio][1] # Move value to last_value
                state[gpio][4] = time.time()    # Set last_check to now
                state[gpio][1] = input
                logger.debug("Sensor %s (%s): is now %s." % (state[gpio][0], gpio, state[gpio][1]))

            # If we don't have at least two values, skip upload.
            if None == state[gpio][2]:
                logger.debug("Sensor %s (%s): skipping first value." % (state[gpio][0], gpio))
                continue

            # Check if empty values, above max_idle_time, value has changed.
            if None == state[gpio][5] \
                or (time.time()-state[gpio][5] > max_idle_time) \
                or (state[gpio][1] != state[gpio][2]):
                state[gpio][5] = time.time()    # Set last_upload to now
                #logger.debug('Will upload.')
                messages = append_message(messages, hostname + '/' + type + str(gpio), input, changed)
            else:
              logger.debug(
                  'Sensor %s (%s): Skipping upload. Value: %s Prev: %s Last_upload: %s.' \
                  % (state[gpio][0], gpio, state[gpio][1], state[gpio][2], state[gpio][5]))
  
    # Send all
    logger.debug(messages)
    if 0 < len(messages):

        try:
            publish.multiple(messages, hostname=mosquitto_server, port=1883, client_id="", keepalive=60)
            changed=False
        except Exception as err:
            logger.error("*** Error sending message *** %s." % err)
    else:
        logger.debug('Nothing to upload.')
        print (messages)

    time.sleep(loop_delay)
