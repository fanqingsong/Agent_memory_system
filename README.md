# Agent Memory System

一个基于双轨记忆机制的智能Agent记忆管理系统。

## 项目特性

- 双轨记忆系统
  - 常规记忆：支持连续性和碎片化的平衡
  - 技能记忆：支持任务模式提取和迁移

- 高效存储
  - FAISS向量存储：高性能相似度检索
  - Neo4j图数据库：灵活的关系管理
  - Redis缓存：快速数据访问

- 智能检索
  - 向量检索：基于语义的相似度搜索
  - 图检索：基于关系的路径搜索
  - 混合检索：多维度综合排序

- 实时通信
  - REST API：标准HTTP接口
  - WebSocket：实时双向通信
  - 事件驱动：异步消息处理

## 系统要求

- Python 3.8+
- Neo4j 4.4+
- Redis 6.0+
- FAISS 1.7+
- CUDA 11.0+（可选，用于GPU加速）

## 安装说明

1. 克隆项目
```bash
git clone https://github.com/YansongW/agent-memory-system.git
cd agent-memory-system
```

2. 安装Poetry（如果未安装）
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. 安装依赖
```bash
poetry install
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，设置必要的配置项
```

## 项目结构

```
agent_memory_system/
├── core/                    # 核心功能模块
│   ├── memory/             # 记忆管理
│   │   ├── memory_types.py # 记忆类型定义
│   │   ├── memory_utils.py # 记忆工具函数
│   │   └── memory_manager.py # 记忆管理器
│   ├── storage/            # 存储管理
│   │   ├── vector_store.py # 向量存储
│   │   ├── graph_store.py  # 图存储
│   │   └── cache_store.py  # 缓存存储
│   └── retrieval/          # 检索系统
│       ├── retriever.py    # 检索器
│       └── ranker.py       # 排序器
├── models/                  # 数据模型
│   └── memory_model.py     # 记忆模型定义
├── api/                    # API接口
│   ├── routes.py          # 路由定义
│   └── api.py             # API实现
├── utils/                  # 工具函数
│   ├── config.py          # 配置管理
│   └── logger.py          # 日志管理
└── tests/                  # 单元测试
    ├── test_memory_types.py
    ├── test_memory_utils.py
    ├── test_storage.py
    ├── test_retrieval.py
    └── test_api.py
```

## 测试框架

```
tests/                      # 系统测试
├── client/                 # 测试客户端
│   ├── index.html         # 客户端页面
│   ├── styles.css         # 样式文件
│   └── app.js             # 客户端逻辑
├── data/                   # 测试数据
│   ├── data_generator.py  # 数据生成器
│   └── environment.py     # 环境配置
└── scenarios/             # 测试场景
    └── test_scenarios.py  # 场景定义
```

## 快速开始

1. 启动服务
```bash
poetry run python -m agent_memory_system
```

2. 运行单元测试
```bash
poetry run pytest agent_memory_system/tests/
```

3. 运行系统测试
```bash
poetry run pytest tests/
```

4. 启动测试客户端
```bash
# 确保服务已启动
cd tests/client
python -m http.server 8080
# 访问 http://localhost:8080
```

## API文档

启动服务后访问：http://localhost:8000/docs

## 开发状态

- [x] 核心功能开发
  - [x] 记忆存储模块
  - [x] 记忆管理模块
  - [x] 记忆检索模块
  - [x] API接口模块

- [x] 测试开发
  - [x] H5客户端开发
  - [x] 测试数据生成
  - [x] 测试场景实现
  - [x] 单元测试

- [ ] 集成测试
  - [ ] 系统集成测试
  - [ ] 端到端测试
  - [ ] 性能测试

详细的开发进度请参考 [roadmap.md](docs/architecture/roadmap.md)。

## 开发指南

请参考 [development.md](development.md) 了解详细的开发规范。

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License
# Agent_memory_system
# Agent_memory_system
