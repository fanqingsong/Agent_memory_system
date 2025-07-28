#!/bin/bash

# 生产环境启动脚本
echo "🚀 启动 Agent Memory System 生产环境..."

# 检查 Docker Compose 版本
if ! docker compose version > /dev/null 2>&1; then
    echo "❌ 错误: 需要 Docker Compose v2.20+"
    exit 1
fi

# 停止现有服务
echo "🛑 停止现有服务..."
docker compose down

# 构建并启动生产环境
echo "🔧 构建并启动生产环境..."
docker compose up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "📊 服务状态:"
docker compose ps

echo ""
echo "✅ 生产环境启动完成!"
echo ""
echo "🌐 访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端API: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "  Neo4j: http://localhost:7474"
echo ""
echo "📝 管理命令:"
echo "  - 使用 './bin/stop-prod.sh' 停止服务"
echo "  - 查看日志: 'docker compose logs -f'"
echo "  - 重启服务: 'docker compose restart'" 