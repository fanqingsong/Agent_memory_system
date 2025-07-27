#!/usr/bin/env python3
"""
直接查看存储内容的脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent)
sys.path.append(project_root)

from agent_memory_system.core.memory.memory_manager import MemoryManager
from agent_memory_system.utils.config import init_config
from agent_memory_system.utils.logger import init_logger
import json

def view_vector_storage():
    """查看向量存储内容"""
    print("=" * 50)
    print("向量存储信息")
    print("=" * 50)
    
    try:
        memory_manager = MemoryManager()
        vector_store = memory_manager._vector_store
        
        if not vector_store:
            print("向量存储未初始化")
            return
        
        print(f"向量存储类型: Weaviate")
        print(f"向量维度: {vector_store._dimension}")
        print(f"类名称: {vector_store._class_name}")
        
        if hasattr(vector_store, '_collection') and vector_store._collection:
            total_vectors = len(vector_store)
            print(f"总向量数量: {total_vectors}")
            
            if total_vectors > 0:
                print("\n前5个向量的样本:")
                    try:
                    # 获取前5个向量
                    response = vector_store._collection.query.fetch_objects(
                        limit=5,
                        return_properties=["id"]
                    )
                    for i, obj in enumerate(response.objects):
                        vector = obj.vector
                        print(f"  向量 {i+1} (ID: {obj.properties.get('id', 'N/A')}): 维度={len(vector)}, 样本值={vector[:3]}")
                    except Exception as e:
                    print(f"  获取向量样本失败 - {e}")
        else:
            print("向量类未初始化")
            
    except Exception as e:
        print(f"查看向量存储失败: {e}")

def view_graph_storage():
    """查看图存储内容"""
    print("\n" + "=" * 50)
    print("图存储信息")
    print("=" * 50)
    
    try:
        memory_manager = MemoryManager()
        graph_store = memory_manager._graph_store
        
        if not graph_store:
            print("图存储未初始化")
            return
        
        print(f"图存储类型: Neo4j")
        print(f"连接URI: {graph_store._uri}")
        
        with graph_store._driver.session() as session:
            # 获取节点总数
            result = session.run("MATCH (n) RETURN count(n) as count")
            total_nodes = result.single()["count"]
            print(f"总节点数量: {total_nodes}")
            
            # 获取关系总数
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            total_relationships = result.single()["count"]
            print(f"总关系数量: {total_relationships}")
            
            # 获取节点类型
            result = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
            node_types = result.single()["labels"]
            print(f"节点类型: {node_types}")
            
            # 获取关系类型
            result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types")
            relationship_types = result.single()["types"]
            print(f"关系类型: {relationship_types}")
            
            if total_nodes > 0:
                print("\n前5个节点的信息:")
                result = session.run("MATCH (n) RETURN labels(n) as labels, properties(n) as props LIMIT 5")
                for i, record in enumerate(result):
                    props = {k: v for k, v in record["props"].items() if k != 'vector' and len(str(v)) < 100}
                    print(f"  节点 {i+1}: 标签={record['labels']}, 属性={props}")
                    
    except Exception as e:
        print(f"查看图存储失败: {e}")

def view_cache_storage():
    """查看缓存存储内容"""
    print("\n" + "=" * 50)
    print("缓存存储信息")
    print("=" * 50)
    
    try:
        memory_manager = MemoryManager()
        cache_store = memory_manager._cache_store
        
        if not cache_store:
            print("缓存存储未初始化")
            return
        
        print(f"缓存存储类型: Redis")
        
        redis_client = cache_store._client
        info = redis_client.info()
        
        print(f"Redis版本: {info.get('redis_version', 'unknown')}")
        print(f"内存使用: {info.get('used_memory_human', '0')}")
        
        # 获取键数量
        total_keys = info.get("db0", {}).get("keys", 0)
        print(f"总键数量: {total_keys}")
        
        if total_keys > 0:
            print("\n前10个缓存键:")
            keys = redis_client.keys("*")[:10]
            for i, key in enumerate(keys):
                try:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    key_type = redis_client.type(key)
                    
                    if key_type == "string":
                        value = redis_client.get(key)
                        if value:
                            try:
                                # 尝试解析JSON
                                parsed = json.loads(value)
                                preview = str(parsed)[:50] + "..." if len(str(parsed)) > 50 else str(parsed)
                            except:
                                preview = value.decode()[:50] + "..." if len(value) > 50 else value.decode()
                        else:
                            preview = "[空值]"
                    else:
                        preview = f"[{key_type}类型]"
                    
                    print(f"  键 {i+1}: {key_str} ({key_type}) - {preview}")
                    
                except Exception as e:
                    print(f"  键 {i+1}: {key} - 获取失败: {e}")
                    
    except Exception as e:
        print(f"查看缓存存储失败: {e}")

def main():
    """主函数"""
    print("Agent Memory System 存储内容查看器")
    print("=" * 60)
    
    # 初始化配置和日志
    init_config()
    init_logger()
    
    # 查看各种存储
    view_vector_storage()
    view_graph_storage()
    view_cache_storage()
    
    print("\n" + "=" * 60)
    print("查看完成")

if __name__ == "__main__":
    main() 