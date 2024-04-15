import re
import os
import json

LOGS_DIR = "./rsyslog/logs/hosts"
REGEX = r"^([0-9-A-Z:\+\.]{32})\s([0-9\.a-zA-Z]+)\s([0-9]+):\s([A-Za-z0-9-]+):\s\*.*\s%([A-Z0-9_]+)-([A-Z0-9_]+)-([A-Z0-9_]+):\s(.*)$"

def parse_syslog(file:str):
    logs = []
    with open(file, "r") as f:
        filecontent = f.read().split('\n')
    
    for line in filecontent:
        matches = re.findall(REGEX, line)
        
        for match in matches:
            logs.append(
                {
                    'timestamp': match[0],
                    'ip': match[1],
                    'sequence': match[2],
                    'hostname': match[3],
                    'facility': match[4],
                    'severity': match[5],
                    'mnemonic': match[6],
                    'content': match[7]
                }
            )

    return logs

def get_device_logs():
    devices = {}

    for (root, dirs, file) in os.walk(LOGS_DIR):
        for f in file:
            if ".log" in f:
                # dir_list.append(f"{root}/{f}")
                # print(root, f, sep="/")
                devices[root.split("/")[-1]] = {}
                devices[root.split("/")[-1]]["log_path"] = f"{root}/{f}"

    for device in devices:
        devices[device]["logs"] = parse_syslog(devices[device]["log_path"])

    return devices