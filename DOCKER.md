# UniFile Docker 部署指南

## 快速开始

### 方式一：使用 Docker Compose（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式二：使用 Docker 命令

```bash
# 构建镜像
docker build -t unifile .

# 运行容器
docker run -d \
  --name unifile \
  -p 8080:80 \
  -v unifile-data:/root/.unifile \
  --restart unless-stopped \
  unifile
```

## 访问服务

- 首页：http://localhost:8080/
- 后台：http://localhost:8080/admin/dashboard
- 默认账号：admin / admin123

## 数据持久化

数据库和备份文件存储在 `/root/.unifile` 目录：

```
/root/.unifile/
├── db/
│   └── unifile.db    # SQLite 数据库
└── backups/          # 备份文件
```

使用 Docker Volume 持久化：
```bash
# Docker Compose
docker-compose down -v  # 删除 volumes
docker-compose up -d    # 重新创建

# Docker 命令
docker volume ls                      # 查看 volumes
docker volume rm unifile-data         # 删除 volume
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| TZ | Asia/Shanghai | 时区设置 |

## 常用命令

```bash
# 查看容器状态
docker ps

# 查看日志
docker logs -f unifile

# 进入容器
docker exec -it unifile bash

# 重启容器
docker restart unifile

# 停止容器
docker stop unifile

# 删除容器
docker rm -f unifile

# 删除镜像
docker rmi unifile
```

## 自定义配置

### 修改端口

```bash
# Docker Compose - 修改 docker-compose.yml
ports:
  - "3000:80"  # 改为 3000 端口

# Docker 命令
docker run -d -p 3000:80 ...
```

### 挂载外部数据库

```bash
# 使用已有的 SQLite 数据库
docker run -d \
  -p 8080:80 \
  -v /path/to/your/unifile.db:/root/.unifile/db/unifile.db \
  unifile
```

## 故障排查

### 容器无法启动

```bash
# 查看容器日志
docker logs unifile

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

## 构建优化

### 使用构建缓存

```bash
# 使用 BuildKit 加速
DOCKER_BUILDKIT=1 docker build -t unifile .

# 多平台构建
docker buildx build --platform linux/amd64,linux/arm64 -t unifile .
```

### 减小镜像体积

```bash
# 清理构建缓存
docker builder prune

# 查看镜像大小
docker images unifile
```

## 生产环境建议

1. **使用反向代理**：在 Docker 前使用 Nginx/Caddy 做反向代理
2. **HTTPS**：配置 SSL 证书
3. **定期备份**：设置定时任务备份数据库
4. **监控**：使用 Docker 监控工具监控容器状态
5. **日志收集**：配置日志收集系统

## 镜像发布

```bash
# 登录 Docker Hub
docker login

# 打标签
docker tag unifile yourusername/unifile:latest
docker tag unifile yourusername/unifile:1.0.0

# 推送镜像
docker push yourusername/unifile:latest
docker push yourusername/unifile:1.0.0
```