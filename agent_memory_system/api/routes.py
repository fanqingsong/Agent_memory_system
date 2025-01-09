"""路由定义模块

集中管理所有API路由。

主要功能：
    - API路由注册
    - 路由分组管理
    - 中间件配置
    - 错误处理
    - 文档配置

依赖：
    - fastapi: Web框架
    - memory_api: 记忆API
    - api: 主API
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent_memory_system.api.memory_api import (
    create_memory,
    get_memory,
    update_memory,
    delete_memory,
    retrieve_memories,
    add_memory_relation,
    delete_memory_relation
)
from agent_memory_system.api.api import (
    root,
    search_memories,
    websocket_endpoint
)
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

def create_app() -> FastAPI:
    """创建FastAPI应用
    
    功能描述：
        1. 创建FastAPI实例
        2. 配置CORS
        3. 注册路由
        4. 配置中间件
        5. 配置错误处理
        6. 配置API文档
    
    Returns:
        FastAPI: FastAPI应用实例
    """
    # 创建FastAPI实例
    app = FastAPI(
        title="Agent Memory System API",
        description="智能Agent记忆管理系统API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get("cors.origins", ["*"]),
        allow_credentials=config.get("cors.credentials", True),
        allow_methods=config.get("cors.methods", ["*"]),
        allow_headers=config.get("cors.headers", ["*"])
    )
    
    # 创建路由分组
    v1_router = APIRouter(prefix="/api/v1")
    ws_router = APIRouter()
    
    # 注册基础路由
    v1_router.get("/")(root)
    
    # 注册记忆管理路由
    memory_router = APIRouter(prefix="/memories", tags=["memories"])
    memory_router.post("")(create_memory)
    memory_router.get("/{memory_id}")(get_memory)
    memory_router.put("/{memory_id}")(update_memory)
    memory_router.delete("/{memory_id}")(delete_memory)
    memory_router.post("/retrieve")(retrieve_memories)
    memory_router.post("/search")(search_memories)
    memory_router.post("/{memory_id}/relations")(add_memory_relation)
    memory_router.delete("/{memory_id}/relations/{relation_id}")(delete_memory_relation)
    
    # 注册WebSocket路由
    ws_router.websocket("/ws")(websocket_endpoint)
    
    # 将路由组添加到主路由
    v1_router.include_router(memory_router)
    app.include_router(v1_router)
    app.include_router(ws_router)
    
    # 配置错误处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """全局异常处理器
        
        Args:
            request: 请求对象
            exc: 异常对象
        
        Returns:
            JSONResponse: JSON响应
        """
        log.error(f"全局异常: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "服务器内部错误",
                "detail": str(exc)
            }
        )
    
    return app

# 创建应用实例
app = create_app()
