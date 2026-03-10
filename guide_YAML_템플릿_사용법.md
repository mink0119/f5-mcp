# YAML 템플릿 사용법

`config_templates.yaml`의 각 섹션 설명과, 어떤 MCP 도구로 적용하는지 정리합니다.  
**사용할 기능만 해당 섹션을 채우면 됩니다.**  
YAML을 채운 뒤 LLM/앱이 이 값을 읽어 `create_tool`, `tm_post_tool`, `apply_basic_settings_tool` 등에 인자로 넘기면 됩니다.

---

## connection (공통)

모든 도구 호출 시 필요한 F5 접속 정보.

| 키 | 타입 | 설명 |
|----|------|------|
| tmos_host | 문자열 | F5 관리 IP |
| tmos_port | 정수 | 기본 443 |
| tmos_username | 문자열 | 관리자 계정 |
| tmos_password | 문자열 | 비밀번호 |

**MCP**: 모든 도구의 인자 `tmos_host`, `tmos_port`, `tmos_username`, `tmos_password`로 전달.

---

## 1. basic_settings (기본 설정)

**도구**: `apply_basic_settings_tool`

- **syslog**: **destination(목적지)** 가 핵심. 예: `192.168.47.81:514`.  
  - YAML: `syslog_destination: "192.168.47.81:514"`  
  - 레벨(consoleLog, authPrivFrom 등)은 선택: `syslog_levels`에 넣거나 생략.
- **apply_only_keys**: 적용할 항목만 나열. 필수.
- mgmt 포트로 syslog 보낼 때: `syslog_via_mgmt: true`, `management_route_gateway` 설정.

| 키 | 타입 | 설명 |
|----|------|------|
| apply_only_keys | 리스트 | hostname, nameservers, ntp_servers, timezone, admin_password, root_password, syslog 중 적용할 것만 |
| hostname | 문자열 | 호스트명(FQDN) |
| nameservers | 리스트 | DNS 서버 IP |
| ntp_servers | 리스트 | NTP 서버 |
| timezone | 문자열 | 예: Asia/Seoul |
| admin_password, root_password | 문자열 | 비밀번호 |
| syslog_destination | 문자열 | Syslog 서버 주소:포트 (예: 192.168.47.81:514) |
| syslog_levels | 객체 | 선택. consoleLog, authPrivFrom 등 |

---

## 2. vlan (VLAN)

**도구**: `create_tool(resource_path="net/vlan", url_body=...)` 또는 `tm_post_tool(path="net/vlan", body=...)`

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | VLAN 이름 (예: vlan100) |
| tag | 정수 | 1–4094 |
| interfaces | 문자열 | 예: "1.1" (또는 API에 따라 리스트) |

---

## 3. self_ip (Self IP)

**도구**: `create_tool(resource_path="net/self", url_body=...)`

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | Self IP 이름 |
| address | 문자열 | IP/CIDR (예: 10.10.10.100/24) |
| vlan | 문자열 | VLAN 이름 |
| allowService | 문자열 | 기본 "default" |

---

## 4. route (라우트)

**도구**: `create_tool(resource_path="net/route", url_body=...)`

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | 라우트 이름 |
| network | 문자열 | 대상 네트워크 (예: 0.0.0.0/0) |
| gw | 문자열 | 게이트웨이 IP |

---

## 5. snat_pool (SNAT Pool)

**도구**: `create_tool(resource_path="ltm/snatpool", url_body=...)`

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | SNAT pool 이름 |
| members | 리스트 | IP 또는 범위 (예: "10.10.10.200-10.10.10.210") |

---

## 6. pool (풀)

**도구**: `create_tool(resource_path="ltm/pool", url_body=...)`

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | 풀 이름 |
| loadBalancingMode | 문자열 | round-robin, least-connections-node 등 |
| monitors | 리스트 | 모니터 경로 (예: ["/Common/http"]) |
| members | 리스트 | 멤버 객체. name: "IP:port" 형식 |

---

## 7. virtual_server (가상 서버)

**도구**: `create_tool(resource_path="ltm/virtual", url_body=...)`

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | 가상 서버 이름 |
| destination | 문자열 | 예: 10.10.10.50:80 |
| pool | 문자열 | 풀 이름 |
| sourceAddressTranslation | 객체 | type: snat, pool: snat_pool 이름 |
| ipProtocol | 문자열 | tcp |
| profiles | 리스트 | { name, context } |

