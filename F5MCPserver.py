#!/Users/minkyu/Downloads/2.git/f5-mcp/mamba-env/bin/python
"""F5 TMOS AI Agent - MCP 서버"""

from mcp.server.fastmcp import FastMCP
from Tools.F5object import F5_object
from Tools.settings import load_devices_from_file


def _conn(tmos_host=None, tmos_port=None, tmos_username=None, tmos_password=None):
    """요청 단위 연결 오버라이드. 다중 장비·비밀번호 변경 시 호출마다 다른 값을 넘길 수 있음."""
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


def _resolve_devices(
    device_name=None,
    device_index=None,
    apply_to_all=False,
    tmos_host=None,
    tmos_port=None,
    tmos_username=None,
    tmos_password=None,
):
    """연결 대상 결정: (연결 오버라이드 dict 또는 None, 표시이름) 의 리스트.
    - tmos_host 등이 있으면 → 해당 1대 (소스/엔비 수정 없이 인자로 전달한 경우)
    - apply_to_all=True → 장비 목록 파일의 모든 장비
    - device_name / device_index → 파일에서 1대만 선택
    - 없으면 → [(None, "default")] 로 .env 기본 사용
    """
    has_override = tmos_host is not None or tmos_port is not None or tmos_username is not None or tmos_password is not None
    if has_override:
        c = _conn(tmos_host, tmos_port, tmos_username, tmos_password)
        return [(c, tmos_host or "override")]
    devices = load_devices_from_file()
    if apply_to_all:
        if not devices:
            return [({"error": "F5_DEVICES_FILE 또는 devices.yaml/devices.json 없음 또는 비어 있음"}, "apply_to_all")]
        return [(_conn(d["host"], d.get("port"), d["username"], d["password"]), d["name"]) for d in devices]
    if device_name is not None:
        for d in devices:
            if d.get("name") == device_name:
                return [(_conn(d["host"], d.get("port"), d["username"], d["password"]), d["name"])]
        return [({"error": f"device_name '{device_name}' not in devices file"}, device_name)]
    if device_index is not None:
        try:
            idx = int(device_index)
            if 0 <= idx < len(devices):
                d = devices[idx]
                return [(_conn(d["host"], d.get("port"), d["username"], d["password"]), d["name"])]
        except (TypeError, ValueError):
            pass
        return [({"error": f"device_index {device_index} invalid or out of range"}, "device_index")]
    return [(None, "default")]


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
    """도구에 공통으로 붙일 device_name, device_index, apply_to_all, tmos_* 인자 설명."""
    return (
        "device_name: 장비 목록 파일의 name으로 1대 지정. "
        "device_index: 목록 인덱스(0부터)로 1대 지정. "
        "apply_to_all: True면 목록 전체에 동일 설정 적용. "
        "tmos_host/tmos_port/tmos_username/tmos_password: 인자로 직접 연결 지정(파일/엔비 불필요). "
        + doc_extra
    )


mcp = FastMCP("f5_tmos_agent")


@mcp.tool()
def show_stats_tool(
    object_name: str,
    object_type: str,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 통계 조회. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(object_name=object_name, object_type=object_type, **(c or {})).stats())


