# 使用 Python 3.9 作为基础镜像
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 配置国内镜像源
RUN if [ -f /etc/apt/sources.list ]; then \
        sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
        sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list; \
    elif [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
        sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources; \
    fi

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 配置pip国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 创建requirements.txt文件
RUN echo "torch>=2.0.0\ntransformers>=4.30.0\nsentence-transformers>=2.2.2\nfaiss-cpu>=1.7.4\nnetworkx>=3.1\nneo4j>=5.9.0\nnumpy>=1.24.0\npandas>=2.0.0\npydantic>=2.0.0\npydantic-settings>=2.0.0\nfastapi>=0.100.0\nuvicorn>=0.22.0\npython-dotenv>=1.0.0\nloguru>=0.7.0\nredis>=5.2.1\nportalocker>=2.7.0\npsutil>=5.9.0\nfilelock>=3.12.2\ncryptography>=41.0.0" > requirements.txt

# 安装Python依赖
RUN pip install -r requirements.txt

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