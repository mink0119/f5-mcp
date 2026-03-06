"""F5 TMOS iControl REST API 클라이언트"""

import requests
import urllib3
from Tools.settings import get_endpoint_settings, build_endpoint_settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _connection_overrides_from_kwargs(kwargs):
    """kwargs에서 연결 오버라이드만 추출 (tmos_host, tmos_port, tmos_username, tmos_password 등)"""
    keys = ("tmos_host", "tmos_port", "tmos_username", "tmos_password", "tmos_auth_b64", "tmos_verify_tls", "tmos_timeout_seconds")
    m = {
        "tmos_host": "host",
        "tmos_port": "port",
        "tmos_username": "username",
        "tmos_password": "password",
        "tmos_auth_b64": "auth_b64",
        "tmos_verify_tls": "verify_tls",
        "tmos_timeout_seconds": "timeout_seconds",
    }
    overrides = {}
    for k in keys:
        if k in kwargs and kwargs[k] is not None:
            overrides[m[k]] = kwargs[k]
    return overrides if overrides else None


class F5_object:
    """F5 TMOS 리소스 관리 클래스"""

    def __init__(self, endpoint_kind: str = "TMOS", **kwargs):
        """Initialize F5 API 클라이언트
        
        Parameters:
        -----------
        object_name, object_type, url_body, lines_number : 기존 리소스/요청 인자
        tmos_host, tmos_port, tmos_username, tmos_password (또는 tmos_auth_b64) : 요청 단위 연결 오버라이드.
            넘기면 해당 호출만 이 연결로 수행 (다중 장비·비밀번호 변경 후 재인증 시 유리).
        """
        self.payload = kwargs.get('url_body')
        self.object_type = kwargs.get('object_type')
        self.object_name = kwargs.get('object_name')
        self.lines_number = kwargs.get('lines_number')

        overrides = _connection_overrides_from_kwargs(kwargs)
        if overrides:
            self._settings = build_endpoint_settings(**overrides)
        else:
            self._settings = get_endpoint_settings(endpoint_kind)
        self._session = requests.Session()

    def _request(self, method: str, path: str, json_body=None):
        """HTTP 요청 실행"""
        url = f"{self._settings.base_url}{path}"
        
        try:
            resp = self._session.request(
                method,
                url,
                headers=self._settings.headers,
                json=json_body,
                verify=self._settings.verify_tls,
                timeout=self._settings.timeout_seconds,
            )
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": str(e), "url": url}

        # 응답 처리
        try:
            body = resp.json() if "json" in resp.headers.get("Content-Type", "") else resp.text
        except ValueError:
            body = resp.text

        if resp.ok:
            return body

        return {
            "ok": False,
            "status_code": resp.status_code,
            "reason": resp.reason,
            "url": url,
            "body": body,
        }
    
    def stats(self):
        """리소스 통계 조회"""
        path = f"/mgmt/tm/ltm/{self.object_type}/{self.object_name}/stats"
        return self._request("GET", path)
        
    def logs(self):
        """시스템 로그 조회"""
        path = f"/mgmt/tm/sys/log/ltm?$limit={self.lines_number}"
        return self._request("GET", path)
        
    def list(self):
        """리소스 목록 조회"""
        path = f"/mgmt/tm/ltm/{self.object_type}/"
        return self._request("GET", path)
        
    def create(self):
        """리소스 생성"""
        path = f"/mgmt/tm/ltm/{self.object_type}/"
        return self._request("POST", path, json_body=self.payload)
        
    def update(self):
        """리소스 수정 (ltm 또는 sys 엔드포인트)"""
        # sys 설정 (예: global-settings)
        if self.object_type in ['global-settings', 'dns', 'ntp', 'snmp']:
            path = f"/mgmt/tm/sys/{self.object_type}"
        # ltm 리소스 (예: virtual, pool)
        else:
            path = f"/mgmt/tm/ltm/{self.object_type}/{self.object_name}"
        return self._request("PATCH", path, json_body=self.payload)

    def delete(self):
        """리소스 삭제"""
        path = f"/mgmt/tm/ltm/{self.object_type}/{self.object_name}"
        return self._request("DELETE", path)

    def sys_version(self):
        """시스템 버전 조회 (연결 테스트)"""
        return self._request("GET", "/mgmt/tm/sys/version")
    
    def get_dns(self):
        """현재 DNS 설정 조회"""
        return self._request("GET", "/mgmt/tm/sys/dns")
    
    def set_dns(self, nameservers, search_domains=None):
        """DNS 서버 설정
        
        Parameters:
        -----------
        nameservers : list
            DNS 서버 주소 리스트 (예: ['8.8.8.8', '8.8.4.4'])
        search_domains : list, optional
            로컬 도메인 검색 리스트 (예: ['example.com', 'test.local'])
        """
        # DNS 서버 설정 (필수)
        payload = {"nameServers": nameservers}
        
        # 검색 도메인 설정 (선택사항 - 지정된 경우만 추가)
        if search_domains:
            payload["search"] = search_domains
            
        return self._request("PATCH", "/mgmt/tm/sys/dns", json_body=payload)
    
    def clear_dns_search_domains(self):
        """DNS 검색 도메인 삭제
        
        Search domain을 비우려면 단독으로 PATCH 요청을 해야 함
        """
        # search 필드를 제거하려고 함. 빈 배열이 작동하지 않으면 다른 값 시도
        payload = {"search": []}
        return self._request("PATCH", "/mgmt/tm/sys/dns", json_body=payload)
    
    def get_ntp(self):
        """현재 NTP 설정 조회"""
        return self._request("GET", "/mgmt/tm/sys/ntp")
    
    def set_ntp(self, servers, timezone=None):
        """NTP 서버 및 타임존 설정
        
        Parameters:
        -----------
        servers : list
            NTP 서버 주소 리스트 (예: ['time.google.com', 'time.cloudflare.com'])
        timezone : str, optional
            타임존 (예: 'UTC', 'Asia/Seoul', 'America/New_York')
        """
        payload = {"servers": servers}
        if timezone:
            payload["timezone"] = timezone
        return self._request("PATCH", "/mgmt/tm/sys/ntp", json_body=payload)
    
    def get_syslog(self):
        """현재 Syslog 설정 조회"""
        return self._request("GET", "/mgmt/tm/sys/syslog")
    
    def set_syslog(self, **kwargs):
        """Syslog 로그 레벨 및 설정 변경
        
        Parameters:
        -----------
        consoleLog : str, optional
            콘솔 로그 ('enabled' 또는 'disabled')
        clusteredHostSlot : str, optional
            클러스터 호스트 로깅 ('enabled' 또는 'disabled')
        cronFrom, cronTo, daemonFrom, daemonTo, authPrivFrom, authPrivTo : str, optional
            각 서비스의 로그 레벨 범위 (emerg, alert, crit, err, warning, notice, info, debug)
        """
        return self._request("PATCH", "/mgmt/tm/sys/syslog", json_body=kwargs)

    def get_management_routes(self):
        """management route 목록 조회. GET /mgmt/tm/sys/management-route (mgmt 포트 라우팅)"""
        return self._request("GET", "/mgmt/tm/sys/management-route")

    def add_management_route(
        self,
        name: str,
        network: str,
        gateway: str,
        route_type: str = "gateway",
        description: str = None,
        mtu: int = None,
    ):
        """management route 추가. syslog를 mgmt 포트로 보낼 때 목적지로 가는 경로가 필요하면 먼저 추가.
        name: 라우트 이름(고유), network: 'default' 또는 'x.x.x.x/prefix', gateway: 게이트웨이 IP.
        """
        path = "/mgmt/tm/sys/management-route"
        body = {"name": name, "network": network, "gateway": gateway, "type": route_type}
        if description is not None:
            body["description"] = description
        if mtu is not None:
            body["mtu"] = mtu
        return self._request("POST", path, json_body=body)

    def get_hostname(self):
        """현재 호스트명 조회"""
        return self._request("GET", "/mgmt/tm/sys/global-settings")
    
    def set_hostname(self, hostname: str):
        """호스트명 설정
        
        Parameters:
        -----------
        hostname : str
            설정할 호스트명 (예: 'ai-test.com', 'f5-bigip-01')
        """
        payload = {"hostname": hostname}
        return self._request("PATCH", "/mgmt/tm/sys/global-settings", json_body=payload)

    def set_user_password(self, username: str, password: str):
        """사용자(admin, root 등) 비밀번호 설정. PATCH /mgmt/tm/auth/user/<username>"""
        path = f"/mgmt/tm/auth/user/{username}"
        return self._request("PATCH", path, json_body={"password": password})

    def set_password_policy_enforcement(self, enabled: bool = False):
        """비밀번호 정책(복잡도 등) 적용 여부. False면 disabled (tmsh: modify auth password-policy policy-enforcement disabled).
        기본 설정 초기 세팅 시 먼저 호출해 두면 이후 비밀번호 설정 시 복잡도 제한 없이 설정 가능.
        """
        base = "/mgmt/tm/auth/password-policy"
        body = {"policyEnforcement": "enabled" if enabled else "disabled"}
        r = self._request("PATCH", base, json_body=body)
        if isinstance(r, dict) and r.get("ok") is False and r.get("status_code") == 404:
            r = self._request("PATCH", base + "/default", json_body=body)
        if isinstance(r, dict) and r.get("ok") is False and r.get("status_code") == 404:
            get_r = self._request("GET", base)
            if get_r.get("ok") and get_r.get("body", {}).get("items"):
                name = get_r["body"]["items"][0].get("name", "default")
                r = self._request("PATCH", f"{base}/{name}", json_body=body)
        return r

    # ============= Auth User (계정) 생성/조회/수정/삭제 =============
    def list_auth_users(self):
        """auth user 목록 조회. GET /mgmt/tm/auth/user"""
        return self._request("GET", "/mgmt/tm/auth/user")

    def create_auth_user(
        self,
        name: str,
        password: str,
        description: str = None,
        partition_access: list = None,
        shell: str = None,
    ):
        """auth user 생성. POST /mgmt/tm/auth/user
        partition_access: [ {"name": "all-partitions", "role": "admin"} ] (role: admin, operator, guest, manager 등)
        """
        payload = {"name": name, "password": password}
        if description is not None:
            payload["description"] = description
        if partition_access is not None:
            payload["partitionAccess"] = partition_access
        if shell is not None:
            payload["shell"] = shell
        return self._request("POST", "/mgmt/tm/auth/user", json_body=payload)

    def get_auth_user(self, name: str):
        """auth user 단일 조회. GET /mgmt/tm/auth/user/<name>"""
        path = f"/mgmt/tm/auth/user/{name}"
        return self._request("GET", path)

    def update_auth_user(self, name: str, password: str = None, description: str = None, partition_access: list = None, shell: str = None):
        """auth user 수정. PATCH /mgmt/tm/auth/user/<name>"""
        path = f"/mgmt/tm/auth/user/{name}"
        payload = {}
        if password is not None:
            payload["password"] = password
        if description is not None:
            payload["description"] = description
        if partition_access is not None:
            payload["partitionAccess"] = partition_access
        if shell is not None:
            payload["shell"] = shell
        return self._request("PATCH", path, json_body=payload)

    def delete_auth_user(self, name: str):
        """auth user 삭제. DELETE /mgmt/tm/auth/user/<name>"""
        path = f"/mgmt/tm/auth/user/{name}"
        return self._request("DELETE", path)

    def apply_basic_settings(
        self,
        hostname=None,
        nameservers=None,
        search_domains=None,
        ntp_servers=None,
        timezone=None,
        admin_password=None,
        root_password=None,
        syslog=None,
        syslog_via_mgmt=False,
        management_route_name=None,
        management_route_network="default",
        management_route_gateway=None,
    ):
        """장비 초기 기본 설정 템플릿: hostname, dns, ntp(+timezone), syslog, admin/root 비밀번호를 한 번에 적용.
        - 시작 시 password-policy 정책 적용을 비활성화한 뒤, hostname → dns → ntp → (선택) management route → syslog 순으로 적용.
        - syslog_via_mgmt=True 이고 management_route_gateway 가 있으면, syslog 설정 직전에 management route 추가 (mgmt 포트로 syslog 통신 시 필요).
        - admin/root 비밀번호 변경은 반드시 마지막에 수행.
        """
        results = []
        all_ok = True

        # 1. 초기 세팅: 비밀번호 복잡도 비활성화 + 초기 UI 설정 마법사 제거 (tmsh: modify sys db setup.run value false)
        r = self.set_password_policy_enforcement(enabled=False)
        results.append({"step": "password_policy_disabled", "result": r})
        if isinstance(r, dict) and r.get("ok") is False:
            all_ok = False
        r = self.set_sys_db("setup.run", "false")
        results.append({"step": "setup_run_disabled", "result": r})
        if isinstance(r, dict) and r.get("ok") is False:
            all_ok = False

        if hostname is not None and hostname != "":
            r = self.set_hostname(hostname)
            results.append({"step": "hostname", "result": r})
            if isinstance(r, dict) and r.get("ok") is False:
                all_ok = False

        if nameservers is not None:
            r = self.set_dns(nameservers, search_domains)
            results.append({"step": "dns", "result": r})
            if isinstance(r, dict) and r.get("ok") is False:
                all_ok = False

        if ntp_servers is not None:
            r = self.set_ntp(ntp_servers, timezone)
            results.append({"step": "ntp", "result": r})
            if isinstance(r, dict) and r.get("ok") is False:
                all_ok = False

        # syslog를 mgmt 포트로 보낼 경우: 먼저 management route 추가
        if (
            syslog is not None
            and isinstance(syslog, dict)
            and syslog
            and syslog_via_mgmt
            and management_route_gateway
        ):
            route_name = management_route_name or "syslog_mgmt_route"
            r = self.add_management_route(
                name=route_name,
                network=management_route_network,
                gateway=management_route_gateway,
                description="route for syslog via management port",
            )
            results.append({"step": "management_route", "result": r})
            if isinstance(r, dict) and r.get("ok") is False:
                all_ok = False

        if syslog is not None and isinstance(syslog, dict) and syslog:
            r = self.set_syslog(**syslog)
            results.append({"step": "syslog", "result": r})
            if isinstance(r, dict) and r.get("ok") is False:
                all_ok = False

        # 비밀번호 변경은 항상 마지막 (중간에 변경 시 이후 API 인증 실패 방지)
        if admin_password is not None and admin_password != "":
            r = self.set_user_password("admin", admin_password)
            results.append({"step": "admin_password", "result": r})
            if isinstance(r, dict) and r.get("ok") is False:
                all_ok = False

        if root_password is not None and root_password != "":
            r = self.set_user_password("root", root_password)
            results.append({"step": "root_password", "result": r})
            if isinstance(r, dict) and r.get("ok") is False:
                all_ok = False

        return {"ok": all_ok, "results": results}

    # ============= HA(이중화) 설정 =============
    def list_cm_devices(self):
        """cm device 목록 조회. GET /mgmt/tm/cm/device (selfDevice, hostname, configsyncIp 등 확인용)"""
        return self._request("GET", "/mgmt/tm/cm/device")

    def get_cm_device(self, device_name: str, partition: str = "Common"):
        """단일 cm device 조회. device_name은 호스트명 등. partition 기본 Common."""
        path = f"/mgmt/tm/cm/device/~{partition}~{device_name}"
        return self._request("GET", path)

    def update_cm_device(
        self,
        device_name: str,
        configsync_ip: str = None,
        mirror_ip: str = None,
        unicast_addresses: list = None,
        partition: str = "Common",
    ):
        """cm device 설정 수정 (configsyncIp, mirrorIp, unicastAddress).
        unicast_addresses: [ {"ip": "x.x.x.x", "port": 1026}, ... ] (failover 통신용)
        """
        path = f"/mgmt/tm/cm/device/~{partition}~{device_name}"
        body = {}
        if configsync_ip is not None:
            body["configsyncIp"] = configsync_ip
        if mirror_ip is not None:
            body["mirrorIp"] = mirror_ip
        if unicast_addresses is not None:
            body["unicastAddress"] = unicast_addresses
        if not body:
            return {"ok": False, "error": "configsync_ip, mirror_ip, unicast_addresses 중 하나 이상 필요"}
        return self._request("PATCH", path, json_body=body)

    def add_to_trust(
        self,
        device: str,
        device_name: str,
        username: str,
        password: str,
        port: int = None,
    ):
        """피어 장비를 trust 도메인에 추가. device=피어 mgmt IP 또는 FQDN, device_name=피어 호스트명."""
        path = "/mgmt/tm/cm/add-to-trust"
        body = {
            "device": device,
            "deviceName": device_name,
            "username": username,
            "password": password,
        }
        if port is not None:
            body["port"] = port
        return self._request("POST", path, json_body=body)

    def list_cm_device_groups(self):
        """device group 목록 조회. GET /mgmt/tm/cm/device-group"""
        return self._request("GET", "/mgmt/tm/cm/device-group")

    def create_cm_device_group(
        self,
        name: str,
        group_type: str = "sync-failover",
        auto_sync: str = None,
        partition: str = "Common",
        **kwargs,
    ):
        """device group 생성. group_type: sync-failover | sync-only."""
        path = "/mgmt/tm/cm/device-group"
        body = {"name": name, "type": group_type}
        if auto_sync is not None:
            body["autoSync"] = auto_sync
        for k, v in kwargs.items():
            if v is not None:
                body[k] = v
        return self._request("POST", path, json_body=body)

    def get_cm_device_group_devices(self, group_name: str, partition: str = "Common"):
        """device group에 속한 device 목록 조회."""
        path = f"/mgmt/tm/cm/device-group/~{partition}~{group_name}/devices"
        return self._request("GET", path)

    def add_cm_device_to_group(self, group_name: str, device_name: str, partition: str = "Common"):
        """device group에 device 추가. device_name은 cm device 이름(호스트명)."""
        path = f"/mgmt/tm/cm/device-group/~{partition}~{group_name}/devices"
        # REST에서 추가 시 name으로 참조. 형식은 ~partition~deviceName
        body = {"name": f"~{partition}~{device_name}"}
        return self._request("POST", path, json_body=body)

    def run_config_sync_to_group(self, group_name: str):
        """config-sync to-group 실행 (tmsh run cm config-sync to-group <name>)."""
        path = "/mgmt/tm/util/bash"
        cmd = f"tmsh run cm config-sync to-group {group_name}"
        body = {"command": "run", "utilCmdArgs": f"-c '{cmd}'"}
        return self._request("POST", path, json_body=body)

    def get_cm_sync_status(self):
        """HA/Sync 상태 조회. GET /mgmt/tm/cm/sync-status"""
        return self._request("GET", "/mgmt/tm/cm/sync-status")

    def apply_ha_settings(
        self,
        group_name: str,
        group_type: str,
        primary_hostname: str,
        primary_configsync_ip: str,
        primary_mirror_ip: str,
        primary_unicast: list,
        secondary_device_ip: str,
        secondary_device_name: str,
        secondary_username: str,
        secondary_password: str,
        secondary_configsync_ip: str,
        secondary_mirror_ip: str,
        secondary_unicast: list,
        secondary_port: int = None,
    ):
        """HA 이중화 일괄 적용 (현재 연결이 Primary 기준).
        1) Primary self device 설정 2) Secondary self device 설정(별도 연결) 3) add-to-trust 4) device group 생성 5) 두 device 추가 6) config-sync.
        secondary_unicast/primary_unicast: [ {"ip": "x.x.x.x", "port": 1026}, ... ]
        """
        from Tools.settings import build_endpoint_settings

        results = []
        all_ok = True

        # 1. Primary(self) device 설정
        r = self.update_cm_device(
            primary_hostname,
            configsync_ip=primary_configsync_ip,
            mirror_ip=primary_mirror_ip,
            unicast_addresses=primary_unicast,
        )
        results.append({"step": "primary_device_config", "result": r})
        if isinstance(r, dict) and r.get("ok") is False and "status_code" in r:
            all_ok = False

        # 2. Secondary device 설정 (Secondary에 연결해 PATCH)
        sec_settings = build_endpoint_settings(
            host=secondary_device_ip,
            port=secondary_port or 443,
            username=secondary_username,
            password=secondary_password,
        )
        sec_session = requests.Session()
        sec_url = f"{sec_settings.base_url}/mgmt/tm/cm/device/~Common~{secondary_device_name}"
        try:
            sec_resp = sec_session.request(
                "PATCH",
                sec_url,
                headers=sec_settings.headers,
                json={
                    "configsyncIp": secondary_configsync_ip,
                    "mirrorIp": secondary_mirror_ip,
                    "unicastAddress": secondary_unicast,
                },
                verify=getattr(sec_settings, "verify_tls", False),
                timeout=getattr(sec_settings, "timeout_seconds", 20),
            )
            sec_body = sec_resp.json() if sec_resp.headers.get("Content-Type", "").find("json") >= 0 else sec_resp.text
            r = sec_body if sec_resp.ok else {"ok": False, "status_code": sec_resp.status_code, "body": sec_body}
        except Exception as e:
            r = {"ok": False, "error": str(e)}
        sec_session.close()
        results.append({"step": "secondary_device_config", "result": r})
        if isinstance(r, dict) and (r.get("ok") is False or r.get("status_code", 0) not in (0, 200)):
            all_ok = False

        # 3. Primary에서 Secondary를 trust에 추가
        r = self.add_to_trust(
            device=secondary_device_ip,
            device_name=secondary_device_name,
            username=secondary_username,
            password=secondary_password,
            port=secondary_port,
        )
        results.append({"step": "add_to_trust", "result": r})
        if isinstance(r, dict) and r.get("ok") is False and "status_code" in r:
            all_ok = False

        # 4. Device group 생성
        r = self.create_cm_device_group(name=group_name, group_type=group_type)
        results.append({"step": "create_device_group", "result": r})
        if isinstance(r, dict) and r.get("ok") is False and "status_code" in r:
            all_ok = False

        # 5. 두 device를 group에 추가
        for dev_name in (primary_hostname, secondary_device_name):
            r = self.add_cm_device_to_group(group_name, dev_name)
            results.append({"step": f"add_to_group_{dev_name}", "result": r})
            if isinstance(r, dict) and r.get("ok") is False and "status_code" in r:
                all_ok = False

        # 6. Config sync 실행
        r = self.run_config_sync_to_group(group_name)
        results.append({"step": "config_sync", "result": r})
        if isinstance(r, dict) and r.get("ok") is False and "status_code" in r:
            all_ok = False

        return {"ok": all_ok, "results": results}

    # ============= L4 표준 DB 설정 =============
    def set_sys_db(self, name: str, value: str):
        """sys db 변수 설정 (PATCH /mgmt/tm/sys/db/<name>)
        name에 dot 포함 가능 (예: ui.system.preferences.recordsperscreen)
        """
        path = f"/mgmt/tm/sys/db/{name}"
        return self._request("PATCH", path, json_body={"value": value})

    def patch_ltm_connection_settings(self, **kwargs):
        """ltm global-settings connection PATCH (camelCase 키)"""
        return self._request(
            "PATCH",
            "/mgmt/tm/ltm/global-settings/connection",
            json_body=kwargs,
        )

    def get_sys_db(self, name: str):
        """sys db 변수 현재값 조회 (GET) — 적용 전 장비 실제 상태 확인용"""
        path = f"/mgmt/tm/sys/db/{name}"
        return self._request("GET", path)

    def get_ltm_connection_settings(self):
        """ltm global-settings connection 현재값 조회 (GET) — 적용 전 장비 실제 상태 확인용"""
        return self._request("GET", "/mgmt/tm/ltm/global-settings/connection")

    def get_l4_standard_db_state(self):
        """L4 표준 DB 관련 항목의 장비 현재값을 조회. 적용 전/후 비교용.
        반환: sys_db 7개 실제 value, connection 3개 실제값. (setup.run은 기본 설정에서 적용) 조회 실패 시 해당 키에 error 포함.
        """
        db_keys = [
            "ui.system.preferences.recordsperscreen",
            "ui.system.preferences.advancedselection",
            "tm.fastl4_ack_mirror",
            "pvasyncookies.enabled",
            "tm.dupsynenforce",
            "tm.monitorencap",
            "bigd.mgmtroutecheck",
        ]
        sys_db = {}
        for name in db_keys:
            r = self.get_sys_db(name)
            if isinstance(r, dict):
                if r.get("ok") is False:
                    sys_db[name] = {"error": r.get("reason") or r.get("error"), "value": None}
                else:
                    sys_db[name] = {"value": r.get("value"), "defaultValue": r.get("defaultValue")}
            else:
                sys_db[name] = {"value": None, "error": "invalid response"}

        conn_r = self.get_ltm_connection_settings()
        connection = {}
        if isinstance(conn_r, dict) and conn_r.get("ok") is False:
            connection["_error"] = conn_r.get("reason") or conn_r.get("error")
        else:
            # 단일 리소스 또는 items[0] 형태 모두 처리
            body = conn_r if isinstance(conn_r, dict) else {}
            if body.get("items") and len(body["items"]) > 0:
                body = body["items"][0]
            for key in ("globalSynChallengeThreshold", "defaultVsSynChallengeThreshold", "vlanSynCookie"):
                connection[key] = body.get(key)

        return {"sys_db": sys_db, "connection": connection}

    def get_ltm_profile(self, profile_type: str, profile_name: str):
        """단일 LTM 프로파일 현재 설정 조회 (GET) — 적용 전 장비 실제 상태 확인용"""
        path = f"/mgmt/tm/ltm/profile/{profile_type}/{profile_name}"
        return self._request("GET", path)

    def get_l4_standard_profiles_state(self):
        """L4 표준 프로파일 5개의 장비 현재값 조회. 적용 전/후 비교용.
        각 프로파일이 없으면 not_found, 있으면 비교용 핵심 필드만 추출.
        """
        standard_profiles = [
            ("http", "HTTP_DEFAULT"),
            ("tcp", "TCP_DEFAULT"),
            ("fastl4", "FL4_DEFAULT"),
            ("fastl4", "FL4_UDP"),
            ("client-ssl", "clientssl_sni_default"),
        ]
        compare_keys = {
            "http": ["name", "defaultsFrom", "description"],
            "tcp": ["name", "defaultsFrom", "hardwareSynCookie", "synCookieEnable", "idleTimeout"],
            "fastl4": [
                "name", "defaultsFrom", "idleTimeout", "pvaAcceleration",
                "looseClose", "looseInitialization", "synCookieEnable", "synCookieWhitelist",
                "hardwareSynCookie", "softwareSynCookie", "resetOnTimeout",
            ],
            "client-ssl": ["name", "defaultsFrom", "sniDefault"],
        }
        result = {}
        for profile_type, profile_name in standard_profiles:
            r = self.get_ltm_profile(profile_type, profile_name)
            if isinstance(r, dict) and r.get("ok") is False:
                result[profile_name] = {"exists": False, "error": r.get("reason") or r.get("error") or "not_found"}
                continue
            if not isinstance(r, dict):
                result[profile_name] = {"exists": False, "error": "invalid response"}
                continue
            body = r
            if body.get("items") and len(body["items"]) > 0:
                body = body["items"][0]
            keys = compare_keys.get(profile_type, ["name", "defaultsFrom"])
            result[profile_name] = {
                "exists": True,
                "type": profile_type,
                "current": {k: body.get(k) for k in keys},
            }
        return result

    def apply_l4_standard_db(self):
        """L4 표준 DB 설정 일괄 적용 (sys db 7개 + ltm connection 3개). setup.run은 기본 설정(apply_basic_settings)에서 적용."""
        db_vars = [
            ("ui.system.preferences.recordsperscreen", "100"),
            ("ui.system.preferences.advancedselection", "advanced"),
            ("tm.fastl4_ack_mirror", "disable"),
            ("pvasyncookies.enabled", "false"),
            ("tm.dupsynenforce", "disable"),
            ("tm.monitorencap", "enable"),
            ("bigd.mgmtroutecheck", "enable"),
        ]
        results = []
        all_ok = True
        for name, value in db_vars:
            r = self.set_sys_db(name, value)
            results.append({"name": name, "value": value, "result": r})
            if isinstance(r, dict) and r.get("ok") is False:
                all_ok = False
        conn_r = self.patch_ltm_connection_settings(
            globalSynChallengeThreshold="0",
            defaultVsSynChallengeThreshold="0",
            vlanSynCookie="disabled",
        )
        results.append({"step": "ltm_connection", "result": conn_r})
        if isinstance(conn_r, dict) and conn_r.get("ok") is False:
            all_ok = False
        return {"ok": all_ok, "results": results}

    def apply_l4_standard_profiles(self):
        """L4 표준 프로파일 5개 생성 (HTTP_DEFAULT, TCP_DEFAULT, FL4_DEFAULT, FL4_UDP, clientssl_sni_default)"""
        profiles = [
            ("http", {"name": "HTTP_DEFAULT", "defaultsFrom": "http"}),
            (
                "tcp",
                {
                    "name": "TCP_DEFAULT",
                    "defaultsFrom": "f5-tcp-progressive",
                    "hardwareSynCookie": "disabled",
                    "synCookieEnable": "disabled",
                },
            ),
            (
                "fastl4",
                {
                    "name": "FL4_DEFAULT",
                    "defaultsFrom": "/Common/fastL4",
                    "looseClose": "enabled",
                    "looseInitialization": "enabled",
                    "pvaAcceleration": "none",
                    "synCookieEnable": "disabled",
                    "synCookieWhitelist": "disabled",
                    "hardwareSynCookie": "disabled",
                    "softwareSynCookie": "disabled",
                },
            ),
            (
                "fastl4",
                {
                    "name": "FL4_UDP",
                    "defaultsFrom": "/Common/fastL4",
                    "idleTimeout": "5",
                    "pvaAcceleration": "none",
                    "looseClose": "enabled",
                    "looseInitialization": "enabled",
                    "synCookieEnable": "disabled",
                    "resetOnTimeout": "disabled",
                },
            ),
            (
                "client-ssl",
                {"name": "clientssl_sni_default", "sniDefault": True},
            ),
        ]
        results = []
        all_ok = True
        for profile_type, payload in profiles:
            path = f"/mgmt/tm/ltm/profile/{profile_type}"
            r = self._request("POST", path, json_body=payload)
            if isinstance(r, dict) and r.get("ok") is False and r.get("status_code") in (409, 422):
                # 이미 존재하면 PATCH로 표준 옵션 적용 (FastL4 등 옵션이 부모와 다를 때)
                name = payload.get("name")
                patch_path = f"/mgmt/tm/ltm/profile/{profile_type}/{name}"
                patch_body = {k: v for k, v in payload.items() if k not in ("name", "defaultsFrom")}
                if patch_body:
                    r = self._request("PATCH", patch_path, json_body=patch_body)
                results.append({"profile": name, "result": r, "note": "updated existing"})
            else:
                results.append({"profile": payload.get("name"), "result": r})
            if isinstance(r, dict) and r.get("ok") is False:
                if r.get("status_code") not in (409, 422):
                    all_ok = False
        return {"ok": all_ok, "results": results}
