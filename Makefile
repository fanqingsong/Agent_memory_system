.PHONY: help start stop restart logs status clean build up down

# 默认目标
help:
	@echo "Agent Memory System - Docker 管理命令"
	@echo ""
	@echo "可用命令:"
	@echo "  make start     - 启动服务"
	@echo "  make stop      - 停止服务"
	@echo "  make restart   - 重启服务"
	@echo "  make logs      - 查看日志"
	@echo "  make status    - 查看状态"
	@echo "  make clean     - 清理服务和数据"
	@echo "  make build     - 构建镜像"
	@echo "  make up        - 启动服务（前台）"
	@echo "  make down      - 停止服务"
	@echo ""
	@echo "示例:"
	@echo "  make start     # 启动基础服务"
	@echo "  make logs      # 查看所有日志"

# 启动服务
start:
	@echo "启动 Agent Memory System 服务..."
	@if [ -f "scripts/docker-start.sh" ]; then \
		./scripts/docker-start.sh start; \
	else \
		docker-compose up -d --build; \
	fi

# 停止服务
stop:
	@echo "停止 Agent Memory System 服务..."
	@if [ -f "scripts/docker-start.sh" ]; then \
		./scripts/docker-start.sh stop; \
	else \
		docker-compose down; \
	fi

# 重启服务
restart:
	@echo "重启 Agent Memory System 服务..."
	@if [ -f "scripts/docker-start.sh" ]; then \
		./scripts/docker-start.sh restart; \
	else \
		docker-compose down && docker-compose up -d --build; \
	fi

# 查看日志
logs:
	@echo "查看服务日志..."
	@if [ -f "scripts/docker-start.sh" ]; then \
		./scripts/docker-start.sh logs; \
	else \
		docker-compose logs -f; \
	fi

# 查看状态
status:
	@echo "服务状态:"
	@if [ -f "scripts/docker-start.sh" ]; then \
		./scripts/docker-start.sh status; \
	else \
		docker-compose ps; \
	fi

# 清理服务和数据
clean:
	@echo "清理服务和数据..."
	@if [ -f "scripts/docker-start.sh" ]; then \
		./scripts/docker-start.sh cleanup; \
	else \
		docker-compose down -v --remove-orphans; \
	fi

# 构建镜像
build:
	@echo "构建 Docker 镜像..."
	docker-compose build --no-cache

# 启动服务（前台）
up:
	@echo "启动服务（前台模式）..."
	docker-compose up --build

# 停止服务
down:
	@echo "停止服务..."
	docker-compose down



# 查看特定服务日志
logs-app:
	@echo "查看应用服务日志..."
	docker-compose logs -f app

logs-neo4j:
	@echo "查看 Neo4j 日志..."
	docker-compose logs -f neo4j

logs-redis:
	@echo "查看 Redis 日志..."
	docker-compose logs -f redis

# 进入容器
shell-app:
	@echo "进入应用容器..."
	docker-compose exec app bash

shell-neo4j:
	@echo "进入 Neo4j 容器..."
	docker-compose exec neo4j bash

shell-redis:
	@echo "进入 Redis 容器..."
	docker-compose exec redis sh

# 备份数据
backup:
	@echo "备份数据..."
	@mkdir -p backups
	docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/backups/ || true
	docker cp agent-memory-neo4j:/backups/. ./backups/ || true
	@echo "备份完成，数据保存在 ./backups/ 目录"

# 恢复数据
restore:
	@echo "恢复数据..."
	@if [ ! -d "backups" ]; then \
		echo "错误: 未找到备份目录"; \
		exit 1; \
	fi
	docker-compose exec neo4j neo4j-admin load --database=neo4j --from=/backups/ || true
	@echo "数据恢复完成"

# 检查健康状态
health:
	@echo "检查服务健康状态..."
	@curl -f http://localhost:8000/health || echo "应用服务不可用"
	@docker-compose exec -T neo4j cypher-shell -u neo4j -p password123 "RETURN 1" > /dev/null 2>&1 || echo "Neo4j 不可用"
	@docker-compose exec -T redis redis-cli ping > /dev/null 2>&1 || echo "Redis 不可用" 