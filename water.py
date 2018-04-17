#!/usr/bin/env python3

# DIY water detection sensor 2.0 with self test.
# GPL 2018 <dev@falkp.no>

# requirement: apt install python3-rpi.gpio
# Should also work with python2

# Example output:
# water_1: dry
# water_2: wet
# water_3: fail

# Fail = Test failed (bad cable?)
# Connect LEDs with + on testpin, - on "sensor"-pin. Multiple sensors can share testpin.

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
import sys
import time


testpin=17 # Test pin (required)
sensors={
    # GPIO number: 'description'
    27: 'water_1',  # Water sensor 1
    22: 'water_2',  # Water sensor 2
#   23: 'water_3',  # Water sensor 3
# nn: 'water_n|...
}

verbose = False
run_test = True # Run sensor test before each read.
delay=1 # To allow gpio to settle

results={}
statusok='dry'
statuscritical='wet'
statusfail='fail'

# Sensor test
if run_test:
    if verbose:
        print ("* Testing sensors, testpin %s set to high." % testpin)
    GPIO.setup(testpin, GPIO.OUT)
    GPIO.output(testpin, GPIO.HIGH)

    for pin in list(sensors):
        reading=False

        if verbose:
            print ("  Setting up for test mode of pin %s" % pin)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        time.sleep(delay)
        if GPIO.input(pin):
            reading=True
        else:
            results[pin] = statusfail
            del sensors[pin] # Don't use sensor

        GPIO.cleanup(pin)
        if verbose: 
            print ("  ->%s-test result is: %s" % (pin, reading))

# Sensor read
# if verbose: print ("\n* Testpin %s set to input.\n" % testpin)
GPIO.setup(testpin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

for pin in sensors:
    reading=False

    # Sensor output reset loop
    if verbose: print ("  Setting up for read of pin %s, and all other sensor pins low." % pin)
    for i, p in enumerate(sensors):
        if pin == p:
            if verbose: print ("D Setting pin %s high" % p)
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, GPIO.HIGH)
        else:
            if verbose: print ("D Setting pin %s low" % p)
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, GPIO.LOW)

    if verbose: print ("  Reading sensor on", pin)

    time.sleep(delay) # Allow gpio to settle
    if GPIO.input(testpin): # We really read the test pin here
        reading=True
        results[pin] = statuscritical
    else:
        results[pin] = statusok

GPIO.cleanup()

# Print results

for i in results:
    print ("%s: %s" % (i, results[i]))

