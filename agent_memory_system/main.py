"""主入口模块

启动FastAPI应用服务器。

主要功能：
    - 加载环境变量
    - 初始化日志
    - 启动FastAPI应用

作者：Cursor_for_YansongW
创建日期：2024-01-15
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import uvicorn
from loguru import logger

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from agent_memory_system.api.api import app
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