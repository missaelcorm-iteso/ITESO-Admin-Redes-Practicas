from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

from get_snmp import get_devices_snmp, load_config

def normalize_dict(data):
    # Initialize a dictionary to hold arrays indexed by 'index'
    bidimensional_array = {}

    # Iterate through each object in the JSON data
    for obj in data:
        # Extract the index
        index = obj['index']
        
        # Remove the 'index' key from the object
        del obj['index']
        
        # If the index is not already in the dictionary, create a new array for it
        if index not in bidimensional_array:
            bidimensional_array[index] = []
        
        # Append the object to the corresponding array in the dictionary
        bidimensional_array[index].append(obj)

    # Convert the dictionary to a list of lists
    table = [values for _, values in sorted(bidimensional_array.items())]
    
    return table
 

@app.route('/')
def devices():
    devices, _ = load_config()
    return render_template('devices.html', devices=devices)

@app.route('/device/<device_ip>')
def device_logs(device_ip):
    devices, _ = load_config()
    
    selected_device = None
    for device in devices:
        if device['ip'] == device_ip:
            selected_device = device
            break
        
    if not selected_device:
        return "Device not found", 404
    
    device_data = get_devices_snmp()[device_ip]
    
    for oid in device_data['snmp_data']:
        if oid.get('sub_oids') is not None:
            oid['sub_oids'] = normalize_dict(oid['sub_oids'])
    
    return render_template('device_snmp.html', device=selected_device, json_data=device_data['snmp_data'])

if __name__ == '__main__':
    app.run(debug=True)