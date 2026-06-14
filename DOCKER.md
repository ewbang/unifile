# UniFile Docker 部署指南

## 快速开始

### 方式一：拉取镜像启动（推荐）

```bash
# 拉取镜像
docker pull mrpc2060/unifile

# 一键启动
docker run -d \
  --name unifile \
  -p 8080:80 \
  -v unifile-data:/root/.unifile \
  --restart unless-stopped \
  mrpc2060/unifile
```

### 方式二：一键部署（本地构建）

```bash
# 构建镜像并启动服务
./deploy.sh
```

脚本会自动：
1. 清理并重新编译前端
2. 构建 Docker 镜像
3. 清理悬空镜像
4. 启动服务

### 手动部署

```bash
# 使用 Docker Compose
cd docker
docker compose up -d --build
```

## 访问服务

- 首页：http://localhost:8080/
- 后台：http://localhost:8080/admin/dashboard
- 默认账号：admin / admin123

## 常用命令

```bash
# 查看日志
docker compose -f docker/docker-compose.yml logs -f

# 停止服务
docker compose -f docker/docker-compose.yml down

# 重启服务
docker compose -f docker/docker-compose.yml restart

# 查看容器状态
docker ps

# 进入容器
docker exec -it unifile bash
```

## 数据持久化

数据库和备份文件存储在 Docker volume `unifile-data` 中，容器重建不会丢失数据。

数据目录结构：
```
/root/.unifile/
├── db/
│   └── unifile.db    # SQLite 数据库
└── backups/          # 备份文件
```

```bash
# 查看 volumes
docker volume ls

# 删除 volume（会丢失数据）
docker compose -f docker/docker-compose.yml down -v

# 重新创建
docker compose -f docker/docker-compose.yml up -d
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| TZ | Asia/Shanghai | 时区设置 |

## 自定义配置

### 修改端口

修改 `docker/docker-compose.yml`：
```yaml
ports:
  - "3000:80"  # 改为 3000 端口
```

### 挂载外部数据库

```bash
docker run -d \
  -p 8080:80 \
  -v /path/to/your/unifile.db:/root/.unifile/db/unifile.db \
  unifile
```

## 构建优化

```bash
# 使用 BuildKit 加速
DOCKER_BUILDKIT=1 docker build -f docker/Dockerfile -t unifile .

# 多平台构建
docker buildx build --platform linux/amd64,linux/arm64 -f docker/Dockerfile -t unifile .

# 清理构建缓存
docker builder prune

# 清理悬空镜像
docker image prune -f

# 查看镜像大小
docker images unifile
```

## 故障排查

### 容器无法启动

```bash
# 查看容器日志
docker compose -f docker/docker-compose.yml logs

# 检查容器状态
docker inspect unifile
```

### 数据库损坏

```bash
# 进入容器
docker exec -it unifile bash

# 检查数据库
sqlite3 /root/.unifile/db/unifile.db "PRAGMA integrity_check;"

# 从备份还原
cp /root/.unifile/backups/备份文件.db /root/.unifile/db/unifile.db
```

### 端口冲突

```bash
# 检查端口占用
netstat -tlnp | grep 8080
lsof -i :8080

# 使用其他端口
docker run -d -p 9090:80 ...
```

## 生产环境建议

1. **使用反向代理**：在 Docker 前使用 Nginx/Caddy 做反向代理
2. **HTTPS**：配置 SSL 证书
3. **定期备份**：设置定时任务备份数据库
4. **监控**：使用 Docker 监控工具监控容器状态
5. **日志收集**：配置日志收集系统
