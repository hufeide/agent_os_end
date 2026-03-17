"""
PromptTemplate - 提示词模板

定义提示词模板的结构和管理。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


@dataclass
class PromptTemplate:
    """提示词模板"""
    template: str
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version: str = "1.0"
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_rate: float = 0.0
    
    def __post_init__(self):
        if not self.name:
            self.name = f"prompt_{self.id[:8]}"
        if not self.variables:
            self._extract_variables()
    
    def _extract_variables(self) -> None:
        """提取模板变量"""
        import re
        pattern = r'\{(\w+)\}'
        self.variables = list(set(re.findall(pattern, self.template)))
    
    def render(self, **kwargs) -> str:
        """
        渲染模板
        
        Args:
            **kwargs: 变量值
            
        Returns:
            渲染后的字符串
        """
        self.usage_count += 1
        self.updated_at = datetime.now()
        
        rendered = self.template
        for key, value in kwargs.items():
            rendered = rendered.replace(f"{{{key}}}", str(value))
        
        return rendered
    
    def validate(self, **kwargs) -> tuple[bool, List[str]]:
        """
        验证变量
        
        Args:
            **kwargs: 变量值
            
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        for var in self.variables:
            if var not in kwargs:
                errors.append(f"Missing required variable: {var}")
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "template": self.template,
            "description": self.description,
            "version": self.version,
            "variables": self.variables,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "usage_count": self.usage_count,
            "success_rate": self.success_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """从字典创建"""
        template = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            template=data.get("template", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            variables=data.get("variables", []),
            metadata=data.get("metadata", {}),
            usage_count=data.get("usage_count", 0),
            success_rate=data.get("success_rate", 0.0)
        )
        
        if "created_at" in data:
            template.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            template.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return template


@dataclass
class PromptLibrary:
    """提示词库"""
    templates: Dict[str, PromptTemplate] = field(default_factory=dict)
    
    def add(self, template: PromptTemplate) -> None:
        """添加模板"""
        self.templates[template.id] = template
    
    def get(self, template_id: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self.templates.get(template_id)
    
    def get_by_name(self, name: str) -> Optional[PromptTemplate]:
        """通过名称获取模板"""
        for template in self.templates.values():
            if template.name == name:
                return template
        return None
    
    def remove(self, template_id: str) -> bool:
        """删除模板"""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False
    
    def list_templates(self) -> List[PromptTemplate]:
        """列出所有模板"""
        return list(self.templates.values())
    
    def get_most_used(self, limit: int = 10) -> List[PromptTemplate]:
        """获取使用最多的模板"""
        return sorted(
            self.templates.values(),
            key=lambda t: t.usage_count,
            reverse=True
        )[:limit]
    
    def get_most_successful(self, limit: int = 10) -> List[PromptTemplate]:
        """获取成功率最高的模板"""
        return sorted(
            self.templates.values(),
            key=lambda t: t.success_rate,
            reverse=True
        )[:limit]
