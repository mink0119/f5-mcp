# F5 MCP 개발 가이드라인

이 문서는 F5 MCP 서버 코드를 수정·추가할 때 참고하는 개발 가이드라인입니다.  
플랜 문서(**F5 MCP 코드리뷰·가이드·정리**)를 기준으로, 지속적인 코드 수정 시 일관된 품질과 동작을 유지하기 위한 규칙을 정리했습니다.

---

## 1. 프로젝트 목표 (수정 시 항상 유지할 것)

- **목적**: 모든 엔지니어가 F5 설정을 **자연어로 동일한 품질**로 수행하기 위한 MCP 서버
- **3대 기능**
  1. **기본 설정** — hostname, NTP, DNS, syslog, admin/root 비밀번호 등
  2. **L4 표준 설정** — sys_db, LTM connection, 표준 프로파일
  3. **그 외 개별 기능** — VLAN, Self IP, Pool, Virtual Server, HA, auth user 등 자연어 처리

코드/문서를 바꿀 때 위 목적과 3대 기능 구분이 깨지지 않도록 할 것.

---

## 2. 코드 수정 시 체크리스트 (코드 리뷰 기준)

### 2.1 기본설정 (`Tools/F5object.py`, `apply_basic_settings`)

- [ ] **사용자 말로 준 값만 적용**: `_has_any_user_provided_value`와 ask_user 반환 조건이 "사용자가 말로 지정한 값"만 기준인지 확인
- [ ] 장비에서 조회한 값(get_hostname, list_cm_devices 등)은 **절대** 기본설정 인자로 사용하지 않음
- [ ] 값이 하나도 없으면 반드시 `action: "ask_user"` + `basic_settings_guide` / `message` 반환

### 2.2 AI 규칙 (`AI_AGENT_SYSTEM_PROMPT.md`)

- [ ] "말로 지정하지 않은 항목은 apply_basic_settings_tool 인자로 넣지 말 것" 규칙이 도구 호출 흐름과 맞는지
- [ ] 기본설정·L4 표준·HA 관련 금지/필수 문구가 실제 코드 동작과 일치하는지

### 2.3 HA 이중화 (`Tools/F5object.py`, `apply_ha_settings`)

- [ ] **Step 0b**: `secondary_cm_name == primary_hostname_actual`(충돌)일 때 `secondary_device_name_actual` = 호출자 `secondary_device_name`의 short form (예: `bigip2.ncurity.com` → `bigip2`)
- [ ] 충돌 시 Secondary hostname을 위 short form으로 설정하고, **add_to_trust / add_to_group / config_sync**까지 모두 같은 `secondary_device_name_actual` 사용
- [ ] **add_to_trust**: TMSH 폴백 시 비밀번호 `'` → `'"'"'` 이스케이프 적용 (특수문자 @# 등 포함)

### 2.4 도구와 F5object 매핑 (`F5MCPserver.py`)

- [ ] `apply_basic_settings_tool` / `apply_ha_tool` 인자가 `F5object` 메서드 시그니처·의도와 일치하는지
- [ ] `tmos_host` / `tmos_port` / `tmos_username` / `tmos_password` 전달이 모든 툴에서 일관된지 (접속 정보는 저장하지 않고 호출 시마다 입력)

### 2.5 반환값·에러 일관성

- [ ] 단계별 반환은 `{ "ok": bool, "step": "...", "result": ... }` 형태 유지
- [ ] 클라이언트(AI)가 "완료 / 미완료 / ask_user"를 구분할 수 있도록 `action`, `do_not_report_as_complete` 등 명확히 사용
- [ ] 실패 시 단계명·장비·API(REST vs TMSH) 구분이 에러 메시지에 포함되도록 할 것

---

## 3. 문서 정리 규칙 (사용 가이드 MD)

### 3.1 문서 역할 분리

| 문서 | 역할 |
|------|------|
| **DEPLOYMENT_AND_USAGE.md** | Windows/macOS 설치·배포·사용 (Python, 의존성, Claude 연동) |
| **TMOS_AI_AGENT_GUIDE.md** (또는 USAGE_GUIDE) | 사용법·시나리오·자연어 예시·툴 호출 순서 |
| **AI_AGENT_SYSTEM_PROMPT.md** | AI 전용 규칙(금지/필수/시나리오) |
| **F5_TMOS_STANDARD_CONFIG_GUIDE.md** | 표준 설정 플로우(기본, L4, HA, 검증) |
| **F5_TMOS_API_GENERIC_GUIDE.md** | tm_get/post/patch/put/delete 등 범용 API |
| **DEVELOPMENT_GUIDELINES.md** | 코드 수정 시 가이드라인(본 문서) |

### 3.2 문서 수정 시

- 툴 시그니처·인자 변경 시 TMOS_AI_AGENT_GUIDE, AI_AGENT_SYSTEM_PROMPT 등 영향 받는 가이드를 함께 수정할 것.
- 접속 정보는 저장·로드하지 않고 호출 시마다 `tmos_host` / `tmos_username` / `tmos_password` 로 전달한다는 점을 가이드에 반영할 것.

---

## 4. 코드 스타일·우선순위

- **플랜 기반**: 기능 추가/변경 시 플랜 문서 또는 이 가이드의 체크리스트를 먼저 확인하고, 목표와 3대 기능에 맞게 수정할 것.
- **일관성**: 새 툴은 기존 툴과 동일하게 `tmos_host`, `tmos_port`, `tmos_username`, `tmos_password` 인자를 받고, `_resolve_connection`으로 연결 정보를 검증한 뒤 `F5_object(**(conn or {}))` 로 호출할 것.
- **에러 메시지**: 사용자/AI가 원인을 알 수 있도록 구체적으로 작성할 것.
