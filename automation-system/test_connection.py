from netmiko import ConnectHandler

frr_defaults = {
    'device_type': 'linux',
    'username': 'netadmin',
    'password': 'super-strong-password',
    'port': 22,
}

core_routers = [{**frr_defaults, 'host': f"172.16.0.{x}"} for x in range(1, 5)]

for router in core_routers:
    print(f"[*] Connecting to {router['host']}...")
    
    try:
        with ConnectHandler(**router) as ssh:

            print("\n[*] Running \"show version\"")
            output = ssh.send_command("show version")
            if "FRRouting" not in output:
                raise Exception("Unknown output")
            print(output.splitlines()[0])

            print("\n[*] Running \"show ip bgp\"")
            output = ssh.send_command("show ip bgp")
            print(output)

    except Exception as e:
        print(f"[-] Error: {e}")

    if router != core_routers[:-1]:
        print("\n----------------------------------------------------------------------\n")
