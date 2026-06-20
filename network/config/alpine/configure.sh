#!/bin/sh

## Without this script, the Alpine node would have two (or more) interfaces (e.g., eth0 and eth1)
##  potentially both trying to set a default gateway in the same routing table.
## We therefore separate the management traffic from the data plane traffic

# Move the management interface (eth0) into its own routing table
ip link add management type vrf table 1001 # Any number > 255 will do (the ones before are reserved)
ip link set management up
ip link set eth0 master management

# Add a default route for management traffic (the gateway is the one defined in the clab topology)
ip route add default via 10.255.255.1 dev eth0 vrf management

ip addr add dev eth1 $MY_IP
ip route add default via $MY_GW
