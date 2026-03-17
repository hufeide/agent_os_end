"""
GPUBatchInference - GPU批量推理

支持GPU加速的批量推理服务。
"""

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class InferenceRequest:
    """推理请求"""
    id: str
    prompt: str
    future: asyncio.Future = field(default_factory=asyncio.get_event_loop().create_future)
    timestamp: datetime = field(default_factory=datetime.now)


class GPUBatchInference:
    """
    GPU批量推理
    
    支持批量提交推理请求，积累到一定数量后批量处理，提高GPU利用率。
    """
    
    def __init__(
        self,
        llm: Any,
        batch_size: int = 8,
        max_queue_size: int = 100,
        timeout: float = 1.0
    ):
        self.llm = llm
        self.batch_size = batch_size
        self.max_queue_size = max_queue_size
        self.timeout = timeout
        
        self._queue: List[InferenceRequest] = []
        self._lock = threading.RLock()
        self._processing = False
        self._stats = {
            "total_requests": 0,
            "total_batches": 0,
            "avg_batch_size": 0
        }
    
    async def submit(self, prompt: str, request_id: str = None) -> Any:
        """
        提交推理请求
        
        Args:
            prompt: 提示词
            request_id: 请求ID
            
        Returns:
            推理结果
        """
        if request_id is None:
            import uuid
            request_id = str(uuid.uuid4())
        
        request = InferenceRequest(id=request_id, prompt=prompt)
        
        with self._lock:
            if len(self._queue) >= self.max_queue_size:
                await self.flush()
            
            self._queue.append(request)
            self._stats["total_requests"] += 1
            
            if len(self._queue) >= self.batch_size:
                asyncio.create_task(self.flush())
        
        return await request.future
    
    async def flush(self) -> None:
        """处理队列中的所有请求"""
        with self._lock:
            if self._processing or not self._queue:
                return
            
            self._processing = True
            
            batch = self._queue.copy()
            self._queue.clear()
        
        try:
            prompts = [r.prompt for r in batch]
            
            results = await self._batch_generate(prompts)
            
            for request, result in zip(batch, results):
                if not request.future.done():
                    request.future.set_result(result)
            
            self._stats["total_batches"] += 1
            
            batch_size = len(batch)
            current_avg = self._stats["avg_batch_size"]
            total_batches = self._stats["total_batches"]
            self._stats["avg_batch_size"] = (current_avg * (total_batches - 1) + batch_size) / total_batches
            
        except Exception as e:
            for request in batch:
                if not request.future.done():
                    request.future.set_exception(e)
        
        finally:
            with self._lock:
                self._processing = False
    
    async def _batch_generate(self, prompts: List[str]) -> List[Any]:
        """批量生成"""
        if hasattr(self.llm, "batch_generate"):
            return await self.llm.batch_generate(prompts)
        
        results = []
        for prompt in prompts:
            if asyncio.iscoroutinefunction(self.llm):
                result = await self.llm(prompt)
            else:
                result = self.llm(prompt)
            results.append(result)
        
        return results
    
    async def wait_for_completion(self) -> None:
        """等待所有请求完成"""
        while True:
            with self._lock:
                if not self._queue and not self._processing:
                    return
            await asyncio.sleep(0.1)
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        with self._lock:
            return len(self._queue)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return dict(self._stats)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.flush()
