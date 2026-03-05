#!/Users/minkyu/Downloads/2.git/f5-mcp/mamba-env/bin/python
import os
import sys
sys.path.insert(0, '/Users/minkyu/Downloads/2.git/f5-mcp')

from dotenv import load_dotenv
load_dotenv('/Users/minkyu/Downloads/2.git/f5-mcp/.env')

import requests
import urllib3
import json
urllib3.disable_warnings()

host = os.getenv('TMOS_HOST')
port = os.getenv('TMOS_PORT')
auth = os.getenv('TMOS_AUTH_BASIC_B64')

headers = {
    'Authorization': f'Basic {auth}',
    'Content-Type': 'application/json'
}

# DNS 조회
print("=== DNS 설정 ===")
resp = requests.get(f'https://{host}:{port}/mgmt/tm/sys/dns', headers=headers, verify=False, timeout=20)
if resp.status_code == 200:
    data = resp.json()
    print(f"주요 필드: {[k for k in data.keys() if k not in ['kind', 'selfLink', 'generation']]}")
    print(json.dumps({k: data[k] for k in ['nameservers', 'search'] if k in data}, indent=2))

# NTP 조회
print("\n=== NTP 설정 ===")
resp = requests.get(f'https://{host}:{port}/mgmt/tm/sys/ntp', headers=headers, verify=False, timeout=20)
if resp.status_code == 200:
    data = resp.json()
    print(f"주요 필드: {[k for k in data.keys() if k not in ['kind', 'selfLink', 'generation']]}")
    if 'timezone' in data:
        print(f"Timezone: {data['timezone']}")
    if 'servers' in data:
        print(f"Servers 샘플: {data['servers'][:1] if data['servers'] else 'None'}")

# Syslog 조회
print("\n=== Syslog 관련 ===")
resp = requests.get(f'https://{host}:{port}/mgmt/tm/sys/log-config', headers=headers, verify=False, timeout=20)
if resp.status_code == 200:
    print("log-config: OK")

# eventlog server
resp = requests.get(f'https://{host}:{port}/mgmt/tm/sys/eventlog/server', headers=headers, verify=False, timeout=20)
if resp.status_code == 200:
    print("eventlog/server: OK")

# syslog server
resp = requests.get(f'https://{host}:{port}/mgmt/tm/sys/syslog', headers=headers, verify=False, timeout=20)
if resp.status_code == 200:
    print("syslog: OK")
    data = resp.json()
    print(f"주요 필드: {[k for k in data.keys() if k not in ['kind', 'selfLink', 'generation']]}")
