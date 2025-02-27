import requests
import json
import socket
import time
import os
import yaml
import pynvml

with open(os.path.join(os.path.split(__file__)[0], 'config.yaml')) as f:
    config = yaml.safe_load(f)

pynvml.nvmlInit()
host = config['local']['host']
target = 'http://{}:{}/api/ping'.format(config['lab']['center']['ip'], config['lab']['center']['port'])
gpu_nums = pynvml.nvmlDeviceGetCount()
handle_list = [pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(gpu_nums)]


def get_host_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        return ip


def get_gpu_info():
    gpu_info = {}
    for i in range(len(handle_list)):
        meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle_list[i])
        gpu_info[i] = {
            'status': '{:.1f}M/{:.1f}M'.format(meminfo.used / 2**20, meminfo.total / 2**20),
            'percentage': round(meminfo.used / meminfo.total * 100)
        }
    return gpu_info


if __name__ == "__main__":
    body = {
        'ip': None, 
        'host': host, 
        'gpu_nums': gpu_nums,
        'gpu_info': {}, 
        '_date': None}
    error_count = 0
    while True:
        body['ip'] = get_host_ip()
        body['gpu_info'] = get_gpu_info()
        body['_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        success = False
        try:
            res = requests.post(target, json.dumps(body))
            if res.status_code == 200:
                success = True
                print('Success ping')
        except Exception:
            pass
        if not success:
            error_count += 1
            if error_count > 3:
                print('Failed to connect 3 times, try again in 5 minutes...')
                time.sleep(3 * 60)
                continue
        else:
            error_count = 0
        time.sleep(10)
