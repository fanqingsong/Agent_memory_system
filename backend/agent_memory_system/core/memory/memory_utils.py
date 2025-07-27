"""记忆处理工具模块

提供记忆处理相关的工具函数。

主要功能：
    - 记忆预处理
    - 记忆后处理
    - 记忆关系处理
    - 记忆优化工具
    - 记忆状态管理

依赖：
    - memory_model: 记忆数据模型
    - memory_types: 记忆类型处理
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from agent_memory_system.models.memory_model import (
    Memory,
    MemoryRelation,
    MemoryStatus,
    MemoryType,
    MemoryVector
)
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

def preprocess_memory(memory: Memory) -> Memory:
    """预处理记忆
    
    功能描述：
        对新记忆进行预处理，包括：
        1. 生成记忆ID
        2. 设置创建时间
        3. 初始化状态
        4. 计算向量表示
        5. 设置初始重要性
    
    Args:
        memory: 待处理的记忆对象
    
    Returns:
        Memory: 处理后的记忆对象
    """
    # 生成记忆ID
    if not memory.id:
        content_hash = hashlib.md5(
            memory.content.encode('utf-8')
        ).hexdigest()
        memory.id = f"{memory.memory_type.value}_{content_hash[:8]}"
    
    # 设置时间戳
    now = datetime.utcnow()
    memory.created_at = now
    memory.accessed_at = now
    memory.updated_at = now
    
    # 初始化状态
    memory.status = MemoryStatus.ACTIVE
    memory.access_count = 0
    
    # 计算向量表示
    if not memory.vectors:
        memory.vectors = generate_memory_vectors(memory)
    
    # 设置初始重要性
    if not memory.importance:
        memory.importance = calculate_initial_importance(memory)
    
    return memory

def postprocess_memory(memory: Memory) -> Memory:
    """后处理记忆
    
    功能描述：
        对记忆进行后处理，包括：
        1. 更新访问时间
        2. 更新访问计数
        3. 更新重要性
        4. 优化向量表示
        5. 清理无效关系
    
    Args:
        memory: 待处理的记忆对象
    
    Returns:
        Memory: 处理后的记忆对象
    """
    # 更新访问信息
    memory.accessed_at = datetime.utcnow()
    memory.access_count += 1
    
    # 更新重要性
    memory.importance = update_importance(memory)
    
    # 优化向量表示
    memory.vectors = optimize_vectors(memory.vectors)
    
    # 清理无效关系
    memory.relations = clean_relations(memory.relations)
    
    return memory

def generate_memory_vectors(memory: Memory) -> List[MemoryVector]:
    """生成记忆的向量表示
    
    功能描述：
        为记忆生成多种类型的向量表示：
        1. 语义向量：基于OpenAI embedding API的语义向量
        2. TF-IDF向量：基于词频的统计特征（fallback）
    
    Args:
        memory: 记忆对象
    
    Returns:
        List[MemoryVector]: 向量表示列表
    """
    vectors = []
    
    try:
        # 使用OpenAI embedding API生成语义向量
        from agent_memory_system.core.embedding.embedding_service import generate_embedding_vector
        
        semantic_vector = generate_embedding_vector(memory.content)
        vectors.append(MemoryVector(
            vector_type="semantic",
            vector=np.array(semantic_vector),
            dimension=len(semantic_vector)
        ))
        
        log.info(f"成功生成记忆 {memory.id} 的语义向量，维度: {len(semantic_vector)}")
        
    except Exception as e:
        log.error(f"生成语义向量失败，回退到TF-IDF: {e}")
        
        # 回退到TF-IDF向量
        tfidf_vector = generate_tfidf_vector(memory.content)
        vectors.append(MemoryVector(
            vector_type="tfidf",
            vector=tfidf_vector,
            dimension=len(tfidf_vector)
        ))
    
    return vectors

def generate_tfidf_vector(text: str, dimension: int = 1024) -> np.ndarray:
    """生成文本的TF-IDF向量
    
    Args:
        text: 输入文本
        dimension: 向量维度，默认1024（BAAI/bge-large-zh-v1.5）
    
    Returns:
        np.ndarray: TF-IDF向量
    """
    try:
        # 预处理文本，确保有足够的内容
        if len(text.strip()) < 3:
            # 对于太短的文本，添加一些默认词汇
            text = f"query: {text} question"
        
        # 使用预定义的词汇表来确保固定维度
        vectorizer = TfidfVectorizer(
            max_features=dimension,  # 使用配置的维度
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,  # 允许单个文档中的词汇
            vocabulary=None  # 不限制词汇表
        )
        
        # 尝试生成向量
        try:
            vector = vectorizer.fit_transform([text]).toarray()[0]
        except ValueError as e:
            # 如果仍然失败，使用字符级别的特征
            log.warning(f"TF-IDF向量生成失败，使用字符特征: {e}")
            # 创建基于字符的简单特征向量
            char_features = np.zeros(dimension)
            for i, char in enumerate(text.lower()):
                if i < dimension:
                    char_features[i] = ord(char) / 255.0  # 归一化字符值
            return char_features
        
        # 如果向量长度不足指定维度，用零填充
        if len(vector) < dimension:
            vector = np.pad(vector, (0, dimension - len(vector)), 'constant')
        # 如果向量长度超过指定维度，截断
        elif len(vector) > dimension:
            vector = vector[:dimension]
            
        return vector
    except Exception as e:
        log.error(f"生成TF-IDF向量失败: {e}")
        # 返回零向量作为fallback
        return np.zeros(dimension)

def calculate_initial_importance(memory: Memory) -> int:
    """计算记忆的初始重要性
    
    功能描述：
        基于多个因素计算记忆的初始重要性：
        1. 内容长度
        2. 关系数量
        3. 记忆类型
        4. 向量特征
    
    Args:
        memory: 记忆对象
    
    Returns:
        int: 重要性评分(1-10)
    """
    importance = 5  # 基础重要性
    
    # 内容长度影响
    content_length = len(memory.content)
    if content_length > 1000:
        importance += 2
    elif content_length > 500:
        importance += 1
    
    # 关系数量影响
    relation_count = len(memory.relations)
    if relation_count > 5:
        importance += 2
    elif relation_count > 2:
        importance += 1
    
    # 记忆类型影响
    if memory.memory_type == MemoryType.SKILL:
        importance += 2
    elif memory.memory_type == MemoryType.LONG_TERM:
        importance += 1
    
    return max(1, min(10, importance))

def update_importance(memory: Memory) -> int:
    """更新记忆的重要性
    
    功能描述：
        基于多个因素更新记忆的重要性：
        1. 当前重要性
        2. 访问频率
        3. 时间衰减
        4. 关系变化
    
    Args:
        memory: 记忆对象
    
    Returns:
        int: 更新后的重要性评分(1-10)
    """
    importance = memory.importance
    
    # 访问频率影响
    access_bonus = min(memory.access_count / 10, 2)
    importance += access_bonus
    
    # 时间衰减
    age = datetime.utcnow() - memory.created_at
    decay = min(age.total_seconds() / (24 * 3600), 1)  # 每天衰减1分
    importance -= decay
    
    # 关系变化影响
    relation_change = len(memory.relations) - memory.relations_count
    if relation_change > 0:
        importance += min(relation_change / 2, 1)
    
    return max(1, min(10, round(importance)))

def optimize_vectors(
    vectors: List[MemoryVector]
) -> List[MemoryVector]:
    """优化向量表示
    
    功能描述：
        对向量表示进行优化：
        1. 去除冗余维度
        2. 归一化处理
        3. 压缩存储
    
    Args:
        vectors: 向量表示列表
    
    Returns:
        List[MemoryVector]: 优化后的向量表示
    """
    optimized = []
    
    for vector in vectors:
        # 归一化处理
        norm = np.linalg.norm(vector.vector)
        if norm > 0:
            vector.vector = vector.vector / norm
        
        # TODO: 添加维度压缩
        # TODO: 添加存储优化
        
        optimized.append(vector)
    
    return optimized

def clean_relations(
    relations: List[MemoryRelation]
) -> List[MemoryRelation]:
    """清理记忆关系
    
    功能描述：
        清理无效的记忆关系：
        1. 移除重复关系
        2. 移除无效目标
        3. 更新关系强度
        4. 合并相似关系
    
    Args:
        relations: 关系列表
    
    Returns:
        List[MemoryRelation]: 清理后的关系列表
    """
    # 移除重复关系
    unique_relations = {
        (r.relation_type, r.target_id): r
        for r in relations
    }
    
    # 更新关系强度
    for relation in unique_relations.values():
        if relation.strength > 0:
            relation.strength = min(
                relation.strength * 0.9,  # 关系强度衰减
                10
            )
    
    # 移除强度过低的关系
    valid_relations = [
        r for r in unique_relations.values()
        if r.strength >= 1
    ]
    
    return valid_relations

def calculate_similarity(
    memory1: Memory,
    memory2: Memory
) -> float:
    """计算两个记忆的相似度
    
    功能描述：
        基于多个特征计算记忆相似度：
        1. 内容相似度
        2. 向量相似度
        3. 关系相似度
        4. 时间相似度
    
    Args:
        memory1: 第一个记忆对象
        memory2: 第二个记忆对象
    
    Returns:
        float: 相似度分数(0-1)
    """
    # 内容相似度
    content_sim = calculate_content_similarity(
        memory1.content,
        memory2.content
    )
    
    # 向量相似度
    vector_sim = calculate_vector_similarity(
        memory1.vectors,
        memory2.vectors
    )
    
    # 关系相似度
    relation_sim = calculate_relation_similarity(
        memory1.relations,
        memory2.relations
    )
    
    # 时间相似度
    time_sim = calculate_time_similarity(
        memory1.created_at,
        memory2.created_at
    )
    
    # 加权平均
    weights = [0.4, 0.3, 0.2, 0.1]  # 权重可配置
    similarity = sum([
        content_sim * weights[0],
        vector_sim * weights[1],
        relation_sim * weights[2],
        time_sim * weights[3]
    ])
    
    return similarity

def calculate_content_similarity(
    content1: str,
    content2: str
) -> float:
    """计算内容相似度
    
    Args:
        content1: 第一个内容
        content2: 第二个内容
    
    Returns:
        float: 相似度分数(0-1)
    """
    # 使用TF-IDF向量计算余弦相似度
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([content1, content2])
    similarity = cosine_similarity(
        vectors[0:1],
        vectors[1:2]
    )[0][0]
    
    return float(similarity)

def calculate_vector_similarity(
    vectors1: List[MemoryVector],
    vectors2: List[MemoryVector]
) -> float:
    """计算向量相似度
    
    Args:
        vectors1: 第一组向量
        vectors2: 第二组向量
    
    Returns:
        float: 相似度分数(0-1)
    """
    similarities = []
    
    for v1 in vectors1:
        for v2 in vectors2:
            if v1.vector_type == v2.vector_type:
                # 计算余弦相似度
                similarity = cosine_similarity(
                    v1.vector.reshape(1, -1),
                    v2.vector.reshape(1, -1)
                )[0][0]
                similarities.append(float(similarity))
    
    return max(similarities) if similarities else 0.0

def calculate_relation_similarity(
    relations1: List[MemoryRelation],
    relations2: List[MemoryRelation]
) -> float:
    """计算关系相似度
    
    Args:
        relations1: 第一组关系
        relations2: 第二组关系
    
    Returns:
        float: 相似度分数(0-1)
    """
    # 提取关系类型和目标ID
    rel_set1 = {
        (r.relation_type, r.target_id)
        for r in relations1
    }
    rel_set2 = {
        (r.relation_type, r.target_id)
        for r in relations2
    }
    
    # 计算Jaccard相似度
    intersection = len(rel_set1 & rel_set2)
    union = len(rel_set1 | rel_set2)
    
    return intersection / union if union > 0 else 0.0

def calculate_time_similarity(
    time1: datetime,
    time2: datetime
) -> float:
    """计算时间相似度
    
    Args:
        time1: 第一个时间
        time2: 第二个时间
    
    Returns:
        float: 相似度分数(0-1)
    """
    # 计算时间差（小时）
    time_diff = abs((time1 - time2).total_seconds() / 3600)
    
    # 使用高斯衰减
    sigma = 24  # 24小时的标准差
    similarity = np.exp(-0.5 * (time_diff / sigma) ** 2)
    
    return float(similarity)

def merge_memories(
    memories: List[Memory],
    threshold: float = 0.8
) -> List[Memory]:
    """合并相似记忆
    
    功能描述：
        合并相似度高于阈值的记忆：
        1. 合并内容
        2. 合并关系
        3. 合并向量
        4. 更新属性
    
    Args:
        memories: 记忆列表
        threshold: 相似度阈值
    
    Returns:
        List[Memory]: 合并后的记忆列表
    """
    if not memories:
        return []
    
    # 构建相似度矩阵
    n = len(memories)
    similarity_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            similarity = calculate_similarity(
                memories[i],
                memories[j]
            )
            similarity_matrix[i][j] = similarity
            similarity_matrix[j][i] = similarity
    
    # 查找需要合并的记忆组
    merged_groups = []
    visited = set()
    
    for i in range(n):
        if i in visited:
            continue
        
        group = {i}
        for j in range(i + 1, n):
            if similarity_matrix[i][j] >= threshold:
                group.add(j)
        
        if len(group) > 1:
            merged_groups.append(group)
            visited.update(group)
    
    # 执行合并
    result = []
    for i in range(n):
        if i not in visited:
            result.append(memories[i])
    
    for group in merged_groups:
        group_memories = [memories[i] for i in group]
        merged = merge_memory_group(group_memories)
        result.append(merged)
    
    return result

def merge_memory_group(memories: List[Memory]) -> Memory:
    """合并一组记忆
    
    Args:
        memories: 待合并的记忆列表
    
    Returns:
        Memory: 合并后的记忆
    """
    base = memories[0]
    
    # 合并内容
    contents = [m.content for m in memories]
    base.content = "\n".join(contents)
    
    # 合并关系
    all_relations = []
    for memory in memories:
        all_relations.extend(memory.relations)
    base.relations = clean_relations(all_relations)
    
    # 更新属性
    base.importance = max(m.importance for m in memories)
    base.access_count = sum(m.access_count for m in memories)
    base.updated_at = datetime.utcnow()
    
    # 重新生成向量
    base.vectors = generate_memory_vectors(base)
    
    return base

def calculate_memory_importance(memory: Memory) -> int:
    """计算记忆重要性
    
    Args:
        memory: 记忆对象
    
    Returns:
        int: 重要性评分(1-10)
    """
    return calculate_initial_importance(memory)

def generate_memory_embedding(memory: Memory) -> List[float]:
    """生成记忆嵌入向量
    
    Args:
        memory: 记忆对象
    
    Returns:
        List[float]: 嵌入向量
    """
    vectors = generate_memory_vectors(memory)
    if vectors:
        return vectors[0].vector.tolist()
    return []

def validate_memory_data(memory: Memory) -> bool:
    """验证记忆数据
    
    Args:
        memory: 记忆对象
    
    Returns:
        bool: 是否有效
    """
    if not memory.content or len(memory.content.strip()) == 0:
        return False
    
    if memory.importance < 1 or memory.importance > 10:
        return False
    
    return True

def create_memory_context(memory: Memory) -> Dict[str, any]:
    """创建记忆上下文
    
    Args:
        memory: 记忆对象
    
    Returns:
        Dict[str, any]: 上下文信息
    """
    return {
        "id": str(memory.id),
        "content": memory.content,
        "type": memory.memory_type.value,
        "importance": memory.importance,
        "created_at": memory.created_at.isoformat(),
        "relations_count": len(memory.relations),
        "tags": memory.metadata.tags
    }
