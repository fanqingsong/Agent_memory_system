# Agent Memory System - Docker 部署指南

## 快速开始

### 前置要求
- Docker Desktop 或 Docker Engine
- Docker Compose
- 至少 4GB 内存

### 1. 配置环境变量
```bash
cp env.example .env
# 编辑 .env 文件，配置 OPENAI_API_KEY 等必要变量
```

### 2. 启动服务
```bash
# Linux/Mac
./scripts/docker-start.sh start

# Windows
scripts\docker-start.bat start
```

### 3. 访问服务
- 应用 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- Neo4j 浏览器: http://localhost:7474

## 服务说明

| 服务 | 端口 | 描述 |
|------|------|------|
| app | 8000 | FastAPI 应用 |
| neo4j | 7474, 7687 | 图数据库 |
| redis | 6379 | 缓存数据库 |


## 管理命令

```bash
# 启动服务
./scripts/docker-start.sh start

# 停止服务
./scripts/docker-start.sh stop

# 查看日志
./scripts/docker-start.sh logs

# 查看状态
./scripts/docker-start.sh status
``` 