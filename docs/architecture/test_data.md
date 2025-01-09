# 测试数据设计

## 1. 测试数据管理

### 1.1 数据隔离

```python
# 测试环境配置
class TestEnvironment:
    # 数据库配置
    db_config = {
        'test_db_prefix': 'test_',  # 测试数据库前缀
        'test_collection_prefix': 'test_',  # 测试集合前缀
        'isolation_level': 'READ COMMITTED'  # 事务隔离级别
    }
    
    # 存储配置
    storage_config = {
        'faiss_index_prefix': 'test_',  # FAISS索引前缀
        'neo4j_database': 'test_memory',  # Neo4j测试数据库
        'redis_prefix': 'test:'  # Redis键前缀
    }
    
    # 环境标记
    environment_markers = {
        'is_test': True,
        'test_id': '',  # 每次测试运行的唯一标识
        'timestamp': ''  # 测试开始时间
    }
```

### 1.2 数据生成器

```python
# 记忆数据生成器
class MemoryDataGenerator:
    # 常规记忆生成
    def generate_regular_memory(self, count: int) -> List[Dict]:
        memories = []
        for i in range(count):
            memory = {
                'id': f'test_mem_{i}',
                'content': f'测试记忆内容 {i}',
                'timestamp': datetime.now(),
                'importance': random.randint(1, 10),
                'embedding': np.random.rand(768),  # 随机向量
                'metadata': {
                    'source': 'test',
                    'type': 'regular',
                    'tags': ['test', f'tag_{i}']
                }
            }
            memories.append(memory)
        return memories
    
    # 技能记忆生成
    def generate_skill_memory(self, count: int) -> List[Dict]:
        skills = []
        for i in range(count):
            skill = {
                'id': f'test_skill_{i}',
                'task_type': f'test_task_{i}',
                'workflow': [
                    f'step_{j}' for j in range(random.randint(3, 6))
                ],
                'conditions': [
                    f'condition_{j}' for j in range(random.randint(2, 4))
                ],
                'success_rate': random.uniform(0.7, 1.0),
                'embedding': np.random.rand(768),
                'metadata': {
                    'source': 'test',
                    'type': 'skill',
                    'complexity': random.randint(1, 5)
                }
            }
            skills.append(skill)
        return skills
```

### 1.3 关系生成器

```python
# 记忆关系生成器
class RelationGenerator:
    def generate_relations(self, memories: List[Dict]) -> List[Dict]:
        relations = []
        memory_count = len(memories)
        
        # 生成随机关系
        for i in range(memory_count):
            # 每个记忆与2-4个其他记忆建立关系
            relation_count = random.randint(2, 4)
            for _ in range(relation_count):
                target_idx = random.randint(0, memory_count - 1)
                if target_idx != i:
                    relation = {
                        'source': memories[i]['id'],
                        'target': memories[target_idx]['id'],
                        'type': random.choice(['related', 'depends', 'similar']),
                        'weight': random.uniform(0.5, 1.0),
                        'metadata': {
                            'source': 'test',
                            'timestamp': datetime.now()
                        }
                    }
                    relations.append(relation)
        
        return relations
```

## 2. 测试数据操作

### 2.1 数据初始化

```python
# 测试数据初始化器
class TestDataInitializer:
    def __init__(self):
        self.memory_generator = MemoryDataGenerator()
        self.relation_generator = RelationGenerator()
    
    async def initialize_test_data(self, config: Dict) -> str:
        """初始化测试数据
        
        Args:
            config: 测试配置
                - regular_memory_count: 常规记忆数量
                - skill_memory_count: 技能记忆数量
                - relation_density: 关系密度
        
        Returns:
            test_id: 测试ID
        """
        try:
            # 生成测试ID
            test_id = f'test_{int(time.time())}_{random.randint(1000, 9999)}'
            
            # 生成记忆数据
            regular_memories = self.memory_generator.generate_regular_memory(
                config['regular_memory_count']
            )
            skill_memories = self.memory_generator.generate_skill_memory(
                config['skill_memory_count']
            )
            
            # 生成关系数据
            all_memories = regular_memories + skill_memories
            relations = self.relation_generator.generate_relations(all_memories)
            
            # 存储数据
            await self.store_test_data(test_id, regular_memories, skill_memories, relations)
            
            return test_id
            
        except Exception as e:
            logger.error(f'测试数据初始化失败: {e}')
            raise
```

### 2.2 数据清理

```python
# 测试数据清理器
class TestDataCleaner:
    async def cleanup_test_data(self, test_id: str):
        """清理测试数据
        
        Args:
            test_id: 测试ID
        """
        try:
            # 清理FAISS索引
            await self.cleanup_faiss(f'test_{test_id}')
            
            # 清理Neo4j数据
            await self.cleanup_neo4j(test_id)
            
            # 清理Redis缓存
            await self.cleanup_redis(f'test:{test_id}:*')
            
            logger.info(f'测试数据清理完成: {test_id}')
            
        except Exception as e:
            logger.error(f'测试数据清理失败: {e}')
            raise
    
    async def cleanup_all_test_data(self):
        """清理所有测试数据"""
        try:
            # 清理所有测试数据库
            await self.cleanup_faiss('test_*')
            await self.cleanup_neo4j_database('test_memory')
            await self.cleanup_redis('test:*')
            
            logger.info('所有测试数据清理完成')
            
        except Exception as e:
            logger.error(f'清理所有测试数据失败: {e}')
            raise
```

