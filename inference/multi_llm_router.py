"""
MultiLLMRouter - 多LLM路由器

支持多个LLM的智能路由。
"""

from typing import Any, Callable, Dict, List, Optional
import asyncio


class LLMRouter:
    """LLM路由器基类"""
    
    def __init__(self, name: str, llm: Any, weight: float = 1.0):
        self.name = name
        self.llm = llm
        self.weight = weight
        self._stats = {
            "calls": 0,
            "successes": 0,
            "failures": 0,
            "total_latency": 0.0
        }
    
    async def generate(self, prompt: str, **kwargs) -> Any:
        """生成"""
        import time
        start = time.time()
        self._stats["calls"] += 1
        
        try:
            if asyncio.iscoroutinefunction(self.llm):
                result = await self.llm(prompt, **kwargs)
            elif callable(self.llm):
                result = self.llm(prompt, **kwargs)
            else:
                result = await self.llm.generate(prompt, **kwargs)
            
            self._stats["successes"] += 1
            self._stats["total_latency"] += time.time() - start
            return result
        except Exception as e:
            self._stats["failures"] += 1
            raise e
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return dict(self._stats)


class MultiLLMRouter:
    """
    多LLM路由器
    
    支持多个LLM的智能路由，根据任务类型、负载和性能选择合适的LLM。
    """
    
    def __init__(
        self,
        routers: List[LLMRouter] = None,
        strategy: str = "weighted"
    ):
        self.routers: List[LLMRouter] = routers or []
        self.strategy = strategy
        
        self._capabilities: Dict[str, List[str]] = {}
        
        self._current_index = 0
    
    def add_router(self, router: LLMRouter, capabilities: List[str] = None) -> None:
        """
        添加路由器
        
        Args:
            router: LLM路由器
            capabilities: 支持的能力列表
        """
        self.routers.append(router)
        
        if capabilities:
            self._capabilities[router.name] = capabilities
    
    def set_capabilities(self, router_name: str, capabilities: List[str]) -> None:
        """
        设置路由器能力
        
        Args:
            router_name: 路由器名称
            capabilities: 能力列表
        """
        self._capabilities[router_name] = capabilities
    
    async def generate(
        self,
        prompt: str,
        capability: str = None,
        **kwargs
    ) -> Any:
        """
        生成文本
        
        Args:
            prompt: 提示词
            capability: 所需能力
            **kwargs: 其他参数
            
        Returns:
            生成结果
        """
        if not self.routers:
            raise ValueError("No routers available")
        
        router = self._select_router(capability)
        
        if not router:
            router = self.routers[0]
        
        return await router.generate(prompt, **kwargs)
    
    async def batch_generate(
        self,
        prompts: List[str],
        capabilities: List[str] = None
    ) -> List[Any]:
        """
        批量生成
        
        Args:
            prompts: 提示词列表
            capabilities: 能力列表
            
        Returns:
            结果列表
        """
        if not self.routers:
            raise ValueError("No routers available")
        
        if capabilities and len(capabilities) == len(prompts):
            results = []
            for prompt, cap in zip(prompts, capabilities):
                router = self._select_router(cap)
                if not router:
                    router = self.routers[0]
                result = await router.generate(prompt)
                results.append(result)
            return results
        
        router = self._select_router()
        if not router:
            router = self.routers[0]
        
        if hasattr(router.llm, "batch_generate"):
            return await router.llm.batch_generate(prompts)
        
        coros = [router.generate(p) for p in prompts]
        return await asyncio.gather(*coros)
    
    def _select_router(self, capability: str = None) -> Optional[LLMRouter]:
        """
        选择路由器
        
        Args:
            capability: 所需能力
            
        Returns:
            选中的路由器
        """
        if capability:
            for name, caps in self._capabilities.items():
                if capability in caps:
                    for router in self.routers:
                        if router.name == name:
                            return router
        
        if self.strategy == "weighted":
            return self._weighted_select()
        elif self.strategy == "round_robin":
            return self._round_robin_select()
        elif self.strategy == "random":
            import random
            return random.choice(self.routers)
        elif self.strategy == "least_loaded":
            return self._least_loaded_select()
        
        return self.routers[0] if self.routers else None
    
    def _weighted_select(self) -> LLMRouter:
        """加权选择"""
        import random
        
        total_weight = sum(r.weight for r in self.routers)
        r = random.uniform(0, total_weight)
        
        cumulative = 0
        for router in self.routers:
            cumulative += router.weight
            if r <= cumulative:
                return router
        
        return self.routers[0]
    
    def _round_robin_select(self) -> LLMRouter:
        """轮询选择"""
        router = self.routers[self._current_index]
        self._current_index = (self._current_index + 1) % len(self.routers)
        return router
    
    def _least_loaded_select(self) -> LLMRouter:
        """最低负载选择"""
        return min(
            self.routers,
            key=lambda r: r._stats["calls"]
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "total_routers": len(self.routers),
            "routers": {
                r.name: r.get_stats()
                for r in self.routers
            },
            "strategy": self.strategy
        }
    
    def get_router(self, name: str) -> Optional[LLMRouter]:
        """获取指定路由器"""
        for router in self.routers:
            if router.name == name:
                return router
        return None
