#!/bin/sh
# 启动 nginx 和后端

# 启动 nginx（后台）
nginx

# 启动后端（前台，exec 替换进程避免重复fork）
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
