#!/bin/bash

# 开发环境启动脚本
echo "🚀 启动 Agent Memory System 开发环境..."

# 检查 Docker Compose 版本
if ! docker compose version > /dev/null 2>&1; then
    echo "❌ 错误: 需要 Docker Compose v2.20+ 来支持 watch 功能"
    exit 1
fi

# 停止现有服务
echo "🛑 停止现有服务..."
docker compose -f docker-compose.dev.yml down

# 启动开发环境
echo "🔧 启动开发环境 (支持热重载)..."
docker compose -f docker-compose.dev.yml up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 服务状态:"
docker compose -f docker-compose.dev.yml ps

echo ""
echo "✅ 开发环境启动完成!"
echo ""
echo "🌐 访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端API: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "  Neo4j: http://localhost:7474"
echo ""
echo "📝 开发提示:"
echo "  - 修改后端代码会自动重启服务"
echo "  - 修改前端代码会自动刷新页面"
echo "  - 使用 './bin/stop-dev.sh' 停止服务"
echo "  - 使用 'docker compose -f docker-compose.dev.yml logs -f' 查看日志" 