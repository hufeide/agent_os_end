"""
ResearchSkill - 研究技能

提供信息搜索和研究报告生成功能。
"""

from .skill import Skill, SkillResult
from ..tools import ToolRegistry, SearchTool, WebTool
import time


class ResearchSkill(Skill):
    """研究技能"""
    
    name = "research"
    description = "Research and gather information on a topic"
    category = "research"
    tools = ["search", "web"]
    
    def __init__(self, tool_registry: ToolRegistry = None):
        super().__init__()
        self.tool_registry = tool_registry or ToolRegistry()
        
        if len(self.tool_registry) == 0:
            self.tool_registry.register(SearchTool())
            self.tool_registry.register(WebTool())
    
    async def execute(self, input=None, **kwargs) -> SkillResult:
        """执行研究"""
        start_time = time.time()
        
        topic = kwargs.get("topic", input)
        if not topic:
            return SkillResult(
                success=False,
                error="No topic provided"
            )
        
        try:
            search_tool = self.tool_registry.get("search")
            web_tool = self.tool_registry.get("web")
            
            search_result = await search_tool.execute(query=topic, max_results=5)
            
            findings = []
            if search_result.success and search_result.result:
                for item in search_result.result.get("results", [])[:3]:
                    if item.get("url"):
                        web_result = await web_tool.execute(url=item["url"])
                        if web_result.success:
                            findings.append({
                                "source": item.get("title", ""),
                                "content": web_result.result.get("content", "")[:1000]
                            })
            
            report = self._generate_report(topic, findings)
            
            return SkillResult(
                success=True,
                result={
                    "topic": topic,
                    "findings": findings,
                    "report": report
                },
                execution_time=time.time() - start_time,
                metadata={"findings_count": len(findings)}
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _generate_report(self, topic: str, findings: list) -> str:
        """生成研究报告"""
        report = f"# Research Report: {topic}\n\n"
        
        if findings:
            report += "## Key Findings\n\n"
            for i, finding in enumerate(findings, 1):
                report += f"{i}. {finding.get('source', 'Unknown')}\n"
                content = finding.get('content', '')
                if content:
                    report += f"   {content[:200]}...\n\n"
        else:
            report += "No findings available.\n"
        
        return report


class AnalysisSkill(Skill):
    """分析技能"""
    
    name = "analysis"
    description = "Analyze data and provide insights"
    category = "analysis"
    
    def __init__(self):
        super().__init__()
    
    async def execute(self, input=None, **kwargs) -> SkillResult:
        """执行分析"""
        start_time = time.time()
        
        data = kwargs.get("data", input)
        if not data:
            return SkillResult(
                success=False,
                error="No data provided"
            )
        
        try:
            insights = self._analyze_data(data)
            
            return SkillResult(
                success=True,
                result={
                    "data": data,
                    "insights": insights,
                    "summary": f"Analysis complete. Found {len(insights)} key insights."
                },
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _analyze_data(self, data):
        """分析数据"""
        insights = []
        
        if isinstance(data, dict):
            insights.append(f"Data contains {len(data)} keys: {list(data.keys())}")
        elif isinstance(data, list):
            insights.append(f"Data contains {len(data)} items")
        elif isinstance(data, str):
            insights.append(f"Data is a string with {len(data)} characters")
        
        return insights


class WritingSkill(Skill):
    """写作技能"""
    
    name = "writing"
    description = "Generate written content"
    category = "writing"
    tools = ["file"]
    
    def __init__(self, tool_registry: ToolRegistry = None):
        super().__init__()
        self.tool_registry = tool_registry
    
    async def execute(self, input=None, **kwargs) -> SkillResult:
        """执行写作"""
        start_time = time.time()
        
        content = kwargs.get("content", input)
        task_name = kwargs.get("task_name", "Untitled")
        
        if not content:
            return SkillResult(
                success=False,
                error="No content provided"
            )
        
        try:
            output_path = kwargs.get("output_path")
            
            result = {
                "task_name": task_name,
                "content": content,
                "word_count": len(content.split())
            }
            
            if output_path and self.tool_registry:
                file_tool = self.tool_registry.get("file")
                if file_tool:
                    await file_tool.execute(
                        operation="write",
                        path=output_path,
                        content=content
                    )
                    result["saved_to"] = output_path
            
            return SkillResult(
                success=True,
                result=result,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
