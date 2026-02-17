"""
OmniJARVIS Agent Registry — Central import point for all agents.

Provides the :data:`AGENT_REGISTRY` mapping agent names to their
classes, and convenience imports for every agent shipped with the system.
"""

from assistant.agents.base_agent import BaseAgent, AgentResult
from assistant.agents.focus_agent import FocusAgent
from assistant.agents.executive_agent import ExecutiveAgent
from assistant.agents.memory_agent import MemoryAgent
from assistant.agents.analysis_agent import AnalysisAgent
from assistant.agents.system_agent import SystemAgent
from assistant.agents.documentation_agent import DocumentationAgent
from assistant.agents.code_agent import CodeAgent
from assistant.agents.communication_agent import CommunicationAgent
from assistant.agents.cloud_agent import CloudAgent
from assistant.agents.vision_agent import VisionAgent
from assistant.agents.mobility_agent import MobilityAgent
from assistant.agents.productivity_agent import ProductivityAgent
from assistant.agents.security_agent import SecurityAgent

AGENT_REGISTRY = {
    "executive": ExecutiveAgent,
    "memory": MemoryAgent,
    "analysis": AnalysisAgent,
    "system": SystemAgent,
    "documentation": DocumentationAgent,
    "code": CodeAgent,
    "communication": CommunicationAgent,
    "cloud": CloudAgent,
    "vision": VisionAgent,
    "mobility": MobilityAgent,
    "productivity": ProductivityAgent,
    "security": SecurityAgent,
    "focus": FocusAgent,
}

__all__ = [
    "BaseAgent",
    "AgentResult",
    "AGENT_REGISTRY",
    "FocusAgent",
    "ExecutiveAgent",
    "MemoryAgent",
    "AnalysisAgent",
    "SystemAgent",
    "DocumentationAgent",
    "CodeAgent",
    "CommunicationAgent",
    "CloudAgent",
    "VisionAgent",
    "MobilityAgent",
    "ProductivityAgent",
    "SecurityAgent",
]
