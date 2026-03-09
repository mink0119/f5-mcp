# F5 MCP 서버 — 배포 및 사용 가이드 (Windows / macOS)

이 문서는 **Windows**와 **macOS**에서 F5 MCP 서버를 설치하고 사용하는 방법을 단계별로 안내합니다.

---

## 1. 사전 요구사항

- **Python 3.7 이상**  
  - Windows: [python.org](https://www.python.org/downloads/)에서 설치 시 **"Add Python to PATH"** 반드시 선택  
  - macOS: `python3` 또는 Homebrew 등으로 설치
- **F5 장비 접속 정보**  
  - TMOS(BIG-IP): 관리 IP, 관리자 계정(admin 등), 비밀번호  
  - (선택) F5OS: 호스트, 포트, 인증 정보

---

## 2. 프로젝트 준비

### 2.1 코드 받기

- 저장소를 클론했거나 압축을 푼 **f5-mcp** 폴더로 이동합니다.

```cmd
REM Windows (예)
cd C:\Users\사용자명\Projects\f5-mcp
```

```bash
# macOS
cd /Users/사용자명/projects/f5-mcp
```

### 2.2 가상환경 (선택)

같은 PC에서 여러 프로젝트를 쓸 때 권장합니다.

**Windows**

```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2.3 의존성 설치

프로젝트 루트(f5-mcp 폴더)에서 실행합니다.

```cmd
REM Windows
pip install -r requirements.txt
```

```bash
# macOS
pip install -r requirements.txt
```

---

## 3. 접속 정보 (mgmt IP·계정·비밀번호)

**접속 정보는 파일이나 .env에 기록하지 않습니다.**  
Claude 등에서 MCP 도구를 사용할 때마다 **tmos_host**(관리 IP), **tmos_username**, **tmos_password** 를 인자로 입력하면 됩니다. 필요 시 **tmos_port**(기본 443)도 입력할 수 있습니다.

---

## 4. 실행 방법

### 4.1 터미널에서 직접 실행 (동작 확인용)

프로젝트 루트에서 다음 중 하나를 실행합니다.

**Windows**

```cmd
python -m F5MCPserver
```

또는

```cmd
scripts\run_mcp.bat
```

**macOS**

```bash
python3 -m F5MCPserver
```

또는 (실행 권한이 있으면)

```bash
./scripts/run_mcp.sh
```

실행 권한이 없다면 한 번만 부여합니다.

```bash
chmod +x scripts/run_mcp.sh
./scripts/run_mcp.sh
```

정상이면 MCP 서버가 stdio로 대기합니다. Claude Desktop 같은 클라이언트는 이 프로세스를 자식으로 띄워 사용합니다.

### 4.2 Claude Desktop에서 MCP로 사용

Claude Desktop이 이 MCP 서버를 자동으로 실행하도록 설정합니다.

#### 1) 설정 파일 위치

| OS      | 설정 파일 경로 |
|--------|--------------------------------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |

경로가 없으면 해당 폴더를 만들고 `claude_desktop_config.json` 파일을 생성합니다.

#### 2) 설정 내용 (Windows)

`claude_desktop_config.json` 예시:

```json
{
  "mcpServers": {
    "f5-mcp": {
      "command": "C:\\Users\\사용자명\\경로\\f5-mcp\\scripts\\run_mcp.bat",
      "args": [],
      "env": {
        "F5_ENDPOINT_TYPE": "F5OS"
      }
    }
  }
}
```

- **`command`**: **f5-mcp** 폴더의 `scripts\run_mcp.bat` **절대 경로**를 넣습니다.
- Windows JSON에서는 경로의 `\` 를 `\\` 로 씁니다.
- F5OS를 쓰지 않으면 `env` 안의 `F5_ENDPOINT_TYPE` 은 생략해도 됩니다.

실제 경로 예: `C:\Projects\f5-mcp\scripts\run_mcp.bat`  
→ JSON: `"C:\\Projects\\f5-mcp\\scripts\\run_mcp.bat"`

#### 3) 설정 내용 (macOS)

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

- **`command`**: **f5-mcp** 폴더의 `scripts/run_mcp.sh` **절대 경로**를 넣습니다.
- `run_mcp.sh` 에 실행 권한이 있어야 합니다: `chmod +x scripts/run_mcp.sh`

#### 4) 적용 방법

1. 설정 파일 저장
2. **Claude Desktop을 완전 종료** (창만 닫지 말고 Quit)
3. Claude Desktop 다시 실행
4. **새 채팅**을 열고 F5 관련 요청으로 MCP 도구가 호출되는지 확인

코드를 수정했는데도 이전처럼 동작할 때는 **CLAUDE_CACHE_AND_MCP.md** 의 재시작·경로 확인 절차를 따르세요.

---

## 5. 사용 흐름 요약

1. **설치**: Python 설치 → 프로젝트 폴더로 이동 → `pip install -r requirements.txt`
2. **접속 정보**: 파일 저장 없음. 도구 사용 시마다 **tmos_host**, **tmos_username**, **tmos_password** 입력.
3. **실행**  
   - 확인용: 터미널에서 `python -m F5MCPserver` 또는 `scripts\run_mcp.bat` / `scripts/run_mcp.sh`  
   - 실제 사용: Claude Desktop 설정에 `command` 로 위 스크립트 **절대 경로** 지정 후 Claude 재시작
4. **사용**: Claude에서 새 채팅을 열고 "기본 설정 해줘", "L4 표준 설정 해줘", "VLAN 만들어줘" 등 자연어로 요청

설정 플로우와 도구 사용법은 다음 문서를 참고하세요.

- **F5_TMOS_STANDARD_CONFIG_GUIDE.md** — 기본 설정·L4 표준·검증·HA 등 표준 프로세스
- **TMOS_AI_AGENT_GUIDE.md** — 도구 목록·사용 예시·Claude 연동
- **F5_TMOS_API_GENERIC_GUIDE.md** — tm_get/post/patch/put/delete 등 범용 API 사용

---

## 6. 문제 해결

| 증상 | 확인 사항 |
|------|-----------|
| `python`(또는 `python3`)을 찾을 수 없음 | Python 설치 여부, PATH 등록 여부 (Windows는 설치 시 "Add to PATH" 선택) |
| `pip install` 실패 | 네트워크, 프록시, Python 버전(3.7+) |
| Claude에서 F5 도구가 안 보임 | `command` 가 **이 f5-mcp** 의 run_mcp.bat / run_mcp.sh **절대 경로**인지 확인 |
| 코드 수정 후에도 예전처럼 동작 | Claude **완전 종료** 후 재실행, 새 채팅에서 재시도. 자세한 절차: **CLAUDE_CACHE_AND_MCP.md** |

설정 예시 파일은 프로젝트에 포함되어 있습니다.

- Windows: `claude_desktop_config.windows.example.json`
- macOS: `claude_desktop_config.mac.example.json`

`ABSOLUTE/PATH/TO/f5-mcp` 부분만 실제 설치 경로로 바꿔 사용하면 됩니다.
