@echo off
chcp 65001 >nul
title Stable Fast 3D - Local Gradio

set "PROJECT_DIR=D:\AIGC\stable-fast-3d"
set "HUGGINGFACE_HUB_CACHE=D:\AIGC\hf-cache\hub"
set "U2NET_HOME=D:\AIGC\u2net"
set "HF_HUB_OFFLINE=1"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "GRADIO_ANALYTICS_ENABLED=False"

set "HTTP_PROXY="
set "HTTPS_PROXY="
set "ALL_PROXY="
set "NO_PROXY=localhost,127.0.0.1,::1"

cd /d "%PROJECT_DIR%"
start "" "http://127.0.0.1:7860"
".venv\Scripts\python.exe" -u gradio_app.py
pause
