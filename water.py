#!/usr/bin/env python3

# DIY water detection sensor. See hardware setup at https://github.com/ways/rpisensor/

import sys, time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

sensors={
# GPIO number: 'description'
    17: 'test',    # Test pin (required)
    27: 'water_1', # Water sensor 1
    22: 'water_2'  # Water sensor 2
# nn: 'water_n|...
}

verbose = False
run_test = True # Run test before read
outputfile = sys.argv[1]

pins=list(sensors.keys())

# Sensor test
if run_test: # Run test of all sensors connected
    for pinid, pin in enumerate(pins):
        reading=False

        if 0 == pinid: # Set test pin to high
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
            continue

        if verbose: print ("Setting up for test mode of pin ", pin)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
        if verbose: print ("Testing sensor on", pin)
        if GPIO.input(pin):
            reading=True
            print ("%s-test: %s" % (sensors[pin], reading))

# Sensor read
for pinid, pin in enumerate(pins):
    reading=False

    if 0 == pinid: # Set test pin to input
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        continue

    # Sensor output reset loop
    if verbose: print ("Setting up for read of pin %s, and all other sensor pins low." % pin)
    for i, p in enumerate(pins):
        if 0 == i: # Skip test pin
            continue
        if pin == p:
            if verbose: print ("Setting pin %s high" % p)
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, GPIO.HIGH)
        else:
            if verbose: print ("Setting pin %s low" % p)
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, GPIO.LOW)

#    time.sleep(1)
    if verbose: print ("Reading sensor on", pin)
    if GPIO.input(pins[0]): # We really read the test pin here
        reading=True
    print ("%s: %s" % (sensors[pin], reading))

#GPIO.cleanup()

