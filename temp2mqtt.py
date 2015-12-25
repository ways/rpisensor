#!/usr/bin/env python3

import time  # Time calculations
import os  # os.sys.exit
import socket  # hostname

try:
    import yaml  # config
    import paho.mqtt.publish as publish  # mosquitto
    import logging  # logging
    import RPi.GPIO as GPIO  # gpio setup

    GPIO.setmode(GPIO.BCM)
    from w1thermsensor import W1ThermSensor  # w1 temp
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
        logging.basicConfig(filename=logfile, level=logging.DEBUG)
    else:
        logging.basicConfig(filename=logfile, level=logging.INFO)

    logging.debug("Logger set to %s." % ('debug' if verbose else 'info'))
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


def append_message(msg, topic, payload):
    return msg + [{
        'topic': topic,
        'payload': payload}]


def init_sensors():
    """
       Initialize sensor setups
    """

    if 1 > len(config['sensors']):
        error = 'No sensors configured!'
        logger.error(error)
        os.sys.exit(1)

    for sensor in config['sensors']:
        logger.info("Initializing %s with pullup." % config['sensors'][sensor]['type'])
        GPIO.setup(config['sensors'][sensor]['gpio'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        for count, w1 in enumerate(W1ThermSensor.get_available_sensors()):
            logger.debug('Reading each sensor and throwing away first result: %s->%s'
                         % (w1.id, float("%.1f" % w1.get_temperature())))
            continue


# Main


sys_version = 1

# Hostname is used in topic
hostname = socket.gethostname()

config = load_config()
logger = enable_logging(config['verbose'])

mosquitto_server = config['mqtt']['broker']
try:
    loop_delay = config['delay']['max_idle_time']
except KeyError:
    loop_delay = 2

init_sensors()

# Loop

while True:
    messages = []

    for sensor in config['sensors']:
        # Gather settings
        input = None
        type = config['sensors'][sensor]['type']
        gpio = config['sensors'][sensor]['gpio']

        logger.debug("Reading %s" % type)
        for count, w1 in enumerate(W1ThermSensor.get_available_sensors()):
            # try:
            input = float("%.1f" % w1.get_temperature())  # Read from sensor
            # except W1ThermSensorError:
            #  logger.error("Unable to read %s sensor on gpio %." % (type, gpio))
            #  logger.error("Sensor %s (%s): gave invalid data %s." % (w1.id, input))
            #  continue
            logger.debug("Sensor %s is now: %s." % (w1.id, input))
            messages = append_message(messages, hostname + '/' + 'temp_' + str(count), input)

    # Send all
    if 0 < len(messages):
        logger.debug('Will upload:')
        logger.debug(messages)

        try:
            publish.multiple(messages, hostname=mosquitto_server, port=1883, client_id="", keepalive=60)
            changed = False
        except Exception as err:
            logger.error("*** Error sending message *** %s." % err)
    else:
        logger.debug('Nothing to upload.')

    time.sleep(loop_delay)
