#!/usr/bin/env python3
"""F5 TMOS AI Agent - MCP 서버 (Windows/macOS 공용)"""

from mcp.server.fastmcp import FastMCP
from Tools.F5object import F5_object


def _conn(tmos_host=None, tmos_port=None, tmos_username=None, tmos_password=None):
    """요청 단위 연결. mgmt IP·계정·비밀번호는 호출 시마다 전달."""
    d = {}
    if tmos_host is not None:
        d["tmos_host"] = tmos_host
    if tmos_port is not None:
        d["tmos_port"] = tmos_port
    if tmos_username is not None:
        d["tmos_username"] = tmos_username
    if tmos_password is not None:
        d["tmos_password"] = tmos_password
    return d


def _resolve_connection(
    tmos_host=None,
    tmos_port=None,
    tmos_username=None,
    tmos_password=None,
):
    """연결 1대 결정. tmos_host, tmos_username, tmos_password 가 모두 있어야 함. [(conn_dict, name)] 또는 [(error_dict, name)]."""
    if not (tmos_host and str(tmos_host).strip()):
        return [({"error": "tmos_host, tmos_username, tmos_password 를 모두 입력해 주세요."}, "connection")]
    if not (tmos_username and str(tmos_username).strip()) or not (tmos_password is not None):
        return [({"error": "tmos_host, tmos_username, tmos_password 를 모두 입력해 주세요."}, "connection")]
    c = _conn(tmos_host, tmos_port, tmos_username, tmos_password)
    return [(c, tmos_host)]


def _run_per_device(conns, run_one):
    """conns = [(conn_dict|None, display_name), ...]. 단일이면 run_one(conn) 결과만 반환, 다수면 [{device, result}, ...]."""
    if len(conns) == 1:
        conn, _ = conns[0]
        if isinstance(conn, dict) and "error" in conn:
            return conn
        return run_one(conn)
    results = []
    for conn, name in conns:
        if isinstance(conn, dict) and "error" in conn:
            results.append({"device": name, "result": conn})
        else:
            results.append({"device": name, "result": run_one(conn)})
    return {"apply_to_all": True, "results": results}


def _device_params(doc_extra=""):
    """도구에 공통 연결 인자 설명. mgmt IP·계정·비밀번호는 호출 시마다 입력."""
    return (
        "tmos_host: F5 관리 IP(필수). "
        "tmos_username / tmos_password: 계정·비밀번호(필수). "
        "tmos_port: 포트(선택, 기본 443). "
        + doc_extra
    )


mcp = FastMCP("f5_tmos_agent")


@mcp.tool()
def show_stats_tool(
    object_name: str,
    resource_path: str = None,
    object_type: str = None,
    partition: str = "Common",
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 통계 조회. resource_path 예: ltm/pool, net/vlan. object_type만 주면 ltm 하위로 처리(기존 호환). """ + _device_params()
    if not resource_path and not object_type:
        return {"ok": False, "error": "resource_path 또는 object_type 중 하나 필요"}
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    def _run(c):
        k = dict(object_name=object_name, partition=partition, **(c or {}))
        if resource_path:
            k["resource_path"] = resource_path
        else:
            k["object_type"] = object_type
        return F5_object(**k).stats()
    return _run_per_device(conns, _run)


@mcp.tool()
def get_one_tool(
    object_name: str,
    resource_path: str = None,
    object_type: str = None,
    partition: str = "Common",
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """단일 리소스 조회. resource_path 예: ltm/pool, net/vlan, net/self. """ + _device_params()
    if not resource_path and not object_type:
        return {"ok": False, "error": "resource_path 또는 object_type 중 하나 필요"}
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    k = dict(object_name=object_name, partition=partition, **(conn or {}))
    if resource_path:
        k["resource_path"] = resource_path
    else:
        k["object_type"] = object_type
    return F5_object(**k).get_one()


@mcp.tool()
def show_logs_tool(
    lines_number: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """시스템 로그 조회. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(lines_number=lines_number, **(c or {})).logs())


