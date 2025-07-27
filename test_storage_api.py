#!/usr/bin/env python3
"""
测试存储API的简单脚本
"""

import requests
import json

def test_storage_apis():
    base_url = "http://localhost:8000"
    
    # 测试健康检查
    print("1. 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"健康检查状态: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {response.json()}")
    except Exception as e:
        print(f"健康检查失败: {e}")
    
    # 测试向量存储API
    print("\n2. 测试向量存储API...")
    try:
        response = requests.get(f"{base_url}/storage/vector")
        print(f"向量存储API状态: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"错误响应: {response.text}")
    except Exception as e:
        print(f"向量存储API失败: {e}")
    
    # 测试图存储API
    print("\n3. 测试图存储API...")
    try:
        response = requests.get(f"{base_url}/storage/graph")
        print(f"图存储API状态: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"错误响应: {response.text}")
    except Exception as e:
        print(f"图存储API失败: {e}")
    
    # 测试缓存存储API
    print("\n4. 测试缓存存储API...")
    try:
        response = requests.get(f"{base_url}/storage/cache")
        print(f"缓存存储API状态: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"错误响应: {response.text}")
    except Exception as e:
        print(f"缓存存储API失败: {e}")
    
    # 测试所有存储API
    print("\n5. 测试所有存储API...")
    try:
        response = requests.get(f"{base_url}/storage/all")
        print(f"所有存储API状态: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"错误响应: {response.text}")
    except Exception as e:
        print(f"所有存储API失败: {e}")

if __name__ == "__main__":
    test_storage_apis() 