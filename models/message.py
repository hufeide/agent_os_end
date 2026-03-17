"""
Message - 消息模型

定义Agent之间通信的消息结构。
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from datetime import datetime
from enum import Enum
import uuid


class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """消息模型"""
    role: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "tool_call_id": self.tool_call_id,
            "tool_calls": self.tool_calls,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建"""
        msg = cls(
            id=data.get("id", str(uuid.uuid4())),
            role=data.get("role", "user"),
            content=data.get("content", ""),
            name=data.get("name"),
            tool_call_id=data.get("tool_call_id"),
            tool_calls=data.get("tool_calls", []),
            metadata=data.get("metadata", {})
        )
        if "timestamp" in data:
            msg.timestamp = datetime.fromisoformat(data["timestamp"])
        return msg
    
    @classmethod
    def system_message(cls, content: str, **kwargs) -> 'Message':
        """创建系统消息"""
        return cls(role=MessageRole.SYSTEM.value, content=content, **kwargs)
    
    @classmethod
    def user_message(cls, content: str, **kwargs) -> 'Message':
        """创建用户消息"""
        return cls(role=MessageRole.USER.value, content=content, **kwargs)
    
    @classmethod
    def assistant_message(cls, content: str, **kwargs) -> 'Message':
        """创建助手消息"""
        return cls(role=MessageRole.ASSISTANT.value, content=content, **kwargs)
    
    @classmethod
    def tool_message(cls, content: str, tool_call_id: str, **kwargs) -> 'Message':
        """创建工具消息"""
        return cls(
            role=MessageRole.TOOL.value,
            content=content,
            tool_call_id=tool_call_id,
            **kwargs
        )


@dataclass
class Conversation:
    """对话模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, message: Message) -> None:
        """添加消息"""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_messages(self) -> List[Message]:
        """获取所有消息"""
        return self.messages.copy()
    
    def clear(self) -> None:
        """清空对话"""
        self.messages.clear()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "messages": [m.to_dict() for m in self.messages],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
