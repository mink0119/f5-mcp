@echo off
REM MCP 서버 실행 (Windows). 프로젝트 루트로 이동 후 python -m F5MCPserver 실행.
cd /d "%~dp0.."
python -m F5MCPserver