@mcp.tool()
def show_logs_tool(
    lines_number: str,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """시스템 로그 조회. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(lines_number=lines_number, **(c or {})).logs())


@mcp.tool()
def list_tool(
    object_type: str,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 목록 조회. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(object_type=object_type, **(c or {})).list())


@mcp.tool()
def create_tool(
    object_type: str,
    url_body: dict,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 생성. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(object_type=object_type, url_body=url_body, **(c or {})).create())


@mcp.tool()
def update_tool(
    object_type: str,
    url_body: dict,
    object_name: str = None,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 또는 설정 수정. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(
        conns,
        lambda c: F5_object(object_type=object_type, object_name=object_name, url_body=url_body, **(c or {})).update(),
    )


@mcp.tool()
def delete_tool(
    object_type: str,
    object_name: str,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 삭제. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(object_type=object_type, object_name=object_name, **(c or {})).delete())


@mcp.tool()
def list_devices_tool():
    """장비 목록 파일(devices.yaml / devices.json 또는 F5_DEVICES_FILE)에 정의된 장비 목록 조회.
    비밀번호는 제외하고 name, host, port만 반환. 소스 수정 없이 이 파일만 수정해 대상 장비를 관리할 수 있음."""
    devices = load_devices_from_file()
    if not devices:
        return {"ok": False, "message": "장비 목록 파일 없음 또는 비어 있음. devices.yaml 또는 F5_DEVICES_FILE 설정.", "devices": []}
    return {"ok": True, "devices": [{"name": d["name"], "host": d["host"], "port": d["port"]} for d in devices]}


@mcp.tool()
def health_check_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """연결 상태 확인. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).sys_version())


# ============= Auth User (계정) 관리 =============
@mcp.tool()
def list_auth_users_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 목록 조회. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).list_auth_users())


@mcp.tool()
def create_auth_user_tool(
    name: str,
    password: str,
    description: str = None,
    partition_access: list = None,
    shell: str = None,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 생성. """ + _device_params("partition_access: [ {\"name\": \"all-partitions\", \"role\": \"admin\"} ] 등.")
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(
        conns,
        lambda c: F5_object(**(c or {})).create_auth_user(
            name=name, password=password, description=description, partition_access=partition_access, shell=shell,
        ),
    )


@mcp.tool()
def get_auth_user_tool(
    name: str,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 단일 조회. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_auth_user(name))


@mcp.tool()
def update_auth_user_tool(
    name: str,
    password: str = None,
    description: str = None,
    partition_access: list = None,
    shell: str = None,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 수정. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(
        conns,
        lambda c: F5_object(**(c or {})).update_auth_user(
            name=name, password=password, description=description, partition_access=partition_access, shell=shell,
        ),
    )


@mcp.tool()
def delete_auth_user_tool(
    name: str,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 삭제. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).delete_auth_user(name))


# ============= 호스트명 설정 =============
@mcp.tool()
def get_hostname_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 호스트명 조회. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_hostname())


@mcp.tool()
def set_hostname_tool(
    hostname: str,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """F5 BIG-IP 호스트명 설정. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).set_hostname(hostname))


# ============= DNS 설정 =============
@mcp.tool()
def get_dns_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 DNS 설정 조회. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_dns())


@mcp.tool()
def set_dns_tool(
    nameservers: list,
    search_domains: list = None,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """DNS 서버 설정. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).set_dns(nameservers, search_domains))


@mcp.tool()
def clear_dns_search_domains_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """DNS 검색 도메인 삭제. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).clear_dns_search_domains())


# ============= NTP 설정 =============
@mcp.tool()
def get_ntp_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 NTP 설정 조회. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_ntp())


@mcp.tool()
def set_ntp_tool(
    servers: list,
    timezone: str = None,
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """NTP 서버 및 타임존 설정. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).set_ntp(servers, timezone))


# ============= Syslog 설정 =============
@mcp.tool()
def get_syslog_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 Syslog 설정 조회. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_syslog())


@mcp.tool()
def get_management_routes_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """management route 목록 조회 (mgmt 포트 라우팅). syslog를 mgmt로 보낼 때 경로 확인용. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_management_routes())