@mcp.tool()
def list_tool(
    resource_path: str = None,
    object_type: str = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 목록 조회. resource_path 예: ltm/pool, net/vlan, net/self. object_type만 주면 ltm/object_type(기존 호환). """ + _device_params()
    if not resource_path and not object_type:
        return {"ok": False, "error": "resource_path 또는 object_type 중 하나 필요"}
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    def _run(c):
        k = dict(**(c or {}))
        if resource_path:
            k["resource_path"] = resource_path
        else:
            k["object_type"] = object_type
        return F5_object(**k).list()
    return _run_per_device(conns, _run)


@mcp.tool()
def create_tool(
    resource_path: str = None,
    object_type: str = None,
    url_body: dict = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 생성. resource_path 예: ltm/pool, net/vlan, net/self. object_type만 주면 ltm/object_type(기존 호환). url_body는 API 스펙(camelCase). """ + _device_params()
    if not resource_path and not object_type:
        return {"ok": False, "error": "resource_path 또는 object_type 중 하나 필요"}
    if not url_body:
        return {"ok": False, "error": "url_body 필요"}
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    def _run(c):
        k = dict(url_body=url_body, **(c or {}))
        if resource_path:
            k["resource_path"] = resource_path
        else:
            k["object_type"] = object_type
        return F5_object(**k).create()
    return _run_per_device(conns, _run)


@mcp.tool()
def update_tool(
    url_body: dict,
    object_name: str,
    resource_path: str = None,
    object_type: str = None,
    partition: str = "Common",
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 수정. resource_path 예: ltm/pool, net/vlan. object_name은 리소스 이름. """ + _device_params()
    if not resource_path and not object_type:
        return {"ok": False, "error": "resource_path 또는 object_type 중 하나 필요"}
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    def _run(c):
        k = dict(object_name=object_name, url_body=url_body, partition=partition, **(c or {}))
        if resource_path:
            k["resource_path"] = resource_path
        else:
            k["object_type"] = object_type
        return F5_object(**k).update()
    return _run_per_device(conns, _run)


@mcp.tool()
def delete_tool(
    object_name: str,
    resource_path: str = None,
    object_type: str = None,
    partition: str = "Common",
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 삭제. resource_path 예: ltm/pool, net/vlan, net/self. """ + _device_params()
    if not resource_path and not object_type:
        return {"ok": False, "error": "resource_path 또는 object_type 중 하나 필요"}
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    def _run(c):
        k = dict(object_name=object_name, partition=partition, **(c or {}))
        if resource_path:
            k["resource_path"] = resource_path
        else:
            k["object_type"] = object_type
        return F5_object(**k).delete()
    return _run_per_device(conns, _run)


# ============= Generic TMOS API (모든 설정 생성/수정/삭제) =============
# 기본/표준 설정 외 F5 API 스펙의 모든 엔드포인트를 path로 지정해 사용. 참고: https://clouddocs.f5.com/api/icontrol-rest/APIRef.html

@mcp.tool()
def tm_api_reference_tool():
    """F5 iControl REST API 네임스페이스 요약. tm_get/post/patch/put/delete_tool 사용 시 path 참고용.
    상세 스펙: https://clouddocs.f5.com/api/icontrol-rest/APIRef.html
    """
    return {
        "reference_url": "https://clouddocs.f5.com/api/icontrol-rest/APIRef.html",
        "path_prefix": "path는 tm 하위 경로 (예: ltm/pool, net/vlan). /mgmt/tm/ 는 자동 추가.",
        "namespaces": [
            {"prefix": "ltm", "description": "LTM: pool, virtual, node, snatpool, snat, policy, rule, virtual-address, default-node-monitor, nat, ifile 등"},
            {"prefix": "net", "description": "네트워크: vlan, self, route, arp, interface, route-domain, trunk, packet-filter, port-mirror 등"},
            {"prefix": "sys", "description": "시스템: syslog, dns, ntp, db, management-route, global-settings, clock, service, snmp, license, provision 등"},
            {"prefix": "cm", "description": "클러스터/HA: device, device-group, add-to-trust, traffic-group, trust-domain 등"},
            {"prefix": "auth", "description": "인증: user, partition, password-policy, ldap, radius-server, tacacs, source 등"},
            {"prefix": "gtm", "description": "GTM: server, datacenter, wideip, pool, persist, topology 등"},
            {"prefix": "analytics", "description": "분석: report, global-settings, predefined-report 등"},
            {"prefix": "apm", "description": "APM: application, access-info, acl, application-filter, url-filter 등"},
            {"prefix": "ilx", "description": "iRules LX: workspace, plugin, global-settings"},
            {"prefix": "util", "description": "유틸: bash (tmsh 실행) 등"},
            {"prefix": "vcmp", "description": "VCMP: guest, virtual-disk, traffic-profile 등"},
            {"prefix": "pem", "description": "PEM: listener, policy, subscriber 등"},
            {"prefix": "wam", "description": "WAM: application, policy, ad-policy 등"},
            {"prefix": "wom", "description": "WOM: local-endpoint, remote-endpoint 등"},
        ],
        "usage": "tm_get_tool(path), tm_post_tool(path, body), tm_patch_tool(path, body), tm_put_tool(path, body), tm_delete_tool(path). 리소스 path 예: ltm/pool/~Common~my_pool",
    }


@mcp.tool()
def tm_get_tool(
    path: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """TMOS API GET. path는 tm 하위 경로 (예: ltm/pool, ltm/pool/~Common~my_pool, net/vlan, sys/syslog).
    컬렉션은 목록, 리소스 id 포함 시 단일 조회. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).tm_request("GET", path)


@mcp.tool()
def tm_post_tool(
    path: str,
    body: dict,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """TMOS API POST. path에 리소스 생성 또는 액션 실행. body는 API 스펙의 속성 (camelCase).
    예: path=ltm/pool, body={"name":"my_pool","loadBalancingMode":"round-robin"} """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).tm_request("POST", path, json_body=body)


@mcp.tool()
def tm_patch_tool(
    path: str,
    body: dict,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """TMOS API PATCH. path는 리소스까지 포함 (예: ltm/pool/~Common~my_pool). body는 변경할 속성만. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).tm_request("PATCH", path, json_body=body)


@mcp.tool()
def tm_put_tool(
    path: str,
    body: dict,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """TMOS API PUT. path는 리소스까지 포함. body는 전체 속성 (교체). """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).tm_request("PUT", path, json_body=body)


@mcp.tool()
def tm_delete_tool(
    path: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """TMOS API DELETE. path는 삭제할 리소스까지 포함 (예: ltm/pool/~Common~my_pool). """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).tm_request("DELETE", path)


@mcp.tool()
def health_check_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """연결 상태 확인. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).sys_version())


# ============= Auth User (계정) 관리 =============
@mcp.tool()
def list_auth_users_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 목록 조회. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).list_auth_users())


@mcp.tool()
def create_auth_user_tool(
    name: str,
    password: str,
    description: str = None,
    partition_access: list = None,
    shell: str = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 생성. """ + _device_params("partition_access: [ {\"name\": \"all-partitions\", \"role\": \"admin\"} ] 등.")
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(
        conns,
        lambda c: F5_object(**(c or {})).create_auth_user(
            name=name, password=password, description=description, partition_access=partition_access, shell=shell,
        ),
    )


@mcp.tool()
def get_auth_user_tool(
    name: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 단일 조회. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_auth_user(name))


@mcp.tool()
def update_auth_user_tool(
    name: str,
    password: str = None,
    description: str = None,
    partition_access: list = None,
    shell: str = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 수정. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(
        conns,
        lambda c: F5_object(**(c or {})).update_auth_user(
            name=name, password=password, description=description, partition_access=partition_access, shell=shell,
        ),
    )


@mcp.tool()
def delete_auth_user_tool(
    name: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 삭제. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).delete_auth_user(name))


# ============= 호스트명 설정 =============
@mcp.tool()
def get_hostname_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 호스트명 조회. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_hostname())


@mcp.tool()
def set_hostname_tool(
    hostname: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """F5 BIG-IP 호스트명 설정. hostname은 FQDN 형식으로만 장비에 전달됨(필수). 짧은 이름은 bigip2.localdomain 형태로 보정 후 전달. CM device name도 함께 변경됨. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).set_hostname_sync_device_name(hostname))


# ============= DNS 설정 =============
@mcp.tool()
def get_dns_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 DNS 설정 조회. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_dns())


@mcp.tool()
def set_dns_tool(
    nameservers: list,
    search_domains: list = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """DNS 서버 설정. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).set_dns(nameservers, search_domains))


