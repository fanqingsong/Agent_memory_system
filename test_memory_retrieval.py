#!/usr/bin/env python3
"""测试记忆检索功能"""

import asyncio
import json
import requests
from datetime import datetime

def test_memory_retrieval():
    """测试记忆检索功能"""
    
    # 测试数据
    base_url = "http://localhost:8000"
    
    print("=== 测试记忆检索功能 ===")
    
    # 1. 首先获取所有记忆
    print("\n1. 获取所有记忆...")
    try:
        response = requests.get(f"{base_url}/memories")
        if response.status_code == 200:
            memories = response.json()
            print(f"找到 {len(memories)} 个记忆")
            for memory in memories[:3]:  # 只显示前3个
                print(f"  - ID: {memory['id']}")
                print(f"    内容: {memory['content'][:50]}...")
                print(f"    类型: {memory['memory_type']}")
                print(f"    重要性: {memory['importance']}")
                print()
        else:
            print(f"获取记忆失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 2. 测试记忆搜索
    print("\n2. 测试记忆搜索...")
    search_query = {
        "query": "我是青松",
        "threshold": 0.3,
        "limit": 5
    }
    
    try:
        response = requests.post(
            f"{base_url}/memories/search",
            json=search_query,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            results = response.json()
            print(f"搜索到 {len(results)} 个相关记忆")
            for result in results:
                print(f"  - 相似度: {result.get('score', 0):.3f}")
                print(f"    内容: {result['memory']['content'][:50]}...")
                print()
        else:
            print(f"搜索失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"搜索请求失败: {e}")
    
    # 3. 测试WebSocket聊天
    print("\n3. 测试WebSocket聊天...")
    print("请手动在浏览器中测试聊天功能")
    print("访问: http://localhost:3000/chat")
    print("发送消息: '我是谁？' 来测试记忆检索")

if __name__ == "__main__":
    test_memory_retrieval() 