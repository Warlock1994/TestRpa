@echo off
chcp 65001 >nul
title Web RPA - 启动中...

echo ========================================
echo        Web RPA 一键启动脚本
echo ========================================
echo.

:: 获取脚本所在目录
set "ROOT_DIR=%~dp0"

:: 设置项目内置的 Python 和 Node.js 路径（根目录）
set "PYTHON_DIR=%ROOT_DIR%Python313"
set "NODEJS_DIR=%ROOT_DIR%nodejs"

:: 检查内置 Python 是否存在
if not exist "%PYTHON_DIR%\python.exe" (
    echo [错误] 未找到内置 Python，请确保 Python313 目录存在
    pause
    exit /b 1
)

:: 检查内置 Node.js 是否存在
if not exist "%NODEJS_DIR%\node.exe" (
    echo [错误] 未找到内置 Node.js，请确保 nodejs 目录存在
    pause
    exit /b 1
)

echo [信息] 使用内置 Python: %PYTHON_DIR%
echo [信息] 使用内置 Node.js: %NODEJS_DIR%
echo.

echo [信息] 正在同步配置文件...
:: 复制配置文件到前端 public 目录
if exist "%ROOT_DIR%WebRPAConfig.json" (
    copy /Y "%ROOT_DIR%WebRPAConfig.json" "%ROOT_DIR%frontend\public\WebRPAConfig.json" >nul
    echo [信息] 配置文件已同步到前端
)

echo [信息] 正在读取配置文件...
:: 读取配置文件中的端口号
set FRONTEND_PORT=5173
set BACKEND_PORT=8000

if exist "%ROOT_DIR%read-config.ps1" (
    for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT_DIR%read-config.ps1" frontend.port 2^>nul') do set FRONTEND_PORT=%%i
    for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT_DIR%read-config.ps1" backend.port 2^>nul') do set BACKEND_PORT=%%i
)

:: 如果读取失败，使用默认端口
if "%FRONTEND_PORT%"=="" set FRONTEND_PORT=5173
if "%BACKEND_PORT%"=="" set BACKEND_PORT=8000

echo [信息] 配置端口 - 后端: %BACKEND_PORT%, 前端: %FRONTEND_PORT%
echo.

echo [信息] 正在启动后端服务...
:: 使用 start 命令启动新窗口
start "WebRPA-Backend" /D "%ROOT_DIR%" cmd /k "%ROOT_DIR%start-backend.bat"

echo [信息] 等待后端启动...
timeout /t 3 /nobreak >nul

echo [信息] 正在启动前端服务...
:: 使用 start 命令启动新窗口
start "WebRPA-Frontend" /D "%ROOT_DIR%" cmd /k "%ROOT_DIR%start-frontend.bat"

echo.
echo ========================================
echo        服务启动完成！
echo ========================================
echo.
echo   后端地址: http://localhost:%BACKEND_PORT%
echo   前端地址: http://localhost:%FRONTEND_PORT%
echo.
echo   服务窗口已启动（可手动最小化）
echo   已禁用快速编辑模式
echo.
echo ========================================
echo       5秒后自动打开浏览器访问WebRPA
echo ========================================
timeout /t 5 /nobreak >nul

start "" "http://localhost:%FRONTEND_PORT%"