@mcp.tool()
def clear_dns_search_domains_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """DNS 검색 도메인 삭제. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).clear_dns_search_domains())


# ============= NTP 설정 =============
@mcp.tool()
def get_ntp_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 NTP 설정 조회. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_ntp())


@mcp.tool()
def set_ntp_tool(
    servers: list,
    timezone: str = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """NTP 서버 및 타임존 설정. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).set_ntp(servers, timezone))


# ============= Syslog 설정 =============
@mcp.tool()
def get_syslog_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 Syslog 설정 조회. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_syslog())


@mcp.tool()
def get_management_routes_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """management route 목록 조회 (mgmt 포트 라우팅). syslog를 mgmt로 보낼 때 경로 확인용. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_management_routes())


@mcp.tool()
def add_management_route_tool(
    name: str,
    network: str,
    gateway: str,
    description: str = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """management route 추가. syslog를 mgmt 포트로 보낼 때 목적지로 가는 경로가 필요하면 사용. network: default 또는 x.x.x.x/prefix. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).add_management_route(
        name=name, network=network, gateway=gateway, description=description,
    )


@mcp.tool()
def set_syslog_tool(
    console_log: str = None,
    clustered_host_slot: str = None,
    cron_from: str = None,
    cron_to: str = None,
    daemon_from: str = None,
    daemon_to: str = None,
    auth_priv_from: str = None,
    auth_priv_to: str = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """Syslog 로그 레벨 및 설정 변경. """ + _device_params()
    payload = {}
    if console_log:
        payload["consoleLog"] = console_log
    if clustered_host_slot:
        payload["clusteredHostSlot"] = clustered_host_slot
    if cron_from:
        payload["cronFrom"] = cron_from
    if cron_to:
        payload["cronTo"] = cron_to
    if daemon_from:
        payload["daemonFrom"] = daemon_from
    if daemon_to:
        payload["daemonTo"] = daemon_to
    if auth_priv_from:
        payload["authPrivFrom"] = auth_priv_from
    if auth_priv_to:
        payload["authPrivTo"] = auth_priv_to
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).set_syslog(**payload))


