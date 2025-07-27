#!/usr/bin/env python3
"""
Weaviate集成测试脚本

测试Weaviate向量存储的基本功能：
- 连接测试
- 添加向量
- 搜索向量
- 获取向量
- 删除向量
- 批量操作
- 统计信息

作者：Cursor_for_YansongW
创建日期：2024-01-15
"""

import sys
import os
import numpy as np
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from agent_memory_system.core.storage.vector_store import VectorStore
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log


def test_weaviate_connection():
    """测试Weaviate连接"""
    print("=== 测试Weaviate连接 ===")
    try:
        vector_store = VectorStore()
        print("✓ Weaviate连接成功")
        return vector_store
    except Exception as e:
        print(f"✗ Weaviate连接失败: {e}")
        return None


def test_add_vector(vector_store):
    """测试添加向量"""
    print("\n=== 测试添加向量 ===")
    try:
        # 生成测试向量
        test_vector = np.random.rand(1024).astype('float32')
        test_id = "test_vector_001"
        test_metadata = {
            "content": "这是一个测试记忆",
            "memory_type": "conversation",
            "importance": 8,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # 添加向量
        success = vector_store.add(test_id, test_vector, test_metadata)
        if success:
            print("✓ 添加向量成功")
            return test_id, test_vector
        else:
            print("✗ 添加向量失败")
            return None, None
    except Exception as e:
        print(f"✗ 添加向量异常: {e}")
        return None, None


def test_search_vector(vector_store, query_vector):
    """测试搜索向量"""
    print("\n=== 测试搜索向量 ===")
    try:
        # 搜索相似向量
        results = vector_store.search(query_vector, top_k=5)
        print(f"✓ 搜索成功，找到 {len(results)} 个相似向量")
        for i, (id_value, distance) in enumerate(results):
            print(f"  结果 {i+1}: ID={id_value}, 距离={distance:.4f}")
        return results
    except Exception as e:
        print(f"✗ 搜索向量异常: {e}")
        return []


def test_get_vector(vector_store, vector_id):
    """测试获取向量"""
    print("\n=== 测试获取向量 ===")
    try:
        # 获取向量
        vector = vector_store.get(vector_id)
        if vector is not None:
            print(f"✓ 获取向量成功，维度: {vector.shape}")
            return vector
        else:
            print("✗ 获取向量失败")
            return None
    except Exception as e:
        print(f"✗ 获取向量异常: {e}")
        return None


def test_batch_operations(vector_store):
    """测试批量操作"""
    print("\n=== 测试批量操作 ===")
    try:
        # 生成批量测试数据
        batch_vectors = []
        batch_ids = []
        batch_metadata = []
        
        for i in range(3):
            batch_vectors.append(np.random.rand(1024).astype('float32'))
            batch_ids.append(f"batch_test_{i+1:03d}")
            batch_metadata.append({
                "content": f"批量测试记忆 {i+1}",
                "memory_type": "batch_test",
                "importance": 6 + i,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z"
            })
        
        # 批量添加
        success = vector_store.add_batch(batch_vectors, batch_ids, batch_metadata)
        if success:
            print("✓ 批量添加成功")
            
            # 批量搜索
            search_results = vector_store.search_batch(batch_vectors[:2], k=3)
            print(f"✓ 批量搜索成功，结果数量: {len(search_results)}")
            
            return batch_ids
        else:
            print("✗ 批量添加失败")
            return []
    except Exception as e:
        print(f"✗ 批量操作异常: {e}")
        return []


def test_vector_stats(vector_store):
    """测试向量统计信息"""
    print("\n=== 测试向量统计信息 ===")
    try:
        # 获取统计信息
        stats = vector_store.get_stats()
        print("✓ 获取统计信息成功:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 获取向量数量
        count = len(vector_store)
        print(f"  总向量数量: {count}")
        
        return stats
    except Exception as e:
        print(f"✗ 获取统计信息异常: {e}")
        return {}


def test_delete_vector(vector_store, vector_id):
    """测试删除向量"""
    print("\n=== 测试删除向量 ===")
    try:
        # 删除向量
        success = vector_store.delete(vector_id)
        if success:
            print("✓ 删除向量成功")
            
            # 验证删除
            vector = vector_store.get(vector_id)
            if vector is None:
                print("✓ 向量已成功删除")
            else:
                print("✗ 向量删除验证失败")
        else:
            print("✗ 删除向量失败")
    except Exception as e:
        print(f"✗ 删除向量异常: {e}")


def test_cleanup(vector_store, test_ids):
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")
    try:
        for test_id in test_ids:
            if test_id:
                vector_store.delete(test_id)
        print("✓ 测试数据清理完成")
    except Exception as e:
        print(f"✗ 清理测试数据异常: {e}")


def main():
    """主测试函数"""
    print("开始Weaviate集成测试...")
    
    # 测试连接
    vector_store = test_weaviate_connection()
    if not vector_store:
        print("连接失败，测试终止")
        return
    
    test_ids = []
    
    try:
        # 测试添加向量
        test_id, test_vector = test_add_vector(vector_store)
        if test_id:
            test_ids.append(test_id)
        
        # 测试搜索向量
        if test_vector is not None:
            test_search_vector(vector_store, test_vector)
        
        # 测试获取向量
        if test_id:
            test_get_vector(vector_store, test_id)
        
        # 测试批量操作
        batch_ids = test_batch_operations(vector_store)
        test_ids.extend(batch_ids)
        
        # 测试统计信息
        test_vector_stats(vector_store)
        
        # 测试删除向量
        if test_id:
            test_delete_vector(vector_store, test_id)
            test_ids.remove(test_id)
        
        print("\n=== 测试完成 ===")
        print("✓ 所有测试通过！Weaviate集成正常工作")
        
    except Exception as e:
        print(f"\n=== 测试失败 ===")
        print(f"✗ 测试过程中发生异常: {e}")
    
    finally:
        # 清理测试数据
        test_cleanup(vector_store, test_ids)
        
        # 关闭连接
        try:
            vector_store.close()
            print("✓ Weaviate连接已关闭")
        except:
            pass


if __name__ == "__main__":
    main() 