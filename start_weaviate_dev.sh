#!/bin/bash

# Weaviate开发环境启动脚本
# 用于快速启动包含Weaviate向量数据库的开发环境

set -e

echo "🚀 启动Agent Memory System开发环境 (包含Weaviate)"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查docker-compose是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose未安装，请先安装docker-compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到.env文件，从env.example复制..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ 已创建.env文件，请根据需要编辑配置"
    else
        echo "❌ 未找到env.example文件"
        exit 1
    fi
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data logs

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.dev.yml down

# 启动服务
echo "🔧 启动开发环境服务..."
docker-compose -f docker-compose.dev.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.dev.yml ps

# 检查Weaviate健康状态
echo "🔍 检查Weaviate健康状态..."
if curl -f http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
    echo "✅ Weaviate服务运行正常"
else
    echo "⚠️  Weaviate服务可能还在启动中，请稍后检查"
fi

# 检查其他服务
echo "🔍 检查其他服务..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端API服务运行正常"
else
    echo "⚠️  后端API服务可能还在启动中"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务运行正常"
else
    echo "⚠️  前端服务可能还在启动中"
fi

echo ""
echo "🎉 开发环境启动完成！"
echo ""
echo "📱 访问地址："
echo "  前端界面: http://localhost:3000"
echo "  后端API: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "  Neo4j浏览器: http://localhost:7474"
echo "  Weaviate管理: http://localhost:8080/v1/meta"
echo ""
echo "📋 常用命令："
echo "  查看日志: docker-compose -f docker-compose.dev.yml logs -f"
echo "  停止服务: docker-compose -f docker-compose.dev.yml down"
echo "  重启服务: docker-compose -f docker-compose.dev.yml restart"
echo ""
echo "🧪 测试Weaviate集成："
echo "  python test_weaviate_integration.py"
echo "" 