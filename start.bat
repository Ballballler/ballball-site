@echo off
REM 编码：GB18030 + CRLF（cmd 原生读 ANSI；UTF-8 或纯 LF 都会让中文乱码/吞首字符）
cd /d "%~dp0"

REM ============================================================
REM  Ballball 的主页 —— 一键启动
REM  双击即可：自动建虚拟环境 / 装依赖 / 起服务 / 开后台
REM ============================================================

if exist ".venv\Scripts\python.exe" goto :run

echo [1/3] 首次运行，正在创建虚拟环境...
set PY=python
where python >nul 2>nul || set PY=py -3
%PY% -m venv .venv
if errorlevel 1 (
  echo 创建虚拟环境失败，请确认已安装 Python 3.10 以上版本。
  pause
  exit /b 1
)

echo [2/3] 正在安装依赖...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo 依赖安装失败，请检查网络或 pip 源。
  pause
  exit /b 1
)

:run
echo [3/3] 启动服务： http://127.0.0.1:8800
echo       后台地址： http://127.0.0.1:8800/admin.html
echo       口令： 用你在后台设置的那个（删掉 data\admin.json 才退回 admin12345）
echo       关闭这个窗口即停止服务。
start "" http://127.0.0.1:8800/admin.html
".venv\Scripts\python.exe" run.py --port 8800

pause
