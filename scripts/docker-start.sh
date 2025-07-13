#!/bin/bash

# Agent Memory System Docker 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_message $RED "错误: Docker 未安装"
        print_message $YELLOW "请先安装 Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_message $RED "错误: Docker Compose 未安装"
        print_message $YELLOW "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_message $GREEN "✓ Docker 和 Docker Compose 已安装"
}

# 检查环境变量文件
check_env_file() {
    if [ ! -f ".env" ]; then
        print_message $YELLOW "未找到 .env 文件，正在创建..."
        if [ -f "env.example" ]; then
            cp env.example .env
            print_message $GREEN "✓ 已从 env.example 创建 .env 文件"
            print_message $YELLOW "请编辑 .env 文件配置您的环境变量"
        else
            print_message $RED "错误: 未找到 env.example 文件"
            exit 1
        fi
    else
        print_message $GREEN "✓ .env 文件已存在"
    fi
}

# 创建必要的目录
create_directories() {
    print_message $BLUE "创建必要的目录..."
    mkdir -p data logs
    print_message $GREEN "✓ 目录创建完成"
}

# 构建和启动服务
start_services() {
    print_message $BLUE "构建和启动服务..."
    
    # 检查是否包含 Ollama 服务
    if [ "$1" = "--with-ollama" ]; then
        print_message $YELLOW "启动包含 Ollama 的完整服务..."
        docker-compose --profile ollama up -d --build
    else
        print_message $YELLOW "启动基础服务..."
        docker-compose up -d --build
    fi
    
    print_message $GREEN "✓ 服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    print_message $BLUE "等待服务就绪..."
    
    # 等待 Neo4j
    print_message $YELLOW "等待 Neo4j 就绪..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T neo4j cypher-shell -u neo4j -p password123 "RETURN 1" > /dev/null 2>&1; then
            print_message $GREEN "✓ Neo4j 已就绪"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_message $RED "错误: Neo4j 启动超时"
        exit 1
    fi
    
    # 等待 Redis
    print_message $YELLOW "等待 Redis 就绪..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            print_message $GREEN "✓ Redis 已就绪"
            break
        fi
        sleep 1
        timeout=$((timeout - 1))
    done
    
    if [ $timeout -le 0 ]; then
        print_message $RED "错误: Redis 启动超时"
        exit 1
    fi
    
    # 等待应用服务
    print_message $YELLOW "等待应用服务就绪..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_message $GREEN "✓ 应用服务已就绪"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_message $RED "错误: 应用服务启动超时"
        exit 1
    fi
}

# 显示服务状态
show_status() {
    print_message $BLUE "服务状态:"
    docker-compose ps
    
    print_message $BLUE "服务访问地址:"
    print_message $GREEN "  - 应用 API: http://localhost:8000"
    print_message $GREEN "  - API 文档: http://localhost:8000/docs"
    print_message $GREEN "  - Neo4j 浏览器: http://localhost:7474"
    print_message $GREEN "  - Redis 客户端: localhost:6379"
    
    if [ "$1" = "--with-ollama" ]; then
        print_message $GREEN "  - Ollama API: http://localhost:11434"
    fi
}

# 显示日志
show_logs() {
    print_message $BLUE "显示服务日志 (按 Ctrl+C 退出)..."
    docker-compose logs -f
}

# 停止服务
stop_services() {
    print_message $BLUE "停止服务..."
    docker-compose down
    print_message $GREEN "✓ 服务已停止"
}

# 清理服务
cleanup_services() {
    print_message $BLUE "清理服务..."
    docker-compose down -v --remove-orphans
    print_message $GREEN "✓ 服务已清理"
}

# 主函数
main() {
    case "$1" in
        "start")
            check_docker
            check_env_file
            create_directories
            start_services "$2"
            wait_for_services
            show_status "$2"
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 2
            start_services "$2"
            wait_for_services
            show_status "$2"
            ;;
        "logs")
            show_logs
            ;;
        "cleanup")
            cleanup_services
            ;;
        "status")
            docker-compose ps
            ;;
        *)
            echo "用法: $0 {start|stop|restart|logs|cleanup|status} [--with-ollama]"
            echo ""
            echo "命令:"
            echo "  start       启动服务"
            echo "  stop        停止服务"
            echo "  restart     重启服务"
            echo "  logs        显示日志"
            echo "  cleanup     清理服务（包括数据卷）"
            echo "  status      显示服务状态"
            echo ""
            echo "选项:"
            echo "  --with-ollama  包含 Ollama 服务"
            echo ""
            echo "示例:"
            echo "  $0 start              # 启动基础服务"
            echo "  $0 start --with-ollama # 启动包含 Ollama 的完整服务"
            echo "  $0 logs               # 查看日志"
            echo "  $0 stop               # 停止服务"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@" 