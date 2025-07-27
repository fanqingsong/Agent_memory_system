#!/usr/bin/env python3
"""
测试OpenAI客户端

这个脚本直接测试OpenAI客户端，不导入整个项目。
"""

import asyncio
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入OpenAI客户端
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent_memory_system', 'utils'))
from openai_client import LLMClient


async def test_openai_embedding():
    """测试OpenAI embedding API"""
    print("=== 测试OpenAI Embedding API ===")
    
    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    api_base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.siliconflow.cn/v1")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
    
    print(f"OpenAI API Key: {'已设置' if api_key else '未设置'}")
    print(f"OpenAI API Base URL: {api_base_url}")
    print(f"Embedding Model: {embedding_model}")
    
    if not api_key:
        print("❌ 错误: 未设置OPENAI_API_KEY环境变量")
        return False
    
    try:
        # 测试LLM客户端
        print("\n--- 测试LLM客户端 ---")
        client = LLMClient(
            provider="openai",
            api_key=api_key,
            api_base_url=api_base_url,
            embedding_model=embedding_model
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


async def main():
    """主测试函数"""
    print("开始测试OpenAI Embedding功能...\n")
    
    # 设置环境变量（如果未设置）
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未设置OPENAI_API_KEY环境变量")
        print("请设置环境变量后再运行测试")
        return
    
    # 运行测试
    result = await test_openai_embedding()
    
    # 输出测试结果
    print(f"\n{'='*50}")
    print("测试结果汇总:")
    print("="*50)
    
    if result:
        print("✅ 测试通过！OpenAI embedding功能正常工作。")
    else:
        print("❌ 测试失败，请检查配置和网络连接。")


if __name__ == "__main__":
    asyncio.run(main()) 