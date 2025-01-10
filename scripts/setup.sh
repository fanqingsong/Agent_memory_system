#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_message $RED "错误: 未找到命令 '$1'"
        print_message $YELLOW "请先安装 $1"
        exit 1
    fi
}

# 检查Python版本
check_python_version() {
    local version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)
    
    if [ "$major" -lt 3 ]; then
        print_message $RED "错误: Python版本必须 >= 3.9"
        print_message $YELLOW "当前版本: $version"
        exit 1
    fi
    
    if [ "$major" -eq 3 ] && [ "$minor" -lt 9 ]; then
        print_message $RED "错误: Python版本必须 >= 3.9"
        print_message $YELLOW "当前版本: $version"
        exit 1
    fi
    
    if [ "$major" -eq 3 ] && [ "$minor" -ge 12 ]; then
        print_message $RED "错误: Python版本必须 < 3.12"
        print_message $YELLOW "当前版本: $version"
        exit 1
    fi
}

# 创建目录
create_directories() {
    local dirs=("data" "logs" "data/faiss_index")
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_message $GREEN "创建目录: $dir"
        fi
    done
}

# 安装Poetry
install_poetry() {
    if ! command -v poetry &> /dev/null; then
        print_message $YELLOW "正在安装Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        print_message $GREEN "Poetry安装完成"
    else
        print_message $GREEN "Poetry已安装"
    fi
}

# 配置Poetry
configure_poetry() {
    print_message $YELLOW "配置Poetry..."
    poetry config virtualenvs.create true
    poetry config virtualenvs.in-project true
}

# 安装项目依赖
install_dependencies() {
    print_message $YELLOW "安装项目依赖..."
    poetry install
    print_message $GREEN "依赖安装完成"
}

# 创建环境变量文件
create_env_file() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_message $GREEN "创建.env文件"
        else
            print_message $RED "错误: 未找到.env.example文件"
            exit 1
        fi
    else
        print_message $GREEN ".env文件已存在"
    fi
}

# 检查Neo4j
check_neo4j() {
    print_message $YELLOW "检查Neo4j..."
    if ! command -v neo4j &> /dev/null; then
        print_message $RED "警告: 未找到Neo4j"
        print_message $YELLOW "请参考文档安装Neo4j: https://neo4j.com/docs/operations-manual/current/installation/"
    else
        print_message $GREEN "Neo4j已安装"
    fi
}

# 检查Redis
check_redis() {
    print_message $YELLOW "检查Redis..."
    if ! command -v redis-cli &> /dev/null; then
        print_message $RED "警告: 未找到Redis"
        print_message $YELLOW "请参考文档安装Redis: https://redis.io/docs/getting-started/"
    else
        print_message $GREEN "Redis已安装"
    fi
}

# 主函数
main() {
    print_message $GREEN "开始设置Agent Memory System环境..."
    
    # 检查必要的命令
    check_command "python3"
    check_command "pip3"
    check_command "curl"
    
    # 检查Python版本
    check_python_version
    
    # 创建必要的目录
    create_directories
    
    # 安装和配置Poetry
    install_poetry
    configure_poetry
    
    # 安装项目依赖
    install_dependencies
    
    # 创建环境变量文件
    create_env_file
    
    # 检查数据库
    check_neo4j
    check_redis
    
    print_message $GREEN "环境设置完成!"
    print_message $YELLOW "请确保:"
    print_message $YELLOW "1. 配置.env文件中的必要参数"
    print_message $YELLOW "2. 启动Neo4j服务"
    print_message $YELLOW "3. 启动Redis服务"
    print_message $GREEN "然后运行: poetry run python -m agent_memory_system.main"
}

# 执行主函数
main