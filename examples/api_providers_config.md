# API提供商配置示例

本文档展示了如何配置不同的API提供商来使用兼容OpenAI接口的大模型服务。

## 支持的提供商

### 1. 硅基流动 SiliconFlow (推荐)
```bash
# 环境变量配置
LLM_PROVIDER=openai
OPENAI_API_KEY=your-siliconflow-api-key
OPENAI_API_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_MODEL=Qwen/QwQ-32B
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
```

### 2. OpenAI官方API
```bash
# 环境变量配置
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE_URL=https://api.openai.com/v1  # 默认值，可选
OPENAI_MODEL=gpt-3.5-turbo
```

### 3. Azure OpenAI
```bash
# 环境变量配置
LLM_PROVIDER=openai
OPENAI_API_KEY=your-azure-openai-api-key
OPENAI_API_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment
OPENAI_MODEL=gpt-35-turbo  # Azure部署名称
```

### 4. Anthropic Claude (通过兼容层)
```bash
# 环境变量配置
LLM_PROVIDER=openai
OPENAI_API_KEY=your-claude-api-key
OPENAI_API_BASE_URL=https://api.anthropic.com/v1
OPENAI_MODEL=claude-3-sonnet-20240229
```

### 5. Google Gemini (通过兼容层)
```bash
# 环境变量配置
LLM_PROVIDER=openai
OPENAI_API_KEY=your-gemini-api-key
OPENAI_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta
OPENAI_MODEL=gemini-pro
```

### 6. 本地Ollama
```bash
# 环境变量配置
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b
```

## Docker Compose配置示例

### 使用硅基流动 SiliconFlow
```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - LLM_PROVIDER=openai
      - OPENAI_API_KEY=${SILICONFLOW_API_KEY}
      - OPENAI_API_BASE_URL=https://api.siliconflow.cn/v1
      - OPENAI_MODEL=Qwen/QwQ-32B
      - OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
```

### 使用Azure OpenAI
```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - LLM_PROVIDER=openai
      - OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - OPENAI_API_BASE_URL=${AZURE_OPENAI_ENDPOINT}/openai/deployments/${AZURE_OPENAI_DEPLOYMENT}
      - OPENAI_MODEL=gpt-35-turbo
```

### 使用本地Ollama
```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=qwen2.5:0.5b
```

## 环境变量文件示例

创建 `.env` 文件：

```bash
# 硅基流动 SiliconFlow (推荐)
LLM_PROVIDER=openai
OPENAI_API_KEY=your-siliconflow-api-key
OPENAI_API_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_MODEL=Qwen/QwQ-32B
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# 或者使用OpenAI官方API
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-openai-api-key
# OPENAI_API_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-3.5-turbo
# OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# 或者使用Azure OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your-azure-api-key
# OPENAI_API_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment
# OPENAI_MODEL=gpt-35-turbo

# 或者使用本地Ollama
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=qwen2.5:0.5b
```

## 代码中的使用

```python
from agent_memory_system.utils.openai_client import LLMClient

# 使用配置中的设置
client = LLMClient()

# 或者手动指定
client = LLMClient(
    provider="openai",
    api_key="your-api-key",
    api_base_url="https://your-custom-endpoint.com/v1",
    model="your-model"
)

# 调用API
response = await client.chat_completion(
    system_prompt="你是一个有用的助手",
    user_message="你好！"
)
```

## 常见问题

### 1. API基础URL格式
- OpenAI官方: `https://api.openai.com/v1`
- Azure OpenAI: `https://your-resource.openai.azure.com/openai/deployments/your-deployment`
- 自定义服务: `https://your-domain.com/v1`

### 2. 模型名称
- OpenAI官方: `gpt-3.5-turbo`, `gpt-4`
- Azure OpenAI: `gpt-35-turbo`, `gpt-4` (使用部署名称)
- 其他服务: 根据提供商的具体模型名称

### 3. 认证方式
- 大多数服务使用API密钥认证
- 某些服务可能需要额外的头部信息

### 4. 错误处理
如果遇到API调用错误，请检查：
- API密钥是否正确
- API基础URL是否正确
- 模型名称是否支持
- 网络连接是否正常

## 测试配置

使用以下命令测试配置：

```bash
# 测试OpenAI配置
curl -X POST "https://api.openai.com/v1/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# 测试Ollama配置
curl -X POST "http://localhost:11434/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:0.5b",
    "prompt": "Hello!"
  }'
``` 