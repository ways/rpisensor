#!/bin/bash -x

# mosquitto_pub -d -h 10.47.243.237 -i sensor01 -t temp01 -m 0
host="sensor01"
#mosquitto_pub="/usr/bin/mosquitto_pub -h 10.47.243.237 -i ${host} --quiet "
mosquitto_pub="/usr/bin/mosquitto_pub -h test.mosquitto.org -i ${host} --quiet "
gpio="/usr/local/bin/gpio"

#w1
w1sensors=$(ls /sys/bus/w1/devices/)

#pir
${gpio} mode 1 in

#reed
${gpio} mode 2 up
${gpio} mode 2 in

#send pir
${mosquitto_pub} -t ${host}pir01 -m $( [[ 1 -eq $( ${gpio} read 1) ]] && echo "motion" || echo "none" )

#send reed
${mosquitto_pub} -t ${host}reed01 -m $( [[ 1 -eq $( ${gpio} read 2) ]] && echo "open" || echo "closed" )

#send temp
count=0
for w1sensor in ${w1sensors} ; do
  [[ ${w1sensor} == 'w1_bus_master1' ]] && continue
  rawtemp=$( cat /sys/bus/w1/devices/../../../devices/w1_bus_master1/${w1sensor}/w1_slave |grep 't=' |cut -d'=' -f2)
  ${mosquitto_pub} -t ${host}temp${count} -m $( echo "scale=2; ${rawtemp}/1000" | /usr/bin/bc )
  count=$(( $count +1 ))
done
