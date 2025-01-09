# 数据流设计

## 1. 数据结构设计

### 1.1 记忆数据结构

```python
# 基础记忆结构
class MemoryBase:
    id: str                     # 记忆唯一标识
    timestamp: datetime         # 创建时间
    last_access: datetime       # 最后访问时间
    importance: float          # 重要性得分
    embedding: np.ndarray      # 向量表示(FAISS存储)
    metadata: Dict             # 元数据

# 常规记忆结构
class RegularMemory(MemoryBase):
    content: str               # 记忆内容
    context: str              # 上下文信息
    fragments: List[str]      # 记忆片段
    relations: List[str]      # 关联记忆ID(Neo4j关系)

# 技能记忆结构
class SkillMemory(MemoryBase):
    task_type: str            # 任务类型
    workflow: List[str]       # 工作流步骤
    conditions: List[str]     # 适用条件
    success_rate: float       # 成功率
    related_skills: List[str] # 关联技能(Neo4j关系)
```

### 1.2 存储映射结构

```python
# FAISS存储结构
class FAISSVector:
    id: str                   # 向量ID
    vector: np.ndarray        # 向量数据(维度768)
    type: str                # 记忆类型(regular/skill)

# Neo4j节点结构
class MemoryNode:
    id: str                   # 节点ID(与FAISS ID对应)
    type: str                # 节点类型(regular/skill)
    properties: Dict         # 节点属性(除向量外的所有属性)

# Neo4j关系结构
class MemoryRelation:
    source_id: str           # 源节点ID
    target_id: str           # 目标节点ID
    type: str               # 关系类型
    properties: Dict        # 关系属性

# Redis缓存结构
class MemoryCache:
    key: str                # 缓存键(memory:{id})
    value: Dict            # 完整记忆数据
    ttl: int              # 过期时间
```

### 1.3 数据映射规则

1. 向量数据(FAISS)：
- 存储所有记忆的向量表示
- 用于相似度检索
- 维度固定为768

2. 图数据(Neo4j)：
- 存储记忆的属性和关系
- 用于关系查询和图分析
- 与FAISS通过ID关联

3. 缓存数据(Redis)：
- 存储热点记忆的完整数据
- 加速频繁访问的记忆
- 采用LRU策略管理

## 2. 数据流转过程

### 2.1 写入流程

```mermaid
sequenceDiagram
    participant Input as 输入层
    participant Process as 处理层
    participant FAISS as 向量存储
    participant Neo4j as 图存储
    participant Redis as 缓存
    
    Input->>Process: 原始记忆数据
    Process->>Process: 数据预处理
    Process->>Process: 向量化编码
    Process->>FAISS: 存储向量
    Process->>Neo4j: 存储属性和关系
    Process->>Redis: 更新缓存
    Redis-->>Process: 确认
    FAISS-->>Process: 确认
    Neo4j-->>Process: 确认
```

### 2.2 读取流程

```mermaid
sequenceDiagram
    participant Query as 查询层
    participant Process as 处理层
    participant FAISS as 向量存储
    participant Neo4j as 图存储
    participant Redis as 缓存
    
    Query->>Process: 查询请求
    Process->>Redis: 查询缓存
    alt 缓存命中
        Redis-->>Process: 返回数据
    else 缓存未命中
        Process->>FAISS: 向量检索
        Process->>Neo4j: 图检索
        FAISS-->>Process: 相似向量
        Neo4j-->>Process: 关联数据
        Process->>Process: 数据合并
        Process->>Redis: 更新缓存
    end
    Process-->>Query: 返回结果
```

## 3. 数据处理流程

### 3.1 常规记忆处理

```mermaid
graph TB
    Input[原始数据] --> Preprocess[预处理]
    Preprocess --> Structure[结构化]
    Structure --> Encode[向量化]
    
    subgraph Processing[处理阶段]
        Structure --> Extract[特征提取]
        Structure --> Split[分片处理]
        Structure --> Relate[关系构建]
    end
    
    Encode --> Store[存储]
    Extract --> Store
    Split --> Store
    Relate --> Store
```

### 3.2 技能记忆处理

```mermaid
graph TB
    Input[任务数据] --> Analyze[任务分析]
    Analyze --> Pattern[模式识别]
    Pattern --> Abstract[抽象化]
    
    subgraph Processing[处理阶段]
        Pattern --> Workflow[工作流提取]
        Pattern --> Rule[规则提取]
        Pattern --> Condition[条件提取]
    end
    
    Abstract --> Validate[验证]
    Validate --> Store[存储]
```

## 4. 数据优化流程

### 4.1 记忆强化

```mermaid
graph TB
    Access[访问触发] --> Evaluate[评估]
    Evaluate --> Update[更新强度]
    Update --> Reorganize[重组关系]
    
    subgraph Optimization[优化过程]
        Update --> Compress[压缩]
        Update --> Merge[合并]
        Update --> Index[重建索引]
    end
```

### 4.2 记忆衰减

```mermaid
graph TB
    Time[时间触发] --> Calculate[计算衰减]
    Calculate --> Threshold[阈值判断]
    
    subgraph Decision[决策过程]
        Threshold --> Keep[保留]
        Threshold --> Archive[归档]
        Threshold --> Delete[删除]
    end
```

## 5. 数据安全流程

```mermaid
graph TB
    Input[输入数据] --> Validate[数据验证]
    Validate --> Sanitize[数据清洗]
    Sanitize --> Encrypt[加密]
    
    subgraph Security[安全处理]
        Encrypt --> Access[访问控制]
        Encrypt --> Audit[审计日志]
        Encrypt --> Backup[备份]
    end
    
    Security --> Store[安全存储]
``` 