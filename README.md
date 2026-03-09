# F5 MCP 서버

F5 장비(TMOS/BIG-IP)에 **iControl REST API**로 접속하는 **MCP(Model Context Protocol) 서버**입니다.  
가상 서버, 풀, 프로파일, 기본 설정, L4 표준 설정, HA 등 자연어 요청으로 설정할 수 있습니다.

**접속 정보**: mgmt IP·계정·비밀번호는 파일에 저장하지 않습니다. 모든 도구 호출 시 **tmos_host**, **tmos_username**, **tmos_password** 를 인자로 입력합니다.

---

## 목차

1. [프로젝트 구조](#1-프로젝트-구조)
2. [문서(.md) 안내](#2-문서md-안내)
3. [배포 및 설치 가이드](#3-배포-및-설치-가이드)
4. [개발 지침 및 가이드](#4-개발-지침-및-가이드)

---

## 1. 프로젝트 구조

```
f5-mcp/
├── F5MCPserver.py          # MCP 서버 진입점. 도구 정의 및 stdio 트랜스포트
├── Tools/
│   ├── F5object.py         # F5 iControl REST API 클라이언트 (CRUD, 기본설정, L4 표준, HA 등)
│   └── settings.py         # 연결 설정 생성 (build_endpoint_settings). 저장소/파일 없음
├── scripts/
│   ├── run_mcp.bat         # Windows용 MCP 실행 (프로젝트 루트에서 python -m F5MCPserver)
│   ├── run_mcp.sh         # macOS/Linux용 MCP 실행
│   └── commit-if-changes.sh # 변경 시 커밋 헬퍼 (선택)
├── explore_configs.py      # DNS/NTP/Syslog 등 조회 스크립트 (CLI 인자로 host/계정 전달)
├── requirements.txt        # Python 의존성 (requests, mcp, python-dotenv, PyYAML)
├── claude_desktop_config.json
├── claude_desktop_config.windows.example.json
├── claude_desktop_config.mac.example.json
└── *.md                    # 가이드 문서: guide_*, prompt_* (아래 §2 참고)
```

- **실제 동작**: `F5MCPserver.py`가 MCP 도구를 정의하고, 각 도구는 `_resolve_connection(tmos_host, …)`로 연결을 검증한 뒤 `Tools.F5object.F5_object`로 API 호출을 수행합니다.
- **접속 정보**: `.env`나 장비 목록 파일은 사용하지 않습니다. 호출 시마다 `tmos_host`, `tmos_username`, `tmos_password`(및 선택 `tmos_port`)를 넘깁니다.

---

## 2. 문서(.md) 안내

이름 규칙: **guide_** = 사용·설정 가이드, **prompt_** = AI 규칙.

| 파일 | 설명 |
|------|------|
| **README.md** (본 문서) | 프로젝트 소개, 구조, 문서 목록, **배포·설치**, **개발 지침** 통합 |
| **guide_표준설정_플로우.md** | 표준 설정 플로우: 기본 설정(Section 0), L4 DB/프로파일(Section 1), One-Arm, 이중화, VLAN/Self IP/Route, SNAT, 프로파일. 적용 전/후 검증 절차 포함 |
| **guide_도구_사용법.md** | 도구 목록·사용 예시·Claude 연동. CRUD, auth user, 기본/L4 표준, HA 툴 정리 및 자연어 시나리오 |
| **guide_범용_API.md** | 범용 TMOS API: tm_get / tm_post / tm_patch / tm_put / tm_delete. path·body로 모든 설정 생성/수정/삭제 |
| **prompt_AI에이전트_규칙.md** | AI 에이전트용 규칙: 기본설정·L4 표준·HA 시 금지/필수, ask_user 처리, 시나리오별 동작 |

배포·설치는 본 README의 **§3 배포 및 설치 가이드**, 개발 시 참고할 규칙은 **§4 개발 지침 및 가이드**에 정리되어 있습니다.

---

## 3. 배포 및 설치 가이드

Windows와 macOS에서 설치·실행·Claude 연동 방법입니다.

### 3.1 사전 요구사항

- **Python 3.7 이상**
  - Windows: [python.org](https://www.python.org/downloads/)에서 설치 시 **"Add Python to PATH"** 선택
  - macOS: `python3` 또는 Homebrew 등
- **F5 접속 정보**: 관리 IP, 계정(예: admin), 비밀번호 (도구 호출 시마다 입력)

### 3.2 프로젝트 준비

**코드 위치**

```cmd
REM Windows
cd C:\Users\사용자명\경로\f5-mcp
```

```bash
# macOS
cd /Users/사용자명/경로/f5-mcp
```

**가상환경(선택)**

```cmd
REM Windows
python -m venv .venv
.venv\Scripts\activate
```

```bash
# macOS
python3 -m venv .venv
source .venv/bin/activate
```

**의존성 설치**

```cmd
REM Windows
pip install -r requirements.txt
```

```bash
# macOS
pip install -r requirements.txt
```

### 3.3 접속 정보

접속 정보는 **파일이나 .env에 기록하지 않습니다.**  
Claude 등에서 MCP 도구를 쓸 때마다 **tmos_host**(관리 IP), **tmos_username**, **tmos_password** 를 인자로 넣습니다. **tmos_port**(기본 443)는 선택입니다.

### 3.4 실행 방법

**터미널에서 확인용**

- Windows: `python -m F5MCPserver` 또는 `scripts\run_mcp.bat`
- macOS: `python3 -m F5MCPserver` 또는 `./scripts/run_mcp.sh` (필요 시 `chmod +x scripts/run_mcp.sh`)

**Claude Desktop에서 MCP로 사용**

1. **설정 파일 위치**
   - **Windows**:  
     `%APPDATA%\Claude\claude_desktop_config.json`  
     풀 경로: `C:\Users\사용자명\AppData\Roaming\Claude\claude_desktop_config.json`  
     - **폴더/파일이 없으면**: `C:\Users\사용자명\AppData\Roaming\` 아래에 `Claude` 폴더를 만들고, 그 안에 `claude_desktop_config.json` 파일을 생성하면 됩니다.  
     - **Microsoft Store(MSIX) 설치본**을 쓰는 경우, 앱이 실제로 읽는 경로는 다음일 수 있습니다.  
       `C:\Users\사용자명\AppData\Local\Packages\Claude_xxxxx\LocalCache\Roaming\Claude\claude_desktop_config.json`  
       (Packages 아래 폴더명에 `Claude`가 포함된 것을 찾아 사용. MCP가 안 먹히면 이 경로에 설정 파일을 두고 수정해 보세요.)
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
2. **설정 예시 (Windows)** — `command`에 run_mcp.bat **절대 경로**

```json
{
  "mcpServers": {
    "f5-mcp": {
      "command": "C:\\Users\\사용자명\\경로\\f5-mcp\\scripts\\run_mcp.bat",
      "args": [],
      "env": {}
    }
  }
}
```

3. **설정 예시 (macOS)** — `command`에 run_mcp.sh **절대 경로**

```json
{
  "mcpServers": {
    "f5-mcp": {
      "command": "/Users/사용자명/경로/f5-mcp/scripts/run_mcp.sh",
      "args": [],
      "env": {}
    }
  }
}
```

4. 설정 저장 후 **Claude Desktop 완전 종료** → 다시 실행 → **새 채팅**에서 F5 도구 사용

설정 예시 파일: `claude_desktop_config.windows.example.json`, `claude_desktop_config.mac.example.json` (경로만 실제로 바꿔 사용).

### 3.5 사용 흐름 요약

1. 설치: Python → 프로젝트 폴더 → `pip install -r requirements.txt`
2. 접속: 파일 없음. 도구 사용 시마다 **tmos_host**, **tmos_username**, **tmos_password** 입력
3. 실행: 터미널에서 `python -m F5MCPserver` 또는 Claude 설정에 run_mcp 스크립트 **절대 경로** 지정
4. 사용: Claude 새 채팅에서 "기본 설정 해줘", "L4 표준 설정 해줘", "VLAN 만들어줘" 등 요청

### 3.6 문제 해결

| 증상 | 확인 사항 |
|------|-----------|
| Windows에서 설정 경로 없음 | `C:\Users\사용자명\AppData\Roaming\Claude` 폴더를 만들고 그 안에 `claude_desktop_config.json` 생성. MSIX 설치면 `AppData\Local\Packages\...\LocalCache\Roaming\Claude` 경로 확인 |
| `python`/`python3` 없음 | Python 설치 및 PATH (Windows: "Add to PATH" 선택) |
| `pip install` 실패 | 네트워크, Python 3.7+ |
| Claude에서 F5 도구 안 보임 | `command`가 이 f5-mcp의 run_mcp.bat / run_mcp.sh **절대 경로**인지 확인 |
| 코드 수정 후에도 예전 동작 | Claude **완전 종료** 후 재실행, 새 채팅 |

---

## 4. 개발 지침 및 가이드

코드를 수정·추가할 때 맞추면 좋은 목표와 규칙입니다.

### 4.1 프로젝트 목표 (유지할 것)

- **목적**: F5 설정을 **자연어로 동일한 품질**로 수행하기 위한 MCP 서버
- **3대 기능**
  1. **기본 설정** — hostname, NTP, DNS, syslog, admin/root 비밀번호 등
  2. **L4 표준 설정** — sys_db, LTM connection, 표준 프로파일
  3. **그 외** — VLAN, Self IP, Pool, Virtual Server, HA, auth user 등 자연어 처리

코드/문서 변경 시 위 목적과 3대 기능 구분을 유지할 것.

### 4.2 코드 수정 시 체크리스트

**기본설정** (`Tools/F5object.py`, `apply_basic_settings`)

- [ ] 사용자가 **말로 준 값만** 적용. 장비에서 조회한 값은 기본설정 인자로 사용하지 않음
- [ ] 값이 하나도 없으면 `action: "ask_user"` + `basic_settings_guide` / `message` 반환

**AI 규칙** (`prompt_AI에이전트_규칙.md`)

- [ ] “말로 지정하지 않은 항목은 apply_basic_settings_tool 인자에 넣지 말 것” 등 규칙이 실제 호출 흐름과 맞는지
- [ ] 기본설정·L4 표준·HA 관련 문구가 코드 동작과 일치하는지

**HA 이중화** (`Tools/F5object.py`, `apply_ha_settings`)

- [ ] Secondary CM name과 Primary가 충돌할 때 `secondary_device_name_actual` short form 적용 후 add_to_trust / config_sync까지 동일 이름 사용
- [ ] add_to_trust TMSH 폴백 시 비밀번호 이스케이프 (`'` → `'"'"'`)

**도구·연결** (`F5MCPserver.py`)

- [ ] 모든 툴에서 `tmos_host` / `tmos_port` / `tmos_username` / `tmos_password` 일관 전달 (접속 정보는 호출 시마다만 사용)
- [ ] `apply_basic_settings_tool` / `apply_ha_tool` 인자가 `F5object` 메서드와 맞는지

**반환값·에러**

- [ ] 단계별 반환은 `{ "ok", "step", "result" }` 형태 유지
- [ ] `action`, `do_not_report_as_complete` 등으로 완료/미완료/ask_user 구분
- [ ] 실패 시 단계·장비·API(REST vs TMSH) 구분이 에러 메시지에 드러나도록

### 4.3 문서 수정 시

- 툴 시그니처·인자 변경 시 **guide_도구_사용법.md**, **prompt_AI에이전트_규칙.md** 등 영향 받는 가이드도 함께 수정
- 접속 정보는 저장하지 않고 `tmos_host` / `tmos_username` / `tmos_password` 로만 전달한다는 점을 문서에 반영

### 4.4 코드 스타일·우선순위

- **일관성**: 새 툴도 `tmos_host`, `tmos_port`, `tmos_username`, `tmos_password` 를 받고, `_resolve_connection`으로 검증한 뒤 `F5_object(**(conn or {}))` 로 호출
- **에러 메시지**: 사용자/AI가 원인을 알 수 있도록 구체적으로 작성

---

이 README에 배포·설치와 개발 지침을 모두 두었습니다. 상세 플로우·도구 사용법은 위 **문서(.md) 안내**의 각 가이드를 참고하면 됩니다.
