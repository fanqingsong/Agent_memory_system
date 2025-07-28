#!/bin/bash

# 生产环境停止脚本
echo "🛑 停止 Agent Memory System 生产环境..."

# 停止生产环境服务
echo "🔧 停止生产环境服务..."
docker compose down

# 检查是否还有相关容器在运行
echo "🔍 检查剩余容器..."
if docker ps --filter "name=agent-memory" --format "table {{.Names}}\t{{.Status}}" | grep -q "agent-memory"; then
    echo "⚠️  发现相关容器仍在运行:"
    docker ps --filter "name=agent-memory" --format "table {{.Names}}\t{{.Status}}"
    echo ""
    read -p "是否强制停止这些容器? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔧 强制停止相关容器..."
        docker ps --filter "name=agent-memory" -q | xargs -r docker stop
        docker ps --filter "name=agent-memory" -q | xargs -r docker rm
    fi
else
    echo "✅ 所有相关容器已停止"
fi

echo ""
echo "✅ 生产环境已停止!"
echo ""
echo "📝 管理命令:"
echo "  - 启动生产环境: './bin/start-prod.sh'"
echo "  - 查看日志: 'docker compose logs -f'"
echo "  - 清理数据: 'docker compose down -v'" 