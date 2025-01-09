[本文档为开发规范，请严格遵守；在进行修改时，请向我申请权限。未获得修改确认时，严禁进行修改。]

作者：Cursor_for_YansongW

# Agent记忆系统开发规范

## 1. 代码风格规范

### 1.1 基本要求
- 使用Python 3.8+
- 严格遵循PEP 8编码规范
- 使用black进行代码格式化
- 使用pylint进行代码质量检查
- 使用isort进行import语句排序

### 1.2 格式化规则
- 每行最大字符数：88个字符
- 缩进：4个空格（禁止使用tab）
- 函数/类定义之间空2行
- 类中方法定义之间空1行
- 运算符前后必须有空格
- 逗号后必须有空格
- 括号内紧贴括号不需要空格
- 行尾不允许有空格
- 文件末尾必须有一个空行

### 1.3 Import规范
- 按以下顺序分组，组间空1行：
  1. 标准库导入
  2. 第三方库导入
  3. 本地模块导入
- 每组内按字母顺序排序
- 禁止使用通配符导入（from xxx import *）
- 禁止使用相对导入（from ..xxx import yyy）
```python
# 正确示例
import os
import sys

import numpy as np
import torch
from transformers import AutoModel

from memory_system.core import MemoryManager
from memory_system.utils import helpers
```

### 1.4 命名规范
- 类名：使用大驼峰命名法（如：MemoryManager）
- 函数名/变量名：使用小写字母和下划线（如：get_memory）
- 常量：使用大写字母和下划线（如：MAX_MEMORY_SIZE）
- 私有成员：使用单下划线前缀（如：_internal_cache）

### 1.5 代码复杂度限制
- 单个函数不超过50行（不含注释和空行）
- 单个类不超过500行
- 单个文件不超过1000行
- 圈复杂度不超过10
- 继承深度不超过3层
- 单个函数参数不超过5个
- 嵌套层级不超过3层

## 2. 文档规范

### 2.1 Docstring要求
- 所有模块、类、函数必须包含docstring
- 使用Google风格的docstring格式
- 必须包含参数说明、返回值说明和异常说明
```python
def add_memory(content: str, importance: int) -> MemoryId:
    """添加新的记忆条目。

    Args:
        content (str): 记忆内容
        importance (int): 重要性评分(1-10)

    Returns:
        MemoryId: 新创建的记忆ID

    Raises:
        ValueError: 当importance不在1-10范围内时
        StorageError: 当存储操作失败时
    """
    pass
```

### 2.2 注释规范

#### 2.2.1 总体要求
- 注释必须详尽完整，确保对代码的每个方面都有清晰的说明
- 注释必须及时更新，与代码保持同步
- 使用中文进行注释，保持语言的一致性
- 注释应该是自解释的，不应该依赖其他部分的注释

#### 2.2.2 模块级注释
必须在每个模块文件开头包含以下内容：
```python
"""
模块名称：Memory Manager
模块功能：负责管理系统的记忆存储和检索功能
核心类：
    - MemoryManager: 记忆管理器
    - MemoryStorage: 存储管理器
核心函数：
    - store_memory(): 存储记忆
    - retrieve_memory(): 检索记忆
依赖库：
    - numpy: 用于向量计算
    - pandas: 用于数据处理
    - torch: 用于模型推理
数据流：
    1. 输入数据 -> 预处理
    2. 预处理 -> 向量化
    3. 向量化 -> 存储/检索
作者：Cursor_for_YansongW
创建日期：YYYY-MM-DD
修改日期：YYYY-MM-DD
"""
```

#### 2.2.3 类级注释
每个类定义必须包含以下注释内容：
```python
class MemoryManager:
    """记忆管理器类
    
    功能描述：
        负责管理系统中所有的记忆操作，包括存储、检索、更新和删除
    
    属性说明：
        - storage: MemoryStorage类实例，负责底层存储
        - encoder: TextEncoder类实例，负责文本编码
        - cache: Dict，用于缓存常用记忆
    
    依赖关系：
        - 依赖MemoryStorage类进行存储操作
        - 依赖TextEncoder类进行文本编码
        - 依赖ConfigManager类获取配置
    
    主要方法：
        - store(): 存储新记忆
        - retrieve(): 检索相关记忆
        - update(): 更新已有记忆
        - delete(): 删除指定记忆
    
    使用示例：
        manager = MemoryManager()
        manager.store("这是一条新记忆")
    """
```

