#!/bin/sh
# MCP 서버 실행 (macOS/Linux). 프로젝트 루트로 이동 후 python -m F5MCPserver 실행.
cd "$(dirname "$0")/.." && exec python3 -m F5MCPserver 2>/dev/null || exec python -m F5MCPserver
