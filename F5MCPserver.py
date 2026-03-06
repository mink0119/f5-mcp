#!/Users/minkyu/Downloads/2.git/f5-mcp/mamba-env/bin/python
"""F5 TMOS AI Agent - MCP 서버"""

from mcp.server.fastmcp import FastMCP
from Tools.F5object import F5_object


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


mcp = FastMCP("f5_tmos_agent")


@mcp.tool()
def show_stats_tool(
    object_name: str,
    object_type: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 통계 조회. tmos_host/tmos_username/tmos_password 넘기면 해당 연결로만 요청 (다중 장비·계정 변경 시 유리)."""
    return F5_object(object_name=object_name, object_type=object_type, **_conn(tmos_host, tmos_port, tmos_username, tmos_password)).stats()


@mcp.tool()
def show_logs_tool(
    lines_number: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """시스템 로그 조회"""
    return F5_object(lines_number=lines_number, **_conn(tmos_host, tmos_port, tmos_username, tmos_password)).logs()


@mcp.tool()
def list_tool(
    object_type: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 목록 조회"""
    return F5_object(object_type=object_type, **_conn(tmos_host, tmos_port, tmos_username, tmos_password)).list()


@mcp.tool()
def create_tool(
    object_type: str,
    url_body: dict,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 생성"""
    return F5_object(object_type=object_type, url_body=url_body, **_conn(tmos_host, tmos_port, tmos_username, tmos_password)).create()


@mcp.tool()
def update_tool(
    object_type: str,
    url_body: dict,
    object_name: str = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 또는 설정 수정. object_type, url_body, object_name(ltm일 때). 연결 오버라이드 선택."""
    return F5_object(
        object_type=object_type, object_name=object_name, url_body=url_body,
        **_conn(tmos_host, tmos_port, tmos_username, tmos_password),
    ).update()


@mcp.tool()
def delete_tool(
    object_type: str,
    object_name: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """리소스 삭제"""
    return F5_object(object_type=object_type, object_name=object_name, **_conn(tmos_host, tmos_port, tmos_username, tmos_password)).delete()


@mcp.tool()
def health_check_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """연결 상태 확인"""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).sys_version()


# ============= Auth User (계정) 관리 =============
@mcp.tool()
def list_auth_users_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 목록 조회"""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).list_auth_users()


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
    """auth user(계정) 생성. name(사용자명), password 필수.
    partition_access: [ {"name": "all-partitions", "role": "admin"} ] 형태. role: admin, operator, guest, manager 등.
    shell: bash, tmsh, none (선택).
    """
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).create_auth_user(
        name=name,
        password=password,
        description=description,
        partition_access=partition_access,
        shell=shell,
    )


@mcp.tool()
def get_auth_user_tool(
    name: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 단일 조회"""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).get_auth_user(name)


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
    """auth user(계정) 수정. name 필수. password, description, partition_access, shell 중 변경할 것만 넘김."""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).update_auth_user(
        name=name,
        password=password,
        description=description,
        partition_access=partition_access,
        shell=shell,
    )


@mcp.tool()
def delete_auth_user_tool(
    name: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """auth user(계정) 삭제. name(사용자명) 필수."""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).delete_auth_user(name)


# ============= 호스트명 설정 =============
@mcp.tool()
def get_hostname_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 호스트명 조회"""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).get_hostname()


@mcp.tool()
def set_hostname_tool(
    hostname: str,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """F5 BIG-IP 호스트명 설정. hostname 필수. 연결 오버라이드 선택."""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).set_hostname(hostname)


# ============= DNS 설정 =============
@mcp.tool()
def get_dns_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 DNS 설정 조회"""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).get_dns()


@mcp.tool()
def set_dns_tool(
    nameservers: list,
    search_domains: list = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """DNS 서버 설정. nameservers 필수. 연결 오버라이드 선택."""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).set_dns(nameservers, search_domains)


@mcp.tool()
def clear_dns_search_domains_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """DNS 검색 도메인 삭제"""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).clear_dns_search_domains()


# ============= NTP 설정 =============
@mcp.tool()
def get_ntp_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 NTP 설정 조회"""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).get_ntp()


@mcp.tool()
def set_ntp_tool(
    servers: list,
    timezone: str = None,
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """NTP 서버 및 타임존 설정. servers 필수. 연결 오버라이드 선택."""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).set_ntp(servers, timezone)


# ============= Syslog 설정 =============
@mcp.tool()
def get_syslog_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """현재 Syslog 설정 조회"""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).get_syslog()


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
    """Syslog 로그 레벨 및 설정 변경. 연결 오버라이드 선택."""
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
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).set_syslog(**payload)


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
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """장비 초기 기본 설정을 한 번에 적용합니다 (템플릿).
    '기본 설정 해줘' 요청 시 이 툴을 사용하세요.
    tmos_host/tmos_username/tmos_password 를 넘기면 해당 연결 사용 (다중 장비·비밀번호 변경 후 재호출 시 유리).
    """
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
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).apply_basic_settings(
        hostname=hostname,
        nameservers=nameservers,
        search_domains=search_domains,
        ntp_servers=ntp_servers,
        timezone=timezone,
        admin_password=admin_password,
        root_password=root_password,
        syslog=syslog,
    )


# ============= L4 표준 설정 =============
@mcp.tool()
def get_l4_standard_db_state_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 DB 항목의 장비 현재값 조회. 연결 오버라이드 선택."""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).get_l4_standard_db_state()


@mcp.tool()
def get_l4_standard_profiles_state_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 프로파일 5개의 장비 현재 설정 조회. 연결 오버라이드 선택."""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).get_l4_standard_profiles_state()


@mcp.tool()
def apply_l4_standard_db_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 DB 설정 적용. 연결 오버라이드 선택."""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).apply_l4_standard_db()


@mcp.tool()
def apply_l4_standard_profiles_tool(
    tmos_host: str = None,
    tmos_port: int = None,
    tmos_username: str = None,
    tmos_password: str = None,
):
    """L4 표준 프로파일 생성. 연결 오버라이드 선택."""
    return F5_object(**_conn(tmos_host, tmos_port, tmos_username, tmos_password)).apply_l4_standard_profiles()


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
