# ==================== 最终运行镜像 ====================
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

# 前端产物（预编译）
COPY frontend/dist /usr/share/nginx/html

# 数据目录
RUN mkdir -p \
    /root/.unifile/db \
    /root/.unifile/backups

# nginx配置 + pid路径修复
COPY docker/nginx.conf /etc/nginx/http.d/default.conf

# 启动脚本
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/api/health >/dev/null || exit 1

CMD ["/start.sh"]