@mcp.tool()
def add_management_route_tool(
    name: str,
    network: str,
    gateway: str,
    description: str = None,
    device_name: str = None,
    device_index: int = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """management route 추가. syslog를 mgmt 포트로 보낼 때 목적지로 가는 경로가 필요하면 사용. network: default 또는 x.x.x.x/prefix. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, False, tmos_host, tmos_port, tmos_username, tmos_password)
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
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
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
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).set_syslog(**payload))


# ============= 장비 기본 설정 (템플릿) =============
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
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """장비 초기 기본 설정을 한 번에 적용 (템플릿).
    syslog_via_mgmt=True 이고 management_route_gateway 를 주면, syslog 설정 직전에 management route 추가 (mgmt 포트로 syslog 통신 시 필요).
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
    kwargs = dict(
        hostname=hostname,
        nameservers=nameservers,
        search_domains=search_domains,
        ntp_servers=ntp_servers,
        timezone=timezone,
        admin_password=admin_password,
        root_password=root_password,
        syslog=syslog,
        syslog_via_mgmt=syslog_via_mgmt,
        management_route_name=management_route_name,
        management_route_network=management_route_network,
        management_route_gateway=management_route_gateway,
    )
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).apply_basic_settings(**kwargs))


# ============= L4 표준 설정 =============
@mcp.tool()
def get_l4_standard_db_state_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 DB 항목의 장비 현재값 조회. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_l4_standard_db_state())


@mcp.tool()
def get_l4_standard_profiles_state_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 프로파일 5개의 장비 현재 설정 조회. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).get_l4_standard_profiles_state())


@mcp.tool()
def apply_l4_standard_db_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 DB 설정 적용. apply_to_all 시 목록 전체에 동일 적용. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).apply_l4_standard_db())


@mcp.tool()
def apply_l4_standard_profiles_tool(
    device_name: str = None,
    device_index: int = None,
    apply_to_all: bool = False,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 프로파일 생성. apply_to_all 시 목록 전체에 동일 적용. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, apply_to_all, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).apply_l4_standard_profiles())


# ============= HA(이중화) 설정 =============
@mcp.tool()
def get_ha_status_tool(
    device_name: str = None,
    device_index: int = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """HA(이중화) 상태 조회: cm device 목록, device group 목록, sync-status. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, False, tmos_host, tmos_port, tmos_username, tmos_password)
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
    group_name: device group 이름. group_type: sync-failover | sync-only.
    primary_*: Primary 장비 호스트명, configsync IP, mirror IP, unicast 리스트 [{"ip":"x.x.x.x","port":1026}].
    secondary_*: Secondary mgmt IP, 호스트명, 계정, configsync/mirror/unicast.
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
    device_name: str = None,
    device_index: int = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """cm device 목록 조회 (hostname, configsyncIp, mirrorIp, failoverState 등). """ + _device_params()
    conns = _resolve_devices(device_name, device_index, False, tmos_host, tmos_port, tmos_username, tmos_password)
    return _run_per_device(conns, lambda c: F5_object(**(c or {})).list_cm_devices())


@mcp.tool()
def add_to_trust_tool(
    peer_device_ip: str,
    peer_device_name: str,
    peer_username: str,
    peer_password: str,
    peer_port: int = None,
    device_name: str = None,
    device_index: int = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 연결된 장비(Primary)에서 피어 장비를 trust 도메인에 추가. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, False, tmos_host, tmos_port, tmos_username, tmos_password)
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
    auto_sync: str = None,
    device_name: str = None,
    device_index: int = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """device group 생성. group_type: sync-failover | sync-only. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, False, tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).create_cm_device_group(
        name=name, group_type=group_type, auto_sync=auto_sync,
    )


@mcp.tool()
def add_device_to_group_tool(
    group_name: str,
    device_to_add: str,
    device_name: str = None,
    device_index: int = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """device group에 device(호스트명) 추가. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, False, tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).add_cm_device_to_group(group_name, device_to_add)


@mcp.tool()
def run_config_sync_tool(
    group_name: str,
    device_name: str = None,
    device_index: int = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """config-sync to-group 실행. """ + _device_params()
    conns = _resolve_devices(device_name, device_index, False, tmos_host, tmos_port, tmos_username, tmos_password)
    conn, _ = conns[0]
    if isinstance(conn, dict) and "error" in conn:
        return conn
    return F5_object(**(conn or {})).run_config_sync_to_group(group_name)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
