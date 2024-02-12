from netmiko import ConnectHandler
import re
import os
import sys
from dotenv import load_dotenv
import yaml

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

def parse_interfaces(interfaces_str_list:list):
    PATTERN = r"([A-Za-z0-9\/]+)\s+([0-9\.]+|[a-z]+)\s+([A-Z]+)\s+([A-Za-z]+)\s+([A-Za-z]+\s[A-Za-z]+|[A-Za-z]+)\s+([A-Za-z]+)"
    
    interfaces = []
    
    for item in interfaces_str_list:
        matches = re.findall(PATTERN, item)
        
        for match in matches:
            interfaces.append(
                {
                    'name': match[0],
                    'ip_address': match[1],
                    'is_okay': match[2],
                    'method': match[3],
                    'status': match[4],
                    'protocol': match[5]
                }
            )
        
    return interfaces

def get_devices_info(device_inv:dict):
    devices = []

    for device in device_inv:
        routerParams = {
            'ip': device['ip'],
            'port': CISCO_PORT,
            'username': CISCO_USERNAME,
            'password': CISCO_PASSWORD,
            'secret': CISCO_SECRET,
            'device_type': 'cisco_ios'
        }

        connection = ConnectHandler(**routerParams)

        connection.enable()

        hostname_raw = connection.find_prompt()
        hostname_parsed = hostname_raw[:-1]

        interfaces_raw = connection.send_command('show ip interface brief').split('\n')[1::]
        interfaces_parsed = parse_interfaces(interfaces_raw)

        device['interfaces'] = interfaces_parsed
        device['hostname'] = hostname_parsed

        devices.append(device)

        # print('Closing Connection')
        connection.disconnect()
    
    return devices

try:
    with open('inventory.yaml', 'r') as file:
        device_inv = yaml.safe_load(file)['routers']
except FileNotFoundError:
    print('Error: The inventory file does not exist.')
    sys.exit(1)

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    devices_data = get_devices_info(device_inv)
    return render_template('index.html', devices=devices_data)

if __name__ == '__main__':
    app.run(debug=True)