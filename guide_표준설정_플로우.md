# F5 TMOS 표준 설정 프로세스 플로우

## 개요

이 문서는 **구성/구축 미팅에서 정리한 표준**을 기준으로, 자연어로 요청 시 F5 TMOS를 자동 설정하는 AI Agent용 **프로세스 플로우와 필수 파라미터**를 정의합니다.  
MCP 툴을 사용하는 다른 사용자도 이 가이드만 따라 하면 표준 설정 흐름을 적용할 수 있습니다.

**문서 구조**
- **Section 0**: 장비 기본 설정 (템플릿) — hostname, admin/root 비밀번호, DNS, NTP, syslog
- **Section 1**: L4 표준 설정 (DB 7개 + connection 3개, 프로파일 5개 — setup.run은 기본 설정에서 적용) — 적용 방법 및 **적용 전/후 검증 절차**
- **Section 2–7**: One-Arm, 이중화, VLAN/Self IP/Route, SNAT, Profile, Virtual Server & Pool — 프로세스 플로우와 필수 파라미터

**다중 장비·계정 유동 관리**  
- **장비 목록 파일**: `devices.yaml`(또는 `F5_DEVICES_FILE` 경로)에 IP·계정을 두고, 소스 수정 없이 이 파일만 수정해 사용 가능. 도구에 `device_name`, `device_index`, `apply_to_all` 로 대상 지정.  
- **요청 단위 지정**: 모든 툴은 선택 인자 `tmos_host`, `tmos_port`, `tmos_username`, `tmos_password` 를 받으며, 넘기면 해당 호출만 그 연결로 수행.

---

## 0. 장비 기본 설정 (템플릿)

"**기본 설정 해줘**" 요청 시 사용하는 템플릿이다. 장비 초기화 시 hostname, admin/root 비밀번호, DNS, NTP(+timezone), syslog를 한 번에 적용할 수 있다.

### 0.1 적용 항목

| 항목 | 설명 | MCP 툴 개별 설정 |
|------|------|------------------|
| 초기 세팅 | password-policy 비활성화, setup.run false (초기 UI 설정 마법사 제거) | apply_basic_settings_tool 시작 시 자동 |
| hostname | 호스트명 | set_hostname_tool |
| admin 비밀번호 | admin 계정 비밀번호 | (apply_basic_settings_tool 내부) |
| root 비밀번호 | root 계정 비밀번호 | (apply_basic_settings_tool 내부) |
| DNS | nameservers | set_dns_tool |
| NTP | servers, timezone | set_ntp_tool |
| Syslog | **원격 목적지** syslog_destination(예: 192.168.47.81:514), 또는 consoleLog/authPrivFrom·To 등 레벨 | set_syslog_tool / apply_basic_settings_tool(syslog_destination=...) |
| Syslog via mgmt | mgmt 포트로 syslog 통신 시 **management route** 필요 | syslog_via_mgmt=True, management_route_gateway 등 (apply_basic_settings_tool) |

### 0.2 적용 순서 (내부 동작)

1. **맨 처음 (초기 세팅)**  
   - `tmsh modify auth password-policy policy-enforcement disabled` → 비밀번호 정책(복잡도) 비활성화.  
   - `tmsh modify sys db setup.run value false` → 초기 UI 설정 마법사 제거.  
   위 두 가지를 먼저 수행한 뒤 아래 순서로 진행.
2. **이후**: hostname → dns → ntp 순으로 적용.
3. **Syslog 전에 (선택)**: **mgmt 포트로 syslog 통신**할 경우 `syslog_via_mgmt=True` 및 `management_route_gateway` 를 주면, syslog 설정 직전에 **management route** 추가 (tmsh: sys management-route).
4. **Syslog**: 원격 목적지(syslog_destination, 예: 192.168.47.81:514) 설정 및/또는 consoleLog, authPrivFrom/To 등 레벨 적용.
5. **맨 마지막**: admin 비밀번호 → root 비밀번호 변경. (중간에 비밀번호를 바꾸면 API가 기존 인증을 쓰므로 이후 호출에서 401이 날 수 있음.)

### 0.3 MCP에서 적용

