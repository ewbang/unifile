# UniFile Docker 构建脚本
# 优化：alpine + 单层安装删除 + 激进清理

# ==================== 阶段1：前端构建 ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --production=false

COPY frontend/ ./
RUN npx vite build

# ==================== 阶段2：后端运行 ====================
FROM python:3.11-alpine

WORKDIR /app

# 单层完成：安装编译依赖 -> 编译Python包 -> 删除编译依赖 -> 安装运行时依赖
RUN apk add --no-cache \
    gcc g++ musl-dev libffi-dev openssl-dev \
    && apk add --no-cache nginx supervisor curl \
    && pip install --no-cache-dir --no-compile \
        fastapi==0.115.0 \
        "uvicorn[standard]==0.30.0" \
        sqlalchemy==2.0.35 \
        aiosqlite==0.20.0 \
        pydantic-settings==2.5.0 \
        "python-jose[cryptography]==3.3.0" \
        "passlib[bcrypt]==1.7.4" \
        bcrypt==4.1.3 \
        python-multipart==0.0.12 \
        oss2==2.19.0 \
        esdk-obs-python==3.24.12 \
        cos-python-sdk-v5==1.9.35 \
        qiniu==7.12.0 \
        bce-python-sdk==0.9.72 \
        tos==2.7.0 \
        httpx==0.27.0 \
        aiofiles==24.1.0 \
        redis==5.1.0 \
    && apk del gcc g++ musl-dev libffi-dev openssl-dev \
    && find /usr/local/lib/python3.11 -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.11 -name '*.pyc' -delete 2>/dev/null || true \
    && find /usr/local/lib/python3.11 -name 'tests' -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.11 -name 'test' -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.11 -name '*.dist-info' -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf /var/cache/apk/* /root/.cache /tmp/*

# 复制后端代码
COPY backend/ ./

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# 创建数据目录
RUN mkdir -p /root/.unifile/db /root/.unifile/backups

# 复制配置文件
COPY docker/nginx.conf /etc/nginx/http.d/default.conf
COPY docker/supervisord.conf /etc/supervisord.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/api/health || exit 1

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
