#!/usr/bin/env python3
"""测试Weaviate数据"""

import weaviate
import json

def test_weaviate_data():
    """测试Weaviate数据"""
    
    print("=== 测试Weaviate数据 ===")
    
    try:
        # 连接到Weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=8080
        )
        
        print("✓ 成功连接到Weaviate")
        
        # 获取AgentMemory类
        collection = client.collections.get("AgentMemory")
        print(f"✓ 获取到类: {collection.name}")
        
        # 获取所有对象
        response = collection.query.fetch_objects(
            limit=10,
            return_properties=["memory_id", "content", "memory_type"]
        )
        
        print(f"✓ 找到 {len(response.objects)} 个对象")
        
        for i, obj in enumerate(response.objects):
            print(f"\n对象 {i+1}:")
            print(f"  ID: {obj.uuid}")
            print(f"  memory_id: {obj.properties.get('memory_id', 'N/A')}")
            print(f"  content: {obj.properties.get('content', 'N/A')[:50]}...")
            print(f"  memory_type: {obj.properties.get('memory_type', 'N/A')}")
            
            # 检查向量
            vector = obj.vector
            if vector is not None:
                print(f"  向量维度: {len(vector)}")
                print(f"  向量前5个值: {vector[:5]}")
            else:
                print("  向量: None")
        
        # 测试向量搜索
        print("\n=== 测试向量搜索 ===")
        
        # 创建一个测试向量（全零向量）
        test_vector = [0.0] * 1024
        
        try:
            search_response = collection.query.near_vector(
                near_vector=test_vector,
                limit=5,
                return_properties=["memory_id", "content"]
            )
            
            print(f"✓ 向量搜索成功，找到 {len(search_response.objects)} 个结果")
            
            for i, obj in enumerate(search_response.objects):
                print(f"  结果 {i+1}:")
                print(f"    memory_id: {obj.properties.get('memory_id', 'N/A')}")
                print(f"    content: {obj.properties.get('content', 'N/A')[:50]}...")
                print(f"    距离: {obj.metadata.distance}")
        
        except Exception as e:
            print(f"✗ 向量搜索失败: {e}")
        
        client.close()
        
    except Exception as e:
        print(f"✗ 连接失败: {e}")

if __name__ == "__main__":
    test_weaviate_data() 