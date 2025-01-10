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

# 检测系统类型
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VERSION=$VERSION_ID
    else
        OS=$(uname -s)
        VERSION=$(uname -r)
    fi
    print_message $GREEN "检测到系统: $OS $VERSION"
}

# 安装Neo4j
install_neo4j() {
    print_message $YELLOW "正在安装Neo4j..."
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        # 添加Neo4j仓库
        curl -fsSL https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
        echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
        sudo apt-get update
        sudo apt-get install -y neo4j
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        # 添加Neo4j仓库
        sudo rpm --import https://debian.neo4j.com/neotechnology.gpg.key
        sudo cat << EOF > /etc/yum.repos.d/neo4j.repo
[neo4j]
name=Neo4j RPM Repository
baseurl=https://yum.neo4j.com/stable
enabled=1
gpgcheck=1
EOF
        sudo yum install -y neo4j
    else
        print_message $RED "不支持的系统类型: $OS"
        print_message $YELLOW "请手动安装Neo4j: https://neo4j.com/docs/operations-manual/current/installation/"
        exit 1
    fi
    sudo systemctl enable neo4j
    sudo systemctl start neo4j
    print_message $GREEN "Neo4j安装完成"
}

# 安装Redis
install_redis() {
    print_message $YELLOW "正在安装Redis..."
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        sudo apt-get update
        sudo apt-get install -y redis-server
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        sudo yum install -y epel-release
        sudo yum install -y redis
    else
        print_message $RED "不支持的系统类型: $OS"
        print_message $YELLOW "请手动安装Redis: https://redis.io/docs/getting-started/"
        exit 1
    fi
    sudo systemctl enable redis
    sudo systemctl start redis
    print_message $GREEN "Redis安装完成"
}

# 检查Neo4j
check_neo4j() {
    print_message $YELLOW "检查Neo4j..."
    if ! command -v neo4j &> /dev/null; then
        print_message $YELLOW "未找到Neo4j，准备安装..."
        install_neo4j
    else
        print_message $GREEN "Neo4j已安装"
        # 检查服务状态
        if ! systemctl is-active --quiet neo4j; then
            print_message $YELLOW "Neo4j服务未运行，正在启动..."
            sudo systemctl start neo4j
        fi
    fi
}

# 检查Redis
check_redis() {
    print_message $YELLOW "检查Redis..."
    if ! command -v redis-cli &> /dev/null; then
        print_message $YELLOW "未找到Redis，准备安装..."
        install_redis
    else
        print_message $GREEN "Redis已安装"
        # 检查服务状态
        if ! systemctl is-active --quiet redis; then
            print_message $YELLOW "Redis服务未运行，正在启动..."
            sudo systemctl start redis
        fi
    fi
}

# 安装项目依赖
install_dependencies() {
    print_message $YELLOW "安装项目依赖..."
    # 根据系统类型选择正确的FAISS包
    if [[ "$OS" == *"Linux"* ]]; then
        poetry add "faiss-cpu@^1.7.4"
        poetry remove faiss-windows
    fi
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

# 主函数
main() {
    print_message $GREEN "开始设置Agent Memory System环境..."
    
    # 检测系统类型
    detect_os
    
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
    
    # 检查并安装数据库
    check_neo4j
    check_redis
    
    print_message $GREEN "环境设置完成!"
    print_message $YELLOW "请确保:"
    print_message $YELLOW "1. 配置.env文件中的必要参数"
    print_message $YELLOW "2. Neo4j服务已启动"
    print_message $YELLOW "3. Redis服务已启动"
    print_message $GREEN "然后运行: poetry run python -m agent_memory_system.main"
}

# 执行主函数
main