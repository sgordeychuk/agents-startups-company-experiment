"""Data extraction utilities."""

from typing import Any


def extract_idea_from_chat(chat_result: Any) -> dict[str, Any]:
    """
    Extract structured idea from chat conversation.

    Args:
        chat_result: AutoGen chat result object

    Returns:
        Structured idea dictionary
    """
    # TODO: Implement proper extraction logic
    # This should parse the chat history and extract:
    # - Problem statement
    # - Solution description
    # - Target market
    # - Key features
    # - Unique value proposition

    if not chat_result:
        return {}

    # Placeholder structure
    return {
        "problem": None,
        "solution": None,
        "target_market": None,
        "features": [],
        "value_proposition": None,
        "raw_content": str(chat_result),
    }


def extract_research_from_chat(chat_result: Any) -> dict[str, Any]:
    """
    Extract structured research from chat conversation.

    Args:
        chat_result: AutoGen chat result object

    Returns:
        Structured research dictionary
    """
    # TODO: Implement proper extraction logic

    if not chat_result:
        return {}

    return {
        "competitors": [],
        "market_size": {},
        "risks": [],
        "opportunities": [],
        "raw_content": str(chat_result),
    }


def extract_prototype_from_chat(chat_result: Any) -> dict[str, Any]:
    """
    Extract structured prototype info from chat conversation.

    Args:
        chat_result: AutoGen chat result object

    Returns:
        Structured prototype dictionary
    """
    # TODO: Implement proper extraction logic

    if not chat_result:
        return {}

    return {
        "architecture": None,
        "components": [],
        "code": {},
        "tech_stack": [],
        "raw_content": str(chat_result),
    }


def extract_decision(message: str, agent_name: str) -> dict[str, Any]:
    """
    Extract a decision from an agent message.

    Args:
        message: The agent message
        agent_name: Name of the agent

    Returns:
        Structured decision dictionary
    """
    return {
        "agent": agent_name,
        "decision": message,
        "reasoning": None,
        "confidence": None,
    }


def summarize_conversation(messages: list[dict[str, Any]], max_length: int = 1000) -> str:
    """
    Summarize a conversation for context passing.

    Args:
        messages: List of conversation messages
        max_length: Maximum summary length

    Returns:
        Summarized conversation string
    """
    # TODO: Implement proper summarization
    # This could use an LLM for better summarization

    if not messages:
        return ""

    # Simple concatenation with truncation
    content = "\n".join(
        f"{m.get('role', 'unknown')}: {m.get('content', '')[:200]}" for m in messages
    )

    if len(content) > max_length:
        content = content[:max_length] + "..."

    return content
