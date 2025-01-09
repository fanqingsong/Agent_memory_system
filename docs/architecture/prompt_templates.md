# Prompt模板设计

## 1. 基础模板结构

### 1.1 系统提示模板

```python
# 系统提示配置
class SystemPromptConfig:
    # 基础设置
    role_definition: str      # 角色定义
    behavior_rules: List[str] # 行为规则
    constraints: List[str]    # 约束条件
    
    # 记忆集成
    memory_usage: Dict = {
        "use_regular_memory": True,
        "use_skill_memory": True,
        "memory_threshold": 0.7
    }
    
    # 输出控制
    output_format: Dict = {
        "structure": "json",
        "language": "chinese",
        "style": "concise"
    }
```

### 1.2 对话模板

```python
# 对话上下文
class ConversationContext:
    # 基本信息
    conversation_id: str     # 对话ID
    user_id: str            # 用户ID
    start_time: datetime    # 开始时间
    
    # 上下文控制
    max_turns: int          # 最大轮次
    max_tokens: int         # 最大token数
    memory_window: int      # 记忆窗口
    
    # 状态信息
    current_topic: str      # 当前话题
    active_memories: List[str] # 活跃记忆
```

## 2. 记忆集成模板

### 2.1 常规记忆模板

```python
# 常规记忆提示
class RegularMemoryPrompt:
    # 记忆检索
    retrieval_prompt: str = """
    基于以下上下文和记忆信息：
    上下文：{context}
    相关记忆：
    {memories}
    
    请回答问题：{question}
    """
    
    # 记忆更新
    update_prompt: str = """
    基于新的信息：
    {new_information}
    
    请更新以下记忆：
    {existing_memory}
    
    更新要求：
    1. 保持信息的连贯性
    2. 合并重复内容
    3. 突出重要变化
    """
```

### 2.2 技能记忆模板

```python
# 技能记忆提示
class SkillMemoryPrompt:
    # 技能提取
    extraction_prompt: str = """
    基于以下任务执行记录：
    {task_record}
    
    请提取关键技能模式：
    1. 识别核心步骤
    2. 总结关键决策
    3. 提取可复用模式
    """
    
    # 技能应用
    application_prompt: str = """
    对于当前任务：
    {current_task}
    
    基于以下相关技能：
    {relevant_skills}
    
    请制定执行计划：
    1. 选择适用技能
    2. 调整执行参数
    3. 设计执行步骤
    """
```

## 3. 特定场景模板

### 3.1 任务分析模板

```python
# 任务分析提示
class TaskAnalysisPrompt:
    # 任务分解
    decomposition_prompt: str = """
    对于任务：{task}
    
    请进行以下分析：
    1. 任务目标：
       [请详细描述任务的预期结果]
    
    2. 子任务分解：
       [将任务分解为可执行的子任务]
    
    3. 依赖关系：
       [识别子任务间的依赖关系]
    
    4. 资源需求：
       [列出完成任务所需的资源]
    """
    
    # 技能匹配
    skill_matching_prompt: str = """
    基于任务分析：
    {task_analysis}
    
    请匹配所需技能：
    1. 核心技能：
       [列出必需的核心技能]
    
    2. 辅助技能：
       [列出有助于提升效果的技能]
    
    3. 技能组合：
       [说明技能的组合方式]
    """
```

### 3.2 问题解决模板

```python
# 问题解决提示
class ProblemSolvingPrompt:
    # 问题分析
    analysis_prompt: str = """
    关于问题：{problem}
    
    请进行系统分析：
    1. 问题本质：
       [深入分析问题的核心]
    
    2. 影响因素：
       [识别关键影响因素]
    
    3. 可能解决方案：
       [提出潜在的解决方案]
    
    4. 方案评估：
       [评估各方案的可行性]
    """
    
    # 方案执行
    execution_prompt: str = """
    基于分析结果：
    {analysis_result}
    
    执行解决方案：
    1. 执行步骤：
       [详细的执行步骤]
    
    2. 注意事项：
       [执行过程中的关键点]
    
    3. 效果评估：
       [评估执行效果的标准]
    """
```

## 4. 输出格式模板

### 4.1 结构化输出

```python
# 输出格式定义
class OutputFormat:
    # JSON格式
    json_format: Dict = {
        "status": str,      # 执行状态
        "result": Any,      # 执行结果
        "reasoning": str,   # 推理过程
        "confidence": float # 置信度
    }
    
    # 表格格式
    table_format: Dict = {
        "headers": List[str],  # 表头
        "rows": List[List],    # 数据行
        "summary": str         # 摘要
    }
```

### 4.2 交互式输出

```python
# 交互提示
class InteractivePrompt:
    # 澄清提示
    clarification_prompt: str = """
    我理解的是：
    {understanding}
    
    请确认以下内容：
    1. {clarification_point_1}
    2. {clarification_point_2}
    
    是否需要调整？
    """
    
    # 反馈提示
    feedback_prompt: str = """
    执行结果：
    {result}
    
    请提供反馈：
    1. 结果是否符合预期？
    2. 需要哪些改进？
    3. 有无其他建议？
    """
```

## 5. 提示优化

### 5.1 提示增强

```python
# 提示增强配置
class PromptEnhancement:
    # 上下文增强
    context_enhancement: Dict = {
        "add_examples": bool,    # 添加示例
        "add_constraints": bool, # 添加约束
        "add_references": bool   # 添加参考
    }
    
    # 指令增强
    instruction_enhancement: Dict = {
        "add_steps": bool,       # 添加步骤
        "add_criteria": bool,    # 添加标准
        "add_validation": bool   # 添加验证
    }
```

### 5.2 提示评估

```python
# 提示评估指标
class PromptEvaluation:
    # 质量指标
    quality_metrics: Dict = {
        "clarity": float,       # 清晰度
        "completeness": float,  # 完整度
        "consistency": float    # 一致性
    }
    
    # 效果指标
    effectiveness_metrics: Dict = {
        "response_quality": float,  # 响应质量
        "task_completion": float,   # 任务完成度
        "resource_efficiency": float # 资源效率
    }
``` 