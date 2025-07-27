"""主入口模块

启动FastAPI应用服务器。

主要功能：
    - 加载环境变量
    - 初始化日志
    - 启动FastAPI应用
    - 提供API服务

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import uvicorn
from loguru import logger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from agent_memory_system.api.api import app as api_app, get_app_instance
from agent_memory_system.utils.config import init_config
from agent_memory_system.utils.logger import init_logger

def init_app():
    """初始化应用"""
    # 加载环境变量
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        logger.warning(f"环境变量文件不存在: {env_path}")
        env_example_path = os.path.join(project_root, ".env.example")
        if os.path.exists(env_example_path):
            logger.info(f"使用示例环境变量文件: {env_example_path}")
            load_dotenv(env_example_path)
    
    # 初始化配置
    init_config()
    
    # 初始化日志
    init_logger()
    
    # 创建FastAPI应用
    app = FastAPI(
        title="Agent Memory System API",
        description="智能Agent记忆管理系统API",
        version="1.0.0"
    )
    
    # 配置CORS - 允许前端访问
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生产环境中应该限制为具体的前端域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # 注册API路由 - 直接使用API应用的路由
    app.mount("/", api_app)
    
    # 全局异常处理
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return {
            "error": "数据验证失败",
            "detail": exc.errors(),
            "timestamp": "2025-01-09T00:00:00Z"
        }
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"全局异常: {exc}")
        return {
            "error": "服务器内部错误",
            "detail": str(exc),
            "timestamp": "2025-01-09T00:00:00Z"
        }
    
    return app

def main():
    """主函数"""
    # 初始化应用
    app = init_app()
    
    # 获取配置
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"启动服务: host={host}, port={port}, debug={debug}")
    
    # 启动服务器
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info" if not debug else "debug",
        reload=debug
    )

# 创建应用实例供 uvicorn 直接启动使用
app = init_app()

if __name__ == "__main__":
    main()