# 코드 변경 후 커밋 (f5-mcp)

**f5-mcp 안에서의 변경사항**을 여기(f5-mcp 저장소)에 커밋하는 용도입니다.  
Cursor에서 **f5-mcp 폴더를 열어두고** 여기서만 수정·커밋하면 됩니다. 상위 폴더(2.git 등)를 열 필요 없습니다.

## 권장: 커밋 메시지를 꼭 넣기

날짜만 있는 `chore: auto commit - 2025-03-05 12:00` 같은 메시지는 **무슨 변경인지 알 수 없어** 의미가 없습니다.  
**무엇을 수정했는지 설명하는 메시지**를 넣어야 합니다.

## 사용법

**`scripts/commit-if-changes.sh`** — 변경이 있을 때만 `git add` + `git commit` 합니다. **첫 번째 인자로 커밋 메시지(필수)**를 넘깁니다.

```bash
# f5-mcp 폴더에서
./scripts/commit-if-changes.sh "L4 검증 툴 추가 및 가이드에 툴 반환값만 사용하라는 규칙 명시"
```

메시지를 안 주면 스크립트가 사용법을 출력하고 종료합니다 (의미 없는 커밋 방지).

## Cursor / 에이전트에서

코드나 가이드를 수정한 뒤, **에이전트가 커밋까지 할 때**는 반드시 **수정 내용을 요약한 메시지**를 넣어서 호출하라고 요청하면 됩니다.

예:
- "방금 수정한 내용 기준으로 commit-if-changes.sh 에 설명 메시지 넣어서 커밋해줘"
- 에이전트가 실행: `./scripts/commit-if-changes.sh "Add get_l4_standard_*_state_tool, forbid guessing in F5_TMOS_STANDARD_CONFIG_GUIDE and AI_AGENT_SYSTEM_PROMPT"`

---

**참고:** f5-mcp를 git으로 관리하려면 **f5-mcp 폴더를 연 상태에서** 터미널로 `git init` 한 번 실행한 뒤 사용하세요.
