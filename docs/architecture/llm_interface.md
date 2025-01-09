# LLM接口设计

## 1. 输入接口设计

### 1.1 消息结构

```python
# 基础消息结构
class Message:
    role: str                # 角色: system/user/assistant
    content: str             # 消息内容
    timestamp: datetime      # 时间戳
    metadata: Dict           # 元数据

# 对话历史结构
class Conversation:
    id: str                 # 对话ID
    messages: List[Message] # 消息列表
    system_prompt: str      # 系统提示
    metadata: Dict          # 元数据(如domain、task等)

# 多模态消息结构
class MultiModalMessage(Message):
    content_type: str       # 内容类型: text/image/audio
    content_format: str     # 格式: base64/url/text
    content_data: Any       # 实际内容
```

### 1.2 输入处理流程

```mermaid
graph TB
    Input[OpenAI格式输入] --> Parse[消息解析]
    Parse --> Extract[信息提取]
    
    subgraph Processing[处理阶段]
        Extract --> MetadataExtract[元数据提取]
        Extract --> ContentProcess[内容处理]
        Extract --> TypeIdentify[类型识别]
    end
    
    MetadataExtract --> Store[存储]
    ContentProcess --> Store
    TypeIdentify --> Store
```

## 2. 输出设计

### 2.1 Prompt结构

```python
# Prompt组件
class PromptComponent:
    type: str              # 组件类型: context/memory/instruction
    content: str           # 组件内容
    priority: float        # 优先级
    tokens: int           # token数量

# Prompt模板
class PromptTemplate:
    components: List[PromptComponent]  # 组件列表
    max_tokens: int                    # 最大token数
    format: str                        # 格式化方式

# 记忆Prompt
class MemoryPrompt:
    regular_memories: List[str]        # 相关常规记忆
    skill_memories: List[str]          # 相关技能记忆
    context_window: int                # 上下文窗口大小
```

### 2.2 Prompt构造流程

```mermaid
graph TB
    Query[查询意图] --> Retrieve[记忆检索]
    
    subgraph Construction[构造过程]
        Retrieve --> RegularMem[常规记忆选择]
        Retrieve --> SkillMem[技能记忆选择]
        RegularMem --> Merge[合并记忆]
        SkillMem --> Merge
    end
    
    Merge --> Format[格式化]
    Format --> Truncate[长度控制]
    Truncate --> Output[最终Prompt]
```

## 3. 交互流程

### 3.1 基本流程

```mermaid
sequenceDiagram
    participant LLM as 大模型
    participant API as 接口层
    participant Memory as 记忆系统
    participant Prompt as Prompt构造器
    
    LLM->>API: 发送消息(OpenAI格式)
    API->>Memory: 处理并存储消息
    API->>Memory: 检索相关记忆
    Memory->>Prompt: 提供记忆数据
    Prompt->>Prompt: 构造Prompt
    Prompt->>API: 返回Prompt
    API->>LLM: 返回结果
```

### 3.2 实时处理流程

```mermaid
graph TB
    Input[输入流] --> Buffer[消息缓冲]
    Buffer --> Process[实时处理]
    
    subgraph RealTime[实时处理]
        Process --> TokenCount[Token计数]
        Process --> Relevance[相关性计算]
        Process --> Priority[优先级排序]
    end
    
    RealTime --> Window[滑动窗口]
    Window --> Output[输出流]
```

## 4. API规范

### 4.1 OpenAI兼容接口

```python
# Chat完成请求
class ChatCompletionRequest:
    model: str
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False
    
# Chat完成响应
class ChatCompletionResponse:
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict]
    usage: Dict
```

### 4.2 记忆增强接口

```python
# 记忆增强请求
class MemoryEnhancedRequest(ChatCompletionRequest):
    memory_config: Dict = {
        "use_regular_memory": True,
        "use_skill_memory": True,
        "max_memories": 5,
        "memory_threshold": 0.7
    }
    
# 记忆增强响应
class MemoryEnhancedResponse(ChatCompletionResponse):
    memories_used: List[str]  # 使用的记忆ID列表
    memory_stats: Dict       # 记忆使用统计
```

## 5. 性能优化

### 5.1 缓存策略

```mermaid
graph TB
    subgraph CacheLayer[缓存层]
        PromptCache[Prompt缓存]
        MemoryCache[记忆缓存]
        ResultCache[结果缓存]
    end
    
    subgraph Strategy[策略]
        LRU[LRU策略]
        Priority[优先级策略]
        TTL[过期策略]
    end
    
    CacheLayer --> Strategy
```

### 5.2 批处理优化

```mermaid
graph TB
    Messages[消息流] --> Batch[批处理器]
    
    subgraph BatchProcess[批处理]
        Batch --> Aggregate[聚合]
        Aggregate --> Vectorize[向量化]
        Vectorize --> Parallel[并行处理]
    end
    
    Parallel --> Result[结果]
``` 