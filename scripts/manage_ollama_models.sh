#!/bin/bash

# Ollama模型管理脚本
# 用于管理Ollama模型的下载、列表、删除等操作

set -e

# 配置
OLLAMA_HOST="http://localhost:11434"
DEFAULT_MODEL="qwen2.5:0.5b"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查Ollama服务是否运行
check_ollama_service() {
    log_step "检查Ollama服务状态..."
    
    if curl -s "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; then
        log_info "Ollama服务正在运行"
        return 0
    else
        log_error "Ollama服务未运行或无法访问"
        log_info "请确保Ollama容器已启动: docker-compose up -d ollama"
        return 1
    fi
}

# 列出已安装的模型
list_models() {
    log_step "获取已安装的模型列表..."
    
    if ! check_ollama_service; then
        return 1
    fi
    
    response=$(curl -s "$OLLAMA_HOST/api/tags")
    models=$(echo "$response" | jq -r '.models[].name' 2>/dev/null || echo "")
    
    if [ -z "$models" ]; then
        log_warn "没有找到已安装的模型"
    else
        log_info "已安装的模型:"
        echo "$models" | while read -r model; do
            echo "  - $model"
        done
    fi
}

# 下载模型
download_model() {
    local model_name=${1:-$DEFAULT_MODEL}
    
    log_step "开始下载模型: $model_name"
    
    if ! check_ollama_service; then
        return 1
    fi
    
    # 检查模型是否已存在
    existing_models=$(curl -s "$OLLAMA_HOST/api/tags" | jq -r '.models[].name' 2>/dev/null || echo "")
    if echo "$existing_models" | grep -q "^$model_name$"; then
        log_warn "模型 $model_name 已存在，跳过下载"
        return 0
    fi
    
    log_info "开始下载模型 $model_name，这可能需要几分钟..."
    
    # 下载模型
    curl -X POST "$OLLAMA_HOST/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$model_name\"}" \
        --progress-bar
    
    if [ $? -eq 0 ]; then
        log_info "模型 $model_name 下载完成"
    else
        log_error "模型 $model_name 下载失败"
        return 1
    fi
}

# 删除模型
delete_model() {
    local model_name=$1
    
    if [ -z "$model_name" ]; then
        log_error "请指定要删除的模型名称"
        echo "用法: $0 delete <model_name>"
        return 1
    fi
    
    log_step "删除模型: $model_name"
    
    if ! check_ollama_service; then
        return 1
    fi
    
    # 检查模型是否存在
    existing_models=$(curl -s "$OLLAMA_HOST/api/tags" | jq -r '.models[].name' 2>/dev/null || echo "")
    if ! echo "$existing_models" | grep -q "^$model_name$"; then
        log_warn "模型 $model_name 不存在"
        return 0
    fi
    
    # 删除模型
    curl -X DELETE "$OLLAMA_HOST/api/delete" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$model_name\"}"
    
    if [ $? -eq 0 ]; then
        log_info "模型 $model_name 删除成功"
    else
        log_error "模型 $model_name 删除失败"
        return 1
    fi
}

# 测试模型
test_model() {
    local model_name=${1:-$DEFAULT_MODEL}
    
    log_step "测试模型: $model_name"
    
    if ! check_ollama_service; then
        return 1
    fi
    
    # 检查模型是否存在
    existing_models=$(curl -s "$OLLAMA_HOST/api/tags" | jq -r '.models[].name' 2>/dev/null || echo "")
    if ! echo "$existing_models" | grep -q "^$model_name$"; then
        log_error "模型 $model_name 不存在，请先下载"
        return 1
    fi
    
    log_info "发送测试请求到模型 $model_name..."
    
    # 发送测试请求
    response=$(curl -s -X POST "$OLLAMA_HOST/api/generate" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "'$model_name'",
            "prompt": "Hello, please respond with a simple greeting.",
            "stream": false
        }')
    
    if [ $? -eq 0 ]; then
        log_info "模型测试成功"
        echo "响应: $(echo "$response" | jq -r '.response' 2>/dev/null || echo '无法解析响应')"
    else
        log_error "模型测试失败"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "Ollama模型管理脚本"
    echo ""
    echo "用法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  list                   列出已安装的模型"
    echo "  download [model_name]   下载模型 (默认: $DEFAULT_MODEL)"
    echo "  delete <model_name>     删除指定模型"
    echo "  test [model_name]       测试模型 (默认: $DEFAULT_MODEL)"
    echo "  status                  检查Ollama服务状态"
    echo "  help                    显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 list"
    echo "  $0 download"
    echo "  $0 download llama2"
    echo "  $0 delete llama2"
    echo "  $0 test"
    echo ""
    echo "常用小模型推荐:"
    echo "  - qwen2.5:0.5b          (约0.5GB)"
    echo "  - qwen2.5:1.5b          (约1.5GB)"
    echo "  - llama2:7b             (约4GB)"
    echo "  - mistral:7b            (约4GB)"
}

# 主函数
main() {
    local command=${1:-help}
    
    case $command in
        "list")
            list_models
            ;;
        "download")
            download_model "$2"
            ;;
        "delete")
            delete_model "$2"
            ;;
        "test")
            test_model "$2"
            ;;
        "status")
            check_ollama_service
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 检查依赖
check_dependencies() {
    if ! command -v curl &> /dev/null; then
        log_error "curl 未安装"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_warn "jq 未安装，某些功能可能受限"
    fi
}

# 脚本入口
check_dependencies
main "$@" 