- **한 번에 적용**: `apply_basic_settings_tool(hostname=..., nameservers=..., ntp_servers=..., timezone=..., admin_password=..., root_password=..., ...)`  
  넘긴 인자만 적용되며, 생략한 항목은 건너뛴다. **hostname, nameservers, ntp_servers, syslog, admin_password, root_password 를 하나도 넘기지 않으면** 툴은 적용하지 않고 `action: "ask_user"` 와 `missing_required` 를 반환한다. AI는 값을 임의로 넣지 말고, 사용자에게 물어본 뒤 받은 값만 넘길 것.
- **Syslog를 mgmt 포트로 보낼 때**: `syslog_via_mgmt=True`, `management_route_gateway="<mgmt 게이트웨이 IP>"` (필수), `management_route_network="default"` (또는 syslog 서버 대역), `management_route_name="syslog_mgmt_route"` (선택) 를 함께 넘기면 syslog 설정 직전에 management route가 추가됨.
- 예: "기본 설정 해줘. hostname f5-01, DNS 8.8.8.8, NTP time.google.com, timezone Asia/Seoul, admin 비밀번호 변경해줘" → AI가 해당 인자만 넣어서 `apply_basic_settings_tool` 호출.
- 예: "기본 설정에서 syslog는 mgmt로 보낼 거야. mgmt 게이트웨이 192.168.1.1로 route 추가해줘" → `apply_basic_settings_tool(..., syslog_via_mgmt=True, management_route_gateway="192.168.1.1", auth_priv_from="warning", ...)` 등.
- **구조화된 입력**: `config_templates.yaml`과 `guide_YAML_템플릿_사용법.md`를 참고해 YAML로 항목을 채운 뒤, 해당 값을 도구 인자로 넘겨 적용할 수 있다.

---

## 1. L4 표준 설정 (DB 및 Profile)

L4 표준 구성 시 적용하는 sys db, ltm connection, 프로파일을 MCP에서 일괄 적용할 수 있다.

### 1.1 L4 표준 DB 설정 목록

**sys db (7개)** — 각 항목 `tmsh modify sys db <key> value <value>`에 대응.  
(`setup.run` 은 **기본 설정(0장)** 에서 초기 세팅 시 함께 적용됨.)

| key | value |
|-----|--------|
| ui.system.preferences.recordsperscreen | 100 |
| ui.system.preferences.advancedselection | advanced |
| tm.fastl4_ack_mirror | disable |
| pvasyncookies.enabled | false |
| tm.dupsynenforce | disable |
| tm.monitorencap | enable |
| bigd.mgmtroutecheck | enable |

**ltm global-settings connection (3개)** — SYN cookie 관련 전역 비활성화

- globalSynChallengeThreshold: 0
- defaultVsSynChallengeThreshold: 0
- vlanSynCookie: disabled

### 1.2 L4 표준 Profile 목록 (5개)

| 이름 | 타입 | 설명 |
|------|------|------|
| HTTP_DEFAULT | http | defaults-from http |
| TCP_DEFAULT | tcp | f5-tcp-progressive, hardware/syn-cookie disabled |
| FL4_DEFAULT | fastl4 | loose-close/init, pva none, syn-cookie disabled |
| FL4_UDP | fastl4 | idle-timeout 5, pva none |
| clientssl_sni_default | client-ssl | sni-default true |

### 1.3 MCP에서 적용

- **L4 표준 DB 적용**: `apply_l4_standard_db_tool()` 호출 (인자 없음)
- **L4 표준 Profile 적용**: `apply_l4_standard_profiles_tool()` 호출 (인자 없음)

AI Agent 또는 사용자가 위 두 툴을 순서대로 호출하면 L4 표준 DB 설정과 표준 프로파일이 일괄 적용된다.

### 1.4 적용 전/후 검증 (자체 검증)

비교 보고 시 **반드시 장비 실제값을 조회**해 사용해야 한다. 기본값이나 추정값을 쓰면 잘못된 전/후 비교가 나온다.

**금지 사항 (AI Agent·사용자 공통)**  
- **툴 실행 결과에 없는 값은 절대 임의로 채우지 말 것.**  
- "표준값", "이전에 수동으로 썼던 값", "일반적인 기본값" 등을 비교표에 넣지 말 것.  
- MCP 툴 내부 정의를 추측해서 Before/After를 채우지 말 것.  

