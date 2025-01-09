# Agent Memory System

一个基于双轨记忆机制的智能Agent记忆管理系统。本系统实现了一个创新的双轨记忆架构，支持智能Agent的记忆存储、检索、关联、演化等功能。

## 系统架构

### 双轨记忆机制

系统采用双轨记忆架构，包括：

1. 短期记忆（STM）
   - 基于Redis的高速缓存
   - 支持最近访问记忆的快速检索
   - 自动衰减和遗忘机制
   - 容量限制和LRU淘汰策略

2. 长期记忆（LTM）
   - 基于Neo4j的图数据库存储
   - FAISS向量索引支持语义检索
   - 记忆关联网络
   - 基于重要性的强化机制

### 核心模块

1. 记忆管理器（MemoryManager）
   - 记忆的创建、更新和删除
   - 记忆的分类和标注
   - 记忆的重要性评估
   - 记忆的情感属性管理

2. 检索系统（MemoryRetrieval）
   - 语义相似度检索
   - 图结构关联检索
   - 时序关系检索
   - 多维度混合排序

3. 存储系统
   - 向量存储：FAISS索引
   - 图存储：Neo4j数据库
   - 缓存：Redis

4. API服务
   - RESTful API
   - WebSocket实时通信
   - 认证和授权
   - 限流和监控

## 系统要求

### 基础环境
- Python 3.8+
- Neo4j 4.0+
- Redis 6.0+
- CUDA 11.0+(可选，用于GPU加速)

### 硬件推荐配置
- CPU: 4核8线程以上
- 内存: 16GB以上
- 存储: SSD 100GB以上
- GPU: NVIDIA GPU 8GB显存（可选）

## 详细安装步骤

### Windows环境

1. 克隆仓库：
```powershell
git clone https://github.com/YansongW/agent_memory_system.git
cd agent_memory_system
```

2. 运行安装脚本：
```powershell
.\scripts\setup.bat
```

### Linux/MacOS环境

1. 克隆仓库：
```bash
git clone https://github.com/YansongW/agent_memory_system.git
cd agent_memory_system
```

2. 运行安装脚本：
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 环境变量配置

1. 复制配置模板：
```bash
# Windows
copy .env.example .env

# Linux/MacOS
cp .env.example .env
```

2. 根据环境修改配置：
```bash
# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379

# GPU配置(可选)
DEVICE=cpu  # 如果有GPU并安装了CUDA，设置为cuda
```

### LLM支持

系统支持以下LLM提供者:

#### 1. OpenAI (默认)
- 需要提供API密钥
- 支持GPT-3.5和GPT-4模型
- 配置方式:
```bash
# .env文件
LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
```

#### 2. Ollama (本地)
- 完全本地运行,无需API密钥
- 支持多种开源模型
- 安装Ollama:
```bash
# Windows
winget install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

- 下载模型:
```bash
# 下载Llama 2模型
ollama pull llama2

# 或其他模型
ollama pull mistral
ollama pull codellama
```

- 启动服务:
```bash
# 默认在11434端口启动
ollama serve
```

- 配置方式:
```bash
# .env文件
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

优点:
1. 完全本地运行,无需API密钥
2. 支持多种开源模型
3. 可自定义模型和参数
4. 数据隐私得到保护

注意事项:
1. 确保Ollama服务正在运行
2. 选择合适的模型(推荐llama2或codellama)
3. 首次使用需要下载模型
4. 本地运行需要足够的系统资源

## 详细使用指南

### 1. 启动服务

```bash
# 开发模式
poetry run python -m agent_memory_system.main --debug

# 生产模式
poetry run python -m agent_memory_system.main
```

### 2. API使用示例

#### 创建记忆

