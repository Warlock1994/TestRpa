@echo off
chcp 65001 >nul
title Web RPA - 后端

:: 获取脚本所在目录
set "ROOT_DIR=%~dp0"
set "PYTHON_DIR=%ROOT_DIR%Python313"
set "NODEJS_DIR=%ROOT_DIR%nodejs"

:: 设置环境变量
set "PATH=%NODEJS_DIR%;%PYTHON_DIR%;%PYTHON_DIR%\Scripts;%PATH%"

echo.
echo ========================================
echo   Web RPA - 后端服务
echo ========================================
echo.
echo [信息] 正在禁用快速编辑模式...

:: 禁用快速编辑模式 - 使用外部 PowerShell 文件
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT_DIR%disable-quickedit-simple.ps1" 2>nul

echo [完成] 快速编辑模式已禁用
echo [提示] 鼠标点击不会暂停终端
echo.
echo [信息] 正在启动后端服务...
echo.

:: 启动后端
cd /d "%ROOT_DIR%backend"
"%PYTHON_DIR%\python.exe" run.py

echo.
echo [信息] 后端服务已停止
pause
