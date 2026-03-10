# F5 TMOS AI Agent 구축 - 최종 완성 가이드

이 문서는 MCP 서버에 등록된 **툴 목록·사용법·예시**와 Claude Desktop 연동 방법을 정리한 가이드입니다.  
배포 후 다른 사용자도 이 문서와 `guide_표준설정_플로우.md`만 보면 설정 흐름과 툴 호출 순서를 따라 할 수 있습니다.

## 📋 현재 상태

### 완료된 항목 ✅
- [x] TMOS 전용 MCP 서버 구현
- [x] 17개 TMOS 도구 (show_stats, show_logs, list, create, update, delete, health_check, auth user 5종, apply_basic_settings, apply_l4_standard_*, get_l4_standard_*)
- [x] F5 표준 설정 프로세스 플로우 문서화
- [x] AI Agent 시스템 프롬프트 작성
- [x] One-Arm 로드밸런싱 설정 가이드
- [x] 이중화(Redundancy) 설정 가이드
- [x] 자동 파라미터 추출 로직 정의
- [x] 의존성 관리 전략 정의
- [x] 에러 처리 전략 정의

---

## 🚀 빠른 시작

### 1. 환경 변수 설정 (.env)

```bash
# TMOS 장비 접속 정보 (필수)
TMOS_HOST=192.168.47.55      # F5 TMOS 관리 IP
TMOS_PORT=443                 # 기본값
TMOS_AUTH_BASIC_B64=YWRtaW46YWRtaW4=    # Base64 인코딩된 인증정보 (admin:admin)
TMOS_VERIFY_TLS=false         # 테스트 환경에서는 false
TMOS_TIMEOUT_SECONDS=20       # 타임아웃
```

### 2. Claude Desktop 설정 업데이트

```bash
# ~/.zshrc 또는 ~/.bash_profile에 추가
export TMOS_HOST=192.168.47.55
export TMOS_AUTH_BASIC_B64=YWRtaW46YWRtaW4=
```

또는 직접 수정:
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "f5_tmos_ai_agent": {
      "command": "/bin/bash",
      "args": ["-c", "/Users/minkyu/Downloads/2.git/f5-mcp/mamba-env/bin/python /Users/minkyu/Downloads/2.git/f5-mcp/F5MCPserver.py"]
    }
  }
}
```

### 3. Claude Desktop 재시작

```bash
killall -9 Claude
open -a "Claude"
```

---

## 💬 AI Agent 사용 방법

### 예시 1: One-Arm 로드밸런싱 자동 구성

**입력:**
```
"One-arm 로드밸런싱을 구성해 줄 수 있어?
VLAN: 100
Self IP: 10.10.10.100/24
게이트웨이: 10.10.10.1
SNAT Pool: 10.10.10.200-210
Virtual Server: 10.10.10.50:80
Backend 서버: 192.168.1.10:80, 192.168.1.11:80"
```

**AI Agent가 이렇게 처리:**
```
1️⃣ 입력 분석
   ✅ VLAN 설정: vlan100 (ID: 100)
   ✅ Self IP: 10.10.10.100/24
   ✅ 라우트: 0.0.0.0/0 → 10.10.10.1
   ✅ SNAT Pool: 10.10.10.200-210
   ✅ Virtual Server: 10.10.10.50:80
   ✅ Pool Members: 2개

2️⃣ 의존성 계획
   → VLAN 생성 (먼저)
   → Self IP 설정 (VLAN에 의존)
   → Route 생성 (네트워크 설정용)
   → SNAT Pool 생성
   → Pool 및 Monitor 생성
   → Virtual Server 생성 (마지막)

3️⃣ 자동 실행
   🟢 VLAN vlan100 생성 완료
   🟢 Self IP 10.10.10.100 설정 완료
   🟢 Route 0.0.0.0/0 생성 완료
   🟢 SNAT Pool 생성 완료
   🟢 Pool pool_http_1 생성 완료 (Members: 2개)
   🟢 HTTP Monitor 설정 완료
   🟢 Virtual Server vs_http_80 생성 완료

4️⃣ 검증 완료
   ✅ Health Check: PASSED
   ✅ Pool Member 상태: 2/2 UP
   ✅ Virtual Server: ENABLED

