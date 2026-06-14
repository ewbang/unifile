#!/bin/sh
set -e

# 启动 nginx（后台）
nginx

# 启动 uvicorn（前台，PID 1）
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
