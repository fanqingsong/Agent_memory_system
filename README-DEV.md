# Agent Memory System - 开发环境指南

## 🚀 快速开始

### 开发环境（推荐）

```bash
# 启动开发环境（支持热重载）
./dev.sh

# 或者手动启动
docker compose -f docker-compose.dev.yml up -d
```

### 生产环境

```bash
# 启动生产环境
./prod.sh

# 或者手动启动
docker compose up -d --build
```

## 🔧 开发环境特性

### 后端热重载
- 修改 `backend/agent_memory_system/` 下的 Python 代码会自动重启服务
- 修改 `backend/pyproject.toml` 会自动重新构建
- 修改 `backend/Dockerfile` 会自动重新构建

### 前端热重载
- 修改 `frontend/src/` 下的 React 代码会自动刷新页面
- 修改 `frontend/public/` 下的静态文件会自动同步
- 修改 `frontend/package.json` 会自动重新构建

## 📊 服务状态检查

```bash
# 查看所有服务状态
docker compose -f docker-compose.dev.yml ps

# 查看服务日志
docker compose -f docker-compose.dev.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend
```

## 🌐 访问地址

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Neo4j数据库**: http://localhost:7474
- **Redis**: localhost:6379


## 🔍 调试技巧

### 1. 后端调试
```bash
# 查看后端实时日志
docker compose -f docker-compose.dev.yml logs -f backend

# 进入后端容器
docker compose -f docker-compose.dev.yml exec backend bash

# 重启后端服务
docker compose -f docker-compose.dev.yml restart backend
```

### 2. 前端调试
```bash
# 查看前端实时日志
docker compose -f docker-compose.dev.yml logs -f frontend

# 进入前端容器
docker compose -f docker-compose.dev.yml exec frontend sh

# 重启前端服务
docker compose -f docker-compose.dev.yml restart frontend
```

### 3. 数据库调试
```bash
# 查看 Neo4j 日志
docker compose -f docker-compose.dev.yml logs -f neo4j

# 进入 Neo4j 容器
docker compose -f docker-compose.dev.yml exec neo4j cypher-shell -u neo4j -p password123
```

## 🛠️ 常用命令

```bash
# 启动开发环境
./dev.sh

# 启动生产环境
./prod.sh

# 停止所有服务
docker compose -f docker-compose.dev.yml down

# 重新构建并启动
docker compose -f docker-compose.dev.yml up -d --build

# 查看服务状态
docker compose -f docker-compose.dev.yml ps

# 查看实时日志
docker compose -f docker-compose.dev.yml logs -f

# 清理数据卷（谨慎使用）
docker compose -f docker-compose.dev.yml down -v
```

## 📝 开发注意事项

### 1. 文件同步
- 开发环境使用 Docker Compose Watch 功能
- 代码修改会自动同步到容器内
- 如果同步不生效，可以重启对应服务

### 2. 端口冲突
- 确保本地 3000、8000、7474、6379、11434 端口未被占用
- 如有冲突，可以修改 `docker-compose.dev.yml` 中的端口映射

### 3. 数据持久化
- 开发环境使用独立的数据卷（带 `_dev` 后缀）
- 生产环境和开发环境的数据是隔离的
- 如需清理数据，使用 `docker compose -f docker-compose.dev.yml down -v`

### 4. 环境变量
- 开发环境使用 `DEBUG=true`
- 生产环境使用 `DEBUG=false`
- 可以通过修改 `docker-compose.dev.yml` 中的环境变量来调整配置

## 🐛 故障排除

### 1. 服务启动失败
```bash
# 查看详细错误日志
docker compose -f docker-compose.dev.yml logs

# 检查端口占用
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000
```

### 2. 热重载不工作
```bash
# 重启开发环境
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d

# 检查文件权限
ls -la backend/agent_memory_system/
ls -la frontend/src/
```

### 3. 网络连接问题
```bash
# 检查网络
docker network ls
docker network inspect agent_memory_system_agent-memory-network

# 重启网络
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d
```

## 📚 相关文档

- [Docker Compose Watch 文档](https://docs.docker.com/compose/file-watch/)
- [FastAPI 开发文档](https://fastapi.tiangolo.com/tutorial/)
- [React 开发文档](https://react.dev/)
- [Neo4j 文档](https://neo4j.com/docs/) 