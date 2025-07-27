#!/usr/bin/env python3
"""
独立的OpenAI embedding测试

这个脚本直接测试OpenAI API，不依赖项目的其他模块。
"""

import asyncio
import os
import openai
import httpx


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
        # 设置OpenAI客户端
        openai.api_key = api_key
        openai.base_url = api_base_url
        
        # 测试单个文本embedding
        test_text = "这是一个测试文本，用于验证OpenAI embedding功能。"
        print(f"\n测试文本: {test_text}")
        
        response = await openai.Embedding.acreate(
            model=embedding_model,
            input=test_text
        )
        
        embedding = response.data[0].embedding
        print(f"✅ 单个文本embedding成功，维度: {len(embedding)}")
        print(f"向量前5个值: {embedding[:5]}")
        
        # 测试批量embedding
        test_texts = [
            "第一个测试文本",
            "第二个测试文本",
            "第三个测试文本"
        ]
        print(f"\n测试批量文本: {test_texts}")
        
        response = await openai.Embedding.acreate(
            model=embedding_model,
            input=test_texts
        )
        
        embeddings = [data.embedding for data in response.data]
        print(f"✅ 批量embedding成功，数量: {len(embeddings)}")
        for i, emb in enumerate(embeddings):
            print(f"  文本{i+1}维度: {len(emb)}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI embedding测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_http_client():
    """使用HTTP客户端测试"""
    print("\n=== 使用HTTP客户端测试 ===")
    
    api_key = os.getenv("OPENAI_API_KEY")
    api_base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.siliconflow.cn/v1")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
    
    if not api_key:
        print("❌ 错误: 未设置OPENAI_API_KEY环境变量")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": embedding_model,
                "input": "这是一个测试文本"
            }
            
            response = await client.post(
                f"{api_base_url}/embeddings",
                headers=headers,
                json=data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result["data"][0]["embedding"]
                print(f"✅ HTTP客户端测试成功，维度: {len(embedding)}")
                print(f"向量前5个值: {embedding[:5]}")
                return True
            else:
                print(f"❌ HTTP请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ HTTP客户端测试失败: {e}")
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
    tests = [
        ("OpenAI Embedding API", test_openai_embedding),
        ("HTTP客户端", test_http_client),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            result = await test_func()
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