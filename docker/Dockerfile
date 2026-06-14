# ==================== 阶段1: 前端构建 ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# 先复制依赖文件，利用缓存
COPY frontend/package*.json ./
RUN npm install --registry=https://registry.npmmirror.com

# 复制前端源码并构建
COPY frontend/ ./
RUN npm run build

# ==================== 阶段2: 最终运行镜像 ====================
FROM python:3.11-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

# 配置 pip 镜像源
RUN pip config set global.index-url https://mirrors.ustc.edu.cn/pypi/simple

# 仅运行时依赖
RUN apk add --no-cache nginx

# 安装 Python 依赖（优先用预编译 wheel）
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --prefer-binary -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# 后端代码
COPY backend/ .

# 前端产物（从构建阶段复制）
COPY --from=frontend-builder /build/dist /usr/share/nginx/html

# 数据目录
RUN mkdir -p \
    /root/.unifile/db \
    /root/.unifile/backups

# nginx配置
COPY docker/nginx.conf /etc/nginx/http.d/default.conf

# 启动脚本
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

# 确保 nginx 运行目录存在且有权限（兼容 CentOS SELinux）
RUN mkdir -p /run/nginx && chown nginx:nginx /run/nginx

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/api/health >/dev/null || exit 1

CMD ["/start.sh"]
