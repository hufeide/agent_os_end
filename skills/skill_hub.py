"""
SkillHub - 技能中心

管理所有可用技能的注册和获取。
"""

from typing import Dict, List, Optional, Any
from .skill import Skill, SkillResult
import threading


class SkillHub:
    """
    技能中心
    
    管理所有可用技能的注册、获取和调用。
    """
    
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._lock = threading.RLock()
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, skill: Skill) -> None:
        """
        注册技能
        
        Args:
            skill: 技能实例
        """
        with self._lock:
            self._skills[skill.name] = skill
            
            if skill.category not in self._categories:
                self._categories[skill.category] = []
            if skill.name not in self._categories[skill.category]:
                self._categories[skill.category].append(skill.name)
    
    def unregister(self, skill_name: str) -> bool:
        """
        注销技能
        
        Args:
            skill_name: 技能名称
            
        Returns:
            是否成功
        """
        with self._lock:
            if skill_name in self._skills:
                skill = self._skills[skill_name]
                if skill.category in self._categories:
                    self._categories[skill.category].remove(skill_name)
                del self._skills[skill_name]
                return True
            return False
    
    def get(self, name: str) -> Optional[Skill]:
        """
        获取技能
        
        Args:
            name: 技能名称
            
        Returns:
            技能实例
        """
        with self._lock:
            return self._skills.get(name)
    
    def get_all(self) -> List[Skill]:
        """
        获取所有技能
        
        Returns:
            技能列表
        """
        with self._lock:
            return list(self._skills.values())
    
    def list(self) -> List[str]:
        """
        列出所有技能名称
        
        Returns:
            技能名称列表
        """
        with self._lock:
            return list(self._skills.keys())
    
    def list_by_category(self, category: str) -> List[str]:
        """
        按类别列出技能
        
        Args:
            category: 类别
            
        Returns:
            技能名称列表
        """
        with self._lock:
            return self._categories.get(category, [])
    
    def get_categories(self) -> List[str]:
        """
        获取所有类别
        
        Returns:
            类别列表
        """
        with self._lock:
            return list(self._categories.keys())
    
    def find_best_skill(
        self,
        capabilities: List[str],
        preferred_type: Optional[str] = None
    ) -> Optional[Skill]:
        """
        根据能力查找最佳技能
        
        Args:
            capabilities: 能力列表
            preferred_type: 首选类型
            
        Returns:
            技能实例
        """
        with self._lock:
            best_skill = None
            best_match = 0
            
            for skill in self._skills.values():
                match = 0
                for cap in capabilities:
                    if cap.lower() in skill.name.lower():
                        match += 2
                    elif cap.lower() in skill.description.lower():
                        match += 1
                
                if match > best_match:
                    best_match = match
                    best_skill = skill
            
            return best_skill
    
    async def execute(self, skill_name: str, input: Any = None, **kwargs) -> SkillResult:
        """
        执行技能
        
        Args:
            skill_name: 技能名称
            input: 输入数据
            **kwargs: 其他参数
            
        Returns:
            技能执行结果
        """
        skill = self.get(skill_name)
        if not skill:
            return SkillResult(
                success=False,
                error=f"Skill {skill_name} not found"
            )
        
        return await skill.execute(input, **kwargs)
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        获取技能信息
        
        Args:
            skill_name: 技能名称
            
        Returns:
            技能信息
        """
        skill = self.get(skill_name)
        if skill:
            return skill.get_info()
        return None
    
    def clear(self) -> None:
        """清空注册表"""
        with self._lock:
            self._skills.clear()
            self._categories.clear()
    
    def __len__(self) -> int:
        """获取技能数量"""
        with self._lock:
            return len(self._skills)
    
    def __contains__(self, skill_name: str) -> bool:
        """检查技能是否存在"""
        return skill_name in self._skills
