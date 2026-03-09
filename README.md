[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/czirakim-f5-mcp-server-badge.png)](https://mseep.ai/app/czirakim-f5-mcp-server)

# F5 MCP Server
[![smithery badge](https://smithery.ai/badge/@czirakim/F5.MCP.server)](https://smithery.ai/server/@czirakim/F5.MCP.server)

<img width="724" alt="image" src="https://github.com/user-attachments/assets/6bffb811-3e89-49fb-9d31-c7173afc9adc" />

This project is a **MCP (Model Context Protocol) server** that talks to F5 devices via the **iControl REST API**. It exposes tools for managing F5 TMOS (BIG-IP) objects (virtual servers, pools, profiles, etc.) and for applying **L4 standard settings** (DB and profiles) with optional before/after verification.

**For new users:** 접속 정보(mgmt IP·계정·비밀번호)는 도구 호출 시마다 **tmos_host**, **tmos_username**, **tmos_password** 로 입력합니다. MCP 클라이언트(예: Claude Desktop)를 이 서버에 연결한 뒤 [Documentation (Guides)](#documentation-guides)에서 플로우와 도구 사용법을 참고하세요.

## Running MCP on Windows and macOS

이 서버는 **Windows**와 **macOS** 모두에서 동작합니다.  
**설치·배포·실행 방법**은 **[DEPLOYMENT_AND_USAGE.md](DEPLOYMENT_AND_USAGE.md)** 를 참고하세요 (Python 설치, 의존성, .env, 터미널 실행, Claude Desktop 설정까지 단계별 안내).

## Features

- **Tool-Based API**: The project defines tools (`list_tool`, `create_tool`, `update_tool`, `delete_tool`, `apply_l4_standard_db_tool`, `apply_l4_standard_profiles_tool`, etc.) that encapsulate operations on F5 devices.
- **REST API Integration**: Uses Python's `requests` library to communicate with F5 devices via the iControl REST API.
- **Environment Configuration**: Sensitive information like IP addresses and authorization strings are managed through environment variables loaded from a `.env` file.
- **Extensibility**: Modular design allows additional tools or functionalities to be added easily.
- **Transport Support**: The server runs using the `stdio` transport, making it compatible with various client integrations.
- **Dockerfile**: If you want to run this as a Docker container

## Configuration — 접속 정보 (mgmt IP·계정·비밀번호)

**이 서버는 접속 정보를 파일이나 환경변수에 저장하지 않습니다.**  
모든 TMOS 도구 호출 시 **tmos_host**(관리 IP), **tmos_username**, **tmos_password** 를 **필수**로 입력하고, 필요 시 **tmos_port**(기본 443)를 입력합니다. Claude 등에서 도구를 쓸 때마다 사용자가 mgmt IP·계정·비밀번호를 넣으면 됩니다.

- **tmos_host**: F5 관리 IP (필수)
- **tmos_username** / **tmos_password**: 계정·비밀번호 (필수)
- **tmos_port**: 포트 (선택, 기본 443)

F5OS 도구는 별도 엔드포인트 타입으로, 필요 시 Claude Desktop MCP 설정의 `env` 등에서 지정할 수 있습니다.

## F5OS Standard Configuration

For **F5OS deployments**, there is a mandatory initialization step for backup encryption:

### Primary-Key Setup (Required)

The `f5os_init_aaa_primary_key_tool` sets the encryption key used for backup and configuration data protection.

**Step 1: Check current state**
```
f5os_check_aaa_primary_key_state_tool()
```

**Step 2: Set primary-key** (if not already set)
```
f5os_init_aaa_primary_key_tool(passphrase="YourPassphrase", salt="YourSalt")
```

**Step 3: Verify setup**
```
f5os_check_aaa_primary_key_state_tool()
```

**Requirements:**
- passphrase: 6-255 characters
- salt: 6-255 characters
- Store these values securely; they are needed for backup recovery

**CLI equivalent:**
```bash
appliance-1# show system aaa primary-key state status
appliance-1# config
appliance-1(config)# system aaa primary-key set passphrase
```

## TMOS: Basic Settings & L4 Standard (Templates)

For **TMOS (BIG-IP)** there are two template-style flows:

1. **Basic settings (기본 설정)** — "기본 설정 해줘"  
   `apply_basic_settings_tool(hostname=..., nameservers=..., ntp_servers=..., timezone=..., admin_password=..., root_password=..., syslog options...)`  
   Applies hostname, admin/root password, DNS, NTP (+ timezone), and syslog in one go. Only provided parameters are applied.

2. **L4 standard (L4 표준 설정)** — "L4 표준 설정 해줘" Use the **verification tools** first if you need an accurate before/after comparison.

### Basic Settings & Auth User

| Tool | Purpose |
|------|--------|
| `apply_basic_settings_tool(...)` | Apply device basic setup: hostname, admin/root password, DNS, NTP (+ timezone), syslog. Only provided parameters are applied. |
| `list_auth_users_tool()` | List auth users (accounts). |
| `create_auth_user_tool(name, password, partition_access=[{"name":"all-partitions","role":"admin"}], ...)` | Create auth user; use `role`: admin, operator, guest, manager. |
| `get_auth_user_tool(name)` | Get a single auth user. |
| `update_auth_user_tool(name, password=..., description=..., partition_access=..., shell=...)` | Update auth user (password, role, shell, etc.). |
| `delete_auth_user_tool(name)` | Delete auth user. |

| `list_devices_tool()` | List devices from devices.yaml / F5_DEVICES_FILE (name, host, port only). Use when using device_name / apply_to_all. |

### L4 Standard Tools

| Tool | Purpose |
|------|--------|
| `get_l4_standard_db_state_tool()` | Read **current device values** for sys_db (7 items) and ltm connection (3 items). Use this as **Before** when comparing. |
| `get_l4_standard_profiles_state_tool()` | Read **current device settings** for the 5 standard profiles (e.g. idleTimeout, pvaAcceleration). Use this as **Before** when comparing. |
| `apply_l4_standard_db_tool()` | Apply L4 standard sys db (7) + ltm connection (3). (setup.run is applied in basic settings.) |
| `apply_l4_standard_profiles_tool()` | Create or update standard profiles: HTTP_DEFAULT, TCP_DEFAULT, FL4_DEFAULT, FL4_UDP, clientssl_sni_default. |

### HA (이중화) Tools

| Tool | Purpose |
|------|--------|
| `get_ha_status_tool()` | HA 상태: cm devices, device groups, sync-status. |
| `apply_ha_tool(...)` | HA 일괄 적용 (Primary 연결 기준): device 설정 → add-to-trust → device group 생성 → device 추가 → config-sync. |
| `list_cm_devices_tool()` | cm device 목록 (configsyncIp, mirrorIp, failoverState 등). |
| `add_to_trust_tool(peer_device_ip, peer_device_name, peer_username, peer_password)` | 현재 장비에서 피어를 trust 도메인에 추가. |
| `create_device_group_tool(name, group_type)` | device group 생성 (sync-failover \| sync-only). |
| `add_device_to_group_tool(group_name, device_to_add)` | device group에 device 추가. |
| `run_config_sync_tool(group_name)` | config-sync to-group 실행. |

HA 상세 파라미터·플로우: **`F5_TMOS_STANDARD_CONFIG_GUIDE.md`** Section 3.

### Generic TMOS API Tools (모든 설정 생성/수정/삭제)

기본·표준 설정 **외** [F5 iControl REST API](https://clouddocs.f5.com/api/icontrol-rest/APIRef.html) 스펙의 **모든** 엔드포인트를 path로 호출해 자연어 요청을 처리할 수 있습니다.

| Tool | Purpose |
|------|--------|
| `tm_api_reference_tool()` | API 네임스페이스 요약 및 path 참고 (ltm, net, sys, cm, auth, gtm 등). |
| `tm_get_tool(path)` | GET — 컬렉션 또는 단일 리소스 조회. |
| `tm_post_tool(path, body)` | POST — 리소스 생성 또는 액션. |
| `tm_patch_tool(path, body)` | PATCH — 리소스 일부 수정. |
| `tm_put_tool(path, body)` | PUT — 리소스 전체 교체. |
| `tm_delete_tool(path)` | DELETE — 리소스 삭제. |

- **path**: tm 하위 경로 (예: `ltm/pool`, `ltm/pool/~Common~my_pool`, `net/vlan`, `sys/syslog`). 상세 스펙은 [APIRef](https://clouddocs.f5.com/api/icontrol-rest/APIRef.html) 참고.
- **body**: API 속성(camelCase). 각 리소스 페이지의 Properties 표 기준.

**list_tool / create_tool / update_tool / delete_tool / get_one_tool** 도 **resource_path**로 모든 리소스에 사용 가능 (LTM뿐 아니라 **net/vlan**, **net/self**, **ltm/pool** 등). 예: `list_tool(resource_path="net/vlan")`, `create_tool(resource_path="net/vlan", url_body={"name":"vlan100","tag":100})`, `delete_tool(resource_path="net/vlan", object_name="vlan100")`.  
상세: **`F5_TMOS_API_GENERIC_GUIDE.md`**.

### Recommended flow (with verification)

To get a correct **before/after** report (and avoid showing wrong "before" values like default 120 instead of actual device 300):

1. **Before** — Call `get_l4_standard_db_state_tool()` and/or `get_l4_standard_profiles_state_tool()` and save the result.
2. **Apply** — Call `apply_l4_standard_db_tool()` and/or `apply_l4_standard_profiles_tool()`.
3. **After** — Call the same get tool(s) again and compare with the saved Before.

Detailed basic settings (Section 0) and L4 DB/profile list (Section 1): **`F5_TMOS_STANDARD_CONFIG_GUIDE.md`**.

---

## Documentation (Guides)

| File | Description |
|------|-------------|
| **`README.md`** (this file) | Overview, configuration, quick reference. |
| **`DEPLOYMENT_AND_USAGE.md`** | **Windows / macOS 설치·배포·사용 가이드**: Python 설치, 의존성, .env, 터미널 실행, Claude Desktop 연동. |
| **`F5_TMOS_STANDARD_CONFIG_GUIDE.md`** | F5 TMOS standard process flow: basic settings (Section 0), L4 DB/Profile (Section 1), One-Arm, redundancy, VLAN/Self IP/Route, SNAT, profiles. Includes **verification flow** (Section 1.4). |
| **`TMOS_AI_AGENT_GUIDE.md`** | Full tool list (CRUD, auth user, basic/L4 standard, HA), usage examples, Claude Desktop setup, and AI agent behavior. |
| **`F5_TMOS_API_GENERIC_GUIDE.md`** | Generic TMOS API (tm_get/post/patch/put/delete): 모든 설정을 API path로 생성/수정/삭제, 자연어 매핑 예시. |
| **`CLAUDE_CACHE_AND_MCP.md`** | 코드 수정 후 Claude에서 같은 오류가 반복될 때: MCP 재시작 및 설정 확인 절차. |
| **`DEVELOPMENT_GUIDELINES.md`** | 코드 수정 시 참고하는 개발 가이드라인. 코드 리뷰 체크리스트, 문서 규칙, 코드 스타일. |

New users: **설치·실행**은 `DEPLOYMENT_AND_USAGE.md`, **설정 플로우**는 `F5_TMOS_STANDARD_CONFIG_GUIDE.md`, **도구 사용법**은 `TMOS_AI_AGENT_GUIDE.md`를 참고하세요. 코드 수정 후 Claude가 이전처럼 동작하면 **`CLAUDE_CACHE_AND_MCP.md`** (MCP 재시작·설정 확인)를 참고하세요.

---

### Key Files

- **`F5MCPserver.py`**: The main server file that initializes the MCP server and defines the tools.
- **`Tools/F5object.py`**: A utility class for performing CRUD operations on F5 objects.

The repo also contains an example of the Claude desktop app config file.  
Only `F5object.py` is used from the Tools folder. The others were used in development.

**Commit after changes:** With **f5-mcp** open as your project folder, run **`./scripts/commit-if-changes.sh "무엇을 수정했는지 설명"`** (meaningful message required).

### `It was tested with the Claude Desktop app. The MCP server was hosted in Windows WSL.`


<img width="362" alt="image" src="https://github.com/user-attachments/assets/06ac07e0-2ab7-4675-8c7b-c3809bc364ad" />

### Installing via Smithery

To install F5 Device Management Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@czirakim/F5.MCP.server):

```bash
npx -y @smithery/cli install @czirakim/F5.MCP.server --client claude
```


### Credits
This was written by Mihai Cziraki
