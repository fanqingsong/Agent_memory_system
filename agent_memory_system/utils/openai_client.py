"""LLM客户端工具

提供OpenAI和Ollama API的封装。

主要功能：
    - Chat Completion API调用(OpenAI/Ollama)
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
from typing import List, Optional, Dict, Any, Literal
import asyncio
from datetime import datetime, timedelta
import json

import openai
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from agent_memory_system.utils.config import config
from agent_memory_system.utils.logger import log

class LLMClient:
    """LLM API客户端类
    
    功能描述：
        提供OpenAI和Ollama API的统一封装，支持：
        1. Chat Completion API调用
        2. 文本嵌入生成
        3. API配置管理
        4. 错误处理和重试机制
    
    属性说明：
        - provider: LLM提供者(openai/ollama)
        - api_key: OpenAI API密钥
        - model: 使用的模型名称
        - embedding_model: 嵌入模型名称
        - temperature: 生成温度
        - max_tokens: 最大生成长度
        - ollama_base_url: Ollama服务地址
    """
    
    def __init__(
        self,
        provider: Literal["openai", "ollama"] = "openai",
        api_key: str = None,
        api_base_url: str = None,
        model: str = "gpt-3.5-turbo",
        embedding_model: str = "text-embedding-ada-002",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        ollama_base_url: str = "http://localhost:11434"
    ) -> None:
        """初始化LLM客户端
        
        Args:
            provider: LLM提供者(openai/ollama)
            api_key: OpenAI API密钥
            model: 使用的模型名称
            embedding_model: 嵌入模型名称
            temperature: 生成温度
            max_tokens: 最大生成长度
            ollama_base_url: Ollama服务地址
        """
        self.provider = provider
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base_url = api_base_url or os.getenv("OPENAI_API_BASE_URL")
        if provider == "openai" and not self.api_key:
            log.warning("未找到OpenAI API密钥")
        
        self.model = model
        self.embedding_model = embedding_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.ollama_base_url = ollama_base_url
        
        # 设置OpenAI API密钥
        if provider == "openai":
            openai.api_key = self.api_key
        
        # 创建OpenAI客户端（新版本）
        if provider == "openai":
            # 支持自定义API基础URL
            client_kwargs = {"api_key": self.api_key}
            if self.api_base_url:
                client_kwargs["base_url"] = self.api_base_url
            self.openai_client = openai.AsyncOpenAI(**client_kwargs)
        
        # 创建HTTP客户端
        self.http_client = httpx.AsyncClient()
    
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
        if self.provider == "openai":
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
            print(f"########################当前provider: {self.provider}")
            print(f"########################当前model: {self.model}")
            print(f"########################当前temperature: {temperature}")
            print(f"########################当前max_tokens: {max_tokens}")
            print(f"########################当前stream: {stream}")
            print(f"########################当前system_prompt: {system_prompt}")
            print(f"########################当前user_message: {user_message}")
            print(f"########################当前ollama_base_url: {self.ollama_base_url}")
            
            if self.provider == "openai":
                # OpenAI API调用（新版本）
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
                
                response = await self.openai_client.chat.completions.create(
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
                    return "".join(collected_messages)
                else:
                    return response.choices[0].message.content
                
            else:
                # Ollama API调用 - 使用generate端点
                url = f"{self.ollama_base_url}/api/generate"
                
                # 构建完整的提示
                full_prompt = f"{system_prompt}\n\nUser: {user_message}\nAssistant:"
                
                payload = {
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": stream,
                    "options": {
                        "temperature": temperature or self.temperature,
                        "num_predict": max_tokens or self.max_tokens
                    }
                }
                
                if stream:
                    async with self.http_client.stream("POST", url, json=payload) as response:
                        response.raise_for_status()
                        collected_messages = []
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        collected_messages.append(data["response"])
                                except json.JSONDecodeError:
                                    continue
                        return "".join(collected_messages)
                else:
                    response = await self.http_client.post(url, json=payload)
                    response.raise_for_status()
                    response_data = response.json()
                    
                    # 检查Ollama响应格式
                    if "response" in response_data:
                        return response_data["response"]
                    else:
                        log.error(f"意外的Ollama响应格式: {response_data}")
                        raise Exception(f"意外的Ollama响应格式: {response_data}")
                
        except Exception as e:
            log.error(f"LLM API调用失败: {e}")
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
            if self.provider == "openai":
                # OpenAI API调用（新版本）
                response = await self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                return response.data[0].embedding
            else:
                # Ollama API调用 - 使用generate端点进行嵌入
                url = f"{self.ollama_base_url}/api/embeddings"
                
                payload = {
                    "model": self.embedding_model,
                    "prompt": text
                }
                
                try:
                    response = await self.http_client.post(url, json=payload)
                    response.raise_for_status()
                    response_data = response.json()
                    
                    # 检查Ollama嵌入响应格式
                    if "embedding" in response_data:
                        return response_data["embedding"]
                    else:
                        log.error(f"意外的Ollama嵌入响应格式: {response_data}")
                        raise Exception(f"意外的Ollama嵌入响应格式: {response_data}")
                except Exception as e:
                    log.error(f"Ollama嵌入API调用失败: {e}")
                    # 如果嵌入失败，返回零向量作为fallback
                    return [0.0] * 384  # 默认384维向量
                
        except Exception as e:
            log.error(f"生成嵌入向量失败: {e}")
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
                
                if self.provider == "openai":
                    # OpenAI API调用（新版本）
                    response = await self.openai_client.embeddings.create(
                        model=self.embedding_model,
                        input=batch
                    )
                    batch_embeddings = [data.embedding for data in response.data]
                else:
                    # Ollama API调用
                    url = f"{self.ollama_base_url}/api/embeddings"
                    batch_embeddings = []
                    
                    for text in batch:
                        try:
                            payload = {
                                "model": self.embedding_model,
                                "prompt": text
                            }
                            response = await self.http_client.post(url, json=payload)
                            response.raise_for_status()
                            batch_embeddings.append(response.json()["embedding"])
                        except Exception as e:
                            log.error(f"Ollama批量嵌入失败: {e}")
                            # 如果嵌入失败，返回零向量作为fallback
                            batch_embeddings.append([0.0] * 384)
                
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
            if self.provider == "openai":
                # 验证OpenAI API密钥
                await self.openai_client.models.list()
                return True
            else:
                # 验证Ollama服务可用性
                url = f"{self.ollama_base_url}/api/tags"
                response = await self.http_client.get(url)
                response.raise_for_status()
                return True
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """获取可用模型列表
        
        Returns:
            List[str]: 模型列表
        """
        try:
            if self.provider == "openai":
                # 获取OpenAI模型列表
                response = await self.openai_client.models.list()
                return [model.id for model in response.data]
            else:
                # 获取Ollama模型列表
                url = f"{self.ollama_base_url}/api/tags"
                response = await self.http_client.get(url)
                response.raise_for_status()
                return [model["name"] for model in response.json()["models"]]
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
            if self.provider == "openai":
                # 获取OpenAI速率限制信息
                response = openai.Model.list()
                headers = response.headers
                
                return {
                    "requests_remaining": headers.get("x-ratelimit-remaining-requests"),
                    "tokens_remaining": headers.get("x-ratelimit-remaining-tokens"),
                    "reset_timestamp": headers.get("x-ratelimit-reset-tokens")
                }
            else:
                # Ollama没有速率限制
                return {}
        except Exception:
            return {} 