설정이 완료되었습니다! 🎉
```

### 예시 2: 기존 리소스에 새로운 Virtual Server 추가

**입력:**
```
"이미 생성된 pool_http_1을 사용해서 
VSname: vs_http_8080, 
주소: 10.10.10.50:8080 의 Virtual Server를 추가해 줄래"
```

**AI Agent가 이렇게 처리:**
```
1️⃣ 리소스 검증
   ✅ pool_http_1 존재 확인

2️⃣ Virtual Server 생성
   🟢 vs_http_8080 생성 완료
   🟢 Destination: 10.10.10.50:8080
   🟢 Pool: pool_http_1

설정 완료!
```

### 예시 3: 부분 정보 제공 시 자동 제안

**입력:**
```
"VLAN 하나 만들어 줄래"
```

**AI Agent가 이렇게 응답:**
```
VLAN을 생성하려면 다음 정보가 필요합니다:

📋 필수 정보:
1. VLAN ID? (예: 100, 범위: 1-4094)
2. 물리 인터페이스? (예: 1.1, 1.2)

📋 선택 정보:
- VLAN 이름? (생략하면 vlan{id}로 자동 생성)
- 설명?

💡 자동 생성으로 처리할까요?
   - VLAN ID: 100
   - Interface: 1.1
   - Name: vlan100
```

---

## 🛠️ MCP Tools (17개)

### 1. show_stats_tool
**목적:** F5 리소스의 통계 정보 조회

```
파라미터:
- object_name: 리소스 이름 (예: pool1, vs1)
- object_type: 리소스 유형 (virtual, pool, irule, profile)

예시:
show_stats_tool(object_name="pool_http_1", object_type="pool")
```

### 2. show_logs_tool
**목적:** F5의 로그 조회

```
파라미터:
- lines_number: 반환할 로그 라인 수 (예: 100)

예시:
show_logs_tool(lines_number="100")
```

### 3. list_tool
**목적:** F5 리소스 목록 조회

```
파라미터:
- object_type: 리소스 유형 (virtual, pool, vlan, etc)
- object_name: 필터링 이름 (선택)

예시:
list_tool(object_type="pool", object_name="")
```

### 4. create_tool
**목적:** 새로운 F5 리소스 생성

```
파라미터:
- object_type: 생성할 리소스 유형 (virtual, pool)
- url_body: 설정 JSON (예시 아래)

예시:
create_tool(
  object_type="pool",
  url_body={
    "name": "pool_http_1",
    "members": [
      {"address": "192.168.1.10", "port": 80},
      {"address": "192.168.1.11", "port": 80}
    ],
    "monitor": "http"
  }
)
```

### 5. update_tool
**목적:** 기존 리소스 수정

```
파라미터:
- object_type: 리소스 유형
- object_name: 수정할 리소스 이름
- url_body: 수정할 설정

예시:
update_tool(
  object_type="pool",
  object_name="pool_http_1",
  url_body={"description": "Updated description"}
)
```

### 6. delete_tool
**목적:** F5 리소스 삭제

```
파라미터:
- object_type: 삭제할 리소스 유형
- object_name: 삭제할 리소스 이름

예시:
delete_tool(object_type="pool", object_name="pool_http_1")
```

### 7. health_check_tool
**목적:** F5 장비의 기본 연결 상태 확인

```
파라미터: (없음)

예시:
health_check_tool()

