"""图存储模块

使用Neo4j实现高性能的图数据库存储和查询。

主要功能：
    - 节点的增删改查
    - 关系的增删改查
    - 图遍历和路径查询
    - 图算法支持

依赖：
    - neo4j: Neo4j Python驱动
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2024-01-15
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Union

from neo4j import GraphDatabase, Session
from neo4j.exceptions import Neo4jError

from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log


class GraphStore:
    """图存储类
    
    功能描述：
        使用Neo4j实现高性能的图数据库存储和查询功能，支持：
        1. 节点的增删改查操作
        2. 关系的增删改查操作
        3. 图的遍历和路径查询
        4. 常用图算法的支持
    
    属性说明：
        - _driver: Neo4j驱动实例
        - _database: 数据库名称
    
    依赖关系：
        - 依赖Neo4j进行图操作
        - 依赖Config获取配置
        - 依赖Logger记录日志
    """
    
    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None,
        database: str = "neo4j"
    ) -> None:
        """初始化图存储
        
        Args:
            uri: Neo4j连接URI
            user: 用户名
            password: 密码
            database: 数据库名称
        """
        self._uri = uri or config.neo4j.uri
        self._user = user or config.neo4j.user
        self._password = password or config.neo4j.password
        self._database = database
        
        # 连接数据库
        try:
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password)
            )
            # 测试连接
            with self._driver.session(database=self._database) as session:
                session.run("RETURN 1")
            log.info("图存储初始化完成")
        except Neo4jError as e:
            log.error(f"连接Neo4j失败: {e}")
            raise
    
    def add_node(
        self,
        labels: Union[str, List[str]],
        properties: Dict
    ) -> Optional[str]:
        """添加节点
        
        Args:
            labels: 节点标签
            properties: 节点属性
        
        Returns:
            str: 节点ID，如果失败则返回None
        """
        # 转换标签格式
        if isinstance(labels, str):
            labels = [labels]
        labels_str = ":".join(labels)
        
        # 构建查询
        query = (
            f"CREATE (n:{labels_str} $properties) "
            "RETURN id(n) as node_id"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(query, properties=properties)
                record = result.single()
                if record:
                    return str(record["node_id"])
                return None
        except Neo4jError as e:
            log.error(f"添加节点失败: {e}")
            return None
    
    def get_node(
        self,
        node_id: str
    ) -> Optional[Dict]:
        """获取节点
        
        Args:
            node_id: 节点ID
        
        Returns:
            Dict: 节点数据，包含labels和properties
        """
        query = (
            "MATCH (n) "
            "WHERE id(n) = $node_id "
            "RETURN labels(n) as labels, properties(n) as properties"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(query, node_id=int(node_id))
                record = result.single()
                if record:
                    return {
                        "labels": record["labels"],
                        "properties": record["properties"]
                    }
                return None
        except Neo4jError as e:
            log.error(f"获取节点失败: {e}")
            return None
    
    def get_node_by_property(
        self,
        property_name: str,
        property_value: str
    ) -> Optional[Dict]:
        """通过属性获取节点
        
        Args:
            property_name: 属性名
            property_value: 属性值
        
        Returns:
            Dict: 节点数据，包含labels和properties
        """
        query = (
            f"MATCH (n) "
            f"WHERE n.{property_name} = $property_value "
            "RETURN labels(n) as labels, properties(n) as properties"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(query, property_value=property_value)
                record = result.single()
                if record:
                    return {
                        "labels": record["labels"],
                        "properties": record["properties"]
                    }
                return None
        except Neo4jError as e:
            log.error(f"通过属性获取节点失败: {e}")
            return None
    
    def update_node(
        self,
        node_id: str,
        properties: Dict
    ) -> bool:
        """更新节点
        
        Args:
            node_id: 节点ID
            properties: 新的属性
        
        Returns:
            bool: 是否更新成功
        """
        query = (
            "MATCH (n) "
            "WHERE id(n) = $node_id "
            "SET n = $properties "
            "RETURN n"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(
                    query,
                    node_id=int(node_id),
                    properties=properties
                )
                return result.single() is not None
        except Neo4jError as e:
            log.error(f"更新节点失败: {e}")
            return False
    
    def update_node_by_property(
        self,
        property_name: str,
        property_value: str,
        properties: Dict
    ) -> bool:
        """通过属性更新节点
        
        Args:
            property_name: 查找属性名
            property_value: 查找属性值
            properties: 新的属性
        
        Returns:
            bool: 是否更新成功
        """
        query = (
            f"MATCH (n) "
            f"WHERE n.{property_name} = $property_value "
            "SET n += $properties "
            "RETURN n"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(
                    query,
                    property_value=property_value,
                    properties=properties
                )
                return result.single() is not None
        except Neo4jError as e:
            log.error(f"通过属性更新节点失败: {e}")
            return False
    
    def delete_node(self, node_id: str) -> bool:
        """删除节点
        
        Args:
            node_id: 节点ID
        
        Returns:
            bool: 是否删除成功
        """
        query = (
            "MATCH (n) "
            "WHERE id(n) = $node_id "
            "DETACH DELETE n"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                session.run(query, node_id=int(node_id))
                return True
        except Neo4jError as e:
            log.error(f"删除节点失败: {e}")
            return False
    
    def delete_node_by_property(
        self,
        property_name: str,
        property_value: str
    ) -> bool:
        """通过属性删除节点
        
        Args:
            property_name: 查找属性名
            property_value: 查找属性值
        
        Returns:
            bool: 是否删除成功
        """
        query = (
            f"MATCH (n) "
            f"WHERE n.{property_name} = $property_value "
            "DETACH DELETE n"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                session.run(query, property_value=property_value)
                return True
        except Neo4jError as e:
            log.error(f"通过属性删除节点失败: {e}")
            return False
    
    def add_relationship(
        self,
        start_node_id: str,
        end_node_id: str,
        type: str,
        properties: Dict = None
    ) -> Optional[str]:
        """添加关系
        
        Args:
            start_node_id: 起始节点ID
            end_node_id: 结束节点ID
            type: 关系类型
            properties: 关系属性
        
        Returns:
            str: 关系ID，如果失败则返回None
        """
        query = (
            "MATCH (a), (b) "
            "WHERE id(a) = $start_id AND id(b) = $end_id "
            f"CREATE (a)-[r:{type} $properties]->(b) "
            "RETURN id(r) as rel_id"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(
                    query,
                    start_id=int(start_node_id),
                    end_id=int(end_node_id),
                    properties=properties or {}
                )
                record = result.single()
                if record:
                    return str(record["rel_id"])
                return None
        except Neo4jError as e:
            log.error(f"添加关系失败: {e}")
            return None
    
    def get_relationship(
        self,
        relationship_id: str
    ) -> Optional[Dict]:
        """获取关系
        
        Args:
            relationship_id: 关系ID
        
        Returns:
            Dict: 关系数据，包含type和properties
        """
        query = (
            "MATCH ()-[r]->() "
            "WHERE id(r) = $rel_id "
            "RETURN type(r) as type, properties(r) as properties"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(query, rel_id=int(relationship_id))
                record = result.single()
                if record:
                    return {
                        "type": record["type"],
                        "properties": record["properties"]
                    }
                return None
        except Neo4jError as e:
            log.error(f"获取关系失败: {e}")
            return None
    
    def update_relationship(
        self,
        relationship_id: str,
        properties: Dict
    ) -> bool:
        """更新关系
        
        Args:
            relationship_id: 关系ID
            properties: 新的属性
        
        Returns:
            bool: 是否更新成功
        """
        query = (
            "MATCH ()-[r]->() "
            "WHERE id(r) = $rel_id "
            "SET r = $properties "
            "RETURN r"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(
                    query,
                    rel_id=int(relationship_id),
                    properties=properties
                )
                return result.single() is not None
        except Neo4jError as e:
            log.error(f"更新关系失败: {e}")
            return False
    
    def delete_relationship(
        self,
        relationship_id: str
    ) -> bool:
        """删除关系
        
        Args:
            relationship_id: 关系ID
        
        Returns:
            bool: 是否删除成功
        """
        query = (
            "MATCH ()-[r]->() "
            "WHERE id(r) = $rel_id "
            "DELETE r"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                session.run(query, rel_id=int(relationship_id))
                return True
        except Neo4jError as e:
            log.error(f"删除关系失败: {e}")
            return False
    
    def get_neighbors(
        self,
        node_id: str,
        direction: str = "both",
        relationship_type: str = None,
        limit: int = None
    ) -> List[Dict]:
        """获取邻居节点
        
        Args:
            node_id: 节点ID
            direction: 方向("in"/"out"/"both")
            relationship_type: 关系类型
            limit: 返回数量限制
        
        Returns:
            List[Dict]: 邻居节点列表
        """
        # 构建方向
        if direction == "in":
            pattern = "<-[r]-"
        elif direction == "out":
            pattern = "-[r]->"
        else:
            pattern = "-[r]-"
        
        # 构建关系类型
        if relationship_type:
            pattern = pattern.replace("r", f"r:{relationship_type}")
        
        # 构建查询
        query = (
            f"MATCH (a){pattern}(b) "
            "WHERE id(a) = $node_id "
            "RETURN DISTINCT id(b) as node_id, "
            "labels(b) as labels, "
            "properties(b) as properties"
        )
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(query, node_id=int(node_id))
                return [
                    {
                        "id": str(record["node_id"]),
                        "labels": record["labels"],
                        "properties": record["properties"]
                    }
                    for record in result
                ]
        except Neo4jError as e:
            log.error(f"获取邻居节点失败: {e}")
            return []
    
    def find_path(
        self,
        start_node_id: str,
        end_node_id: str,
        relationship_type: str = None,
        max_depth: int = 10
    ) -> Optional[List[Dict]]:
        """查找路径
        
        Args:
            start_node_id: 起始节点ID
            end_node_id: 结束节点ID
            relationship_type: 关系类型
            max_depth: 最大深度
        
        Returns:
            List[Dict]: 路径上的节点列表，如果不存在则返回None
        """
        # 构建关系类型
        rel_pattern = "*1.." + str(max_depth)
        if relationship_type:
            rel_pattern = f"[*1..{max_depth}]"
        
        query = (
            "MATCH p = shortestPath("
            "(a)-[" + rel_pattern + "]->(b)"
            ") "
            "WHERE id(a) = $start_id AND id(b) = $end_id "
            "RETURN [n IN nodes(p) | "
            "{ "
            "id: id(n), "
            "labels: labels(n), "
            "properties: properties(n)"
            "}] as path"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(
                    query,
                    start_id=int(start_node_id),
                    end_id=int(end_node_id)
                )
                record = result.single()
                if record:
                    return record["path"]
                return None
        except Neo4jError as e:
            log.error(f"查找路径失败: {e}")
            return None
    
    def clear(self) -> bool:
        """清空数据库
        
        Returns:
            bool: 是否清空成功
        """
        query = "MATCH (n) DETACH DELETE n"
        
        try:
            with self._driver.session(database=self._database) as session:
                session.run(query)
                return True
        except Neo4jError as e:
            log.error(f"清空数据库失败: {e}")
            return False
    
    def close(self) -> None:
        """关闭连接"""
        if self._driver:
            self._driver.close()
    
    def __enter__(self) -> "GraphStore":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
    
    def get_related_memories(
        self,
        memory_id: str,
        relation_types: Optional[List[str]] = None,
        depth: int = 1
    ) -> Dict[str, List[Dict]]:
        """获取相关记忆
        
        Args:
            memory_id: 记忆ID
            relation_types: 关系类型过滤
            depth: 关系深度
        
        Returns:
            Dict[str, List[Dict]]: 相关记忆字典，键为记忆ID，值为关系列表
        """
        # 构建关系类型过滤
        relation_filter = ""
        if relation_types:
            relation_filter = f":`{'`|`'.join(relation_types)}`"
        
        # 构建查询
        query = (
            f"MATCH (start:Memory {{id: $memory_id}})-[r{relation_filter}*1..{depth}]-(related:Memory) "
            "RETURN related.id as memory_id, type(r[0]) as relation_type, properties(r[0]) as relation_properties"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(query, memory_id=memory_id)
                related_memories = {}
                for record in result:
                    memory_id = record["memory_id"]
                    if memory_id not in related_memories:
                        related_memories[memory_id] = []
                    
                    related_memories[memory_id].append({
                        "type": record["relation_type"],
                        "properties": record["relation_properties"]
                    })
                return related_memories
        except Neo4jError as e:
            log.error(f"获取相关记忆失败: {e}")
            return {}
    
    def get_memories_by_time(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        memory_type: Optional[str] = None
    ) -> List[Dict]:
        """根据时间范围获取记忆
        
        Args:
            start_time: 起始时间
            end_time: 结束时间
            memory_type: 记忆类型过滤
        
        Returns:
            List[Dict]: 记忆列表
        """
        # 构建查询
        if end_time:
            time_filter = "WHERE m.created_at >= $start_time AND m.created_at <= $end_time"
        else:
            time_filter = "WHERE m.created_at >= $start_time"
        
        if memory_type:
            time_filter += f" AND m.type = '{memory_type}'"
        
        query = (
            f"MATCH (m:Memory) {time_filter} "
            "RETURN properties(m) as properties"
        )
        
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(
                    query,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat() if end_time else None
                )
                memories = []
                for record in result:
                    memories.append(record["properties"])
                return memories
        except Neo4jError as e:
            log.error(f"根据时间获取记忆失败: {e}")
            return []
