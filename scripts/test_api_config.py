#!/usr/bin/env python3
"""
API配置测试脚本

用于测试不同API提供商的配置是否正确。

使用方法:
    python scripts/test_api_config.py [provider]

支持的provider:
    - openai: 测试OpenAI API
    
    - azure: 测试Azure OpenAI API
"""

import asyncio
import os
import sys
from typing import Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_memory_system.utils.openai_client import LLMClient
from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

async def test_openai_api():
    """测试OpenAI API"""
    print("🔍 测试OpenAI API配置...")
    
    if not config.llm.api_key:
        print("❌ 未找到OPENAI_API_KEY环境变量")
        return False
    
    try:
        client = LLMClient(
            provider="openai",
            api_key=config.llm.api_key,
            api_base_url=config.llm.api_base_url,
            model=config.llm.model
        )
        
        print(f"✅ 使用模型: {config.llm.model}")
        if config.llm.api_base_url:
            print(f"✅ API基础URL: {config.llm.api_base_url}")
        
        # 测试API调用
        response = await client.chat_completion(
            system_prompt="你是一个有用的助手。请用简短的话回复。",
            user_message="你好，请说'测试成功'",
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"✅ API调用成功: {response}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API测试失败: {e}")
        return False



async def test_azure_openai():
    """测试Azure OpenAI API"""
    print("🔍 测试Azure OpenAI API配置...")
    
    if not config.llm.api_key:
        print("❌ 未找到OPENAI_API_KEY环境变量")
        return False
    
    if not config.llm.api_base_url:
        print("❌ 未找到OPENAI_API_BASE_URL环境变量")
        return False
    
    try:
        client = LLMClient(
            provider="openai",
            api_key=config.llm.api_key,
            api_base_url=config.llm.api_base_url,
            model=config.llm.model
        )
        
        print(f"✅ 使用模型: {config.llm.model}")
        print(f"✅ Azure端点: {config.llm.api_base_url}")
        
        # 测试API调用
        response = await client.chat_completion(
            system_prompt="你是一个有用的助手。请用简短的话回复。",
            user_message="你好，请说'测试成功'",
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"✅ API调用成功: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI API测试失败: {e}")
        return False

async def test_embedding():
    """测试嵌入生成"""
    print("🔍 测试嵌入生成...")
    
    try:
        client = LLMClient(
            provider="openai",
            api_key=config.llm.api_key,
            api_base_url=config.llm.api_base_url
        )
        
        # 测试嵌入生成
        text = "这是一个测试文本"
        embedding = await client.create_embedding(text)
        
        print(f"✅ 嵌入生成成功，维度: {len(embedding)}")
        return True
        
    except Exception as e:
        print(f"❌ 嵌入生成测试失败: {e}")
        return False

async def test_model_list():
    """测试模型列表获取"""
    print("🔍 测试模型列表获取...")
    
    try:
        client = LLMClient(
            provider="openai",
            api_key=config.llm.api_key,
            api_base_url=config.llm.api_base_url
        )
        
        # 获取模型列表
        models = await client.list_models()
        
        print(f"✅ 获取到 {len(models)} 个模型:")
        for model in models[:5]:  # 只显示前5个
            print(f"   - {model}")
        if len(models) > 5:
            print(f"   ... 还有 {len(models) - 5} 个模型")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型列表获取失败: {e}")
        return False

def print_config_info():
    """打印当前配置信息"""
    print("📋 当前配置信息:")
    print(f"   LLM Provider: {config.llm.provider}")
    print(f"   Model: {config.llm.model}")
    
    if config.llm.provider == "openai":
        print(f"   API Key: {'已设置' if config.llm.api_key else '未设置'}")
        print(f"   API Base URL: {config.llm.api_base_url or '使用默认'}")

    
    print()

async def main():
    """主函数"""
    print("🚀 API配置测试工具")
    print("=" * 50)
    
    # 打印配置信息
    print_config_info()
    
    # 获取测试类型
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    results = []
    
    if test_type == "all":
        # 根据当前配置测试
        if config.llm.provider == "openai":
            if config.llm.api_base_url and "azure" in config.llm.api_base_url.lower():
                results.append(await test_azure_openai())
            else:
                results.append(await test_openai_api())

        
        # 测试通用功能
        results.append(await test_embedding())
        results.append(await test_model_list())
        
    elif test_type == "openai":
        results.append(await test_openai_api())
        

        
    elif test_type == "azure":
        results.append(await test_azure_openai())
        
    elif test_type == "embedding":
        results.append(await test_embedding())
        
    elif test_type == "models":
        results.append(await test_model_list())
        
    else:
        print(f"❌ 未知的测试类型: {test_type}")
        print("支持的测试类型: all, openai, azure, embedding, models")
        return
    
    # 输出结果
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    
    if all(results):
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
        failed_count = len([r for r in results if not r])
        print(f"   失败测试数: {failed_count}/{len(results)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        sys.exit(1) 