응답:
{
  "entries": {
    "https://localhost/mgmt/tm/sys/version/0": {
      "nestedStats": {
        "entries": {
          "product": {"description": "BIG-IP"},
          "version": {"description": "13.1.0.0"}
        }
      }
    }
  }
}
```

### 8. list_auth_users_tool
**목적:** auth user(계정) 목록 조회

```
파라미터 (선택): tmos_host, tmos_port, tmos_username, tmos_password
예시: list_auth_users_tool()
```

### 9. create_auth_user_tool
**목적:** auth user(계정) 생성. admin 권한 계정 추가 시 partition_access=[{"name":"all-partitions","role":"admin"}]

```
파라미터: name(필수), password(필수), description(선택), partition_access(선택), shell(선택: bash/tmsh/none), 연결 오버라이드(선택)
예시: create_auth_user_tool(name="ncurity", password="ncurity1@#", partition_access=[{"name":"all-partitions","role":"admin"}])
```

### 10. get_auth_user_tool
**목적:** auth user(계정) 단일 조회

```
파라미터: name(필수), 연결 오버라이드(선택)
예시: get_auth_user_tool(name="ncurity")
```

### 11. update_auth_user_tool
**목적:** auth user(계정) 수정 (비밀번호, description, partition_access, shell 등)

```
파라미터: name(필수), password/description/partition_access/shell(선택), 연결 오버라이드(선택)
예시: update_auth_user_tool(name="ncurity", password="newpass")
```

### 12. delete_auth_user_tool
**목적:** auth user(계정) 삭제

```
파라미터: name(필수), 연결 오버라이드(선택)
예시: delete_auth_user_tool(name="ncurity")
```

### 13. apply_basic_settings_tool
**목적:** 장비 초기 기본 설정 템플릿. "기본 설정 해줘" 요청 시 사용. hostname, admin/root 비밀번호, DNS, NTP(+timezone), syslog를 넘긴 인자만 적용.

```
파라미터 (모두 선택): hostname, nameservers, ntp_servers, timezone, admin_password, root_password, syslog_destination(원격 Syslog IP:port, 예: 192.168.47.81:514), console_log, clustered_host_slot, cron_from, cron_to, daemon_from, daemon_to, auth_priv_from, auth_priv_to, syslog_via_mgmt, management_route_gateway 등. apply_only_keys 필수.

예시:
apply_basic_settings_tool(apply_only_keys=["hostname","nameservers","ntp_servers","timezone","admin_password","root_password"], hostname="f5-01", nameservers=["8.8.8.8"], ntp_servers=["time.google.com"], timezone="Asia/Seoul", admin_password="newadminpass", root_password="newrootpass")
apply_basic_settings_tool(apply_only_keys=["syslog"], syslog_destination="192.168.47.81:514")
```

### 14. apply_l4_standard_db_tool
**목적:** L4 표준 DB 설정 일괄 적용 (GUI 옵션, fastl4 ack mirror, syn cookie 비활성화, dupsynenforce, monitorencap, mgmtroutecheck, ltm connection). setup.run은 기본 설정(apply_basic_settings)에서 적용.

```
파라미터: (없음)

예시:
apply_l4_standard_db_tool()
```

### 15. apply_l4_standard_profiles_tool
**목적:** L4 표준 프로파일 생성 (HTTP_DEFAULT, TCP_DEFAULT, FL4_DEFAULT, FL4_UDP, clientssl_sni_default)

```
파라미터: (없음)

예시:
apply_l4_standard_profiles_tool()
```

### 16. get_l4_standard_db_state_tool
**목적:** L4 표준 DB 항목의 **장비 현재값** 조회 (적용 전/후 비교용). 기본값이 아닌 실제 sys_db·connection 값을 반환한다.

```
파라미터: (없음)

예시:
get_l4_standard_db_state_tool()
# 비교 시: 1) 이 툴 호출 → Before 저장, 2) apply_l4_standard_db_tool() 실행, 3) 이 툴 재호출 → After
```

### 17. get_l4_standard_profiles_state_tool
**목적:** L4 표준 프로파일 5개의 **장비 현재 설정** 조회 (적용 전/후 비교용). idleTimeout, pvaAcceleration 등 실제 값을 반환한다.

```
파라미터: (없음)

예시:
get_l4_standard_profiles_state_tool()
# 비교 시: 1) 이 툴 호출 → Before 저장, 2) apply_l4_standard_profiles_tool() 실행, 3) 이 툴 재호출 → After
```

**비교 보고 시 주의:** 비교표에는 **반드시 위 get 툴이 반환한 값만** 사용할 것. 툴 실행 결과에 없는 값을 "표준값"이나 "이전에 썼던 값"으로 임의 채우지 말 것. (실제 장비값과 다르면 잘못된 Before/After가 됨.)

---

## 📚 문서 참조

### 1. F5 표준 설정 가이드
👉 `guide_표준설정_플로우.md`

**포함 내용:**
- One-Arm 로드밸런싱 상세 가이드
- 이중화(Redundancy) 구성
- VLAN, Self IP, Route 설정
- SNAT Pool 설정
- Profile 설정 (HTTP, TCP, SSL)
- Virtual Server & Pool 생성
- 의존성 매트릭스
- 권장 설정값

### 2. AI Agent 시스템 프롬프트
👉 `prompt_AI에이전트_규칙.md`

**포함 내용:**
- AI Agent 역할 및 원칙
- 자동 설정 시나리오
- 입력/출력 예시
- 오류 처리 전략
- 상태 보고 템플릿
- 금지 사항 및 좋은 사례

---

## 🎯 아키텍처

```
┌─────────────────────────────────────┐
│      Claude AI (자연어 입력)        │
└────────────────────┬────────────────┘
                     │
                     ▼
