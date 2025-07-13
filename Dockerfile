# 使用 Python 3.9 作为基础镜像
FROM registry.cn-hangzhou.aliyuncs.com/library/python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml poetry.lock* ./

# 安装 Poetry
RUN pip install poetry

# 配置 Poetry 不创建虚拟环境（在 Docker 中不需要）
RUN poetry config virtualenvs.create false

# 安装依赖
RUN poetry install --no-dev --no-interaction --no-ansi

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs data/faiss_index

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "-m", "agent_memory_system.main"] 