"""系统性能测试

测试系统在不同负载下的性能表现。

测试内容：
    - 存储性能测试
    - 检索性能测试
    - 并发性能测试
    - 内存使用测试
    - 响应时间测试
    - 吞吐量测试

作者：Cursor_for_YansongW
创建日期：2024-01-09
"""

import gc
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

import numpy as np
import psutil
from fastapi.testclient import TestClient

from agent_memory_system.api.memory_api import app
from agent_memory_system.core.memory.memory_manager import MemoryManager
from agent_memory_system.core.memory.memory_utils import (
    generate_memory_vectors,
    preprocess_memory
)
from agent_memory_system.core.retrieval.memory_retrieval import MemoryRetrieval
from agent_memory_system.core.storage.cache_store import CacheStore
from agent_memory_system.core.storage.graph_store import GraphStore
from agent_memory_system.core.storage.vector_store import VectorStore
from agent_memory_system.models.memory_model import (
    Memory,
    MemoryRelation,
    MemoryStatus,
    MemoryType,
    RetrievalResult
)

class TestPerformance:
    """系统性能测试类"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建存储引擎
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()
        self.cache_store = CacheStore()
        
        # 创建记忆管理器
        self.memory_manager = MemoryManager()
        
        # 创建API客户端
        self.client = TestClient(app)
        
        # 创建测试数据
        self.memory_data = {
            "content": "这是一条测试记忆",
            "memory_type": "short_term",
            "importance": 5,
            "relations": [
                {
                    "relation_type": "test",
                    "target_id": "test_memory_2",
                    "strength": 5
                }
            ]
        }
        
        # 性能指标
        self.metrics = {
            "response_times": [],
            "memory_usage": [],
            "throughput": []
        }
    
    def teardown_method(self):
        """测试后清理"""
        # 清理测试数据
        self.vector_store.clear()
        self.graph_store.clear()
        self.cache_store.clear_all()
        
        # 强制垃圾回收
        gc.collect()
    
    def measure_response_time(self, func):
        """测量响应时间的装饰器"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            self.metrics["response_times"].append(end_time - start_time)
            return result
        return wrapper
    
    def measure_memory_usage(self):
        """测量内存使用"""
        process = psutil.Process()
        memory_info = process.memory_info()
        self.metrics["memory_usage"].append(memory_info.rss / 1024 / 1024)  # MB
    
    def test_storage_performance(self):
        """测试存储性能"""
        batch_sizes = [100, 500, 1000]
        results = {}
        
        for batch_size in batch_sizes:
            # 准备测试数据
            memories = []
            for i in range(batch_size):
                data = self.memory_data.copy()
                data["content"] = f"这是性能测试记忆{i}"
                memories.append(data)
            
            # 测量批量存储性能
            start_time = time.time()
            for data in memories:
                response = self.client.post(
                    "/memories",
                    json=data
                )
            end_time = time.time()
            
            # 记录性能指标
            total_time = end_time - start_time
            throughput = batch_size / total_time
            self.metrics["throughput"].append(throughput)
            
            results[batch_size] = {
                "total_time": total_time,
                "throughput": throughput,
                "avg_time": total_time / batch_size
            }
            
            # 测量内存使用
            self.measure_memory_usage()
            
            # 清理数据
            self.teardown_method()
            self.setup_method()
        
        # 输出性能报告
        print("\n存储性能测试结果:")
        for batch_size, metrics in results.items():
            print(f"\n批量大小: {batch_size}")
            print(f"总时间: {metrics['total_time']:.2f}秒")
            print(f"吞吐量: {metrics['throughput']:.2f}条/秒")
            print(f"平均时间: {metrics['avg_time']*1000:.2f}毫秒/条")
    
    def test_retrieval_performance(self):
        """测试检索性能"""
        # 准备测试数据
        data_size = 1000
        query_sizes = [10, 50, 100]
        results = {}
        
        # 批量创建记忆
        memories = []
        for i in range(data_size):
            data = self.memory_data.copy()
            data["content"] = f"这是性能测试记忆{i}"
            response = self.client.post(
                "/memories",
                json=data
            )
            memories.append(response.json())
        
        for query_size in query_sizes:
            # 准备查询
            queries = [
                f"性能测试记忆{i}"
                for i in range(query_size)
            ]
            
            # 测量检索性能
            start_time = time.time()
            for query in queries:
                response = self.client.post(
                    "/memories/retrieve",
                    json={
                        "query": query,
                        "top_k": 5
                    }
                )
            end_time = time.time()
            
            # 记录性能指标
            total_time = end_time - start_time
            throughput = query_size / total_time
            self.metrics["throughput"].append(throughput)
            
            results[query_size] = {
                "total_time": total_time,
                "throughput": throughput,
                "avg_time": total_time / query_size
            }
            
            # 测量内存使用
            self.measure_memory_usage()
        
        # 输出性能报告
        print("\n检索性能测试结果:")
        for query_size, metrics in results.items():
            print(f"\n查询数量: {query_size}")
            print(f"总时间: {metrics['total_time']:.2f}秒")
            print(f"吞吐量: {metrics['throughput']:.2f}查询/秒")
            print(f"平均时间: {metrics['avg_time']*1000:.2f}毫秒/查询")
    
    def test_concurrent_performance(self):
        """测试并发性能"""
        # 准备测试数据
        data_size = 100
        concurrent_sizes = [10, 20, 50]
        results = {}
        
        # 创建测试记忆
        memories = []
        for i in range(data_size):
            data = self.memory_data.copy()
            data["content"] = f"这是并发测试记忆{i}"
            response = self.client.post(
                "/memories",
                json=data
            )
            memories.append(response.json())
        
        def concurrent_operation():
            """并发操作"""
            # 创建记忆
            response = self.client.post(
                "/memories",
                json=self.memory_data
            )
            memory_id = response.json()["memory_id"]
            
            # 获取记忆
            response = self.client.get(f"/memories/{memory_id}")
            
            # 更新记忆
            memory = response.json()
            memory["importance"] += 1
            response = self.client.put(
                f"/memories/{memory_id}",
                json=memory
            )
            
            # 检索记忆
            response = self.client.post(
                "/memories/retrieve",
                json={
                    "query": memory["content"],
                    "top_k": 5
                }
            )
        
        for concurrent_size in concurrent_sizes:
            # 创建线程池
            with ThreadPoolExecutor(max_workers=concurrent_size) as executor:
                # 测量并发性能
                start_time = time.time()
                futures = [
                    executor.submit(concurrent_operation)
                    for _ in range(concurrent_size)
                ]
                for future in futures:
                    future.result()
                end_time = time.time()
                
                # 记录性能指标
                total_time = end_time - start_time
                throughput = concurrent_size / total_time
                self.metrics["throughput"].append(throughput)
                
                results[concurrent_size] = {
                    "total_time": total_time,
                    "throughput": throughput,
                    "avg_time": total_time / concurrent_size
                }
                
                # 测量内存使用
                self.measure_memory_usage()
        
        # 输出性能报告
        print("\n并发性能测试结果:")
        for concurrent_size, metrics in results.items():
            print(f"\n并发数: {concurrent_size}")
            print(f"总时间: {metrics['total_time']:.2f}秒")
            print(f"吞吐量: {metrics['throughput']:.2f}操作/秒")
            print(f"平均时间: {metrics['avg_time']*1000:.2f}毫秒/操作")
    
    def test_memory_usage(self):
        """测试内存使用"""
        # 准备测试数据
        data_sizes = [1000, 5000, 10000]
        results = {}
        
        for data_size in data_sizes:
            # 记录初始内存使用
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # 批量创建记忆
            memories = []
            for i in range(data_size):
                data = self.memory_data.copy()
                data["content"] = f"这是内存测试记忆{i}"
                response = self.client.post(
                    "/memories",
                    json=data
                )
                memories.append(response.json())
            
            # 记录最终内存使用
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # 记录性能指标
            memory_increase = final_memory - initial_memory
            memory_per_record = memory_increase / data_size
            
            results[data_size] = {
                "initial_memory": initial_memory,
                "final_memory": final_memory,
                "memory_increase": memory_increase,
                "memory_per_record": memory_per_record
            }
            
            # 清理数据
            self.teardown_method()
            self.setup_method()
        
        # 输出性能报告
        print("\n内存使用测试结果:")
        for data_size, metrics in results.items():
            print(f"\n数据量: {data_size}")
            print(f"初始内存: {metrics['initial_memory']:.2f}MB")
            print(f"最终内存: {metrics['final_memory']:.2f}MB")
            print(f"内存增长: {metrics['memory_increase']:.2f}MB")
            print(f"每条记录内存: {metrics['memory_per_record']*1024:.2f}KB")
    
    def test_response_time(self):
        """测试响应时间"""
        # 准备测试数据
        operations = [
            ("create", lambda: self.client.post(
                "/memories",
                json=self.memory_data
            )),
            ("retrieve", lambda: self.client.post(
                "/memories/retrieve",
                json={
                    "query": "测试记忆",
                    "top_k": 5
                }
            )),
            ("update", lambda memory_id: self.client.put(
                f"/memories/{memory_id}",
                json=self.memory_data
            )),
            ("delete", lambda memory_id: self.client.delete(
                f"/memories/{memory_id}"
            ))
        ]
        
        results = {}
        
        for op_name, op_func in operations:
            response_times = []
            
            # 创建测试记忆
            if op_name in ["update", "delete"]:
                response = self.client.post(
                    "/memories",
                    json=self.memory_data
                )
                memory_id = response.json()["memory_id"]
            
            # 测量响应时间
            for _ in range(100):
                start_time = time.time()
                if op_name in ["update", "delete"]:
                    response = op_func(memory_id)
                else:
                    response = op_func()
                end_time = time.time()
                response_times.append(end_time - start_time)
            
            # 计算统计指标
            results[op_name] = {
                "min": min(response_times) * 1000,
                "max": max(response_times) * 1000,
                "avg": sum(response_times) / len(response_times) * 1000,
                "p95": np.percentile(response_times, 95) * 1000,
                "p99": np.percentile(response_times, 99) * 1000
            }
        
        # 输出性能报告
        print("\n响应时间测试结果:")
        for op_name, metrics in results.items():
            print(f"\n操作: {op_name}")
            print(f"最小响应时间: {metrics['min']:.2f}毫秒")
            print(f"最大响应时间: {metrics['max']:.2f}毫秒")
            print(f"平均响应时间: {metrics['avg']:.2f}毫秒")
            print(f"P95响应时间: {metrics['p95']:.2f}毫秒")
            print(f"P99响应时间: {metrics['p99']:.2f}毫秒")
    
    def test_throughput(self):
        """测试吞吐量"""
        # 准备测试数据
        test_duration = 60  # 测试持续时间(秒)
        concurrent_users = [1, 5, 10]
        results = {}
        
        def user_operation():
            """用户操作"""
            while time.time() < self.end_time:
                # 创建记忆
                response = self.client.post(
                    "/memories",
                    json=self.memory_data
                )
                memory_id = response.json()["memory_id"]
                
                # 检索记忆
                response = self.client.post(
                    "/memories/retrieve",
                    json={
                        "query": self.memory_data["content"],
                        "top_k": 5
                    }
                )
                
                # 更新记忆
                response = self.client.put(
                    f"/memories/{memory_id}",
                    json=self.memory_data
                )
                
                # 删除记忆
                response = self.client.delete(f"/memories/{memory_id}")
                
                self.operation_count += 1
        
        for num_users in concurrent_users:
            # 初始化计数器
            self.operation_count = 0
            self.end_time = time.time() + test_duration
            
            # 创建用户线程
            threads = []
            for _ in range(num_users):
                thread = threading.Thread(target=user_operation)
                threads.append(thread)
                thread.start()
            
            # 等待测试完成
            for thread in threads:
                thread.join()
            
            # 计算吞吐量
            throughput = self.operation_count / test_duration
            
            results[num_users] = {
                "operations": self.operation_count,
                "throughput": throughput
            }
            
            # 清理数据
            self.teardown_method()
            self.setup_method()
        
        # 输出性能报告
        print("\n吞吐量测试结果:")
        for num_users, metrics in results.items():
            print(f"\n并发用户数: {num_users}")
            print(f"总操作数: {metrics['operations']}")
            print(f"吞吐量: {metrics['throughput']:.2f}操作/秒")

if __name__ == "__main__":
    # 运行性能测试
    test = TestPerformance()
    
    print("开始性能测试...")
    
    print("\n1. 存储性能测试")
    test.test_storage_performance()
    
    print("\n2. 检索性能测试")
    test.test_retrieval_performance()
    
    print("\n3. 并发性能测试")
    test.test_concurrent_performance()
    
    print("\n4. 内存使用测试")
    test.test_memory_usage()
    
    print("\n5. 响应时间测试")
    test.test_response_time()
    
    print("\n6. 吞吐量测试")
    test.test_throughput()
    
    print("\n性能测试完成!") 