#!/usr/bin/env python3
"""
测试embedding功能的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_memory_system.core.embedding.embedding_service import generate_embedding_vector, get_embedding_service

def test_embedding():
    """测试embedding功能"""
    print("开始测试embedding功能...")
    
    # 测试文本
    test_texts = [
        "我是青松，请记住",
        "今天天气很好",
        "我喜欢编程",
        "人工智能很有趣"
    ]
    
    try:
        # 获取embedding服务
        print("初始化embedding服务...")
        embedding_service = get_embedding_service()
        print(f"Embedding服务初始化成功: model={embedding_service.get_model_name()}, dimension={embedding_service.get_dimension()}")
        
        # 测试单个文本编码
        print("\n测试单个文本编码:")
        for text in test_texts:
            vector = generate_embedding_vector(text)
            print(f"文本: '{text}' -> 向量维度: {len(vector)}")
        
        # 测试相似度计算
        print("\n测试相似度计算:")
        text1 = "我是青松，请记住"
        text2 = "我的名字是青松"
        text3 = "今天天气很好"
        
        similarity1 = embedding_service.similarity(text1, text2)
        similarity2 = embedding_service.similarity(text1, text3)
        
        print(f"'{text1}' 与 '{text2}' 的相似度: {similarity1:.4f}")
        print(f"'{text1}' 与 '{text3}' 的相似度: {similarity2:.4f}")
        
        print("\nEmbedding功能测试完成！")
        
    except Exception as e:
        print(f"Embedding功能测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedding() 