# ============= 장비 기본 설정 (템플릿) =============
# 기본설정에서 "사용자가 말로 지정한 항목"만 적용할 때 사용하는 키 목록 (apply_only_keys와 동일한 집합)
_BASIC_SETTING_KEYS = ("hostname", "nameservers", "ntp_servers", "timezone", "syslog", "admin_password", "root_password")


def _has_any_basic_setting_value(hostname, nameservers, ntp_servers, syslog, admin_password, root_password, timezone=None, apply_only_keys=None):
    """적용할 값이 하나라도 있으면 True. apply_only_keys가 있으면 해당 키에 한정하여 판단."""
    def has_hostname():
        return hostname is not None and str(hostname).strip() != ""
    def has_nameservers():
        return nameservers is not None and isinstance(nameservers, (list, tuple)) and len(nameservers) > 0
    def has_ntp():
        return ntp_servers is not None and isinstance(ntp_servers, (list, tuple)) and len(ntp_servers) > 0
    def has_timezone():
        return timezone is not None and str(timezone).strip() != ""
    def has_syslog():
        return syslog is not None and isinstance(syslog, dict) and len(syslog) > 0
    def has_admin_pw():
        return admin_password is not None and str(admin_password).strip() != ""
    def has_root_pw():
        return root_password is not None and str(root_password).strip() != ""

    if apply_only_keys is not None:
        if not apply_only_keys:
            return False
        checks = {
            "hostname": has_hostname,
            "nameservers": has_nameservers,
            "ntp_servers": has_ntp,
            "timezone": has_timezone,
            "syslog": has_syslog,
            "admin_password": has_admin_pw,
            "root_password": has_root_pw,
        }
        for k in apply_only_keys:
            if k in checks and checks[k]():
                return True
        return False

    if has_hostname() or has_nameservers() or has_ntp() or has_syslog() or has_admin_pw() or has_root_pw():
        return True
    return False