---

## 8. monitor (모니터)

**도구**: `create_tool(resource_path="ltm/monitor/{type}", url_body=...)`  
**type**: http, tcp, https, icmp, udp 등.

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | 모니터 이름 |
| send | 문자열 | (http/https) 전송 문자열. 예: "GET /\\r\\n" |
| receive | 문자열 | 수신 기대 문자열 |
| interval | 정수 | 간격(초) |
| timeout | 정수 | 타임아웃(초) |
| partition | 문자열 | Common |

---

## 9. profile (프로파일)

**도구**: `create_tool(resource_path="ltm/profile/{type}", url_body=...)`  
**type**: http, tcp, client-ssl, server-ssl, fastl4 등.

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | 프로파일 이름 |
| defaultsFrom | 문자열 | 상속 기본 프로파일 (예: /Common/http) |
| idleTimeout | 정수 | (http/tcp/fastl4) 유휴 타임아웃 |
| ciphers | 문자열 | (client-ssl) cipher 문자열. 예: DEFAULT |
| partition | 문자열 | Common |

---

## 10. policy (정책)

**도구**: `create_tool(resource_path="ltm/policy", url_body=...)`

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | 정책 이름 |
| strategy | 문자열 | 예: /Common/first-match |
| rules | 리스트 | rule 객체. ordinal, conditions, actions |

**rules** 내 rule: `name`, `ordinal`, `conditions`(조건 목록), `actions`(동작 목록).  
F5 API 스펙에 맞게 conditions/actions 구조는 clouddocs APIRef 참고.

---

## 11. irule (iRule)

**도구**: `create_tool(resource_path="ltm/rule", url_body=...)`

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | iRule 이름 |
| apiAnonymous | 문자열 | TCL 스크립트 본문 (여러 줄 가능) |

또는 `apiRawLineValues` 등 API 스펙에 맞게 사용.

---

## 12. data_group (데이터 그룹)

**도구**: `create_tool(resource_path="ltm/data-group/internal", url_body=...)` 또는 `ltm/data-group/external`

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | 데이터 그룹 이름 |
| type | 문자열 | string, ip, integer 등 |
| records | 리스트 | { name, data } 또는 external 시 filename 등 |
| partition | 문자열 | Common |

---

## 13. cipher (Cipher)

**도구**: client-ssl 프로파일 생성/수정 시 `create_tool(resource_path="ltm/profile/client-ssl", url_body=...)` 또는 `update_tool`에서 **ciphers** 또는 **cipherGroup** 필드로 지정.

- **ciphers**: cipher 문자열 (예: DEFAULT, HIGH:!aNULL:!eNULL).
- **cipherGroup**: 기존 cipher 그룹 경로 (예: /Common/f5-default).

YAML에는 `cipher_example`처럼 ciphers/cipherGroup 예시만 두고, 실제로는 profile_client_ssl 섹션에 ciphers를 넣어 사용.

---

## 14. ha (이중화)

**도구**: `apply_ha_tool(...)`

Primary/Secondary 호스트명, configsync IP, mirror IP, unicast 리스트, device group 이름·타입 등.  
자세한 필드는 `guide_표준설정_플로우.md` Section 3 참고.

---

## 15. auth_user (계정)

**도구**: `create_auth_user_tool`

| 키 | 타입 | 설명 |
|----|------|------|
| name | 문자열 | 사용자명 |
| password | 문자열 | 비밀번호 |
| partition_access | 리스트 | [{ name: "all-partitions", role: "admin" }] |
| shell | 문자열 | bash 등 |

---

## 16. management_route (Management Route)

**도구**: `add_management_route_tool`

syslog를 mgmt 포트로 보낼 때 등. name, network, gateway, description.

---

## 17. dns (DNS만)

**도구**: `set_dns_tool`  
nameservers 리스트만 사용.

---

## 18. ntp (NTP만)

**도구**: `set_ntp_tool`  
servers, timezone.

---

## 19. l4_standard (L4 표준)

**도구**: `apply_l4_standard_db_tool`, `apply_l4_standard_profiles_tool`  
인자 없이 호출만 하면 됨. YAML에는 `l4_standard: {}`로 두고, “이 섹션이 있으면 L4 표준 적용”으로 사용.
