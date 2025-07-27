"""记忆系统API接口模块

提供记忆系统的HTTP接口。

主要功能：
    - 记忆存储接口
    - 记忆检索接口
    - 记忆更新接口
    - 记忆删除接口
    - 记忆关系管理接口

依赖：
    - memory_model: 记忆数据模型
    - memory_manager: 记忆管理器
    - memory_retrieval: 记忆检索引擎
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

from datetime import datetime
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from agent_memory_system.core.memory.memory_manager import MemoryManager
from agent_memory_system.core.retrieval.memory_retrieval import MemoryRetrieval
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryRelation,
    MemoryStatus,
    MemoryType,
    RetrievalResult
)
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

# 创建FastAPI应用
app = FastAPI(
    title="Agent Memory System API",
    description="Agent记忆系统API接口",
    version="1.0.0"
)

# 请求/响应模型
class MemoryRequest(BaseModel):
    """记忆创建/更新请求"""
    content: str = Field(..., description="记忆内容")
    memory_type: MemoryType = Field(..., description="记忆类型")
    importance: Optional[int] = Field(None, description="重要性(1-10)")
    relations: Optional[List[MemoryRelation]] = Field(
        None,
        description="记忆关系列表"
    )

class MemoryResponse(BaseModel):
    """记忆响应"""
    memory_id: str = Field(..., description="记忆ID")
    content: str = Field(..., description="记忆内容")
    memory_type: MemoryType = Field(..., description="记忆类型")
    importance: int = Field(..., description="重要性")
    status: MemoryStatus = Field(..., description="记忆状态")
    created_at: datetime = Field(..., description="创建时间")
    accessed_at: datetime = Field(..., description="访问时间")
    updated_at: datetime = Field(..., description="更新时间")
    access_count: int = Field(..., description="访问次数")
    relations: List[MemoryRelation] = Field(..., description="记忆关系列表")

class RetrievalRequest(BaseModel):
    """记忆检索请求"""
    query: Optional[str] = Field(None, description="检索查询")
    memory_type: Optional[MemoryType] = Field(None, description="记忆类型")
    relation_filter: Optional[Dict[str, List[str]]] = Field(
        None,
        description="关系过滤条件"
    )
    time_filter: Optional[Dict[str, datetime]] = Field(
        None,
        description="时间范围过滤"
    )
    importance_filter: Optional[Dict[str, int]] = Field(
        None,
        description="重要性范围过滤"
    )
    top_k: int = Field(10, description="返回结果数量")
    threshold: float = Field(0.5, description="相似度阈值")

class RetrievalResponse(BaseModel):
    """记忆检索响应"""
    results: List[RetrievalResult] = Field(..., description="检索结果列表")
    total: int = Field(..., description="结果总数")

# 全局变量
memory_manager: Optional[MemoryManager] = None
memory_retrieval: Optional[MemoryRetrieval] = None

@app.on_event("startup")
async def startup():
    """应用启动时初始化"""
    global memory_manager, memory_retrieval
    
    # 初始化记忆管理器和检索引擎
    try:
        memory_manager = MemoryManager()
        memory_retrieval = memory_manager.retrieval_engine
        log.info("记忆系统API初始化成功")
    except Exception as e:
        log.error(f"记忆系统API初始化失败: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """应用关闭时清理资源"""
    global memory_manager, memory_retrieval
    
    # 清理资源
    try:
        if memory_manager:
            memory_manager.close()
        log.info("记忆系统API关闭成功")
    except Exception as e:
        log.error(f"记忆系统API关闭失败: {str(e)}")
        raise

@app.post(
    "/memories",
    response_model=MemoryResponse,
    summary="创建记忆",
    description="创建新的记忆"
)
async def create_memory(
    request: MemoryRequest
) -> MemoryResponse:
    """创建记忆接口
    
    Args:
        request: 记忆创建请求
    
    Returns:
        MemoryResponse: 创建的记忆
    
    Raises:
        HTTPException: 创建失败时抛出异常
    """
    try:
        # 创建记忆
        memory = Memory(
            content=request.content,
            memory_type=request.memory_type,
            importance=request.importance,
            relations=request.relations or []
        )
        
        # 存储记忆
        stored_memory = memory_manager.store_memory(memory)
        
        return MemoryResponse(
            memory_id=stored_memory.id,
            content=stored_memory.content,
            memory_type=stored_memory.memory_type,
            importance=stored_memory.importance,
            status=stored_memory.status,
            created_at=stored_memory.created_at,
            accessed_at=stored_memory.accessed_at,
            updated_at=stored_memory.updated_at,
            access_count=stored_memory.access_count,
            relations=stored_memory.relations
        )
    except Exception as e:
        log.error(f"创建记忆失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建记忆失败: {str(e)}"
        )

@app.get(
    "/memories/{memory_id}",
    response_model=MemoryResponse,
    summary="获取记忆",
    description="获取指定ID的记忆"
)
async def get_memory(
    memory_id: str
) -> MemoryResponse:
    """获取记忆接口
    
    Args:
        memory_id: 记忆ID
    
    Returns:
        MemoryResponse: 记忆详情
    
    Raises:
        HTTPException: 获取失败时抛出异常
    """
    try:
        # 获取记忆
        memory = memory_manager.get_memory(memory_id)
        if not memory:
            raise HTTPException(
                status_code=404,
                detail=f"记忆不存在: {memory_id}"
            )
        
        return MemoryResponse(
            memory_id=memory.id,
            content=memory.content,
            memory_type=memory.memory_type,
            importance=memory.importance,
            status=memory.status,
            created_at=memory.created_at,
            accessed_at=memory.accessed_at,
            updated_at=memory.updated_at,
            access_count=memory.access_count,
            relations=memory.relations
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"获取记忆失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取记忆失败: {str(e)}"
        )

@app.put(
    "/memories/{memory_id}",
    response_model=MemoryResponse,
    summary="更新记忆",
    description="更新指定ID的记忆"
)
async def update_memory(
    memory_id: str,
    request: MemoryRequest
) -> MemoryResponse:
    """更新记忆接口
    
    Args:
        memory_id: 记忆ID
        request: 记忆更新请求
    
    Returns:
        MemoryResponse: 更新后的记忆
    
    Raises:
        HTTPException: 更新失败时抛出异常
    """
    try:
        # 获取原记忆
        memory = memory_manager.get_memory(memory_id)
        if not memory:
            raise HTTPException(
                status_code=404,
                detail=f"记忆不存在: {memory_id}"
            )
        
        # 更新记忆
        memory.content = request.content
        memory.memory_type = request.memory_type
        if request.importance is not None:
            memory.importance = request.importance
        if request.relations is not None:
            memory.relations = request.relations
        
        # 存储更新
        updated_memory = memory_manager.update_memory_with_object(memory.id, memory)
        
        return MemoryResponse(
            memory_id=updated_memory.id,
            content=updated_memory.content,
            memory_type=updated_memory.memory_type,
            importance=updated_memory.importance,
            status=updated_memory.status,
            created_at=updated_memory.created_at,
            accessed_at=updated_memory.accessed_at,
            updated_at=updated_memory.updated_at,
            access_count=updated_memory.access_count,
            relations=updated_memory.relations
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"更新记忆失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"更新记忆失败: {str(e)}"
        )

@app.delete(
    "/memories/{memory_id}",
    summary="删除记忆",
    description="删除指定ID的记忆"
)
async def delete_memory(
    memory_id: str
) -> Dict[str, str]:
    """删除记忆接口
    
    Args:
        memory_id: 记忆ID
    
    Returns:
        Dict[str, str]: 删除结果
    
    Raises:
        HTTPException: 删除失败时抛出异常
    """
    try:
        # 删除记忆
        memory_manager.delete_memory(memory_id)
        
        return {"message": f"记忆删除成功: {memory_id}"}
    except Exception as e:
        log.error(f"删除记忆失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除记忆失败: {str(e)}"
        )

@app.post(
    "/memories/retrieve",
    response_model=RetrievalResponse,
    summary="检索记忆",
    description="检索符合条件的记忆"
)
async def retrieve_memories(
    request: RetrievalRequest
) -> RetrievalResponse:
    """检索记忆接口
    
    Args:
        request: 检索请求
    
    Returns:
        RetrievalResponse: 检索结果
    
    Raises:
        HTTPException: 检索失败时抛出异常
    """
    try:
        # 构建时间过滤条件
        time_filter = None
        if request.time_filter:
            time_filter = (
                request.time_filter.get("start_time"),
                request.time_filter.get("end_time")
            )
        
        # 构建重要性过滤条件
        importance_filter = None
        if request.importance_filter:
            importance_filter = (
                request.importance_filter.get("min_importance", 1),
                request.importance_filter.get("max_importance", 10)
            )
        
        # 检索记忆
        results = memory_retrieval.retrieve(
            query=request.query,
            memory_type=request.memory_type,
            relation_filter=request.relation_filter,
            time_filter=time_filter,
            importance_filter=importance_filter,
            top_k=request.top_k,
            threshold=request.threshold
        )
        
        return RetrievalResponse(
            results=results,
            total=len(results)
        )
    except Exception as e:
        log.error(f"检索记忆失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"检索记忆失败: {str(e)}"
        )

@app.post(
    "/memories/{memory_id}/relations",
    response_model=MemoryResponse,
    summary="添加记忆关系",
    description="为指定ID的记忆添加关系"
)
async def add_memory_relation(
    memory_id: str,
    relation: MemoryRelation
) -> MemoryResponse:
    """添加记忆关系接口
    
    Args:
        memory_id: 记忆ID
        relation: 记忆关系
    
    Returns:
        MemoryResponse: 更新后的记忆
    
    Raises:
        HTTPException: 添加关系失败时抛出异常
    """
    try:
        # 获取原记忆
        memory = memory_manager.get_memory(memory_id)
        if not memory:
            raise HTTPException(
                status_code=404,
                detail=f"记忆不存在: {memory_id}"
            )
        
        # 添加关系
        memory.relations.append(relation)
        
        # 存储更新
        updated_memory = memory_manager.update_memory_with_object(memory.id, memory)
        
        return MemoryResponse(
            memory_id=updated_memory.id,
            content=updated_memory.content,
            memory_type=updated_memory.memory_type,
            importance=updated_memory.importance,
            status=updated_memory.status,
            created_at=updated_memory.created_at,
            accessed_at=updated_memory.accessed_at,
            updated_at=updated_memory.updated_at,
            access_count=updated_memory.access_count,
            relations=updated_memory.relations
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"添加记忆关系失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"添加记忆关系失败: {str(e)}"
        )

@app.delete(
    "/memories/{memory_id}/relations/{relation_id}",
    response_model=MemoryResponse,
    summary="删除记忆关系",
    description="删除指定ID的记忆关系"
)
async def delete_memory_relation(
    memory_id: str,
    relation_id: str
) -> MemoryResponse:
    """删除记忆关系接口
    
    Args:
        memory_id: 记忆ID
        relation_id: 关系ID
    
    Returns:
        MemoryResponse: 更新后的记忆
    
    Raises:
        HTTPException: 删除关系失败时抛出异常
    """
    try:
        # 获取原记忆
        memory = memory_manager.get_memory(memory_id)
        if not memory:
            raise HTTPException(
                status_code=404,
                detail=f"记忆不存在: {memory_id}"
            )
        
        # 删除关系
        memory.relations = [
            r for r in memory.relations
            if r.target_id != relation_id
        ]
        
        # 存储更新
        updated_memory = memory_manager.update_memory_with_object(memory.id, memory)
        
        return MemoryResponse(
            memory_id=updated_memory.id,
            content=updated_memory.content,
            memory_type=updated_memory.memory_type,
            importance=updated_memory.importance,
            status=updated_memory.status,
            created_at=updated_memory.created_at,
            accessed_at=updated_memory.accessed_at,
            updated_at=updated_memory.updated_at,
            access_count=updated_memory.access_count,
            relations=updated_memory.relations
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"删除记忆关系失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除记忆关系失败: {str(e)}"
        ) 