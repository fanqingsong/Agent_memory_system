"""测试环境配置模块

提供测试环境的配置和管理功能。

主要功能：
    - 测试环境配置
    - 数据库配置
    - 存储配置
    - 环境标记

依赖：
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2024-01-15
"""

import os
import time
import uuid
from datetime import datetime
from typing import Dict, Optional

from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log


class TestEnvironment:
    """测试环境类
    
    功能描述：
        提供测试环境的配置和管理功能，包括：
        1. 数据库配置管理
        2. 存储配置管理
        3. 环境标记管理
        4. 测试ID生成
    
    属性说明：
        - db_config: 数据库配置
        - storage_config: 存储配置
        - environment_markers: 环境标记
    """
    
    def __init__(self) -> None:
        """初始化测试环境"""
        # 数据库配置
        self.db_config = {
            'test_db_prefix': 'test_',  # 测试数据库前缀
            'test_collection_prefix': 'test_',  # 测试集合前缀
            'isolation_level': 'READ COMMITTED'  # 事务隔离级别
        }
        
        # 存储配置
        self.storage_config = {
            'faiss_index_prefix': 'test_',  # FAISS索引前缀
            'neo4j_database': 'test_memory',  # Neo4j测试数据库
            'redis_prefix': 'test:'  # Redis键前缀
        }
        
        # 环境标记
        self.environment_markers = {
            'is_test': True,
            'test_id': '',  # 每次测试运行的唯一标识
            'timestamp': ''  # 测试开始时间
        }
    
    def init_test_environment(self) -> str:
        """初始化测试环境
        
        Returns:
            str: 测试ID
        """
        try:
            # 生成测试ID
            test_id = self.generate_test_id()
            
            # 更新环境标记
            self.environment_markers['test_id'] = test_id
            self.environment_markers['timestamp'] = datetime.utcnow().isoformat()
            
            # 配置数据库
            self.configure_database(test_id)
            
            # 配置存储
            self.configure_storage(test_id)
            
            log.info(f'测试环境初始化完成: {test_id}')
            return test_id
        except Exception as e:
            log.error(f'测试环境初始化失败: {e}')
            raise
    
    def generate_test_id(self) -> str:
        """生成测试ID
        
        Returns:
            str: 测试ID
        """
        timestamp = int(time.time())
        random_id = uuid.uuid4().hex[:8]
        return f'test_{timestamp}_{random_id}'
    
    def configure_database(self, test_id: str) -> None:
        """配置数据库
        
        Args:
            test_id: 测试ID
        """
        # 更新数据库配置
        config.database_config.update({
            'database': f"{self.db_config['test_db_prefix']}{test_id}",
            'collection_prefix': self.db_config['test_collection_prefix'],
            'isolation_level': self.db_config['isolation_level']
        })
    
    def configure_storage(self, test_id: str) -> None:
        """配置存储
        
        Args:
            test_id: 测试ID
        """
        # 更新存储配置
        config.storage_config.update({
            'faiss_index_path': os.path.join(
                'data',
                'test',
                f"{self.storage_config['faiss_index_prefix']}{test_id}"
            ),
            'neo4j_database': self.storage_config['neo4j_database'],
            'redis_prefix': f"{self.storage_config['redis_prefix']}{test_id}:"
        })
    
    def get_test_id(self) -> Optional[str]:
        """获取当前测试ID
        
        Returns:
            str: 测试ID，如果不在测试环境中则返回None
        """
        return self.environment_markers.get('test_id')
    
    def is_test_environment(self) -> bool:
        """检查是否在测试环境中
        
        Returns:
            bool: 是否在测试环境中
        """
        return self.environment_markers.get('is_test', False)
    
    def get_environment_info(self) -> Dict:
        """获取环境信息
        
        Returns:
            Dict: 环境信息
        """
        return {
            'db_config': self.db_config,
            'storage_config': self.storage_config,
            'environment_markers': self.environment_markers
        }
    
    def cleanup_environment(self) -> None:
        """清理测试环境"""
        try:
            # 重置环境标记
            self.environment_markers['test_id'] = ''
            self.environment_markers['timestamp'] = ''
            
            # 重置配置
            config.reset()
            
            log.info('测试环境清理完成')
        except Exception as e:
            log.error(f'测试环境清理失败: {e}')
            raise 