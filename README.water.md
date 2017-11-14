== Overview ==

A short how-to for a DIY water sensor for use with [[Raspberry Pi]], Arduino, etc.

== Version 2 ==

Script used for reading: https://github.com/ways/rpisensor/blob/master/water.py

=== How it works ===

One normally-high GPIO port with current-limiting resistor. One GPIO port and one diode (LED or not) per sensor.

GPIO A is normally high, GPIO B (and C and ...N) is normally in IN-mode. Current is only able to pass around the diode if water is present. In test mode one reverse the GPIO setup. Now current should be able to pass through the LED.

{{{
GPIO-A --| resistor | -----+ 
                           |
GPIO-B ---------------+    |
                      |    |
GPIO-C ----------+    |    |
                 |    |    |
Water? ~~~~~~~~~~~~~~~~~~~~~~~~~~
                 V    V    |
                 +----+----+
}}}

=== Problems ===
* I do not know how a LED submerged in water over time will deteriorate.

=== Installation instructions ===
* The test wire should have a resistor (value not important).
* The test wire is common for all sensors.
* Each measuring point (i.e. under the system floor) needs test wire, marked {{{ test }}} and one input wire, marked i.e. {{{ Water 1}}}.
* Both wires should be connected to a GPIO port, not ground or voltage.
* The wires should be joined with a LED. Don't isolate the LED or its legs. The LEDs legs have to be submerged to give a positive reading.
* Use strips, tape or other ways to keep the LED in place.
* Test sensor after installation, moving.