_BASIC_SETTINGS_ASK_USER_RESPONSE = {
    "AGENT_INSTRUCTION": "기본설정이 적용된 것이 아닙니다. 사용자에게 basic_settings_guide 항목을 보여주고 message로 값을 요청한 뒤, 사용자가 입력한 값으로 apply_basic_settings_tool을 다시 호출하세요. '기본설정 완료'라고 하면 안 됩니다.",
    "ok": False,
    "completed": False,
    "action": "ask_user",
    "do_not_report_as_complete": True,
    "reason": "기본설정 적용 값이 하나도 전달되지 않았습니다. 사용자에게 항목과 값을 물어본 뒤, 받은 값으로 apply_basic_settings_tool을 다시 호출해야 합니다. 이 상태에서는 '기본설정 완료'라고 하면 안 됩니다.",
    "message": "기본 설정에 적용할 항목을 알려주세요. 호스트명, DNS, NTP, Syslog, admin/root 비밀번호 중 원하는 것의 값을 입력해 주시면 해당 항목만 적용합니다.",
    "basic_settings_guide": {
        "description": "기본 설정에서 진행하는 항목입니다. 사용자가 말로 지정한 항목에만 값을 넣어 주세요. 아래 example은 형식 참고용이며, example 값을 그대로 인자로 넣지 말 것(기본값으로 사용 금지).",
        "items": [
            {"key": "hostname", "label": "호스트명", "description": "F5 장비 호스트명(FQDN). 사용자가 지정한 경우에만 넣을 것.", "example": "형식: 문자열 (사용자 지정값만)"},
            {"key": "nameservers", "label": "DNS 서버", "description": "DNS 서버 IP 목록. 사용자가 지정한 경우에만 넣을 것. guide 예시 IP를 기본값으로 넣지 말 것.", "example": "형식: 문자열 배열 (사용자 지정 IP만)"},
            {"key": "ntp_servers", "label": "NTP 서버 및 타임존", "description": "NTP 서버 목록. 사용자가 지정한 경우에만 넣을 것. guide 예시를 기본값으로 넣지 말 것.", "example": "형식: 문자열 배열 (사용자 지정 NTP만)", "optional": "timezone"},
            {"key": "syslog", "label": "Syslog", "description": "로그 레벨 등. 사용자가 지정한 경우에만.", "example": "형식: consoleLog, authPrivFrom 등 키/값"},
            {"key": "admin_password", "label": "admin 비밀번호", "description": "admin 계정 비밀번호. 사용자가 지정한 경우에만.", "example": "형식: 문자열 (사용자 지정값만)"},
            {"key": "root_password", "label": "root 비밀번호", "description": "root 계정 비밀번호. 사용자가 지정한 경우에만.", "example": "형식: 문자열 (사용자 지정값만)"},
        ],
        "note": "사용자가 말로 지정하지 않은 항목은 인자로 넣지 말 것. apply_only_keys에는 사용자가 지정한 키만 포함. (mgmt로 syslog 시 syslog_via_mgmt, management_route_gateway 필요할 수 있음)",
    },
}


