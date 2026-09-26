#!/usr/bin/env bash
# Ballball 的主页 —— 一键启动（Git Bash / macOS / Linux）
set -euo pipefail
cd "$(dirname "$0")"

PY="${PY:-python3}"

if [ ! -x ".venv/Scripts/python.exe" ] && [ ! -x ".venv/bin/python" ]; then
  echo "[1/3] 首次运行，创建虚拟环境..."
  "$PY" -m venv .venv
  echo "[2/3] 安装依赖..."
  if [ -x ".venv/Scripts/python.exe" ]; then .venv/Scripts/python.exe -m pip install -r requirements.txt
  else .venv/bin/pip install -r requirements.txt; fi
fi

if [ -x ".venv/Scripts/python.exe" ]; then VP=".venv/Scripts/python.exe"; else VP=".venv/bin/python"; fi

echo "[3/3] 启动服务： http://127.0.0.1:8800"
echo "       后台地址： http://127.0.0.1:8800/admin.html"
echo "       口令： 用你在后台设置的那个（删掉 data/admin.json 才退回 admin12345）"
"$VP" run.py --port 8800
