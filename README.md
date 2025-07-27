# Agent Memory System

一个基于前后端分离架构的智能Agent记忆管理系统，使用React + Ant Design前端和FastAPI后端。

## 项目架构

```
agent-memory-system/
├── backend/                 # 后端API服务 (FastAPI)
│   ├── agent_memory_system/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                # 前端React应用
│   ├── src/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml       # 主编排文件
```

## 技术栈

### 后端
- **FastAPI**: 现代、快速的Web框架
- **Neo4j**: 图数据库，用于存储记忆关系
- **Redis**: 缓存数据库
- **Weaviate**: 向量数据库，用于高性能向量存储和检索
- **SiliconFlow**: 嵌入模型服务

### 前端
- **React 18**: 现代前端框架
- **Ant Design**: 企业级UI组件库
- **Axios**: HTTP客户端
- **React Router**: 路由管理
- **ECharts**: 数据可视化

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd agent-memory-system
```

### 2. 配置环境变量
```bash
cp env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

### 3. 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 访问应用
- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Neo4j浏览器**: http://localhost:7474
- **Weaviate管理**: http://localhost:8080/v1/meta

## 功能特性

### 前端功能
- 🗨️ **智能对话**: 基于记忆的智能对话界面
- 🧠 **记忆管理**: 记忆的增删改查和搜索
- 📊 **存储监控**: 实时监控三种存储状态
- ⚙️ **系统设置**: 灵活的配置管理

### 后端功能
- 🔍 **向量搜索**: 基于Weaviate的高性能向量存储和检索
- 🕸️ **图数据库**: 基于Neo4j的记忆关系管理
- 💾 **缓存系统**: 基于Redis的高性能缓存
- 🤖 **LLM集成**: 支持多种LLM提供者

## 开发指南

### 前端开发
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start

# 构建生产版本
npm run build
```

### 后端开发
```bash
cd backend

# 安装依赖
pip install -e .

# 启动开发服务器
python -m agent_memory_system.main
```

### 数据库管理
```bash
# 访问Neo4j浏览器
open http://localhost:7474

# 访问Redis CLI
docker exec -it agent-memory-redis redis-cli
```

## API接口

### 记忆管理
- `GET /memories` - 获取所有记忆
- `POST /memories` - 创建新记忆
- `GET /memories/{id}` - 获取单个记忆
- `PUT /memories/{id}` - 更新记忆
- `DELETE /memories/{id}` - 删除记忆
- `POST /memories/search` - 搜索记忆

### 聊天功能
- `POST /chat/message` - 发送消息

### 存储监控
- `GET /storage/all` - 获取所有存储信息
- `GET /storage/vector` - 获取向量存储信息
- `GET /storage/graph` - 获取图存储信息
- `GET /storage/cache` - 获取缓存存储信息

## 部署

### 生产环境部署
```bash
# 构建并启动生产版本
docker-compose -f docker-compose.prod.yml up -d

# 使用Nginx反向代理
# 配置nginx.conf指向前端和后端服务
```

### 环境变量配置
```bash
# 必需的环境变量
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE_URL=https://api.siliconflow.cn/v1
ENCRYPTION_KEY=your-encryption-key

# 可选的环境变量
DEBUG=false
LOG_LEVEL=INFO
MEMORY_MAX_SIZE=10000
```

## 监控和维护

### 健康检查
```bash
# 检查服务状态
curl http://localhost:8000/health
curl http://localhost:3000/health

# 查看存储状态
curl http://localhost:8000/storage/all
```

### 日志查看
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: [Your Name]
- 邮箱: [your.email@example.com]
- 项目链接: [https://github.com/yourusername/agent-memory-system]