@mcp.tool()
def apply_basic_settings_tool(
    hostname: str = None,
    nameservers: list = None,
    search_domains: list = None,
    ntp_servers: list = None,
    timezone: str = None,
    admin_password: str = None,
    root_password: str = None,
    console_log: str = None,
    clustered_host_slot: str = None,
    cron_from: str = None,
    cron_to: str = None,
    daemon_from: str = None,
    daemon_to: str = None,
    auth_priv_from: str = None,
    auth_priv_to: str = None,
    syslog_via_mgmt: bool = False,
    management_route_name: str = None,
    management_route_network: str = "default",
    management_route_gateway: str = None,
    apply_only_keys: list = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """장비 초기 기본 설정을 한 번에 적용 (템플릿).
    [필수] apply_only_keys를 반드시 넘겨야 함. 비우면(apply_only_keys=[]) ask_user 반환.
    [금지] 사용자가 말로 지정하지 않은 항목은 인자로 넣지 말 것. basic_settings_guide의 예시(IP, NTP 서버명 등)를 기본값으로 넣지 말 것. hostname, nameservers, ntp_servers, timezone은 사용자가 말한 경우에만 넣고, 장비 조회값은 넣지 말 것.
    사용자가 지정한 항목만: apply_only_keys=[해당키들], 해당 인자만 전달.
    syslog_via_mgmt=True 이고 management_route_gateway 주면 syslog 전 management route 추가.
    """ + _device_params()
    syslog = None
    if any(
        [
            console_log,
            clustered_host_slot,
            cron_from,
            cron_to,
            daemon_from,
            daemon_to,
            auth_priv_from,
            auth_priv_to,
        ]
    ):
        syslog = {}
        if console_log:
            syslog["consoleLog"] = console_log
        if clustered_host_slot:
            syslog["clusteredHostSlot"] = clustered_host_slot
        if cron_from:
            syslog["cronFrom"] = cron_from
        if cron_to:
            syslog["cronTo"] = cron_to
        if daemon_from:
            syslog["daemonFrom"] = daemon_from
        if daemon_to:
            syslog["daemonTo"] = daemon_to
        if auth_priv_from:
            syslog["authPrivFrom"] = auth_priv_from
        if auth_priv_to:
            syslog["authPrivTo"] = auth_priv_to

    # [엄격 모드] apply_only_keys가 없거나 비어 있으면 아무것도 적용하지 않고 ask_user 반환.
    # 장비 조회값(hostname/NTP/DNS 등)이 인자로 넘어와도, apply_only_keys가 없으면 "사용자 지정"으로 보지 않고 무시함.
    if not apply_only_keys:
        return _BASIC_SETTINGS_ASK_USER_RESPONSE

    if not _has_any_basic_setting_value(hostname, nameservers, ntp_servers, syslog, admin_password, root_password, timezone=timezone, apply_only_keys=apply_only_keys):
        return _BASIC_SETTINGS_ASK_USER_RESPONSE

    # apply_only_keys에 있는 항목만 적용 (나머지는 None으로 덮어서 전달)
    only_set = set(apply_only_keys)

    def _allow(key):
        return key in only_set

    kwargs = dict(
        hostname=hostname if _allow("hostname") else None,
        nameservers=nameservers if _allow("nameservers") else None,
        search_domains=search_domains if _allow("nameservers") else None,
        ntp_servers=ntp_servers if _allow("ntp_servers") else None,
        timezone=timezone if (_allow("ntp_servers") or _allow("timezone")) else None,
        admin_password=admin_password if _allow("admin_password") else None,
        root_password=root_password if _allow("root_password") else None,
        syslog=syslog if _allow("syslog") else None,
        syslog_via_mgmt=syslog_via_mgmt,
        management_route_name=management_route_name,
        management_route_network=management_route_network,
        management_route_gateway=management_route_gateway,
    )
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)

    def _run(c):
        out = F5_object(**(c or {})).apply_basic_settings(**kwargs)
        if isinstance(out, dict) and out.get("action") == "ask_user":
            return {"AGENT_INSTRUCTION": _BASIC_SETTINGS_ASK_USER_RESPONSE["AGENT_INSTRUCTION"], **out}
        return out

    return _run_per_device(conns, _run)


# ============= L4 표준 설정 =============
@mcp.tool()
def get_l4_standard_db_state_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 DB 항목의 장비 현재값 조회. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_l4_standard_db_state())