┌─────────────────────────────────────┐
│    F5 TMOS AI Agent (이 문서)       │
│                                     │
│  - 자연어 파싱                       │
│  - 파라미터 추출                     │
│  - 의존성 관리                       │
│  - 실행 순서 결정                    │
└────────────────────┬────────────────┘
                     │
                     ▼
┌─────────────────────────────────────┐
│      F5 MCP Server                  │
│   (FastMCP Framework)               │
│                                     │
│  7개 Tool 등록:                      │
│  - show_stats_tool                  │
│  - show_logs_tool                   │
│  - list_tool                        │
│  - create_tool    ◄── API 호출 엔진 │
│  - update_tool                      │
│  - delete_tool                      │
│  - health_check_tool                │
│  - list/create/get/update/delete_auth_user_tool │
│  - apply_basic_settings_tool        │
│  - apply_l4_standard_db_tool         │
│  - apply_l4_standard_profiles_tool  │
│  - get_l4_standard_db_state_tool     │
│  - get_l4_standard_profiles_state_tool │
└────────────────────┬────────────────┘
                     │
                     ▼
┌─────────────────────────────────────┐
│      TMOS iControl REST API         │
│   (192.168.47.55:443)               │
│                                     │
│  /mgmt/tm/ltm/pool                  │
│  /mgmt/tm/ltm/virtual               │
│  /mgmt/tm/net/vlan                  │
│  /mgmt/tm/net/self                  │
│  /mgmt/tm/net/route                 │
│  /mgmt/tm/ltm/snat-pool             │
│  등 ...                             │
└─────────────────────────────────────┘
```

---

## 📋 설정 생성 플로우

```
사용자 입력 (자연어)
    │
    ▼
└─ AI Agent 처리
   ├─ 1️⃣ 입력 분석 (자연어 → 구조화)
   ├─ 2️⃣ 파라미터 추출
   ├─ 3️⃣ 검증 (필수값, 충돌)
   ├─ 4️⃣ 의존성 분석
   ├─ 5️⃣ 실행 순서 결정
   └─ 6️⃣ 사용자 확인 요청
    │
    ▼
MCP Tool 순차 실행
    │
    ├─ VLAN 생성 ─────────────────────┐
    │                                 │
    ├─ Self IP 설정 ◄─────────────────┘ (VLAN에 의존)
    │
    ├─ Route 생성
    │
    ├─ SNAT Pool 생성
    │
    ├─ Pool + Monitor 생성
    │
    └─ Virtual Server 생성 ◄─────────── (Pool에 의존)
    │
    ▼
Health Check & 검증
    │
    ├─ sys/version 호출
    ├─ Pool 상태 확인 (UP/DOWN)
    ├─ Virtual Server 상태 확인
    └─ 트래픽 가능성 확인 (선택)
    │
    ▼
최종 보고서 생성
    │
    ├─ 생성된 리소스 목록
    ├─ 각 리소스의 상태
    ├─ 권장 다음 작업
    └─ 추가 설정 안내
```

---

## 🔧 고급 사용법

### 시나리오별 명령어

#### 시나리오 1: 기존 구성 확인
```
"현재 설정된 Virtual Server와 Pool을 보여줄 수 있어?"

→ list_tool(virtual) + list_tool(pool) 자동 호출
```

#### 시나리오 2: Pool에 새 멤버 추가
```
"pool_http_1에 192.168.1.12:80을 새로 추가해 줄래"

