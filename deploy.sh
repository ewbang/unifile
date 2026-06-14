#!/bin/bash
# UniFile Docker 一键部署脚本
# 前端在 Docker 多阶段构建中编译，不需要宿主机安装 Node.js

set -e

IMAGE_NAME="unifile"
IMAGE_TAG="latest"

echo "=========================================="
echo "  UniFile Docker 部署"
echo "=========================================="

# 构建镜像（前端在容器内编译）
echo "[*] 开始构建镜像 ${IMAGE_NAME}:${IMAGE_TAG} ..."
docker build -f docker/Dockerfile -t ${IMAGE_NAME}:${IMAGE_TAG} .

echo ""
echo "[✓] 构建完成！"

# 清理悬空镜像
echo ""
echo "[*] 清理未使用的镜像..."
docker image prune -f

echo ""
echo "镜像信息："
docker images ${IMAGE_NAME} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# 启动服务
echo ""
echo "[*] 启动服务..."
docker-compose -f docker/docker-compose.yml up -d

echo ""
echo "[✓] 部署完成！"
echo ""
echo "访问地址: http://localhost:8080"
echo ""
echo "常用命令："
echo "  查看日志:  docker-compose -f docker/docker-compose.yml logs -f"
echo "  停止服务:  docker-compose -f docker/docker-compose.yml down"
echo "  重启服务:  docker-compose -f docker/docker-compose.yml restart"
