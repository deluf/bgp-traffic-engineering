## This files summarizes the steps required to create the simulated network

# Build the custom docker images
docker build -t local/manager:latest -f Dockerfile.manager .
docker build -t local/frr-ssh:latest -f Dockerfile.frr .

# Create the core switch
sudo ip link add name br-core type bridge
sudo ip link set dev br-core up

# Deploy the network
containerlab deploy
