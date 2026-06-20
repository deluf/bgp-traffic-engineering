from sys import argv
import os
from json import load as json_load
from netmiko import ConnectHandler

MY_AS_NUMBER = "65020"

GW1_NEIGHBOR = "10.0.5.1"
GW2_NEIGHBOR = "10.0.6.1"

gw1_device = {
    'device_type': 'linux',
    'host': '172.16.0.3',
    'username': 'netadmin',
    'password': 'super-strong-password',
    'port': 22,
}

gw2_device = {
    'device_type': 'linux',
    'host': '172.16.0.4',
    'username': 'netadmin',
    'password': 'super-strong-password',
    'port': 22,
}

# Algorithm to solve the knapsack problem using dp
def knapsack(values, weights, capacity):
    n = len(values)
    tab = [[0] * (capacity + 1) for _ in range(n + 1)]

    # Compute maximum carry value
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            if weights[i-1] <= w:
                include_item = values[i-1] + tab[i-1][w - weights[i-1]]
                exclude_item = tab[i-1][w]
                tab[i][w] = max(include_item, exclude_item)
            else:
                tab[i][w] = tab[i-1][w]

    # Select items that produce the maximum carry value
    items_included = []
    w = capacity
    for i in range(n, 0, -1):
        if tab[i][w] != tab[i-1][w]:
            items_included.append(i-1)
            w -= weights[i-1]

    # Reverse added to make it sorted increasing
    items_included.reverse()
    return items_included


# Compute the optimal traffic distribution across two links given a prediction
# The prediction must be a dict with destinations as keys and load predictions as values:
#  {destination1: load, destination2: load, ...}
def compute_distribution(prediction):

    # The traffic distribution problem is solved as a knapsack problem with:
    # - The single loads as both weights and values
    # - Half the total load as the capacity 
    loads = [v for v in prediction.values()]
    target = round(sum(loads)/2)
    knapsack_result = knapsack(values=loads, weights=loads, capacity=target)
    
    # Convert the knapsack output:
    # Destinations selected by the knapsack go in result_1, the others in result_2
    prediction_array = [k for k in prediction.keys()]
    result_1 = []
    result_2 = []
    cur = 0 # knapsack_result is sorted, so there is no need to search the whole array each time
    l = len(knapsack_result)
    for i in range(len(prediction_array)):
        if cur < l and i == knapsack_result[cur]:
            cur += 1
            result_1.append(prediction_array[i])
        else:
            result_2.append(prediction_array[i])

    return (result_1, result_2)


# Takes a list of destinations and outputs the command needed to increase their LOCAL_PREF
def compute_configuration(destinations, neighbor):
        
    commands = []

    # Enter configuration mode
    commands.append("configure terminal")

    # Clear LOCALPREF_PREFIX_LIST of all entries
    commands.append("no ip prefix-list LOCALPREF_PREFIX_LIST")

    # Add all destinations to favour to the list
    # If no destinations are present the prefix list reamins undefined, defaulting to deny everything
    for dest in destinations:
        commands.append("ip prefix-list LOCALPREF_PREFIX_LIST permit " + dest)

    # Exit configuration mode
    commands.append("end")

    return commands


# Opens an SSH connection to the device and runs the specified command
def apply_configuration(commands, device):
    
    try:
        net_connect = ConnectHandler(**device)
        
        print("Sending commands to " + device["host"] + ": " + str(commands) + "\n")
        
        output = net_connect.send_multiline_timing(commands)
        
        print("Output: " + output + "\n")
        
        net_connect.disconnect()

    except Exception as e:
        print("An error occurred: " + str(e))


# File to be run with the following argument:
# - Prediction file (.json)
if __name__ == "__main__":

    # Argument validation
    if len(argv) < 1:
        print("Missing argument: provide the prediction file")
        exit(1)
    
    prediction_file_path = argv[1]
    
    if not os.path.exists(prediction_file_path) or not os.path.isfile(prediction_file_path):
        print("Prediction file not found")
        exit(1)

    # Extract the json content from the file
    with open(prediction_file_path) as prediction_file:
        prediction = json_load(prediction_file)

    # Convert the prediction to the required format:
    # A single dict, not different ones for different customers
    compact_prediction = {}
    for customer, pred in prediction.items():
        for dest, load in pred.items():
            if dest not in compact_prediction:
                compact_prediction[dest] = load
            else:
                compact_prediction[dest] += load

    # Compute the optimal traffic distribution across the two upstream links
    distribution = compute_distribution(compact_prediction)

    # Debug output
    print("Total load: " + str(sum( [v for v in compact_prediction.values()] )))
    print("UP1: " + str(sum( [compact_prediction[dest] for dest in distribution[0]] )) )
    print(distribution[0])
    print("UP2: " + str(sum( [compact_prediction[dest] for dest in distribution[1]] )) )
    print(distribution[1])
    print(" ")

    # Compute the configuration required to enforce the given distribution
    configuration_gw1 = compute_configuration(distribution[0], GW1_NEIGHBOR)
    configuration_gw2 = compute_configuration(distribution[1], GW2_NEIGHBOR)

    # Apply the configuration to routers
    apply_configuration(configuration_gw1, gw1_device)
    apply_configuration(configuration_gw2, gw2_device)
