#!/Users/minkyu/Downloads/2.git/f5-mcp/mamba-env/bin/python
"""F5 TMOS AI Agent - MCP 서버"""

from mcp.server.fastmcp import FastMCP
from Tools.F5object import F5_object

mcp = FastMCP("f5_tmos_agent")


@mcp.tool()
def show_stats_tool(object_name: str, object_type: str):
    """리소스 통계 조회"""
    return F5_object(object_name=object_name, object_type=object_type).stats()


@mcp.tool()
def show_logs_tool(lines_number: str):
    """시스템 로그 조회"""
    return F5_object(lines_number=lines_number).logs()


@mcp.tool()
def list_tool(object_type: str):
    """리소스 목록 조회"""
    return F5_object(object_type=object_type).list()


@mcp.tool()
def create_tool(object_type: str, url_body: dict):
    """리소스 생성"""
    return F5_object(object_type=object_type, url_body=url_body).create()


@mcp.tool()
def update_tool(object_type: str, url_body: dict, object_name: str = None):
    """리소스 또는 설정 수정
    
    object_type: 리소스 타입 (virtual, pool, global-settings 등)
    url_body: 수정할 데이터
    object_name: 리소스 이름 (ltm 리소스의 경우만 필요)
    """
    return F5_object(object_type=object_type, object_name=object_name, url_body=url_body).update()


@mcp.tool()
def delete_tool(object_type: str, object_name: str):
    """리소스 삭제"""
    return F5_object(object_type=object_type, object_name=object_name).delete()


@mcp.tool()
def health_check_tool():
    """연결 상태 확인"""
    return F5_object().sys_version()


# ============= 호스트명 설정 =============
@mcp.tool()
def get_hostname_tool():
    """현재 호스트명 조회"""
    return F5_object().get_hostname()


@mcp.tool()
def set_hostname_tool(hostname: str):
    """F5 BIG-IP 호스트명 설정
    
    hostname: 설정할 호스트명 (예: 'ai-test.com', 'f5-bigip-01')
    """
    return F5_object().set_hostname(hostname)


# ============= DNS 설정 =============
@mcp.tool()
def get_dns_tool():
    """현재 DNS 설정 조회"""
    return F5_object().get_dns()


@mcp.tool()
def set_dns_tool(nameservers: list, search_domains: list = None):
    """DNS 서버 설정
    
    nameservers: DNS 서버 주소 리스트 (예: ['8.8.8.8', '8.8.4.4'])
    search_domains: 로컬 도메인 검색 리스트 (선택사항, 예: ['example.com'])
    """
    return F5_object().set_dns(nameservers, search_domains)


@mcp.tool()
def clear_dns_search_domains_tool():
    """DNS 검색 도메인 삭제
    
    Search domain을 모두 제거합니다
    """
    return F5_object().clear_dns_search_domains()


# ============= NTP 설정 =============
@mcp.tool()
def get_ntp_tool():
    """현재 NTP 설정 조회"""
    return F5_object().get_ntp()


@mcp.tool()
def set_ntp_tool(servers: list, timezone: str = None):
    """NTP 서버 및 타임존 설정
    
    servers: NTP 서버 주소 리스트 (예: ['time.google.com'])
    timezone: 타임존 (예: 'UTC', 'Asia/Seoul', 'America/New_York')
    """
    return F5_object().set_ntp(servers, timezone)


# ============= Syslog 설정 =============
@mcp.tool()
def get_syslog_tool():
    """현재 Syslog 설정 조회"""
    return F5_object().get_syslog()


@mcp.tool()
def set_syslog_tool(console_log: str = None, clustered_host_slot: str = None, 
                    cron_from: str = None, cron_to: str = None,
                    daemon_from: str = None, daemon_to: str = None,
                    auth_priv_from: str = None, auth_priv_to: str = None):
    """Syslog 로그 레벨 및 설정 변경
    
    console_log: 콘솔 로그 ('enabled' 또는 'disabled')
    clustered_host_slot: 클러스터 호스트 로깅 ('enabled' 또는 'disabled')
    cron_from/cron_to: Cron 로그 레벨 (emerg, alert, crit, err, warning, notice, info, debug)
    daemon_from/daemon_to: Daemon 로그 레벨
    auth_priv_from/auth_priv_to: Auth/Priv 로그 레벨
    """
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
    
    return F5_object().set_syslog(**payload)


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
):
    """장비 초기 기본 설정을 한 번에 적용합니다 (템플릿).
    '기본 설정 해줘' 요청 시 이 툴을 사용하세요.
    넘긴 인자만 적용하며, 생략한 항목은 건너뜁니다.
    hostname: 호스트명. nameservers: DNS 서버 리스트. search_domains: DNS 검색 도메인.
    ntp_servers: NTP 서버 리스트. timezone: 타임존 (예: Asia/Seoul).
    admin_password: admin 계정 비밀번호. root_password: root 계정 비밀번호.
    console_log, clustered_host_slot, cron_from/to, daemon_from/to, auth_priv_from/to: syslog 옵션.
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
    return F5_object().apply_basic_settings(
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
def get_l4_standard_db_state_tool():
    """L4 표준 DB 관련 항목의 장비 현재값을 조회합니다.
    적용 전/후 비교 시 반드시 이 툴로 '적용 전' 실제 장비 상태를 먼저 조회하세요.
    sys_db 8개와 ltm connection 3개의 실제 value를 반환합니다 (기본값이 아닌 장비 현재값).
    """
    return F5_object().get_l4_standard_db_state()


@mcp.tool()
def get_l4_standard_profiles_state_tool():
    """L4 표준 프로파일 5개의 장비 현재 설정을 조회합니다.
    적용 전/후 비교 시 반드시 이 툴로 '적용 전' 실제 장비 상태(예: idleTimeout, pvaAcceleration 등)를 먼저 조회하세요.
    """
    return F5_object().get_l4_standard_profiles_state()


@mcp.tool()
def apply_l4_standard_db_tool():
    """L4 표준 DB 설정을 적용합니다.
    GUI 옵션, fastl4 ack mirror, syn cookie 비활성화, dupsynenforce, monitorencap, mgmtroutecheck, setup.run 및 ltm connection 설정 포함.
    비교 보고 시: 먼저 get_l4_standard_db_state_tool()로 적용 전 상태를 조회한 뒤 이 툴 실행, 이후 다시 get_l4_standard_db_state_tool()로 적용 후 확인.
    """
    return F5_object().apply_l4_standard_db()


@mcp.tool()
def apply_l4_standard_profiles_tool():
    """L4 표준 프로파일을 생성합니다.
    HTTP_DEFAULT, TCP_DEFAULT, FL4_DEFAULT, FL4_UDP, clientssl_sni_default.
    비교 보고 시: 먼저 get_l4_standard_profiles_state_tool()로 적용 전 상태를 조회한 뒤 이 툴 실행, 이후 다시 get_l4_standard_profiles_state_tool()로 적용 후 확인.
    """
    return F5_object().apply_l4_standard_profiles()


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
