# 脚本管理工具

这个目录包含了 Agent Memory System 的环境管理脚本。

## 脚本说明

### 开发环境
- `start-dev.sh` - 启动开发环境（支持热重载）
- `stop-dev.sh` - 停止开发环境

### 生产环境
- `start-prod.sh` - 启动生产环境
- `stop-prod.sh` - 停止生产环境

## 使用方法

### 开发环境
```bash
# 启动开发环境
./bin/start-dev.sh

# 停止开发环境
./bin/stop-dev.sh
```

### 生产环境
```bash
# 启动生产环境
./bin/start-prod.sh

# 停止生产环境
./bin/stop-prod.sh
```

## 功能特性

### 启动脚本功能
- ✅ 检查 Docker Compose 版本
- ✅ 自动停止现有服务
- ✅ 构建并启动服务
- ✅ 等待服务启动完成
- ✅ 显示服务状态
- ✅ 提供访问地址信息
- ✅ 显示管理命令提示

### 停止脚本功能
- ✅ 优雅停止服务
- ✅ 检查剩余容器
- ✅ 提供强制停止选项
- ✅ 显示管理命令提示

## 访问地址

启动后可以通过以下地址访问服务：

- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Neo4j**: http://localhost:7474

## 注意事项

1. 确保已安装 Docker Compose v2.20+
2. 脚本会自动处理容器冲突
3. 停止脚本会询问是否强制停止剩余容器
4. 开发环境支持代码热重载 