```python
import requests

# 创建情节记忆
episodic_memory = {
    "content": "今天和小明一起讨论了AI项目",
    "type": "EPISODIC",
    "importance": 8,
    "emotion": "POSITIVE",
    "context": {
        "location": "办公室",
        "time": "2024-12-15 14:30:00",
        "participants": ["小明"]
    },
    "tags": ["工作", "AI", "讨论"]
}

response = requests.post(
    "http://localhost:8000/memories",
    json=episodic_memory,
    headers={"X-API-Key": "your-api-key"}
)
print(response.json())

# 创建技能记忆
skill_memory = {
    "content": "使用FAISS进行向量检索的方法",
    "type": "PROCEDURAL",
    "importance": 9,
    "steps": [
        "初始化FAISS索引",
        "构建向量表示",
        "添加向量到索引",
        "执行相似度搜索"
    ],
    "code_snippet": """
    import faiss
    index = faiss.IndexFlatL2(dimension)
    vectors = model.encode(texts)
    index.add(vectors)
    D, I = index.search(query_vector, k)
    """
}

response = requests.post(
    "http://localhost:8000/memories",
    json=skill_memory,
    headers={"X-API-Key": "your-api-key"}
)
```

#### 检索记忆

```python
# 语义检索
query = {
    "content": "关于AI项目的讨论",
    "type": "EPISODIC",
    "limit": 10,
    "min_similarity": 0.7,
    "time_range": {
        "start": "2024-12-01",
        "end": "2024-12-31"
    }
}

response = requests.post(
    "http://localhost:8000/memories/search",
    json=query,
    headers={"X-API-Key": "your-api-key"}
)

# 关联检索
query = {
    "memory_id": "memory-123",
    "max_depth": 2,
    "relation_types": ["SIMILAR_TO", "LEADS_TO"],
    "min_importance": 5
}

response = requests.post(
    "http://localhost:8000/memories/related",
    json=query,
    headers={"X-API-Key": "your-api-key"}
)
```

#### WebSocket实时通信

```python
import websockets
import json
import asyncio

async def memory_stream():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # 订阅记忆更新
        await websocket.send(json.dumps({
            "type": "subscribe",
            "channels": ["memory_updates", "importance_changes"]
        }))
        
        while True:
            message = await websocket.recv()
            print(json.loads(message))

asyncio.get_event_loop().run_until_complete(memory_stream())
```

## 文档说明

本项目包含以下主要文档：

### 1. 开发文档
- `docs/architecture/roadmap.md`: 开发路线图
  - 详细的开发阶段规划
  - 各阶段任务和里程碑
  - 风险管理计划
  - 进度跟踪记录

- `development.md`: 开发规范
  - 代码风格规范
  - 文档编写规范
  - 测试规范
  - CI/CD规范

- `background.md`: 项目背景
  - 技术选型说明
  - 性能指标要求
  - 应用场景说明
  - 系统架构设计

### 2. API文档
- `docs/api/`: API接口文档
  - RESTful API说明
  - WebSocket接口说明
  - 认证授权说明
  - 示例代码

### 3. 测试文档
- `docs/test/`: 测试相关文档
  - 测试计划
  - 测试用例
  - 性能测试报告
  - 问题跟踪记录

### 4. 部署文档
- `docs/deploy/`: 部署相关文档
  - 环境配置说明
  - 部署步骤指南
  - 监控告警配置
  - 运维手册

## 最近更新

### 2025-01-09
1. 路线图更新
   - 完成核心功能开发
   - 进入集成测试阶段
   - 规划性能优化任务
   - 更新风险管理计划

2. 技术文档更新
   - 补充技术选型说明
   - 完善性能指标要求
   - 扩展应用场景说明
   - 更新系统架构设计

3. 开发规范更新
   - 完善代码风格规范
   - 补充测试规范说明
   - 添加CI/CD规范
   - 更新文档编写规范

## 贡献指南

欢迎提交Issue和Pull Request。在贡献代码前，请：

1. 阅读开发规范文档
2. 遵循代码风格规范
3. 编写完整的测试用例
4. 更新相关文档
5. 提交清晰的PR说明

# Agent_memory_system
