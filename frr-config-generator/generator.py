from yaml import safe_load as yaml_safe_load
from jinja2 import Environment, FileSystemLoader
import os
from sys import argv


# Function that renders the given template using the given config
# Outputs a single {filename: content} pair
def create_config(device_config, template):

    # Render the jinja2 template using the given config
    output = template.render(device=device_config)

    # Assign the hostname as filename (defaults to "default")
    filename = device_config.get("hostname", "default") + ".conf"

    return {filename: output}


# Function that renders the given template using the given config
# If the config contains a list of devices it will render all of them separately
# Outputs a dictionary of {filename: content} pairs
def create_multiple_config(yaml_config, template):
    
    if "devices" in yaml_config:
        result = {}
        # If the config contains a list of devices, render them one by one
        for device in yaml_config["devices"]:
            result = result | create_config(device, template)
        return result
    
    else:
        # If the config contains a single device, just render it
        return create_config(yaml_config, template)


# Function that renders the given template using the config contained in the given YAML file
# If the path is that of a directory, process every file by itself
# Outputs a dictionary of {filename: content} pairs
def config_from_file(path, template):

    # Check for existance
    if not os.path.exists(path):
        print(f"ERROR: the file {path} does not exist.")
        exit(-1)

    # Support functions that processes a single file
    def config_from_single_file(path, template):
        try:
            # Load the YAML file
            with open(path) as yaml_file:
                yaml_config = yaml_safe_load(yaml_file)
            # Render the template
            return create_multiple_config(yaml_config, template)
        except Exception as e:
            print(f"ERROR while parsing {path}: {e}")
            return {}
        
    
    if os.path.isdir(path):
        # If the path is that of a directory, process every file by itself
        result = {}
        for filename in os.listdir(path):
            filepath = os.path.join(path, filename)
            result = result | config_from_single_file(filepath, template)
        return result
    
    else:
        # If the path is a file, process it
        return config_from_single_file(path, template)


# File to be run with the following (optional) arguments:
# - Input file or directory, defaults to "./input/"
# - Output directory, defaults to "./output/"
# - Jinja2 template, defaults to "./template.j2"
if __name__ == "__main__":

    # Argument handling
    input_path = "./input/"
    if len(argv) > 1:
        input_path = argv[1]
    
    output_path = "./output/"
    if len(argv) > 2 and os.path.exists(argv[2]) and os.path.isdir(argv[2]):
        output_path = argv[2]

    template = "./template.j2"
    if len(argv) > 3:
        template = argv[3]

    # Jinja environment and template setup
    env = Environment(loader=FileSystemLoader(os.path.dirname(template)))
    template = env.get_template(os.path.basename(template))
    
    # Compute the result and output it
    for filename, output in config_from_file(input_path, template).items():
        filepath = os.path.join(output_path, filename)
        with open(filepath, "w") as output_file:
            output_file.write(output)