#### 2.2.4 函数级注释
每个函数必须包含以下注释内容：
```python
def store_memory(
    content: str,
    importance: int,
    memory_type: str,
    metadata: dict = None
) -> str:
    """存储新的记忆内容
    
    功能描述：
        将新的记忆内容存储到系统中，并返回唯一标识符
    
    实现逻辑：
        1. 生成唯一标识符
        2. 对内容进行向量化编码
        3. 计算记忆重要性分数
        4. 存储到对应的记忆类型中
    
    参数说明：
        content (str): 记忆内容
            - 支持纯文本格式
            - 长度不超过1000字符
            - 不允许包含特殊字符
        importance (int): 重要性评分
            - 范围：1-10
            - 7分以上自动进入长期记忆
        memory_type (str): 记忆类型
            - 可选值：'short_term', 'long_term', 'working'
        metadata (dict, optional): 额外元数据
            - 可包含标签、时间戳等信息
    
    返回值：
        str: 新创建的记忆ID
            - 格式：'MEM-{timestamp}-{random_string}'
            - 长度：32字符
    
    异常说明：
        - ValueError: 当参数不符合要求时抛出
        - StorageError: 当存储操作失败时抛出
    
    依赖说明：
        - 依赖generate_id()生成唯一ID
        - 依赖text_to_vector()进行向量化
        - 依赖storage.save()进行存储
    
    性能说明：
        - 平均响应时间：100ms
        - 内存消耗：约50MB
    
    使用示例：
        try:
            memory_id = store_memory(
                content="这是一条测试记忆",
                importance=8,
                memory_type="long_term"
            )
        except ValueError as e:
            print(f"参数错误：{e}")
    """
```

#### 2.2.5 代码块注释
对于复杂的代码块，必须添加以下注释：
```python
# 1. 数据预处理
## 1.1 清理特殊字符
special_chars = re.compile(r'[^\w\s]')
cleaned_text = special_chars.sub('', text)

## 1.2 分词处理
# 使用jieba分词器进行分词
# 参数说明：cut_all=False表示精确模式
tokens = jieba.cut(cleaned_text, cut_all=False)

# 2. 向量化处理
## 2.1 加载预训练模型
# 使用sentence-transformers模型
# 模型来源：https://huggingface.co/model
model = SentenceTransformer('model_name')

## 2.2 生成向量
# 将文本转换为768维向量
# 使用mean pooling策略
vector = model.encode(tokens)
```

#### 2.2.6 变量和常量注释
重要的变量和常量必须包含详细注释：
```python
# 系统配置常量
MAX_MEMORY_SIZE = 1000  # 最大记忆条数，超过此数量将触发清理
MEMORY_TIMEOUT = 7 * 24 * 3600  # 记忆超时时间（秒），默认7天
IMPORTANCE_THRESHOLD = 7  # 重要性阈值，高于此值将进入长期记忆

# 向量相关参数
vector_dimension = 768  # 向量维度，与预训练模型对应
similarity_threshold = 0.85  # 相似度阈值，高于此值认为相关
max_return_count = 100  # 最大返回结果数量

# 数据结构定义
memory_cache = {
    'short_term': [],  # 短期记忆列表，使用数组实现
    'long_term': {},   # 长期记忆字典，键为记忆ID
    'working': set()   # 工作记忆集合，使用集合去重
}
```

#### 2.2.7 数据结构注释
对于复杂的数据结构，必须添加结构说明：
```python
# 记忆数据结构
memory_item = {
    # 基础信息
    'id': 'MEM-20231201-abc123',  # 记忆唯一标识符
    'content': '记忆内容',        # 原始文本内容
    'vector': np.array([...]),    # 向量化后的表示
    
    # 元数据
    'metadata': {
        'timestamp': 1701401234,  # 创建时间戳
        'type': 'long_term',      # 记忆类型
        'importance': 8,          # 重要性评分
        'access_count': 0,        # 访问计数
        'last_access': None,      # 最后访问时间
    },
    
    # 关联信息
    'relations': {
        'parents': [],    # 父记忆ID列表
        'children': [],   # 子记忆ID列表
        'siblings': [],   # 相关记忆ID列表
    }
}
```

### 2.3 项目文档规范
#### 2.3.1 README.md要求
- 必须包含以下部分：
  - 项目简介
  - 功能特性
  - 系统要求
  - 安装说明
  - 使用示例
  - 配置说明
  - API文档链接
  - 贡献指南
  - 开源协议

#### 2.3.2 版本号规范
- 采用语义化版本号：主版本号.次版本号.修订号
- 主版本号：不兼容的API修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

#### 2.3.3 API文档生成
- 使用Sphinx生成API文档
- 文档必须包含：
  - 模块说明
  - 类/函数签名
  - 参数说明
  - 返回值说明
  - 异常说明
  - 使用示例

## 3. 测试规范

### 3.1 单元测试要求
- 使用pytest框架
- 测试文件命名为test_*.py
- 每个模块的测试覆盖率不低于85%
- 必须包含正向测试和异常测试
```python
def test_add_memory_success():
    """测试正常添加记忆的情况"""
    pass

def test_add_memory_invalid_importance():
    """测试添加记忆时重要性评分无效的情况"""
    pass
```

