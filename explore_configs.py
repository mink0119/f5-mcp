#!/usr/bin/env python3
"""F5 설정 조회 스크립트 (Windows/macOS 공용). mgmt IP·계정·비밀번호는 인자로 전달."""
import argparse
import json
import sys
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings()


def main():
    parser = argparse.ArgumentParser(description="F5 TMOS DNS/NTP/Syslog 등 설정 조회")
    parser.add_argument("--host", required=True, help="F5 관리 IP (예: 192.168.47.55)")
    parser.add_argument("--port", type=int, default=443, help="포트 (기본 443)")
    parser.add_argument("--username", required=True, help="관리자 계정 (예: admin)")
    parser.add_argument("--password", required=True, help="비밀번호")
    args = parser.parse_args()

    auth = __import__("base64").b64encode(f"{args.username}:{args.password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
    }
    base = f"https://{args.host}:{args.port}"

    # DNS 조회
    print("=== DNS 설정 ===")
    resp = requests.get(f"{base}/mgmt/tm/sys/dns", headers=headers, verify=False, timeout=20)
    if resp.status_code == 200:
        data = resp.json()
        print(f"주요 필드: {[k for k in data.keys() if k not in ['kind', 'selfLink', 'generation']]}")
        print(json.dumps({k: data[k] for k in ["nameservers", "search"] if k in data}, indent=2))
    else:
        print(f"오류: {resp.status_code}")

    # NTP 조회
    print("\n=== NTP 설정 ===")
    resp = requests.get(f"{base}/mgmt/tm/sys/ntp", headers=headers, verify=False, timeout=20)
    if resp.status_code == 200:
        data = resp.json()
        print(f"주요 필드: {[k for k in data.keys() if k not in ['kind', 'selfLink', 'generation']]}")
        if "timezone" in data:
            print(f"Timezone: {data['timezone']}")
        if "servers" in data:
            print(f"Servers 샘플: {data['servers'][:1] if data['servers'] else 'None'}")
    else:
        print(f"오류: {resp.status_code}")

    # Syslog 조회
    print("\n=== Syslog 관련 ===")
    resp = requests.get(f"{base}/mgmt/tm/sys/log-config", headers=headers, verify=False, timeout=20)
    if resp.status_code == 200:
        print("log-config: OK")
    resp = requests.get(f"{base}/mgmt/tm/sys/eventlog/server", headers=headers, verify=False, timeout=20)
    if resp.status_code == 200:
        print("eventlog/server: OK")
    resp = requests.get(f"{base}/mgmt/tm/sys/syslog", headers=headers, verify=False, timeout=20)
    if resp.status_code == 200:
        data = resp.json()
        print("syslog: OK")
        print(f"주요 필드: {[k for k in data.keys() if k not in ['kind', 'selfLink', 'generation']]}")


if __name__ == "__main__":
    main()
