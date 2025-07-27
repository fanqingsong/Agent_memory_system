"""
Embedding服务模块

提供高质量的语义向量生成服务，使用OpenAI embedding API。
"""

import numpy as np
from typing import List, Union, Optional
from loguru import logger as log

from agent_memory_system.utils.config import config
from agent_memory_system.utils.openai_client import LLMClient


class EmbeddingService:
    """Embedding服务类
    
    使用OpenAI embedding API生成高质量的语义向量。
    """
    
    def __init__(
        self,
        model_name: str = "text-embedding-ada-002",
        device: Optional[str] = None,
        max_length: int = 512
    ):
        """初始化Embedding服务
        
        Args:
            model_name: 模型名称，默认使用text-embedding-ada-002
            device: 设备类型（cpu/cuda），None表示自动选择
            max_length: 最大序列长度
        """
        self.model_name = model_name
        self.max_length = max_length
        
        # 自动选择设备
        if device is None:
            import torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        log.info(f"初始化Embedding服务: model={model_name}, device={self.device}")
        
        # 初始化OpenAI客户端
        try:
            self.llm_client = LLMClient(
                provider="openai",
                api_key=config.llm.api_key,
                api_base_url=config.llm.api_base_url,
                model=config.llm.model,
                embedding_model=model_name
            )
            # 根据模型名称设置正确的维度
            if "text-embedding-ada-002" in model_name:
                self.dimension = 1536
            elif "bge-large-zh-v1.5" in model_name:
                self.dimension = 1024
            elif "bge-m3" in model_name:
                self.dimension = 1024
            elif "all-MiniLM-L6-v2" in model_name:
                self.dimension = 384
            else:
                self.dimension = 1024  # 默认维度，匹配BAAI模型
            self._use_openai = True
            log.info(f"成功初始化OpenAI embedding客户端，维度: {self.dimension}")
        except Exception as e:
            log.error(f"初始化OpenAI embedding客户端失败: {e}")
            self._use_openai = False
            self.dimension = 1024  # 使用BAAI模型的默认维度
            # 回退到TF-IDF
            log.warning("回退到TF-IDF方法")
            self._use_tfidf_fallback = True
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        show_progress_bar: bool = False
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """编码文本为向量
        
        Args:
            texts: 要编码的文本或文本列表
            normalize: 是否归一化向量
            show_progress_bar: 是否显示进度条
        
        Returns:
            Union[np.ndarray, List[np.ndarray]]: 编码后的向量
        """
        try:
            # 确保输入是列表格式
            if isinstance(texts, str):
                texts = [texts]
                single_input = True
            else:
                single_input = False
            
            # 过滤空文本
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            if not valid_texts:
                log.warning("没有有效的文本进行编码")
                if single_input:
                    return np.zeros(self.dimension)
                else:
                    return [np.zeros(self.dimension) for _ in texts]
            
            # 使用OpenAI embedding API
            if self._use_openai:
                return self._encode_with_openai(valid_texts, single_input, normalize)
            
            # 检查是否使用TF-IDF fallback
            if hasattr(self, '_use_tfidf_fallback') and self._use_tfidf_fallback:
                return self._encode_with_tfidf(texts, single_input)
            
            # 如果都失败了，返回零向量
            log.error("所有embedding方法都失败了")
            if single_input:
                return np.zeros(self.dimension)
            else:
                return [np.zeros(self.dimension) for _ in texts]
                
        except Exception as e:
            log.error(f"文本编码失败: {e}")
            if isinstance(texts, str):
                return np.zeros(self.dimension)
            else:
                return [np.zeros(self.dimension) for _ in texts]
    
    async def _encode_with_openai_async(
        self,
        texts: List[str],
        single_input: bool,
        normalize: bool = True
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """使用OpenAI API异步编码文本
        
        Args:
            texts: 文本列表
            single_input: 是否为单个输入
            normalize: 是否归一化
        
        Returns:
            Union[np.ndarray, List[np.ndarray]]: 编码后的向量
        """
        try:
            if single_input:
                # 单个文本编码
                embedding = await self.llm_client.create_embedding(texts[0])
                vector = np.array(embedding)
                if normalize:
                    vector = vector / np.linalg.norm(vector)
                return vector
            else:
                # 批量编码
                embeddings = await self.llm_client.create_embeddings(texts)
                vectors = []
                for embedding in embeddings:
                    vector = np.array(embedding)
                    if normalize:
                        vector = vector / np.linalg.norm(vector)
                    vectors.append(vector)
                return vectors
        except Exception as e:
            log.error(f"OpenAI embedding编码失败: {e}")
            if single_input:
                return np.zeros(self.dimension)
            else:
                return [np.zeros(self.dimension) for _ in texts]
    
    def _encode_with_openai(
        self,
        texts: List[str],
        single_input: bool,
        normalize: bool = True
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """使用OpenAI API编码文本（同步包装）
        
        Args:
            texts: 文本列表
            single_input: 是否为单个输入
            normalize: 是否归一化
        
        Returns:
            Union[np.ndarray, List[np.ndarray]]: 编码后的向量
        """
        import asyncio
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，回退到TF-IDF
                log.warning("检测到运行中的事件循环，回退到TF-IDF编码")
                return self._encode_with_tfidf(texts, single_input)
            except RuntimeError:
                # 如果没有运行的事件循环，创建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self._encode_with_openai_async(texts, single_input, normalize)
                    )
                finally:
                    loop.close()
        except Exception as e:
            log.error(f"OpenAI embedding编码失败: {e}")
            if single_input:
                return np.zeros(self.dimension)
            else:
                return [np.zeros(self.dimension) for _ in texts]
    

    def _encode_with_tfidf(self, texts: List[str], single_input: bool) -> Union[np.ndarray, List[np.ndarray]]:
        """使用TF-IDF进行编码（fallback方法）
        
        Args:
            texts: 文本列表
            single_input: 是否为单个输入
        
        Returns:
            Union[np.ndarray, List[np.ndarray]]: 编码后的向量
        """
        try:
            from agent_memory_system.core.memory.memory_utils import generate_tfidf_vector
            
            if single_input:
                vector = generate_tfidf_vector(texts[0], self.dimension)
                return vector
            else:
                result = []
                for text in texts:
                    if text and text.strip():
                        vector = generate_tfidf_vector(text, self.dimension)
                        result.append(vector)
                    else:
                        result.append(np.zeros(self.dimension))
                return result
        except Exception as e:
            log.error(f"TF-IDF编码失败: {e}")
            if single_input:
                return np.zeros(self.dimension)
            else:
                return [np.zeros(self.dimension) for _ in texts]
    
    def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """编码单个文本
        
        Args:
            text: 要编码的文本
            normalize: 是否归一化向量
        
        Returns:
            np.ndarray: 编码后的向量
        """
        return self.encode([text], normalize=normalize)[0]
    
    def similarity(
        self,
        text1: str,
        text2: str,
        normalize: bool = True
    ) -> float:
        """计算两个文本的相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            normalize: 是否归一化向量
        
        Returns:
            float: 相似度分数（0-1之间）
        """
        try:
            # 编码两个文本
            embeddings = self.encode([text1, text2], normalize=normalize)
            
            # 计算余弦相似度
            similarity = np.dot(embeddings[0], embeddings[1])
            if normalize:
                # 归一化向量，余弦相似度就是点积
                return float(similarity)
            else:
                # 计算余弦相似度
                norm1 = np.linalg.norm(embeddings[0])
                norm2 = np.linalg.norm(embeddings[1])
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                return float(similarity / (norm1 * norm2))
                
        except Exception as e:
            log.error(f"计算相似度失败: {e}")
            return 0.0
    
    def batch_similarity(
        self,
        query_text: str,
        candidate_texts: List[str],
        normalize: bool = True
    ) -> List[float]:
        """批量计算查询文本与候选文本的相似度
        
        Args:
            query_text: 查询文本
            candidate_texts: 候选文本列表
            normalize: 是否归一化向量
        
        Returns:
            List[float]: 相似度分数列表
        """
        try:
            # 编码所有文本
            all_texts = [query_text] + candidate_texts
            embeddings = self.encode(all_texts, normalize=normalize)
            
            query_embedding = embeddings[0]
            candidate_embeddings = embeddings[1:]
            
            # 计算相似度
            similarities = []
            for candidate_embedding in candidate_embeddings:
                similarity = np.dot(query_embedding, candidate_embedding)
                if normalize:
                    similarities.append(float(similarity))
                else:
                    norm1 = np.linalg.norm(query_embedding)
                    norm2 = np.linalg.norm(candidate_embedding)
                    if norm1 == 0 or norm2 == 0:
                        similarities.append(0.0)
                    else:
                        similarities.append(float(similarity / (norm1 * norm2)))
            
            return similarities
            
        except Exception as e:
            log.error(f"批量计算相似度失败: {e}")
            return [0.0] * len(candidate_texts)
    
    def get_dimension(self) -> int:
        """获取向量维度
        
        Returns:
            int: 向量维度
        """
        return self.dimension
    
    def get_model_name(self) -> str:
        """获取模型名称
        
        Returns:
            str: 模型名称
        """
        return self.model_name


# 全局embedding服务实例
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取全局embedding服务实例
    
    Returns:
        EmbeddingService: embedding服务实例
    """
    global _embedding_service
    if _embedding_service is None:
        model_name = getattr(config.embedding, 'model_name', 'text-embedding-ada-002')
        device = getattr(config.embedding, 'device', None)
        max_length = getattr(config.embedding, 'max_length', 512)
        
        _embedding_service = EmbeddingService(
            model_name=model_name,
            device=device,
            max_length=max_length
        )
    return _embedding_service


def generate_embedding_vector(text: str) -> List[float]:
    """生成文本的embedding向量
    
    Args:
        text: 输入文本
    
    Returns:
        List[float]: embedding向量
    """
    try:
        embedding_service = get_embedding_service()
        vector = embedding_service.encode_single(text, normalize=True)
        return vector.tolist()
    except Exception as e:
        log.error(f"生成embedding向量失败: {e}")
        # 返回零向量作为fallback
        dimension = getattr(config.embedding, 'dimension', 1536)
        return [0.0] * dimension


def generate_embedding_vectors(texts: List[str]) -> List[List[float]]:
    """批量生成文本的embedding向量
    
    Args:
        texts: 输入文本列表
    
    Returns:
        List[List[float]]: embedding向量列表
    """
    try:
        embedding_service = get_embedding_service()
        vectors = embedding_service.encode(texts, normalize=True)
        return [vector.tolist() for vector in vectors]
    except Exception as e:
        log.error(f"批量生成embedding向量失败: {e}")
        # 返回零向量作为fallback
        dimension = getattr(config.embedding, 'dimension', 1536)
        return [[0.0] * dimension for _ in texts] 