"""Agent implementations for the AI startup company."""

from .base_agent import BaseAgent
from .ceo import CEOAgent
from .designer import DesignerAgent
from .developer import DeveloperAgent
from .legal_advisor import LegalAdvisorAgent
from .marketer import MarketerAgent
from .qa import QAAgent
from .researcher import ResearcherAgent
from .tech_writer import DeckStrategistAgent, TechWriterAgent
__all__ = [
    "BaseAgent",
    "CEOAgent",
    "ResearcherAgent",
    "LegalAdvisorAgent",
    "DeveloperAgent",
    "DesignerAgent",
    "QAAgent",
    "DeckStrategistAgent",
    "MarketerAgent",
    "TechWriterAgent",
]
