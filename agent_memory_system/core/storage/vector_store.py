"""向量存储模块

使用FAISS实现高性能的向量存储和检索。

主要功能：
    - 向量的存储和索引
    - 向量的相似度检索
    - 向量的批量操作
    - 索引的持久化

依赖：
    - faiss: Facebook AI Similarity Search
    - numpy: 数值计算
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2024-01-15
"""

import os
import threading
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

import faiss
from filelock import FileLock

from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log


class VectorStore:
    """向量存储类
    
    功能描述：
        使用FAISS实现高性能的向量存储和检索功能，支持：
        1. 向量的存储和索引构建
        2. 基于相似度的向量检索
        3. 向量的批量操作
        4. 索引的持久化管理
        5. 索引的优化和压缩
    
    属性说明：
        - _index: FAISS索引实例
        - _dimension: 向量维度
        - _index_path: 索引文件路径
        - _id_map: ID到索引的映射
        - _backup_path: 备份文件路径
    
    依赖关系：
        - 依赖FAISS进行向量操作
        - 依赖Config获取配置
        - 依赖Logger记录日志
    """
    
    def __init__(
        self,
        dimension: int = 768,
        index_path: str = None,
        use_gpu: bool = False,
        nlist: int = 100,  # IVF聚类中心数
        nprobe: int = 10,  # 搜索时检查的聚类中心数
        compression_level: int = 0  # 压缩级别(0-无压缩,1-PQ,2-SQ)
    ) -> None:
        """初始化向量存储
        
        Args:
            dimension: 向量维度
            index_path: 索引文件路径
            use_gpu: 是否使用GPU
            nlist: IVF聚类中心数
            nprobe: 搜索时检查的聚类中心数
            compression_level: 压缩级别
        """
        self._dimension = dimension
        self._index_path = index_path or config.faiss_index_path
        self._backup_path = self._index_path + ".backup"
        self._id_map: Dict[str, int] = {}
        self._next_id = 0
        
        # 初始化锁
        self._lock = threading.Lock()
        self._file_lock = FileLock(f"{self._index_path}.lock")
        
        # 创建索引
        if use_gpu and faiss.get_num_gpus() > 0:
            # 使用GPU索引
            if compression_level == 0:
                # 不压缩
                quantizer = faiss.IndexFlatL2(dimension)
                self._index = faiss.IndexIVFFlat(
                    quantizer, dimension, nlist
                )
            elif compression_level == 1:
                # PQ压缩
                quantizer = faiss.IndexFlatL2(dimension)
                self._index = faiss.IndexIVFPQ(
                    quantizer, dimension, nlist,
                    8,  # 子向量数
                    8   # 每个子向量的位数
                )
            else:
                # SQ压缩
                quantizer = faiss.IndexFlatL2(dimension)
                self._index = faiss.IndexIVFScalarQuantizer(
                    quantizer, dimension, nlist,
                    faiss.ScalarQuantizer.QT_8bit
                )
            
            self._index = faiss.index_cpu_to_gpu(
                faiss.StandardGpuResources(),
                0,
                self._index
            )
            log.info("使用GPU向量索引")
        else:
            # 使用CPU索引
            if compression_level == 0:
                # 不压缩
                quantizer = faiss.IndexFlatL2(dimension)
                self._index = faiss.IndexIVFFlat(
                    quantizer, dimension, nlist
                )
            elif compression_level == 1:
                # PQ压缩
                quantizer = faiss.IndexFlatL2(dimension)
                self._index = faiss.IndexIVFPQ(
                    quantizer, dimension, nlist,
                    8,  # 子向量数
                    8   # 每个子向量的位数
                )
            else:
                # SQ压缩
                quantizer = faiss.IndexFlatL2(dimension)
                self._index = faiss.IndexIVFScalarQuantizer(
                    quantizer, dimension, nlist,
                    faiss.ScalarQuantizer.QT_8bit
                )
            log.info("使用CPU向量索引")
        
        # 设置搜索参数
        self._index.nprobe = nprobe
        
        # 加载已有索引
        if os.path.exists(self._index_path):
            try:
                self._load_index()
                log.info("加载向量索引成功")
            except Exception as e:
                # 尝试加载备份
                if os.path.exists(self._backup_path):
                    try:
                        self._load_backup()
                        log.info("从备份加载向量索引成功")
                        return
                    except Exception as backup_error:
                        log.error(f"加载备份索引失败: {backup_error}")
                log.error(f"加载向量索引失败: {e}")
                raise
    
    def _load_index(self) -> None:
        """加载索引文件
        
        从文件加载FAISS索引和ID映射。
        """
        try:
            with self._file_lock:
                self._index = faiss.read_index(self._index_path)
                id_map_path = self._index_path + ".map"
                if os.path.exists(id_map_path):
                    self._id_map = np.load(id_map_path, allow_pickle=True).item()
                    self._next_id = max(self._id_map.values()) + 1 if self._id_map else 0
        except Exception as e:
            log.error(f"加载索引失败: {e}")
            raise
    
    def _save_index(self) -> None:
        """保存索引文件
        
        将FAISS索引和ID映射保存到文件。
        """
        try:
            with self._file_lock:
                os.makedirs(os.path.dirname(self._index_path), exist_ok=True)
                faiss.write_index(self._index, self._index_path)
                id_map_path = self._index_path + ".map"
                np.save(id_map_path, self._id_map)
                log.info("保存向量索引成功")
        except Exception as e:
            log.error(f"保存索引失败: {e}")
            raise
    
    def add(
        self,
        id: str,
        vector: Union[np.ndarray, List[float]]
    ) -> bool:
        """添加向量
        
        Args:
            id: 向量ID
            vector: 向量数据
        
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
                # 添加到索引
                self._index.add(vector.reshape(1, -1))
                self._id_map[id] = self._next_id
                self._next_id += 1
                
                # 保存索引
                self._save_index()
                return True
        except Exception as e:
            log.error(f"添加向量失败: {e}")
            return False
    
    def search(
        self,
        vector: Union[np.ndarray, List[float]],
        k: int = 10,
        threshold: float = None
    ) -> List[Tuple[str, float]]:
        """搜索相似向量
        
        Args:
            vector: 查询向量
            k: 返回的最相似向量数量
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
                # 搜索相似向量
                distances, indices = self._index.search(
                    vector.reshape(1, -1),
                    k
                )
                
                # 转换结果
                results = []
                for distance, index in zip(distances[0], indices[0]):
                    if index == -1:
                        continue
                    if threshold and distance > threshold:
                        continue
                    
                    # 查找ID
                    id = next(
                        (k for k, v in self._id_map.items() if v == index),
                        None
                    )
                    if id:
                        results.append((id, float(distance)))
                
                return results
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
                if id not in self._id_map:
                    return False
                
                # 创建新索引
                new_index = faiss.IndexFlatL2(self._dimension)
                new_id_map = {}
                next_id = 0
                
                # 复制除了要删除的向量之外的所有向量
                for curr_id, curr_index in self._id_map.items():
                    if curr_id == id:
                        continue
                    
                    # 获取向量
                    vector = self._index.reconstruct(curr_index)
                    
                    # 添加到新索引
                    new_index.add(vector.reshape(1, -1))
                    new_id_map[curr_id] = next_id
                    next_id += 1
                
                # 更新索引
                self._index = new_index
                self._id_map = new_id_map
                self._next_id = next_id
                
                # 保存索引
                self._save_index()
                return True
        except Exception as e:
            log.error(f"删除向量失败: {e}")
            return False
    
    def update(
        self,
        id: str,
        vector: Union[np.ndarray, List[float]]
    ) -> bool:
        """更新向量
        
        Args:
            id: 向量ID
            vector: 新的向量数据
        
        Returns:
            bool: 是否更新成功
        """
        try:
            # 删除旧向量
            if not self.delete(id):
                return False
            
            # 添加新向量
            return self.add(id, vector)
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
                if id not in self._id_map:
                    return None
                return self._index.reconstruct(self._id_map[id])
        except Exception as e:
            log.error(f"获取向量失败: {e}")
            return None
    
    def clear(self) -> bool:
        """清空索引
        
        Returns:
            bool: 是否清空成功
        """
        try:
            self._index = faiss.IndexFlatL2(self._dimension)
            self._id_map = {}
            self._next_id = 0
            self._save_index()
            return True
        except Exception as e:
            log.error(f"清空索引失败: {e}")
            return False
    
    def __len__(self) -> int:
        """获取向量数量
        
        Returns:
            int: 向量数量
        """
        return len(self._id_map)
    
    def __contains__(self, id: str) -> bool:
        """检查向量是否存在
        
        Args:
            id: 向量ID
        
        Returns:
            bool: 是否存在
        """
        return id in self._id_map
    
    def add_batch(
        self,
        vectors: Union[np.ndarray, List[List[float]]],
        ids: List[str]
    ) -> bool:
        """批量添加向量
        
        Args:
            vectors: 向量数据列表
            ids: 向量ID列表
        
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
                # 添加到索引
                self._index.add(vectors)
                
                # 更新ID映射
                for i, id in enumerate(ids):
                    self._id_map[id] = self._next_id + i
                self._next_id += len(ids)
                
                # 创建备份
                self._create_backup()
                
                # 保存索引
                self._save_index()
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
                # 搜索相似向量
                distances, indices = self._index.search(vectors, k)
                
                # 转换结果
                results = []
                for batch_distances, batch_indices in zip(distances, indices):
                    batch_results = []
                    for distance, index in zip(batch_distances, batch_indices):
                        if index == -1:
                            continue
                        if threshold and distance > threshold:
                            continue
                        
                        # 查找ID
                        id = next(
                            (k for k, v in self._id_map.items() if v == index),
                            None
                        )
                        if id:
                            batch_results.append((id, float(distance)))
                    results.append(batch_results)
                
                return results
        except Exception as e:
            log.error(f"批量搜索向量失败: {e}")
            return []
    
    def optimize(
        self,
        n_iterations: int = 10,
        min_points_per_centroid: int = 39
    ) -> bool:
        """优化索引
        
        Args:
            n_iterations: 训练迭代次数
            min_points_per_centroid: 每个聚类中心的最小点数
        
        Returns:
            bool: 是否优化成功
        """
        try:
            with self._lock:
                # 获取所有向量
                vectors = []
                for id, index in self._id_map.items():
                    vector = self._index.reconstruct(index)
                    vectors.append(vector)
                vectors = np.array(vectors).astype('float32')
                
                if len(vectors) < min_points_per_centroid:
                    log.warning("向量数量太少,跳过优化")
                    return True
                
                # 训练索引
                self._index.train(vectors)
                
                # 重新添加向量
                self._index.reset()
                self._index.add(vectors)
                
                # 创建备份
                self._create_backup()
                
                # 保存索引
                self._save_index()
                return True
        except Exception as e:
            log.error(f"优化索引失败: {e}")
            return False
    
    def _create_backup(self) -> None:
        """创建索引备份"""
        try:
            with self._file_lock:
                faiss.write_index(self._index, self._backup_path)
                id_map_path = self._backup_path + ".map"
                np.save(id_map_path, self._id_map)
                log.info("创建向量索引备份成功")
        except Exception as e:
            log.error(f"创建索引备份失败: {e}")
            raise
    
    def _load_backup(self) -> None:
        """加载索引备份"""
        try:
            with self._file_lock:
                self._index = faiss.read_index(self._backup_path)
                id_map_path = self._backup_path + ".map"
                if os.path.exists(id_map_path):
                    self._id_map = np.load(id_map_path, allow_pickle=True).item()
                    self._next_id = max(self._id_map.values()) + 1 if self._id_map else 0
        except Exception as e:
            log.error(f"加载索引备份失败: {e}")
            raise
