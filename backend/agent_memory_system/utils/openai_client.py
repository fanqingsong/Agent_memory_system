"""OpenAI客户端工具

提供OpenAI API的封装。

主要功能：
    - Chat Completion API调用
    - 文本嵌入生成
    - API配置管理
    - 错误处理和重试

依赖：
    - openai: OpenAI Python客户端
    - httpx: HTTP客户端
    - config: 配置管理
    - logger: 日志记录

作者：Cursor_for_YansongW
创建日期：2025-01-09
"""

import os
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta

import openai
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log


class OpenAIClient:
    """OpenAI API客户端类
    
    功能描述：
        提供OpenAI API的统一封装，支持：
        1. Chat Completion API调用
        2. 文本嵌入生成
        3. API配置管理
        4. 错误处理和重试机制
    
    属性说明：
        - api_key: OpenAI API密钥
        - api_base_url: API基础URL
        - model: 使用的模型名称
        - embedding_model: 嵌入模型名称
        - temperature: 生成温度
        - max_tokens: 最大生成长度
    """
    
    def __init__(
        self,
        api_key: str = None,
        api_base_url: str = None,
        model: str = "gpt-3.5-turbo",
        embedding_model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> None:
        """初始化OpenAI客户端
        
        Args:
            api_key: OpenAI API密钥
            api_base_url: API基础URL
            model: 使用的模型名称
            embedding_model: 嵌入模型名称
            temperature: 生成温度
            max_tokens: 最大生成长度
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base_url = api_base_url or os.getenv("OPENAI_API_BASE_URL")
        
        if not self.api_key:
            log.warning("未找到OpenAI API密钥")
        
        self.model = model
        self.embedding_model = embedding_model or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 设置OpenAI API密钥和基础URL
        openai.api_key = self.api_key
        if self.api_base_url:
            openai.base_url = self.api_base_url
        
        self.openai_client = openai
        
        # 创建HTTP客户端
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        # 创建同步HTTP客户端
        self.sync_http_client = httpx.Client(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()
    
    @property
    def api_key(self) -> Optional[str]:
        """获取API密钥"""
        return self._api_key
    
    @api_key.setter
    def api_key(self, value: str) -> None:
        """设置API密钥"""
        self._api_key = value
        openai.api_key = value
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def chat_completion(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False
    ) -> str:
        """调用Chat Completion API
        
        Args:
            system_prompt: 系统提示
            user_message: 用户消息
            temperature: 生成温度
            max_tokens: 最大生成长度
            stream: 是否流式输出
        
        Returns:
            str: 生成的回复
            
        Raises:
            Exception: 当API调用失败时
        """
        try:
            log.info(f"开始调用OpenAI Chat API，模型: {self.model}")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = await self.openai_client.ChatCompletion.acreate(
                api_key=self.api_key,
                api_base=self.api_base_url,
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=stream
            )
            
            if stream:
                collected_messages = []
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        collected_messages.append(chunk.choices[0].delta.content)
                result = "".join(collected_messages)
            else:
                result = response.choices[0].message.content
            
            log.info(f"OpenAI Chat API调用成功")
            return result
                
        except Exception as e:
            log.error(f"OpenAI Chat API调用失败: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def create_embedding(
        self,
        text: str
    ) -> List[float]:
        """生成文本嵌入向量
        
        Args:
            text: 输入文本
        
        Returns:
            List[float]: 嵌入向量
            
        Raises:
            Exception: 当API调用失败时
        """
        try:
            log.info(f"开始调用OpenAI embedding API，模型: {self.embedding_model}")
            
            response = await self.openai_client.Embedding.acreate(
                model=self.embedding_model,
                input=text
            )
            
            log.info(f"OpenAI embedding API调用成功")
            return response.data[0].embedding
                
        except Exception as e:
            log.error(f"生成嵌入向量失败: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def create_embedding_sync(
        self,
        text: str
    ) -> List[float]:
        """生成文本嵌入向量（同步版本）
        
        Args:
            text: 输入文本
        
        Returns:
            List[float]: 嵌入向量
            
        Raises:
            Exception: 当API调用失败时
        """
        try:
            log.info(f"开始调用OpenAI embedding API（同步），模型: {self.embedding_model}")
            
            # 使用HTTP客户端直接调用API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.embedding_model,
                "input": text
            }
            
            response = self.sync_http_client.post(
                f"{self.api_base_url}/embeddings",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            log.info(f"OpenAI embedding API调用成功（同步）")
            return result["data"][0]["embedding"]
                
        except Exception as e:
            log.error(f"生成嵌入向量失败: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def create_embeddings_sync(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """批量生成文本嵌入向量（同步版本）
        
        Args:
            texts: 输入文本列表
            batch_size: 批处理大小
        
        Returns:
            List[List[float]]: 嵌入向量列表
            
        Raises:
            Exception: 当API调用失败时
        """
        try:
            embeddings = []
            
            # 分批处理
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # 使用HTTP客户端直接调用API
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": self.embedding_model,
                    "input": batch
                }
                
                response = self.sync_http_client.post(
                    f"{self.api_base_url}/embeddings",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                
                result = response.json()
                batch_embeddings = [data["embedding"] for data in result["data"]]
                
                embeddings.extend(batch_embeddings)
                
                # 避免超过API速率限制
                if i + batch_size < len(texts):
                    import time
                    time.sleep(1)
            
            return embeddings
        except Exception as e:
            log.error(f"批量生成嵌入向量失败: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def create_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """批量生成文本嵌入向量
        
        Args:
            texts: 输入文本列表
            batch_size: 批处理大小
        
        Returns:
            List[List[float]]: 嵌入向量列表
            
        Raises:
            Exception: 当API调用失败时
        """
        try:
            embeddings = []
            
            # 分批处理
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = await self.openai_client.Embedding.acreate(
                    model=self.embedding_model,
                    input=batch
                )
                batch_embeddings = [data.embedding for data in response.data]
                
                embeddings.extend(batch_embeddings)
                
                # 避免超过API速率限制
                if i + batch_size < len(texts):
                    await asyncio.sleep(1)
            
            return embeddings
        except Exception as e:
            log.error(f"批量生成嵌入向量失败: {e}")
            raise
    
    async def validate_api_key(self) -> bool:
        """验证API配置是否有效
        
        Returns:
            bool: 是否有效
        """
        try:
            await self.openai_client.Model.alist()
            return True
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """获取可用模型列表
        
        Returns:
            List[str]: 模型列表
        """
        try:
            response = await self.openai_client.Model.alist()
            return [model.id for model in response.data]
        except Exception as e:
            log.error(f"获取模型列表失败: {e}")
            return []
    
    async def estimate_tokens(self, text: str) -> int:
        """估算文本的token数量
        
        Args:
            text: 输入文本
        
        Returns:
            int: 估算的token数量
        """
        # 简单估算：平均每个单词1.3个token
        words = text.split()
        return int(len(words) * 1.3)
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """获取API速率限制信息
        
        Returns:
            Dict: 速率限制信息
        """
        try:
            response = self.openai_client.Model.list()
            headers = response.headers
            
            return {
                "requests_remaining": headers.get("x-ratelimit-remaining-requests"),
                "tokens_remaining": headers.get("x-ratelimit-remaining-tokens"),
                "reset_timestamp": headers.get("x-ratelimit-reset-tokens")
            }
        except Exception:
            return {}


# 为了向后兼容，保留LLMClient别名
LLMClient = OpenAIClient 