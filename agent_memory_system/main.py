"""主入口模块

启动FastAPI应用服务器。

主要功能：
    - 加载环境变量
    - 初始化日志
    - 启动FastAPI应用
    - 提供静态文件服务
    - 集成WebSocket支持

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import uvicorn
from loguru import logger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from agent_memory_system.api.api import app as api_app
from agent_memory_system.api.chat import router as chat_router
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
        title="Agent Memory System",
        description="智能Agent记忆管理系统",
        version="1.0.0"
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # 挂载静态文件
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(project_root, "agent_memory_system/static")),
        name="static"
    )
    
    # 配置模板
    templates = Jinja2Templates(
        directory=os.path.join(project_root, "agent_memory_system/templates")
    )
    
    # 注册路由
    app.include_router(api_app)
    app.include_router(chat_router, prefix="/chat", tags=["chat"])
    
    # 主页路由
    @app.get("/")
    async def index(request):
        return templates.TemplateResponse(
            "index.html",
            {"request": request}
        )
    
    return app

def main():
    """主函数"""
    app = init_app()
    
    # 获取服务配置
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"启动服务: host={host}, port={port}, debug={debug}")
    
    # 启动服务
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=debug,
        workers=1
    )

if __name__ == "__main__":
    main()