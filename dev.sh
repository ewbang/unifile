#!/bin/bash
# UniFile 本地开发启动脚本

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
PID_FILE="$PROJECT_DIR/.dev.pid"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

start() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  UniFile 本地开发启动${NC}"
    echo -e "${GREEN}========================================${NC}"

    # 检查是否已运行
    if [ -f "$PID_FILE" ]; then
        echo -e "${YELLOW}[!] 服务已在运行中，先执行 stop 停止${NC}"
        return 1
    fi

    # 启动后端
    echo -e "${GREEN}[*] 启动后端 (FastAPI)...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate 2>/dev/null || true
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/unifile-backend.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}    后端 PID: $BACKEND_PID${NC}"

    # 启动前端
    echo -e "${GREEN}[*] 启动前端 (Vite)...${NC}"
    cd "$FRONTEND_DIR"
    nohup npm run dev > /tmp/unifile-frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo -e "${GREEN}    前端 PID: $FRONTEND_PID${NC}"

    # 保存 PID
    echo "$BACKEND_PID,$FRONTEND_PID" > "$PID_FILE"

    echo ""
    echo -e "${GREEN}[✓] 启动完成！${NC}"
    echo ""
    echo -e "后端: ${YELLOW}http://localhost:8000${NC}"
    echo -e "前端: ${YELLOW}http://localhost:5173${NC}"
    echo ""
    echo -e "查看日志:"
    echo -e "  后端: ${YELLOW}tail -f /tmp/unifile-backend.log${NC}"
    echo -e "  前端: ${YELLOW}tail -f /tmp/unifile-frontend.log${NC}"
}

stop() {
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  UniFile 停止服务${NC}"
    echo -e "${RED}========================================${NC}"

    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}[!] 未找到运行中的服务${NC}"
        return 1
    fi

    IFS=',' read -r BACKEND_PID FRONTEND_PID < "$PID_FILE"

    # 停止后端
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null
        echo -e "${RED}[✓] 后端已停止 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${YELLOW}[!] 后端未运行${NC}"
    fi

    # 停止前端
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null
        echo -e "${RED}[✓] 前端已停止 (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}[!] 前端未运行${NC}"
    fi

    # 清理 PID 文件
    rm -f "$PID_FILE"
    echo -e "${GREEN}[✓] 已清理${NC}"
}

status() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}服务未运行${NC}"
        return 1
    fi

    IFS=',' read -r BACKEND_PID FRONTEND_PID < "$PID_FILE"

    echo "运行状态："
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "  后端: ${GREEN}运行中${NC} (PID: $BACKEND_PID)"
    else
        echo -e "  后端: ${RED}已停止${NC}"
    fi

    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "  前端: ${GREEN}运行中${NC} (PID: $FRONTEND_PID)"
    else
        echo -e "  前端: ${RED}已停止${NC}"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    status)
        status
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
