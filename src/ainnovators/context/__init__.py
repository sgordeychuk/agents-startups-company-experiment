"""Shared context pool for agent communication."""

from .observer import ContextObserver
from .shared_context import CompanyContext

__all__ = ["CompanyContext", "ContextObserver"]