### 3.3 测试用例编写规范
- 每个测试用例必须测试单一功能
- 测试用例命名必须清晰表达测试目的
- 必须包含以下类型的测试：
  - 正常流程测试
  - 边界条件测试
  - 异常情况测试
  - 性能测试
```python
def test_store_memory_normal_flow():
    """测试记忆存储的正常流程"""
    pass

def test_store_memory_max_length():
    """测试存储最大长度的记忆"""
    pass

def test_store_memory_invalid_input():
    """测试无效输入的处理"""
    pass

def test_store_memory_performance():
    """测试存储性能是否满足要求"""
    pass
```

### 3.4 性能测试规范
- 必须测试以下指标：
  - 响应时间
  - 内存使用
  - CPU使用率
  - 并发处理能力
- 性能测试场景必须包含：
  - 普通负载测试
  - 压力测试
  - 持久性测试
  - 并发测试

### 3.5 测试环境规范
- 必须维护以下环境：
  - 开发环境
  - 测试环境
  - 预发布环境
  - 生产环境
- 环境配置必须使用配置文件管理
- 测试数据必须使用专门的测试数据集

## 7. 错误处理规范

### 7.1 异常定义
- 必须定义业务相关的异常类
- 异常类必须继承自适当的基类
- 异常命名必须以Error结尾
```python
class MemoryError(Exception):
    """记忆系统基础异常类"""
    pass

class StorageError(MemoryError):
    """存储相关异常"""
    pass

class RetrievalError(MemoryError):
    """检索相关异常"""
    pass
```

### 7.2 异常处理原则
- 只处理可以恢复的异常
- 在适当的层级处理异常
- 禁止捕获后不处理
- 必须记录异常日志
- 向上层抛出时必须保留原始异常信息
```python
try:
    result = memory_store.save(data)
except StorageError as e:
    logger.error(f"存储失败: {e}")
    raise MemoryError("记忆存储失败") from e
```

## 8. 日志规范

### 8.1 日志级别使用
- ERROR：影响系统正常运行的错误
- WARNING：潜在的问题警告
- INFO：重要的业务逻辑信息
- DEBUG：调试相关的信息
- TRACE：最详细的追踪信息

### 8.2 日志格式
- 时间戳：精确到毫秒
- 日志级别
- 进程/线程ID
- 模块名称
- 函数名称
- 行号
- 具体消息
```python
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(process)d:%(thread)d '
           '%(module)s.%(funcName)s:%(lineno)d - %(message)s',
    level=logging.INFO
)
```

### 8.3 日志内容要求
- 必须包含关键参数值
- 必须包含操作结果
- 必须包含错误原因
- 避免记录敏感信息
```python
logger.info(f"开始存储记忆，类型={memory_type}, 重要性={importance}")
logger.error(f"记忆存储失败，ID={memory_id}, 原因={error_msg}")
```

## 9. 安全规范

### 9.1 数据安全
- 敏感数据必须加密存储
- 传输数据必须使用HTTPS
- 密码必须加盐哈希
- 定期备份重要数据
- 实现数据访问控制

### 9.2 代码安全
- 禁止硬编码敏感信息
- 使用参数化查询防止注入
- 实现输入验证和清洗
- 限制资源使用
- 实现超时机制

### 9.3 运行安全
- 实现访问控制和认证
- 记录安全审计日志
- 实现并发控制
- 防止拒绝服务攻击
- 定期安全扫描

## 10. 性能规范

### 10.1 代码性能
- 优化循环结构
- 避免重复计算
- 使用适当的数据结构
- 实现缓存机制
- 避免内存泄漏

### 10.2 响应时间要求
- API响应时间 < 200ms
- 批量操作 < 2s
- 后台任务 < 5min
- 定时任务不影响正常服务

### 10.3 资源使用限制
- CPU使用率 < 70%
- 内存使用率 < 80%
- 磁盘使用率 < 85%
- 单个请求内存 < 500MB

## 11. 代码审查规范

### 11.1 审查重点
- 代码规范遵守情况
- 业务逻辑正确性
- 性能问题
- 安全隐患
- 测试覆盖率

### 11.2 审查清单
- 代码是否符合规范
- 注释是否完整清晰
- 是否有潜在bug
- 是否有重复代码
- 是否有性能问题
- 是否有安全隐患
- 测试是否充分

### 11.3 审查流程
1. 提交代码审查申请
2. 审查人员分配
3. 代码审查
4. 反馈修改
5. 再次审查
6. 审查通过

## 12. 发布规范

### 12.1 发布流程
1. 代码审查通过
2. 更新版本号
3. 更新更新日志
4. 打包构建
5. 测试验证
6. 预发布验证
7. 正式发布
8. 发布确认

### 12.2 发布物要求
- 源代码包
- 构建产物
- 部署文档
- 更新日志
- 回滚方案

### 12.3 发布注意事项
- 避免在业务高峰期发布
- 准备回滚方案
- 灰度发布
- 监控系统状态
- 及时通知相关人员 