## 3. 测试场景

### 3.1 基础测试场景

```python
# 测试场景配置
basic_test_scenarios = [
    {
        'name': '小规模数据测试',
        'config': {
            'regular_memory_count': 100,
            'skill_memory_count': 20,
            'relation_density': 0.3
        }
    },
    {
        'name': '中规模数据测试',
        'config': {
            'regular_memory_count': 1000,
            'skill_memory_count': 200,
            'relation_density': 0.2
        }
    },
    {
        'name': '大规模数据测试',
        'config': {
            'regular_memory_count': 10000,
            'skill_memory_count': 2000,
            'relation_density': 0.1
        }
    }
]
```

### 3.2 特殊测试场景

```python
# 特殊测试场景
special_test_scenarios = [
    {
        'name': '高密度关系测试',
        'config': {
            'regular_memory_count': 100,
            'skill_memory_count': 20,
            'relation_density': 0.8
        }
    },
    {
        'name': '长文本记忆测试',
        'config': {
            'regular_memory_count': 50,
            'skill_memory_count': 10,
            'relation_density': 0.3,
            'content_length': 'long'
        }
    },
    {
        'name': '复杂技能测试',
        'config': {
            'regular_memory_count': 50,
            'skill_memory_count': 50,
            'relation_density': 0.4,
            'skill_complexity': 'high'
        }
    }
]
```

## 4. 测试数据验证

### 4.1 数据完整性检查

```python
# 数据验证器
class DataValidator:
    async def validate_test_data(self, test_id: str) -> ValidationResult:
        """验证测试数据的完整性
        
        Args:
            test_id: 测试ID
        
        Returns:
            validation_result: 验证结果
        """
        try:
            # 检查记忆数据
            memory_result = await self.validate_memories(test_id)
            
            # 检查关系数据
            relation_result = await self.validate_relations(test_id)
            
            # 检查向量索引
            vector_result = await self.validate_vectors(test_id)
            
            # 检查缓存数据
            cache_result = await self.validate_cache(test_id)
            
            return ValidationResult(
                memory_result=memory_result,
                relation_result=relation_result,
                vector_result=vector_result,
                cache_result=cache_result
            )
            
        except Exception as e:
            logger.error(f'数据验证失败: {e}')
            raise
```

### 4.2 一致性检查

```python
# 一致性检查器
class ConsistencyChecker:
    async def check_consistency(self, test_id: str) -> ConsistencyResult:
        """检查测试数据的一致性
        
        Args:
            test_id: 测试ID
        
        Returns:
            consistency_result: 一致性检查结果
        """
        try:
            # 检查FAISS和Neo4j的数据一致性
            vector_graph_consistency = await self.check_vector_graph_consistency(test_id)
            
            # 检查Neo4j和Redis的数据一致性
            graph_cache_consistency = await self.check_graph_cache_consistency(test_id)
            
            # 检查关系的双向一致性
            relation_consistency = await self.check_relation_consistency(test_id)
            
            return ConsistencyResult(
                vector_graph_consistency=vector_graph_consistency,
                graph_cache_consistency=graph_cache_consistency,
                relation_consistency=relation_consistency
            )
            
        except Exception as e:
            logger.error(f'一致性检查失败: {e}')
            raise
```

## 5. 测试数据监控

### 5.1 数据量监控

```python
# 数据量监控器
class DataVolumeMonitor:
    async def monitor_data_volume(self, test_id: str) -> VolumeMetrics:
        """监控测试数据量
        
        Args:
            test_id: 测试ID
        
        Returns:
            volume_metrics: 数据量指标
        """
        try:
            # 获取各存储的数据量
            faiss_volume = await self.get_faiss_volume(test_id)
            neo4j_volume = await self.get_neo4j_volume(test_id)
            redis_volume = await self.get_redis_volume(test_id)
            
            # 计算增长率
            volume_growth = await self.calculate_volume_growth(test_id)
            
            return VolumeMetrics(
                faiss_volume=faiss_volume,
                neo4j_volume=neo4j_volume,
                redis_volume=redis_volume,
                volume_growth=volume_growth
            )
            
        except Exception as e:
            logger.error(f'数据量监控失败: {e}')
            raise
```

### 5.2 性能监控

```python
# 性能监控器
class PerformanceMonitor:
    async def monitor_performance(self, test_id: str) -> PerformanceMetrics:
        """监控测试数据操作性能
        
        Args:
            test_id: 测试ID
        
        Returns:
            performance_metrics: 性能指标
        """
        try:
            # 监控查询性能
            query_metrics = await self.monitor_query_performance(test_id)
            
            # 监控写入性能
            write_metrics = await self.monitor_write_performance(test_id)
            
            # 监控关系操作性能
            relation_metrics = await self.monitor_relation_performance(test_id)
            
            return PerformanceMetrics(
                query_metrics=query_metrics,
                write_metrics=write_metrics,
                relation_metrics=relation_metrics
            )
            
        except Exception as e:
            logger.error(f'性能监控失败: {e}')
            raise
``` 