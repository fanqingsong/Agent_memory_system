# 使用官方Python镜像作为基础镜像
FROM docker.1ms.run/python:3.9.19 as base

# 设置工作目录
WORKDIR /app

# 配置apt国内镜像源
RUN if [ -f /etc/apt/sources.list ]; then \
        sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list; \
    elif [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources; \
    fi

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 配置pip国内镜像
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 开发阶段
FROM base as development

# 复制所有应用代码
COPY . .

# 安装开发依赖
RUN pip install --no-cache-dir -e .[dev]

# 创建必要的目录
RUN mkdir -p /app/data /app/logs

# 暴露端口
EXPOSE 8000

# 开发模式启动命令 - 支持热重载
CMD ["uvicorn", "agent_memory_system.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# 生产阶段
FROM base as production

# 复制所有应用代码
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -e .

# 创建必要的目录
RUN mkdir -p /app/data /app/logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 生产模式启动命令
CMD ["python", "-m", "agent_memory_system.main"] 