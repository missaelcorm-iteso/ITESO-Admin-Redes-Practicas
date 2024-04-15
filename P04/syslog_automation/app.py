from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

from parse_logs import get_device_logs

@app.route('/')
def devices():
    devices = get_device_logs()
    return render_template('devices.html', devices=devices)

@app.route('/device/<device_name>')
def device_logs(device_name):
    devices = get_device_logs()
    
    selected_device = None
    for device, _ in devices.items():
        if device == device_name:
            selected_device = device
            break
        
    if not selected_device:
        return "Device not found", 404
    
    return render_template('device_logs.html', device=selected_device, logs=devices[device]["logs"])

if __name__ == '__main__':
    app.run(debug=True)