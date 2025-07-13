#!/bin/bash

# Docker 测试脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message $BLUE "开始 Docker 测试..."

# 1. 检查 Docker 是否运行
print_message $YELLOW "1. 检查 Docker 服务..."
if ! docker info > /dev/null 2>&1; then
    print_message $RED "错误: Docker 服务未运行"
    exit 1
fi
print_message $GREEN "✓ Docker 服务正常运行"

# 2. 检查 Docker Compose 配置
print_message $YELLOW "2. 验证 Docker Compose 配置..."
if ! docker-compose config > /dev/null 2>&1; then
    print_message $RED "错误: Docker Compose 配置无效"
    exit 1
fi
print_message $GREEN "✓ Docker Compose 配置有效"

# 3. 测试构建镜像
print_message $YELLOW "3. 测试构建应用镜像..."
if ! docker-compose build app > /dev/null 2>&1; then
    print_message $RED "错误: 应用镜像构建失败"
    exit 1
fi
print_message $GREEN "✓ 应用镜像构建成功"

# 4. 测试拉取基础镜像
print_message $YELLOW "4. 测试拉取基础镜像..."
if ! docker pull neo4j:5.9 > /dev/null 2>&1; then
    print_message $RED "错误: Neo4j 镜像拉取失败"
    exit 1
fi

if ! docker pull redis:7-alpine > /dev/null 2>&1; then
    print_message $RED "错误: Redis 镜像拉取失败"
    exit 1
fi

if ! docker pull ollama/ollama:latest > /dev/null 2>&1; then
    print_message $YELLOW "警告: Ollama 镜像拉取失败（可选服务）"
else
    print_message $GREEN "✓ Ollama 镜像拉取成功"
fi

print_message $GREEN "✓ 基础镜像拉取成功"

# 5. 检查端口可用性
print_message $YELLOW "5. 检查端口可用性..."
check_port() {
    local port=$1
    local service=$2
    if netstat -tuln | grep ":$port " > /dev/null 2>&1; then
        print_message $YELLOW "警告: 端口 $port 已被占用（$service）"
        return 1
    else
        print_message $GREEN "✓ 端口 $port 可用"
        return 0
    fi
}

check_port 8000 "应用服务"
check_port 7474 "Neo4j HTTP"
check_port 7687 "Neo4j Bolt"
check_port 6379 "Redis"
check_port 11434 "Ollama"

# 6. 检查环境变量文件
print_message $YELLOW "6. 检查环境变量文件..."
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        print_message $YELLOW "未找到 .env 文件，从 env.example 创建..."
        cp env.example .env
        print_message $GREEN "✓ 已创建 .env 文件"
    else
        print_message $RED "错误: 未找到环境变量文件"
        exit 1
    fi
else
    print_message $GREEN "✓ .env 文件存在"
fi

# 7. 创建必要目录
print_message $YELLOW "7. 创建必要目录..."
mkdir -p data logs
print_message $GREEN "✓ 目录创建完成"

# 8. 测试网络创建
print_message $YELLOW "8. 测试网络创建..."
if ! docker network create agent-memory-test > /dev/null 2>&1; then
    if ! docker network ls | grep agent-memory-test > /dev/null 2>&1; then
        print_message $RED "错误: 网络创建失败"
        exit 1
    fi
fi
print_message $GREEN "✓ 网络创建成功"

# 清理测试网络
docker network rm agent-memory-test > /dev/null 2>&1 || true

print_message $GREEN "🎉 Docker 测试完成！所有检查都通过了。"
print_message $BLUE "现在可以使用以下命令启动服务："
echo ""
print_message $YELLOW "  ./scripts/docker-start.sh start"
print_message $YELLOW "  或"
print_message $YELLOW "  make start"
echo ""
print_message $BLUE "更多信息请查看 DOCKER_README.md" 