**올바른 절차**  
1. **적용 전 (Before)** — `get_l4_standard_db_state_tool()` / `get_l4_standard_profiles_state_tool()` 호출 후, **반환된 JSON 값만** Before로 저장.  
2. **적용** — `apply_l4_standard_db_tool()` / `apply_l4_standard_profiles_tool()` 실행.  
3. **적용 후 (After)** — 같은 get 툴을 **다시 호출**한 뒤, **반환된 값만** After로 사용.  
4. **비교표** — 위 1·3에서 **툴이 반환한 실제 값만** 사용해 표시.  

툴 상세 사용법·파라미터는 `guide_도구_사용법.md`의 MCP Tools 섹션을 참고하면 된다.

---

## 2. One-Arm 로드밸런싱 구성

### 프로세스 플로우
```
One-Arm 요청 
  → VLAN 생성 
  → Self IP 설정 
  → Route 설정 
  → SNAT Pool 설정 
  → Virtual Server/Pool 생성
```

### 필수 파라미터
```json
{
  "vlan": {
    "name": "string (예: vlan100)",
    "vlan_id": "integer (1-4094)",
    "interfaces": ["string (예: 1.1, 1.2)"]
  },
  "self_ip": {
    "name": "string",
    "address": "string (예: 10.10.10.100/24)",
    "vlan": "string"
  },
  "route": [
    {
      "name": "string",
      "network": "string (예: 0.0.0.0/0)",
      "gateway": "string"
    }
  ],
  "snat_pool": {
    "name": "string",
    "addresses": ["string (예: 10.10.10.200-10.10.10.210)"]
  },
  "virtual_server": {
    "name": "string",
    "description": "string",
    "destination": "string (예: 10.10.10.50:80)",
    "pool": "string",
    "snat": "string (snat pool name)"
  },
  "pool": {
    "name": "string",
    "members": ["string (예: 192.168.1.10:80)"],
    "monitor": "string (예: http)"
  }
}
```

### 자동 생성 로직
1. **VLAN 검증**: 중복 확인, 포트 조회
2. **Self IP 검증**: VLAN 존재 여부, IP 충돌 확인
3. **Route 검증**: Gateway IP 유효성, 기본 라우트 확인
4. **SNAT Pool 검증**: IP 범위 유효성
5. **Virtual Server**: 리소스 의존성 확인 후 생성
6. **Pool**: Member 수 권장값 확인 (최소 2개)

---

## 3. 이중화(Redundancy) 구성

### 프로세스 플로우
```
이중화 요청 
  → Primary/Secondary device 설정 (configsyncIp, mirrorIp, unicastAddress)
  → add-to-trust (Secondary를 Primary에서 trust 도메인에 추가)
  → Device Group 생성 (sync-failover | sync-only)
  → 두 device를 group에 추가
  → config-sync to-group 실행
  → HA Status 확인
```

### 3.1 MCP에서 HA 적용

**일괄 적용 (권장)**  
- `apply_ha_tool(...)`: 현재 연결을 **Primary**로 사용해 위 단계를 한 번에 수행.  
  - **필수 인자**: `group_name`, `group_type`(sync-failover|sync-only), `primary_hostname`, `primary_configsync_ip`, `primary_mirror_ip`, `primary_unicast`, `secondary_device_ip`, `secondary_device_name`, `secondary_username`, `secondary_password`, `secondary_configsync_ip`, `secondary_mirror_ip`, `secondary_unicast`.  
  - `primary_unicast` / `secondary_unicast`: failover 통신용 리스트, 예: `[{"ip": "10.0.0.1", "port": 1026}]`.  
  - Primary에 연결할 때는 `tmos_host`(Primary mgmt IP), `tmos_username`, `tmos_password` 로 호출.

**단계별 도구**  
- `list_cm_devices_tool()`: cm device 목록 (hostname, configsyncIp, mirrorIp, failoverState).  
- `add_to_trust_tool(peer_device_ip, peer_device_name, peer_username, peer_password)`: 현재 장비에서 피어를 trust에 추가.  
- `create_device_group_tool(name, group_type)`: device group 생성.  
- `add_device_to_group_tool(group_name, device_to_add)`: group에 device(호스트명) 추가.  
- `run_config_sync_tool(group_name)`: config-sync to-group 실행.  
- `get_ha_status_tool()`: devices, device_groups, sync_status 조회.

