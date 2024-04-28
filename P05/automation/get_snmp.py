from pysnmp.hlapi import *
import yaml
import sys

def load_config():
    global devices, snmp_configs
    try:
        with open('config.yaml', 'r') as file:
            config_file = yaml.safe_load(file)
            devices = config_file['devices']
            snmp_configs = config_file['snmp_configs']
    except FileNotFoundError:
        print('Error: The config file does not exist.')
        sys.exit(1)
    
    return devices, snmp_configs

def snmp_config_exists(config_name):
    return snmp_configs.get(config_name) is not None

def snmpGET(router_ip:str, community:str, oid:dict):
    oid_data = {
        'oid': oid['oid'],
        'oid_name': oid['name'],
        'type': oid['type'],
        'value': None,
    }
    
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData(community),
               UdpTransportTarget((router_ip, 161)),
               ContextData(),
               ObjectType(ObjectIdentity(oid['oid'])))
    )

    if errorIndication:
        print(f"Error de SNMP: {errorIndication}")
    else:
        if errorStatus:
            print(f"Error de SNMP: {errorStatus.prettyPrint()}")
        else:
            for varBind in varBinds:
                oid_data['value'] = varBind[1].prettyPrint()
                # print(f"{oid['name']}: {varBind[1].prettyPrint()}")
                
    return oid_data

def get_device_snmp(device):
    oids_data = []
    if snmp_config_exists(device['snmp_config']):
        snmp_config = snmp_configs[device['snmp_config']]
        
        for oid in snmp_config['oids']:

            data = snmpGET(device['ip'], snmp_config['snmp']['community'], oid)
            
            if oid.get('sub_oids') is not None:
                sub_oids = []
                n_index = int(data['value']) if data['type'] == 'integer' else 0
                for sub_oid in oid['sub_oids']:
                    for i in range(1, n_index+1):
                        sub_oid['oid'] = f"{sub_oid['oid']}.{i}"
                        sub_data = snmpGET(device['ip'], snmp_config['snmp']['community'], sub_oid)
                        
                        sub_data['index'] = i
                        sub_oids.append(sub_data)
                        sub_oid['oid'] = sub_oid['oid'][:-2]
                        
                data['sub_oids'] = sorted(sub_oids, key=lambda x: x['index'])
                    
            oids_data.append(data)
    else:
        print(f"Error: The SNMP config '{device['snmp_config']}' does not exist.")
        
    return oids_data

def get_devices_snmp():
    devices_data = {}
    for device in devices:
        device_data = {
            'name': device['name'],
            'ip': device['ip'],
            'snmp_data': None
        }
        device_data['snmp_data'] = get_device_snmp(device)
        devices_data[device['ip']] = device_data

    return devices_data
