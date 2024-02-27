import sys
from netmiko import ConnectHandler
import os
import yaml
from dotenv import load_dotenv
from datetime import datetime
import time
import json
import re

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
        
try:
    with open('config.yaml', 'r') as file:
        config_file = yaml.safe_load(file)
        devices = config_file['devices']
        config = config_file['config']
except FileNotFoundError:
    print('Error: The config file does not exist.')
    sys.exit(1)

output_dir = config.get('output_dir')
registry_file = config.get('registry_file')

try:
    with open(registry_file, 'r') as file:
        registry = json.load(file)
except FileNotFoundError:
    registry = {}
except json.JSONDecodeError:
    registry = {}

def write_config(path:str, config:str):
    with open(path, 'w') as f:
            f.write(config)

def compare_configs(current_config_path:str, new_config:str):
    with open(current_config_path, 'r') as f:
        config_1 = f.read()
        config_1 = ignore_by_regex(config_1, config.get('regex_ignore'))

    return config_1 == new_config

def save_registry():
    with open(registry_file, 'w') as file:
        json.dump(registry, file, indent=4)

def ignore_by_regex(config:str, regex_list:list):
    for regex in regex_list:
        config = re.sub(regex.get('pattern'), '', config)
        
    return config

def backup_devices():    
    for device in devices:
        
        if registry.get(device['ip']) is None:
            registry[device['ip']] = {
                'name': device['name'],
                'ip': device['ip']
            }
        
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

        device_config = connection.send_command('show run')
        hostname_raw = connection.find_prompt()
        hostname_parsed = hostname_raw[:-1]
        
        connection.disconnect()
        
        config_lines = device_config.split('\n')
        config_lines = config_lines[3:]

        device_config = '\n'.join(config_lines)
        device_config = ignore_by_regex(device_config, config.get('regex_ignore'))
        
        time_now = datetime.now()
        date = time_now.strftime("%Y-%m-%d-%H-%M-%S")
        
        filename = f'{hostname_parsed}-{date}.cfg'
        
        registry[device['ip']]['hostname'] = hostname_parsed

        if registry[device['ip']].get('current_config') is None:
            registry[device['ip']]['current_config'] = filename
        else:
            try:
                if not compare_configs(f'{output_dir}/{registry[device["ip"]].get("current_config")}', device_config):
                    registry[device['ip']]['current_config'] = filename
                else:
                    date = time_now.strftime("%Y-%m-%d %H:%M:%S")
                    print(f'{date} INFO: The current config for {hostname_parsed} is the same as the last backup.')
                    continue
            except FileNotFoundError:
                registry[device['ip']]['current_config'] = filename
        
        write_config(f'{output_dir}/{filename}', device_config)
        save_registry()
        
        date = time_now.strftime("%Y-%m-%d %H:%M:%S")
        print(f'{date} INFO: Backup of {hostname_parsed} completed.')

SECONDS = int(config['export_interval'])

try:
    while True:
        start = time.time()
        backup_devices()
        end = time.time()
        try:
            time.sleep(SECONDS - (end - start))
        except ValueError:
            time.sleep(SECONDS)
except KeyboardInterrupt:
    print('The program was interrupted by the user.')
    sys.exit(0)
except Exception as e:
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ERROR: An error occurred: {e}')
    sys.exit(1)