### 필수 파라미터 (apply_ha_tool 기준)
| 구분 | 항목 | 설명 |
|------|------|------|
| Primary | primary_hostname | Primary 호스트명 (cm device 이름) |
| | primary_configsync_ip | Config Sync용 IP |
| | primary_mirror_ip | State Mirror용 IP |
| | primary_unicast | [{"ip":"x.x.x.x","port":1026}] failover 통신 |
| Secondary | secondary_device_ip | Secondary mgmt IP |
| | secondary_device_name | Secondary 호스트명 |
| | secondary_username, secondary_password | Secondary API 계정 |
| | secondary_configsync_ip, secondary_mirror_ip, secondary_unicast | 동일 형식 |
| Group | group_name | device group 이름 |
| | group_type | sync-failover 또는 sync-only |

### 자동 생성 로직
1. **Primary CM device 이름**: list_cm_devices로 selfDevice 확인 후 실제 device 이름(bigip1 등) 사용. (1호기 device 이름이 다를 수 있음)
2. **Primary/Secondary device**: configsyncIp, mirrorIp, unicastAddress PATCH.
3. **add-to-trust**: Primary에서 Secondary를 trust 도메인에 추가. **REST API를 먼저 시도**하고, 403(Forbidden)일 때만 TMSH bash로 폴백. 반환은 항상 `{ok: true|false, method: "REST"|"TMSH_fallback", ...}` 형태로 정규화되어 성공/실패를 명확히 판단할 수 있음.
4. **Device Group**: 생성 시 기본 적용 — **Save on Automatic Sync**(saveOnAutoSync), **Automatic with Incremental Sync**(autoSync=enabled, fullLoadOnSync=false).
5. 두 device를 group에 추가 후 **config-sync** to-group 실행.
6. **HA 상태**: `get_ha_status_tool()`로 Sync 상태 확인.

---

## 4. VLAN, Self IP, Route 상세 설정

### 3.1 VLAN 생성
```
목표: 네트워크 세분화 및 트래픽 격리

필수:
- name: VLAN 이름 (예: mgmt_vlan)
- vlan_id: 1-4094 범위
- interfaces: 물리 포트 (1.1 형식)

선택:
- description: 설명
- tagged: Tagged/Untagged 설정
```

### 3.2 Self IP 설정
```
목표: F5 자신의 IP 주소 할당

필수:
- name: Self IP 이름
- address: IP/CIDR (예: 10.10.10.100/24)
- vlan: Self IP가 속한 VLAN

선택:
- allow_service: HTTPS, SSH 등 서비스 포트
- description: 설명
```

### 3.3 라우팅 설정
```
목표: 트래픽 경로 지정

필수:
- name: 라우트 이름
- network: 대상 네트워크 (CIDR)
- gateway: 게이트웨이 IP

선택:
- mtu: MTU 값
- metric: 라우트 우선순위
```

---

## 5. SNAT Pool 설정

### 프로세스 플로우
```
SNAT 구성 요청 
  → SNAT Pool 생성 
  → IP 범위 검증 
  → Virtual Server에 적용
```

### 필수 파라미터
```json
{
  "snat_pool": {
    "name": "string",
    "addresses": [
      "10.10.10.200-10.10.10.210",
      "10.10.10.220"
    ]
  }
}
```

### 자동 생성 로직
1. **IP 범위 검증**: Overlapping 확인
2. **주소 포맷**: 단일 IP 또는 범위 지원
3. **Virtual Server 연결**: SNAT 적용 확인

---

## 6. Profile 설정

### 5.1 HTTP Profile
```json
{
  "profile_http": {
    "name": "string",
    "defaults_from": "http",
    "redirect_rewrite": "none|requests|all",
    "compression": "enabled|disabled",
    "compression_content_type_include": [
      "text/",
      "application/json"
    ]
  }
}
```

### 5.2 TCP Profile
```json
{
  "profile_tcp": {
    "name": "string",
    "defaults_from": "tcp",
    "idle_timeout": "integer",
    "send_buffer_size": "integer",
    "receive_buffer_size": "integer"
  }
}
```

