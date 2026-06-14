#!/bin/bash
# UniFile Docker 一键部署脚本

set -e

IMAGE_NAME="unifile"
IMAGE_TAG="latest"

echo "=========================================="
echo "  UniFile Docker 部署"
echo "=========================================="

# 清理并重新编译前端
echo "[*] 清理旧的前端产物..."
rm -rf frontend/dist

echo "[*] 编译前端..."
cd frontend && npm run build && cd ..

# 构建镜像
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
