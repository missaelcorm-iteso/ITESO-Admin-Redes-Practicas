import sys
import os
import yaml
from datetime import datetime
import json
import re

try:
    with open('config.yaml', 'r') as file:
        config_file = yaml.safe_load(file)
        devices = config_file['devices']
        config = config_file['config']
        nsc_config = config_file['network_security_compliance']
except FileNotFoundError:
    print('Error: The config file does not exist.')
    sys.exit(1)

output_dir = config.get('output_dir')
registry_file = config.get('registry_file')

def load_registry():
    global registry
    try:
        with open(registry_file, 'r') as file:
            registry = json.load(file)
    except FileNotFoundError:
        print('Error: The registry file does not exist.')
        sys.exit(1)
    except json.JSONDecodeError:
        print('Error: The registry file is not a valid JSON file.')
        sys.exit(1)

def eval_rule(device_config:str, rule:dict):
    try:
        with open(device_config, 'r') as file:
            output = file.read()
        
        result = re.search(rule['pattern'], output) is not None

        return result == rule['expected']
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_nsc_result():
    nsc_results = []
    
    for device in devices:
        results = []
        score = 0
        for rule in nsc_config['rules']:
            device_config = f"{output_dir}/{registry[device['ip']]['current_config']}"
            result = eval_rule(device_config, rule)
            score += 1 if result else 0
            
            datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            results.append({
                "rule": rule['name'],
                "result": result,
                "score": 100 if result else 0,
                "datetime": datetime_str
            })
            
            print(f"{datetime_str} {'INFO' if result else 'WARNING'} Router: {device['name']}, Rule: {rule['name']}, Success: {result}")
        
        nsc_results.append({
            "name": device['name'],
            "hostname": registry[device['ip']]['hostname'],
            "ip": device['ip'],
            "results": results,
            "score": round((score/len(nsc_config['rules'])*100), 2)
        })
            
    nsc_results_dir = nsc_config['results_dir']

    if not os.path.exists(nsc_results_dir):
        os.makedirs(nsc_results_dir)
        
    nsc_results_file = f"{nsc_results_dir}/nsc_result_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    nsc_results_csv = f"{nsc_results_dir}/nsc_result_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

    with open(nsc_results_file, 'w') as file:
        json.dump(nsc_results, file, indent=4)

    with open(nsc_results_csv, 'w') as file:
        headers = f"Router,Hostname,IP,{','.join([rule['name'] for rule in nsc_config['rules']])},Score\n"
        file.write(headers)
        for result in nsc_results:
            file.write(f"{result['name']},{result['hostname']},{result['ip']},{','.join([str(rule['score']) for rule in result['results']])},{result['score']}\n")
    
    return nsc_results, headers, nsc_results_file, nsc_results_csv



from flask import Flask, render_template, send_from_directory, request, abort

app = Flask(__name__)

@app.route('/')
def index():
    load_registry()
    nsc_results, headers, _, nsc_results_csv = get_nsc_result()
    return render_template('index.html', devices=nsc_results, headers=headers.split(','), csv_file=nsc_results_csv.split('/')[-1])

@app.route('/download/nsc_results')
def download_nsc_results():
    filename = request.args.get('filename')
    
    file_path = os.path.join(nsc_config['results_dir'], filename)

    if not os.path.isfile(file_path):
        abort(404)
    
    if not file_path.startswith(nsc_config['results_dir']):
        abort(403)
    
    return send_from_directory(nsc_config['results_dir'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)