→ update_tool로 기존 pool 수정
```

#### 시나리오 3: 통계 정보 조회
```
"pool_http_1의 현재 처리량을 알 수 있어?"

→ show_stats_tool(pool_http_1) 호출
```

#### 시나리오 4: 다중 구성 (Advanced)
```
"HTTP와 HTTPS를 동시에 설정해 줄 수 있어?
HTTP: 10.10.10.50:80 → pool_http_1
HTTPS: 10.10.10.50:443 → pool_https_1 (SSL인증서: server.crt)"

→ Virtual Server 2개 + SSL Profile 자동 생성
```

---

## ⚠️ 주의사항

### 필수 확인 사항
1. **테스트 환경에서 먼저 검증**
   - 프로덕션 환경에 바로 적용하지 말 것
   
2. **설정 백업**
   - 중요한 변경 전 항상 백업 수행
   ```bash
   # F5에서 직접 UCS 백업 생성
   tmsh save sys config file my_backup.ucs
   ```

3. **이중화 환경**
   - Primary/Standby 모두 테스트 필수
   
4. **트래픽 검증**
   - 설정 후 실제 트래픽으로 테스트

### 위험한 작업

❌ 확인 없이 기존 리소스 삭제
❌ VLAN ID 충돌 리스크 무시
❌ Self IP와 SNAT Pool IP 중복
❌ 게이트웨이 없이 Route 설정

### 권장 사항

✅ 항상 health_check_tool로 연결 상태 확인
✅ 리소스 이름은 명확하고 일관성 있게 지정
✅ 설정 변경 나중 감사 로그 확인
✅ 모니터는 항상 설정 (HTTP, TCP 등)
✅ SNAT Pool은 Pool 크기의 1.5배 이상

---

## 🚦 다음 단계

### Phase 1 (현재): 기본 자동화 ✅
- One-Arm 로드밸런싱 자동 생성
- VLAN, Self IP, Route 자동 설정
- Virtual Server, Pool 자동 생성

### Phase 2 (예정): 이중화 지원
- Device Group 자동 생성
- Cluster Sync 자동화
- Failover 자동 테스트

### Phase 3 (예정): 모니터링
- Monitor 자동 선택 및 설정
- 상태 지속 모니터링
- 알림 설정 자동화

### Phase 4 (예정): 보안 강화
- SSL/TLS 자동 설정
- WAF 정책 자동 적용
- DDoS 보호 자동화

---

## 📞 문제해결

### 문제: "TMOS에 연결할 수 없습니다"
**해결:**
1. TMOS_HOST 및 TMOS_AUTH_BASIC_B64 확인
2. 네트워크 연결성 테스트: `ping {TMOS_HOST}`
3. MCP 로그 확인: `tail -50 ~/Library/Logs/Claude/mcp-server-f5-mcp.log`

### 문제: "VLAN ID 충돌"
**해결:**
```
list_tool(object_type="vlan") 로 기존 VLAN 확인
다른 ID로 재설정 요청
```

### 문제: "Pool Member DOWN"
**해결:**
```
1. show_stats_tool로 멤버 상태 확인
2. Backend 서버 연결성 확인
3. Monitor 설정 검증
```

---

## 📚 추가 학습 자료

- F5 공식 문서: https://techdocs.f5.com/
- iControl REST API: https://devcentral.f5.com/s/articles
- F5 커뮤니티: https://community.f5.com/

---

## 🎓 예제 모음

모든 예제는 `examples/` 디렉토리에 저장됨 (추후 추가)

```
examples/
├── one_arm_basic.md
├── one_arm_with_snat.md
├── redundancy_setup.md
├── ssl_offload.md
├── rate_limiting.md
└── multi_vlan_setup.md
```

---

## ✅ 최종 체크리스트

- [x] TMOS 장비 접속 정보 설정 (.env)
- [x] Claude Desktop 설정 업데이트
- [x] MCP 서버 시작 및 확인
- [x] health_check_tool로 연결 테스트
- [x] TMOS 리소스 목록 조회 (list_tool)
- [x] 표준 설정 가이드 읽기
- [x] AI Agent 첫 설정 요청
- [x] 설정 검증 및 트래픽 테스트

---

**F5 AI Agent 구축 완료! 🎉**

