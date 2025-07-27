"""向量存储模块

使用Weaviate实现高性能的向量存储和检索。

主要功能：
    - 向量的存储和索引
    - 向量的相似度检索
    - 向量的批量操作
    - 类的管理

依赖：
    - weaviate-client: Weaviate Python客户端
    - numpy: 数值计算
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2024-01-15
"""

import threading
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import weaviate

from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log


class VectorStore:
    """向量存储类
    
    功能描述：
        使用Weaviate实现高性能的向量存储和检索功能，支持：
        1. 向量的存储和索引构建
        2. 基于相似度的向量检索
        3. 向量的批量操作
        4. 类的管理和优化
        5. 自动连接管理
    
    属性说明：
        - _client: Weaviate客户端实例
        - _dimension: 向量维度
        - _class_name: 类名称
        - _lock: 线程锁
    
    依赖关系：
        - 依赖Weaviate进行向量操作
        - 依赖Config获取配置
        - 依赖Logger记录日志
    """
    
    def __init__(
        self,
        dimension: int = 1024,  # 默认使用BAAI/bge-large-zh-v1.5的维度
        class_name: str = None,
        distance_metric: str = "cosine"
    ) -> None:
        """初始化向量存储
        
        Args:
            dimension: 向量维度
            class_name: 类名称
            distance_metric: 距离度量类型
        """
        self._dimension = dimension
        self._class_name = class_name or config.storage.weaviate_class_name
        self._distance_metric = distance_metric
        
        # 初始化锁
        self._lock = threading.Lock()
        
        # 连接Weaviate
        self._connect_weaviate()
        
        # 初始化类
        self._init_class()
        
        log.info(f"Weaviate向量存储初始化完成，类名称: {self._class_name}")
    
    def _connect_weaviate(self) -> None:
        """连接Weaviate服务器"""
        try:
            # 使用v4的API
            self._client = weaviate.connect_to_local(
                host=config.storage.weaviate_host,
                port=config.storage.weaviate_port
                )
            log.info("Weaviate连接成功")
        except Exception as e:
            log.error(f"Weaviate连接失败: {e}")
            raise Exception(f"Weaviate连接失败: {e}")
    
    def _init_class(self) -> None:
        """初始化类"""
        try:
            # 检查类是否存在
            if self._client.collections.exists(self._class_name):
                self._collection = self._client.collections.get(self._class_name)
                log.info(f"加载已存在的类: {self._class_name}")
            else:
                # 创建新类
                self._create_class()
                log.info(f"创建新类: {self._class_name}")
            
        except Exception as e:
            log.error(f"初始化类失败: {e}")
            raise
    
    def _create_class(self) -> None:
        """创建类"""
        try:
            from weaviate.classes.config import Configure, DataType, Property
            
            # 定义属性
            properties = [
                Property(name="memory_id", data_type=DataType.TEXT, is_partition_key=True),
                Property(name="content", data_type=DataType.TEXT),
                Property(name="memory_type", data_type=DataType.TEXT),
                Property(name="importance", data_type=DataType.INT),
                Property(name="created_at", data_type=DataType.DATE),
                Property(name="updated_at", data_type=DataType.DATE)
            ]
            
            # 创建类
            self._collection = self._client.collections.create(
                name=self._class_name,
                properties=properties,
                vectorizer_config=Configure.Vectorizer.none(),
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=weaviate.classes.config.VectorDistances.COSINE
                )
            )
            
            log.info(f"创建类成功: {self._class_name}")
            
        except Exception as e:
            log.error(f"创建类失败: {e}")
            raise
    
    def add(
        self,
        id: str,
        vector: Union[np.ndarray, List[float]],
        metadata: Optional[Dict] = None
    ) -> bool:
        """添加向量
        
        Args:
            id: 向量ID
            vector: 向量数据
            metadata: 元数据
        
        Returns:
            bool: 是否添加成功
        
        Raises:
            ValueError: 当向量维度不匹配时
        """
        try:
            # 转换为numpy数组
            vector = np.array(vector).astype('float32')
            if vector.shape != (self._dimension,):
                raise ValueError(
                    f"向量维度不匹配: 期望{self._dimension}, "
                    f"实际{vector.shape[0]}"
                )
            
            with self._lock:
                # 准备数据
                from datetime import datetime
                current_time = datetime.utcnow().isoformat() + "Z"
                
                data = {
                    "memory_id": id,
                    "content": metadata.get("content", "") if metadata else "",
                    "memory_type": metadata.get("memory_type", "") if metadata else "",
                    "importance": metadata.get("importance", 5) if metadata else 5,
                    "created_at": metadata.get("created_at", current_time) if metadata and metadata.get("created_at") else current_time,
                    "updated_at": metadata.get("updated_at", current_time) if metadata and metadata.get("updated_at") else current_time
                }
                
                # 插入数据
                self._collection.data.insert(
                    properties=data,
                    vector=vector.tolist()
                )
                
                log.debug(f"添加向量成功: {id}")
                return True
                
        except Exception as e:
            log.error(f"添加向量失败: {e}")
            return False
    
    def search(
        self,
        vector: Union[np.ndarray, List[float]],
        top_k: int = 10,
        threshold: float = None
    ) -> List[Tuple[str, float]]:
        """搜索相似向量
        
        Args:
            vector: 查询向量
            top_k: 返回的最相似向量数量
            threshold: 相似度阈值
        
        Returns:
            List[Tuple[str, float]]: (向量ID, 相似度)列表
        """
        try:
            # 转换为numpy数组
            vector = np.array(vector).astype('float32')
            if vector.shape != (self._dimension,):
                raise ValueError(
                    f"向量维度不匹配: 期望{self._dimension}, "
                    f"实际{vector.shape[0]}"
                )
            
            with self._lock:
                # 执行搜索
                response = self._collection.query.near_vector(
                    near_vector=vector.tolist(),
                    limit=top_k,
                    return_properties=["memory_id"]
                )
                
                # 处理结果
                search_results = []
                for obj in response.objects:
                    distance = obj.metadata.distance
                    # 检查距离值是否有效
                    if distance is None:
                        continue
                    
                    if threshold and distance > threshold:
                        continue
                    
                    # 获取ID
                    id_value = obj.properties.get("memory_id")
                    if id_value:
                        search_results.append((id_value, float(distance)))
                
                return search_results
                
        except Exception as e:
            log.error(f"搜索向量失败: {e}")
            return []
    
    def delete(self, id: str) -> bool:
        """删除向量
        
        Args:
            id: 向量ID
        
        Returns:
            bool: 是否删除成功
        """
        try:
            with self._lock:
                # 删除数据
                self._collection.data.delete_many(
                    where=weaviate.classes.query.Filter.by_property("memory_id").equal(id)
                )
                
                log.debug(f"删除向量成功: {id}")
                return True
                
        except Exception as e:
            log.error(f"删除向量失败: {e}")
            return False
    
    def update(
        self,
        id: str,
        vector: Union[np.ndarray, List[float]],
        metadata: Optional[Dict] = None
    ) -> bool:
        """更新向量
        
        Args:
            id: 向量ID
            vector: 新的向量数据
            metadata: 新的元数据
        
        Returns:
            bool: 是否更新成功
        """
        try:
            # 删除旧向量
            if not self.delete(id):
                return False
            
            # 添加新向量
            return self.add(id, vector, metadata)
            
        except Exception as e:
            log.error(f"更新向量失败: {e}")
            return False
    
    def get(self, id: str) -> Optional[np.ndarray]:
        """获取向量
        
        Args:
            id: 向量ID
        
        Returns:
            np.ndarray: 向量数据，如果不存在则返回None
        """
        try:
            with self._lock:
                # 查询数据
                response = self._collection.query.fetch_objects(
                    where=weaviate.classes.query.Filter.by_property("memory_id").equal(id),
                    limit=1
                )
                
                if response.objects:
                    # 获取向量
                    vector_data = response.objects[0].vector
                    return np.array(vector_data, dtype='float32')
                else:
                    return None
                    
        except Exception as e:
            log.error(f"获取向量失败: {e}")
            return None
    
    def clear(self) -> bool:
        """清空类
        
        Returns:
            bool: 是否清空成功
        """
        try:
            with self._lock:
                # 删除所有数据
                self._collection.data.delete_many(
                    where=weaviate.classes.query.Filter.by_property("memory_id").not_equal("")
                )
                
                log.info("清空类成功")
            return True
                
        except Exception as e:
            log.error(f"清空类失败: {e}")
            return False
    
    def __len__(self) -> int:
        """获取向量数量
        
        Returns:
            int: 向量数量
        """
        try:
            response = self._collection.aggregate.over_all(total_count=True)
            return response.total_count
        except Exception as e:
            log.error(f"获取向量数量失败: {e}")
            return 0
    
    def __contains__(self, id: str) -> bool:
        """检查向量是否存在
        
        Args:
            id: 向量ID
        
        Returns:
            bool: 是否存在
        """
        try:
            response = self._collection.query.fetch_objects(
                where=weaviate.classes.query.Filter.by_property("memory_id").equal(id),
                limit=1
            )
            return len(response.objects) > 0
        except Exception as e:
            log.error(f"检查向量存在性失败: {e}")
            return False
    
    def add_batch(
        self,
        vectors: Union[np.ndarray, List[List[float]]],
        ids: List[str],
        metadata_list: Optional[List[Dict]] = None
    ) -> bool:
        """批量添加向量
        
        Args:
            vectors: 向量数据列表
            ids: 向量ID列表
            metadata_list: 元数据列表
        
        Returns:
            bool: 是否添加成功
            
        Raises:
            ValueError: 当向量维度不匹配或长度不一致时
        """
        try:
            # 转换为numpy数组
            vectors = np.array(vectors).astype('float32')
            if vectors.shape[1] != self._dimension:
                raise ValueError(
                    f"向量维度不匹配: 期望{self._dimension}, "
                    f"实际{vectors.shape[1]}"
                )
            if len(vectors) != len(ids):
                raise ValueError(
                    f"向量数量与ID数量不匹配: "
                    f"向量{len(vectors)}, ID{len(ids)}"
                )
            
            with self._lock:
                # 准备批量数据
                from datetime import datetime
                current_time = datetime.utcnow().isoformat() + "Z"
                
                batch_data = []
                for i, (vector, id) in enumerate(zip(vectors, ids)):
                    metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
                    data = {
                        "memory_id": id,
                        "content": metadata.get("content", ""),
                        "memory_type": metadata.get("memory_type", ""),
                        "importance": metadata.get("importance", 5),
                        "created_at": metadata.get("created_at", current_time) if metadata.get("created_at") else current_time,
                        "updated_at": metadata.get("updated_at", current_time) if metadata.get("updated_at") else current_time
                    }
                    batch_data.append((data, vector.tolist()))
                
                # 批量插入
                self._collection.data.insert_many(batch_data)
                
                log.info(f"批量添加向量成功，数量: {len(ids)}")
                return True
                
        except Exception as e:
            log.error(f"批量添加向量失败: {e}")
            return False
    
    def search_batch(
        self,
        vectors: Union[np.ndarray, List[List[float]]],
        k: int = 10,
        threshold: float = None
    ) -> List[List[Tuple[str, float]]]:
        """批量搜索相似向量
        
        Args:
            vectors: 查询向量列表
            k: 返回的最相似向量数量
            threshold: 相似度阈值
        
        Returns:
            List[List[Tuple[str, float]]]: 每个查询向量的(向量ID, 相似度)列表
        """
        try:
            # 转换为numpy数组
            vectors = np.array(vectors).astype('float32')
            if vectors.shape[1] != self._dimension:
                raise ValueError(
                    f"向量维度不匹配: 期望{self._dimension}, "
                    f"实际{vectors.shape[1]}"
                )
            
            with self._lock:
                # 批量搜索
                batch_results = []
                for vector in vectors:
                    response = self._collection.query.near_vector(
                        near_vector=vector.tolist(),
                        limit=k,
                        return_properties=["memory_id"]
                    )
                    
                    query_results = []
                    for obj in response.objects:
                        distance = obj.metadata.distance
                        # 检查距离值是否有效
                        if distance is None:
                            continue
                        
                        if threshold and distance > threshold:
                            continue
                        
                        # 获取ID
                        id_value = obj.properties.get("memory_id")
                        if id_value:
                            query_results.append((id_value, float(distance)))
                    
                    batch_results.append(query_results)
                
                return batch_results
                
        except Exception as e:
            log.error(f"批量搜索向量失败: {e}")
            return []
    
    def optimize(self) -> bool:
        """优化类
        
        Returns:
            bool: 是否优化成功
        """
        try:
            with self._lock:
                # Weaviate会自动优化，这里只是记录日志
                log.info("类优化完成（Weaviate自动优化）")
                return True
                
        except Exception as e:
            log.error(f"优化类失败: {e}")
            return False
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Tuple[str, np.ndarray, Dict]]:
        """获取所有向量
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            List[Tuple[str, np.ndarray, Dict]]: (向量ID, 向量, 元数据)列表
        """
        try:
            with self._lock:
                # 获取所有对象
                response = self._collection.query.fetch_objects(
                    limit=limit,
                    offset=offset,
                    return_properties=["memory_id", "content", "memory_type", "importance", "created_at", "updated_at"]
                )
                
                results = []
                for obj in response.objects:
                    # 获取向量ID
                    memory_id = obj.properties.get("memory_id")
                    if not memory_id:
                        continue
                    
                    # 获取向量
                    vector = obj.vector
                    if vector is None:
                        continue
                    
                    # 构建元数据
                    metadata = {
                        "content": obj.properties.get("content", ""),
                        "memory_type": obj.properties.get("memory_type", ""),
                        "importance": obj.properties.get("importance", 0),
                        "created_at": obj.properties.get("created_at", ""),
                        "updated_at": obj.properties.get("updated_at", "")
                    }
                    
                    results.append((memory_id, np.array(vector), metadata))
                
                return results
                
        except Exception as e:
            log.error(f"获取所有向量失败: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """获取类统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            response = self._collection.aggregate.over_all(total_count=True)
            stats = {
                "class_name": self._class_name,
                "num_entities": response.total_count,
                "dimension": self._dimension,
                "distance_metric": self._distance_metric
            }
            return stats
        except Exception as e:
            log.error(f"获取统计信息失败: {e}")
            return {}
    
    def close(self) -> None:
        """关闭连接"""
        try:
            self._client.close()
            log.info("Weaviate连接已关闭")
        except Exception as e:
            log.error(f"关闭Weaviate连接失败: {e}")
    
    def __del__(self) -> None:
        """析构函数"""
        try:
            self.close()
        except:
            pass
