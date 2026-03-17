"""
LLM Client - Qwen3Coder 模型客户端

用于连接 192.168.1.159:19000 的 Qwen3Coder 模型
"""

import requests
import json
from typing import Any, Dict, List, Optional


class Qwen3CoderClient:
    """Qwen3Coder LLM 客户端"""
    
    def __init__(
        self,
        base_url: str = "http://192.168.1.159:19000",
        model: str = "Qwen3Coder",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.chat_endpoint = f"{self.base_url}/v1/chat/completions"
    
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        messages = [{"role": "user", "content": prompt}]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": False
        }
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            response.raise_for_status()
            
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return ""
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def agenerate(self, prompt: str, **kwargs) -> str:
        """异步生成文本"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, prompt)
    
    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """批量生成"""
        results = []
        for prompt in prompts:
            result = self.generate(prompt, **kwargs)
            results.append(result)
        return results


# 全局LLM实例
_llm_client: Optional[Qwen3CoderClient] = None


def get_llm_client() -> Qwen3CoderClient:
    """获取LLM客户端"""
    global _llm_client
    if _llm_client is None:
        _llm_client = Qwen3CoderClient()
    return _llm_client


def set_llm_client(client: Qwen3CoderClient) -> None:
    """设置LLM客户端"""
    global _llm_client
    _llm_client = client
