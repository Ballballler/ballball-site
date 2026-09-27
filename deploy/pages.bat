@echo off
REM 编码：GB18030 + CRLF（cmd 原生读 ANSI，存 UTF-8 或只用 LF 都会出问题）
REM ============================================================
REM  把站点导出成静态站并推送到 gh-pages 分支（Windows 版）
REM
REM  为什么必须本地导出：GitHub Pages 不会运行 Python，
REM  Action 里也没有你的数据库（data/site.db 不该进仓库）。
REM  所以内容是本地拍快照、产物推上去。
REM
REM  用法：双击即可，或在命令行里跑 deploy\pages.bat
REM ============================================================
setlocal
cd /d "%~dp0\.."

set REMOTE=origin
set BRANCH=gh-pages
if "%SITE_URL%"=="" set SITE_URL=https://ballballler.github.io/ballball-site

echo ==^> 1/3 导出静态站
".venv\Scripts\python.exe" tools\export_static.py --out dist --site-url "%SITE_URL%"
if errorlevel 1 goto :fail

echo ==^> 2/3 组装 gh-pages 分支
set "TMP=%TEMP%\ballball-pages-%RANDOM%"
if exist "%TMP%" rmdir /s /q "%TMP%"
mkdir "%TMP%"
xcopy /E /I /Y /Q dist "%TMP%" >nul

pushd "%TMP%"
git init -q
git checkout -q -b %BRANCH%
git add -A
git -c user.name=Ballballler -c user.email=Ballballler@users.noreply.github.com commit -q -m "publish: 静态站快照"
if errorlevel 1 (
  popd
  goto :fail
)

echo ==^> 3/3 推送到 %REMOTE% 的 %BRANCH%
git push --force %REMOTE% %BRANCH%
set RC=%ERRORLEVEL%
popd
rmdir /s /q "%TMP%"

if not "%RC%"=="0" goto :fail

echo.
echo 推送完成。第一次部署还需要最后一步：
echo   GitHub 仓库 -^> Settings -^> Pages -^> Build and deployment
echo   Source 选「Deploy from a branch」
echo   Branch 选 gh-pages、目录选 / (root) -^> Save
echo.
echo 一两分钟后就能在 %SITE_URL% 打开。
echo 之后改内容重跑这个 bat 即可。
echo.
pause
exit /b 0

:fail
echo.
echo 失败了。常见问题：
echo   1. 还没 git remote add origin git@github.com:Ballballler/ballball-site.git
echo   2. SSH key 没加到 GitHub：ssh -T git@github.com 应该回 Hi Ballballler!
echo   3. 仓库还没建：去 https://github.com/new 建一个
echo.
pause
exit /b 1