@mcp.tool()
def get_l4_standard_profiles_state_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 프로파일 5개의 장비 현재 설정 조회. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_l4_standard_profiles_state())


@mcp.tool()
def apply_l4_standard_db_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 DB 설정 적용. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).apply_l4_standard_db())


@mcp.tool()
def apply_l4_standard_profiles_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 프로파일 생성. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).apply_l4_standard_profiles())


# ============= HA(이중화) 설정 =============
@mcp.tool()
def get_ha_status_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """HA(이중화) 상태 조회: cm device 목록, device group 목록, sync-status. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    obj = F5_object(**(conn or {}))
    devices = obj.list_cm_devices()
    groups = obj.list_cm_device_groups()
    sync_status = obj.get_cm_sync_status()
    return {
        "devices": devices,
        "device_groups": groups,
        "sync_status": sync_status,
    }


@mcp.tool()
def apply_ha_tool(
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
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """HA(이중화) 일괄 적용. 현재 연결은 Primary로 사용.
    Primary/Secondary 모두 device name(CM name)과 hostname이 다르면, hostname을 device name에 맞춘 뒤 이중화를 진행함.
    group_name: device group 이름. group_type: sync-failover | sync-only.
    primary_*: Primary 장비 호스트명, configsync IP, mirror IP, unicast 리스트 [{"ip":"x.x.x.x","port":1026}].
    secondary_*: Secondary mgmt IP, 호스트명(또는 의도한 이름; 실제로는 Secondary에서 조회한 CM name 사용), 계정, configsync/mirror/unicast.
    primary_unicast / secondary_unicast: failover 통신용 [ {"ip": "x.x.x.x", "port": 1026}, ... ]
    """
    conns = _resolve_devices(None, None, False, tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).apply_ha_settings(
        group_name=group_name,
        group_type=group_type,
        primary_hostname=primary_hostname,
        primary_configsync_ip=primary_configsync_ip,
        primary_mirror_ip=primary_mirror_ip,
        primary_unicast=primary_unicast,
        secondary_device_ip=secondary_device_ip,
        secondary_device_name=secondary_device_name,
        secondary_username=secondary_username,
        secondary_password=secondary_password,
        secondary_configsync_ip=secondary_configsync_ip,
        secondary_mirror_ip=secondary_mirror_ip,
        secondary_unicast=secondary_unicast,
        secondary_port=secondary_port,
    )


@mcp.tool()
def list_cm_devices_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """cm device 목록 조회 (hostname, configsyncIp, mirrorIp, failoverState 등). """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).list_cm_devices())


@mcp.tool()
def add_to_trust_tool(
    peer_device_ip: str,
    peer_device_name: str,
    peer_username: str,
    peer_password: str,
    peer_port: int = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 연결된 장비(Primary)에서 피어 장비를 trust 도메인에 추가. REST API를 먼저 시도하고 403일 때만 TMSH 폴백. 반환: ok, method(REST|TMSH_fallback), response 등. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).add_to_trust(
        device=peer_device_ip,
        device_name=peer_device_name,
        username=peer_username,
        password=peer_password,
        port=peer_port,
    )


@mcp.tool()
def create_device_group_tool(
    name: str,
    group_type: str = "sync-failover",
    auto_sync: str = "enabled",
    save_on_auto_sync: bool = True,
    full_load_on_sync: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """device group 생성. 기본: autoSync=enabled, saveOnAutoSync=True(Save on Automatic Sync), fullLoadOnSync=False(Incremental Auto Sync). """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).create_cm_device_group(
        name=name,
        group_type=group_type,
        auto_sync=auto_sync,
        save_on_auto_sync=save_on_auto_sync,
        full_load_on_sync=full_load_on_sync,
    )


@mcp.tool()
def add_device_to_group_tool(
    group_name: str,
    device_to_add: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """device group에 device(호스트명) 추가. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).add_cm_device_to_group(group_name, device_to_add)


@mcp.tool()
def run_config_sync_tool(
    group_name: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """config-sync to-group 실행. """ + _device_params()
    conns = _resolve_connection(tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).run_config_sync_to_group(group_name)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
