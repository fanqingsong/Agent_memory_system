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
```

## 代码中的使用

```python
from agent_memory_system.utils.openai_client import OpenAIClient

# 使用配置中的设置
client = OpenAIClient()

# 或者手动指定
client = OpenAIClient(
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
- Azure OpenAI: `gpt-35-turbo` (部署名称)
- 硅基流动: `Qwen/QwQ-32B`, `THUDM/GLM-4-9B-0414`

### 3. 嵌入模型
- OpenAI官方: `text-embedding-ada-002`
- 硅基流动: `BAAI/bge-large-zh-v1.5`

### 4. 错误处理
```python
try:
    response = await client.chat_completion(
        system_prompt="你是一个有用的助手",
        user_message="你好！"
    )
    print(response)
except Exception as e:
    print(f"API调用失败: {e}")
```

### 5. 速率限制
- 大多数API都有速率限制
- 建议实现重试机制
- 使用批量处理减少API调用次数

## 测试配置

```python
# 测试API配置
async def test_api_config():
    client = OpenAIClient()
    
    # 验证API密钥
    is_valid = await client.validate_api_key()
    if not is_valid:
        print("API密钥无效")
        return False
    
    # 获取模型列表
    models = await client.list_models()
    print(f"可用模型: {models}")
    
    # 测试聊天
    response = await client.chat_completion(
        system_prompt="你是一个有用的助手。请用简短的话回复。",
        user_message="你好，请说'测试成功'",
        temperature=0.1,
        max_tokens=50
    )
    print(f"测试回复: {response}")
    
    return True
``` 