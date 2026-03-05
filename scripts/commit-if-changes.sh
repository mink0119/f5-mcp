#!/bin/bash
# f5-mcp 안에서 발생한 변경사항을 이 저장소에 커밋합니다.
# (스크립트 상위 = f5-mcp 루트. 변경이 있을 때만 git add + commit.)
# 사용법: ./scripts/commit-if-changes.sh "수정 내용을 설명하는 커밋 메시지"
# 커밋 메시지를 반드시 인자로 넘겨야 함 (날짜만으로는 의미 없음).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ ! -d .git ]; then
  echo "Not a git repo. Run 'git init' first."
  exit 1
fi
if [ -z "$1" ]; then
  echo "Usage: $0 \"커밋 메시지 (무엇을 수정했는지 설명)\""
  echo "Example: $0 \"Add get_l4_standard_db_state_tool and forbid guessing in guides\""
  exit 1
fi
MSG="$1"
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "$MSG"
  echo "Committed: $MSG"
else
  echo "No changes to commit."
fi
