#!/bin/bash

# First, start the SSH daemon
/usr/sbin/sshd

## Without this script, the FRR node would have two (or more) interfaces (e.g., eth0 and eth1)
##  potentially both trying to set a default gateway in the same routing table.
## We therefore separate the management traffic from the data plane traffic

mgmt_ipv4_addr=$(ip -4 addr show eth0 | grep inet | awk '{print $2}')
mgmt_ipv4_gateway=$(ip route | grep '^default' | awk '{print $3}')
mgmt_ipv6_addr=$(ip -6 addr show | grep -E '^\s*inet6.*global' | awk '{print $2}')
mgmt_ipv6_gateway=$(ip -6 route | grep '^default' | awk '{print $3}')

sysctl -w net.ipv6.conf.all.keep_addr_on_down=1
ip link add management type vrf table 1001
ip link set dev management up

# Remove default routes for the management network from the default routing table
[ -n "${mgmt_ipv4_gateway}" ] && ip route del default via ${mgmt_ipv4_gateway}
[ -n "${mgmt_ipv6_gateway}" ] && ip -6 route del default via ${mgmt_ipv6_gateway}

ip link set dev eth0 master management

# Add default routes for the management network in the management routing table (1001)
[ -n "${mgmt_ipv4_gateway}" ] && ip route add default via ${mgmt_ipv4_gateway} vrf management
[ -n "${mgmt_ipv6_gateway}" ] && ip -6 route add default via ${mgmt_ipv6_gateway} vrf management

sleep 3

vtysh << EOF
configure terminal
interface eth0
ip address ${mgmt_ipv4_addr}
exit
do write
EOF

if [ -n "${mgmt_ipv6_addr}" ]; then
vtysh << EOF
configure terminal
interface eth0
ipv6 address ${mgmt_ipv6_addr}
exit
do write
EOF
fi
