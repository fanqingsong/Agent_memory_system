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
创建日期：2025-01-09
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

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
from agent_memory_system.models.api_models import (
    ErrorResponse,
    SuccessResponse,
    VersionInfo
)
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

# 创建限流器
limiter = Limiter(key_func=get_remote_address)

def create_app() -> FastAPI:
    """创建FastAPI应用"""
    # 创建FastAPI实例
    app = FastAPI(
        title="Agent Memory System API",
        description="智能Agent记忆管理系统API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # 配置中间件
    _configure_middleware(app)
    
    # 配置路由
    _configure_routes(app)
    
    # 配置错误处理
    _configure_error_handlers(app)
    
    return app

def _configure_middleware(app: FastAPI) -> None:
    """配置中间件"""
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 默认允许所有来源
        allow_credentials=True,  # 默认允许凭证
        allow_methods=["*"],  # 默认允许所有方法
        allow_headers=["*"]  # 默认允许所有头部
    )
    
    # 可信主机中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # 默认允许所有主机
    )
    
    # Gzip压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 限流中间件
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def _configure_routes(app: FastAPI) -> None:
    """配置路由"""
    # API版本路由
    api_router = APIRouter()
    
    # V1版本路由
    v1_router = APIRouter(prefix="/api/v1")
    
    # V2版本路由(预留)
    v2_router = APIRouter(prefix="/api/v2")
    
    # WebSocket路由
    ws_router = APIRouter()
    
    # 基础路由
    @api_router.get(
        "/version",
        response_model=VersionInfo,
        tags=["system"]
    )
    @limiter.limit("10/minute")
    async def get_version(request: Request):
        """获取API版本信息"""
        return {
            "version": "1.0.0",
            "build_date": "2024-01-09",
            "supported_versions": ["v1"]
        }
    
    # 记忆管理路由
    memory_router = APIRouter(prefix="/memories", tags=["memories"])
    
    # 添加限流装饰器
    @memory_router.post(
        "",
        response_model=SuccessResponse,
        responses={
            400: {"model": ErrorResponse},
            500: {"model": ErrorResponse}
        }
    )
    @limiter.limit("100/minute")
    async def create_memory_endpoint(request: Request):
        return await create_memory(request)
    
    @memory_router.get(
        "/{memory_id}",
        response_model=SuccessResponse,
        responses={
            404: {"model": ErrorResponse},
            500: {"model": ErrorResponse}
        }
    )
    @limiter.limit("200/minute")
    async def get_memory_endpoint(request: Request, memory_id: str):
        return await get_memory(memory_id)
    
    @memory_router.put(
        "/{memory_id}",
        response_model=SuccessResponse,
        responses={
            404: {"model": ErrorResponse},
            500: {"model": ErrorResponse}
        }
    )
    @limiter.limit("100/minute")
    async def update_memory_endpoint(request: Request, memory_id: str):
        return await update_memory(memory_id, request)
    
    @memory_router.delete(
        "/{memory_id}",
        response_model=SuccessResponse,
        responses={
            404: {"model": ErrorResponse},
            500: {"model": ErrorResponse}
        }
    )
    @limiter.limit("50/minute")
    async def delete_memory_endpoint(request: Request, memory_id: str):
        return await delete_memory(memory_id)
    
    @memory_router.post(
        "/retrieve",
        response_model=SuccessResponse,
        responses={
            400: {"model": ErrorResponse},
            500: {"model": ErrorResponse}
        }
    )
    @limiter.limit("100/minute")
    async def retrieve_memories_endpoint(request: Request):
        return await retrieve_memories(request)
    
    @memory_router.post(
        "/search",
        response_model=SuccessResponse,
        responses={
            400: {"model": ErrorResponse},
            500: {"model": ErrorResponse}
        }
    )
    @limiter.limit("100/minute")
    async def search_memories_endpoint(request: Request):
        return await search_memories(request)
    
    # 注册WebSocket路由
    ws_router.websocket("/ws")(websocket_endpoint)
    
    # 将路由组添加到主路由
    v1_router.include_router(memory_router)
    app.include_router(api_router)
    app.include_router(v1_router)
    app.include_router(v2_router)
    app.include_router(ws_router)

def _configure_error_handlers(app: FastAPI) -> None:
    """配置错误处理"""
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理器"""
        log.error(f"全局异常: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                code=500,
                message="服务器内部错误",
                detail=str(exc)
            ).dict()
        )
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):
        """404错误处理器"""
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                code=404,
                message="资源不存在",
                detail=str(exc)
            ).dict()
        )
    
    @app.exception_handler(400)
    async def bad_request_handler(request: Request, exc: Exception):
        """400错误处理器"""
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                code=400,
                message="请求参数错误",
                detail=str(exc)
            ).dict()
        )

# 创建应用实例
app = create_app()
