import sys
from netmiko import ConnectHandler
import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED_ENV = ['CISCO_USERNAME', 'CISCO_PASSWORD', 'CISCO_SECRET']

CISCO_USERNAME = os.getenv('CISCO_USERNAME')
CISCO_PASSWORD = os.getenv('CISCO_PASSWORD')
CISCO_SECRET = os.getenv('CISCO_SECRET')
CISCO_PORT = os.getenv('CISCO_PORT') or 22

for env in REQUIRED_ENV:
    if os.getenv(env) is None:
        print(f"Error: The environment variable '{env}' is not set.")
        sys.exit(1)

if len(sys.argv) < 3:
    print("Usage: python backup-device.py <ip-device> <path>")
    sys.exit(1)

ip_address = sys.argv[1]
path = sys.argv[2]

routerParams = {
            'ip': f'{ip_address}',
            'port': CISCO_PORT,
            'username': CISCO_USERNAME,
            'password': CISCO_PASSWORD,
            'secret': CISCO_SECRET,
            'device_type': 'cisco_ios'
        }

connection = ConnectHandler(**routerParams)

connection.enable()

config = connection.send_command('show run')
hostname_raw = connection.find_prompt()
hostname_parsed = hostname_raw[:-1]

connection.disconnect()

config_lines = config.split('\n')
config_lines = config_lines[3:]

config = '\n'.join(config_lines)

with open(f'{path}/{hostname_parsed}.cfg', 'w') as f:
    f.write(config)
    