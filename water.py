#!/usr/bin/env python3

# DIY water detection sensor with self test. See hardware setup at https://github.com/ways/rpisensor/

# apt install python3-rpi.gpio

# Example output:
# water_1: dry
# water_2: wet
# water_3: fail

# Fail = Test failed (bad cable?)

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
import sys

testpin=14 # Test pin (required)
sensors={
    # GPIO number: 'description'
    15: 'water_1',  # Water sensor 1
    18: 'water_2',  # Water sensor 2
#    23: 'water_3',  # Water sensor 3
# nn: 'water_n|...
}
verbose = False
run_test = True # Run test before read

results={}
statusok='dry'
statuscritical='wet'
statusfail='fail'

pins=list(sensors.keys())

# Sensor test
if run_test: # Run test of all sensors connected
    GPIO.setup(testpin, GPIO.OUT)
    GPIO.output(testpin, GPIO.HIGH)
    if verbose: print ("\n* Testpin %s set to high.\n" % testpin)

    for pinid, pin in enumerate(pins):
        reading=False

        if verbose:
            print ("D Setting up for test mode of pin %s" % pin)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
        if GPIO.input(pin):
            reading=True
        else:
            results[pin] = statusfail
            del sensors[pin] # Don't read from sensor

        if verbose: 
            print ("  %s-test result is: %s" % (pin, reading))

# Sensor read
GPIO.setup(testpin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
if verbose: print ("\n* Testpin %s set to input.\n" % testpin)

for pinid, pin in enumerate(pins):
    reading=False

    # Sensor output reset loop
    if verbose: print ("D Setting up for read of pin %s, and all other sensor pins low." % pin)
    for i, p in enumerate(pins):
        if pin == p:
            if verbose: print ("D Setting pin %s high" % p)
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, GPIO.HIGH)
        else:
            if verbose: print ("D Setting pin %s low" % p)
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, GPIO.LOW)

    if verbose: print ("  Reading sensor on", pin)
    if GPIO.input(testpin): # We really read the test pin here
        reading=True
        results[pin] = statuscritical
    else:
        results[pin] = statusok

GPIO.cleanup()

# Print results

for i in results:
    print ("%s: %s" % (i, results[i]))