### 5.3 Client SSL Profile
```json
{
  "profile_clientssl": {
    "name": "string",
    "cert": "string (인증서 이름)",
    "key": "string (키 이름)",
    "ciphers": "DEFAULT",
    "ciphers_suite": "HIGH:!aNULL:!eNULL"
  }
}
```

---

## 7. Virtual Server & Pool 생성

### Virtual Server
```json
{
  "virtual_server": {
    "name": "string",
    "destination": "string (IP:Port)",
    "pool": "string (Pool 이름)",
    "profiles": {
      "http": "string",
      "tcp": "string"
    },
    "description": "string",
    "enabled": "true|false"
  }
}
```

### Pool
```json
{
  "pool": {
    "name": "string",
    "pool_members": [
      {
        "node": "string (IP 주소)",
        "port": "integer"
      }
    ],
    "monitor": "string (모니터 이름)",
    "description": "string"
  }
}
```

---

## AI 자동 설정 로직

### 입력 예시
```
"One-arm 로드밸런싱 구성하려고 해. 
VLAN 100, 
Self IP 10.10.10.100/24, 
게이트웨이 10.10.10.1, 
SNAT 10.10.10.200-210, 
Virtual Server 10.10.10.50:80, 
Backend서버 192.168.1.10:80"
```

### AI Agent 처리 절차
1. **입력 파싱**: 자연어 → 구조화된 파라미터 추출
2. **검증**: 필수 파라미터 확인, 충돌 검사
3. **순서 정렬**: 의존성 기반 생성 순서 결정
   ```
   VLAN → Self IP → Route → SNAT Pool 
   → Pool/Monitor → Virtual Server
   ```
4. **생성**: 각 단계별 MCP Tool 호출
5. **검증**: 생성 결과 확인
6. **보고**: 완료 상태 및 설정 정보 반환

### 의존성 매트릭스
```
Virtual Server
  ├─ Pool (필수)
  │  └─ Pool Members (필수)
  ├─ Profiles (선택)
  │  └─ HTTP, TCP, SSL 등
  └─ SNAT Pool (선택)

Self IP
  └─ VLAN (필수)

Route
  └─ Gateway IP 유효성

Pool
  └─ Monitor (권장)
```

---

## 설정 백업 및 검증

### 백업 프로세스
```
구성 변경 → 자동 백업 생성 
  → UCS (Unified Configuration Set) 파일 생성
```

### 검증 프로세스
```
설정 완료 
  → Health Check 실행 (sys/version 호출)
  → Virtual Server 상태 확인
  → Pool Member 상태 확인 (UP/DOWN)
  → 트래픽 흐름 테스트 (선택)
```

---

## 에러 처리 및 롤백

### 에러 분류
1. **검증 에러**: 입력값 오류 → 수정 후 재시도
2. **의존성 에러**: 필수 리소스 없음 → 자동 생성
3. **네트워크 에러**: 장비 접속 불가 → 재시도
4. **설정 에러**: API 호출 실패 → 로그 확인

### 롤백 전략
```
실패 검출 
  → 생성된 리소스 목록 추적
  → 역순으로 삭제 (Virtual Server → Pool → VLAN)
  → 이전 백업에서 복구 (선택)
```

---

## 권장 설정값

| 항목 | 권장값 | 범위 |
|------|--------|------|
| Pool Member 수 | 2+ | 1+ |
| TCP Idle Timeout | 300s | 0-31680000 |
| HTTP Compression | Enabled | - |
| VLAN ID | 100-2000 | 1-4094 |
| Self IP 수 | 1+ | 1+ |
| SNAT 주소 수 | Pool Members와 동일 | 1+ |

---

## 다음 단계

1. ✅ TMOS Tool 구현 (show_stats, list, create, update, delete, health_check)
2. 🔄 AI Agent 프롬프트 엔지니어링
3. 🔄 자동 파라미터 추출 로직 구현
4. 🔄 설정 순서 자동 결정 엔진
5. 🔄 에러 처리 및 롤백 로직
6. 🔄 설정 검증 및 건강성 체크
7. 🔄 설정 이력 관리 및 감사

