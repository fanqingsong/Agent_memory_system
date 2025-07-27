#!/usr/bin/env python3
"""
简化的OpenAI embedding功能测试

这个脚本只测试embedding相关的功能，避免导入其他依赖。
"""

import asyncio
import os
import sys
from typing import List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 只导入必要的模块
from agent_memory_system.utils.config import config
from agent_memory_system.utils.openai_client import LLMClient


async def test_openai_embedding():
    """测试OpenAI embedding API"""
    print("=== 测试OpenAI Embedding API ===")
    
    # 检查配置
    print(f"LLM Provider: {config.llm.provider}")
    print(f"OpenAI API Key: {'已设置' if config.llm.api_key else '未设置'}")
    print(f"OpenAI API Base URL: {config.llm.api_base_url}")
    print(f"Embedding Model: {config.embedding.model_name}")
    
    if not config.llm.api_key:
        print("❌ 错误: 未设置OPENAI_API_KEY环境变量")
        return False
    
    try:
        # 测试LLM客户端
        print("\n--- 测试LLM客户端 ---")
        client = LLMClient(
            provider="openai",
            api_key=config.llm.api_key,
            api_base_url=config.llm.api_base_url,
            embedding_model=config.embedding.model_name
        )
        
        # 测试单个文本embedding
        test_text = "这是一个测试文本，用于验证OpenAI embedding功能。"
        print(f"测试文本: {test_text}")
        
        embedding = await client.create_embedding(test_text)
        print(f"✅ 单个文本embedding成功，维度: {len(embedding)}")
        print(f"向量前5个值: {embedding[:5]}")
        
        # 测试批量embedding
        test_texts = [
            "第一个测试文本",
            "第二个测试文本",
            "第三个测试文本"
        ]
        print(f"\n测试批量文本: {test_texts}")
        
        embeddings = await client.create_embeddings(test_texts)
        print(f"✅ 批量embedding成功，数量: {len(embeddings)}")
        for i, emb in enumerate(embeddings):
            print(f"  文本{i+1}维度: {len(emb)}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI embedding测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_service_simple():
    """测试简化的EmbeddingService"""
    print("\n=== 测试简化的EmbeddingService ===")
    
    try:
        # 直接测试embedding服务的关键功能
        from agent_memory_system.core.embedding.embedding_service import EmbeddingService
        
        # 创建embedding服务
        embedding_service = EmbeddingService()
        print(f"✅ EmbeddingService初始化成功")
        print(f"模型名称: {embedding_service.get_model_name()}")
        print(f"向量维度: {embedding_service.get_dimension()}")
        
        # 测试单个文本编码
        test_text = "这是一个测试文本，用于验证embedding服务。"
        print(f"\n测试文本: {test_text}")
        
        vector = embedding_service.encode_single(test_text)
        print(f"✅ 单个文本编码成功，维度: {len(vector)}")
        print(f"向量前5个值: {vector[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ EmbeddingService测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("开始测试OpenAI Embedding功能...\n")
    
    # 设置环境变量（如果未设置）
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未设置OPENAI_API_KEY环境变量")
        print("请设置环境变量后再运行测试")
        return
    
    if not os.getenv("OPENAI_API_BASE_URL"):
        print("⚠️  警告: 未设置OPENAI_API_BASE_URL环境变量")
        print("将使用默认的OpenAI API地址")
    
    # 运行测试
    tests = [
        ("OpenAI Embedding API", test_openai_embedding),
        ("简化的EmbeddingService", test_embedding_service_simple),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print(f"\n{'='*50}")
    print("测试结果汇总:")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！OpenAI embedding功能正常工作。")
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接。")


if __name__ == "__main__":
    asyncio.run(main()) 