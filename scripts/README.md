# Ollama模型管理脚本

这个脚本用于管理Ollama模型的下载、列表、删除和测试等操作。

## 功能特性

- ✅ 检查Ollama服务状态
- ✅ 列出已安装的模型
- ✅ 下载指定模型
- ✅ 删除指定模型
- ✅ 测试模型功能
- ✅ 彩色日志输出
- ✅ 错误处理和重试

## 使用方法

### 基本用法

```bash
# 显示帮助信息
./scripts/manage_ollama_models.sh help

# 检查Ollama服务状态
./scripts/manage_ollama_models.sh status

# 列出已安装的模型
./scripts/manage_ollama_models.sh list

# 下载默认模型 (qwen2.5:0.5b)
./scripts/manage_ollama_models.sh download

# 下载指定模型
./scripts/manage_ollama_models.sh download qwen2.5:1.5b

# 测试默认模型
./scripts/manage_ollama_models.sh test

# 测试指定模型
./scripts/manage_ollama_models.sh test qwen2.5:0.5b

# 删除指定模型
./scripts/manage_ollama_models.sh delete llama2
```

### 常用小模型推荐

| 模型名称 | 大小 | 说明 |
|---------|------|------|
| qwen2.5:0.5b | ~0.5GB | 超小模型，适合快速测试 |
| qwen2.5:1.5b | ~1.5GB | 小模型，平衡性能和资源 |
| qwen2.5:3b | ~3GB | 中等模型，较好的性能 |
| llama2:7b | ~4GB | 经典模型，性能较好 |
| mistral:7b | ~4GB | 高性能模型 |

## 系统要求

- Linux/macOS系统
- curl (必需)
- jq (可选，用于更好的JSON解析)

## 安装依赖

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install curl jq
```

### CentOS/RHEL
```bash
sudo yum install curl jq
# 或者
sudo dnf install curl jq
```

### macOS
```bash
brew install curl jq
```

## 配置说明

脚本中的主要配置项：

```bash
# Ollama服务地址
OLLAMA_HOST="http://localhost:11434"

# 默认模型
DEFAULT_MODEL="qwen2.5:0.5b"
```

## 故障排除

### 1. Ollama服务未运行
```bash
# 启动Ollama服务
docker-compose up -d ollama

# 检查服务状态
./scripts/manage_ollama_models.sh status
```

### 2. 模型下载失败
- 检查网络连接
- 确保有足够的磁盘空间
- 尝试使用不同的模型

### 3. 权限问题
```bash
# 确保脚本有执行权限
chmod +x scripts/manage_ollama_models.sh
```

## 示例工作流

### 首次设置
```bash
# 1. 启动Ollama服务
docker-compose up -d ollama

# 2. 等待服务启动
sleep 30

# 3. 检查服务状态
./scripts/manage_ollama_models.sh status

# 4. 下载默认模型
./scripts/manage_ollama_models.sh download

# 5. 测试模型
./scripts/manage_ollama_models.sh test
```

### 日常使用
```bash
# 查看已安装的模型
./scripts/manage_ollama_models.sh list

# 测试模型功能
./scripts/manage_ollama_models.sh test

# 下载新模型
./scripts/manage_ollama_models.sh download qwen2.5:1.5b
```

## 注意事项

1. **磁盘空间**: 确保有足够的磁盘空间存储模型
2. **网络连接**: 模型下载需要稳定的网络连接
3. **内存使用**: 运行模型时需要足够的内存
4. **首次下载**: 首次下载模型可能需要较长时间

## 相关链接

- [Ollama官方文档](https://ollama.ai/docs)
- [可用模型列表](https://ollama.ai/library)
- [Docker Compose配置](../docker-compose.yml) 