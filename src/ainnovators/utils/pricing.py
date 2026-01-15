"""Model pricing configuration for cost calculation."""

# Pricing per 1 million tokens (USD)
# Updated January 2026
MODEL_PRICING: dict[str, dict[str, float]] = {
    # Anthropic models
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "claude-haiku-4": {"input": 0.80, "output": 4.00},
    "claude-opus-4": {"input": 15.00, "output": 75.00},
    "claude-opus-4-5": {"input": 15.00, "output": 75.00},
    # OpenAI models
    "gpt-5": {"input": 5.00, "output": 15.00},
    "gpt-5.2": {"input": 2.50, "output": 10.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    # Google models
    "gemini-2.0-flash-exp": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
}

# Default pricing for unknown models
DEFAULT_PRICING: dict[str, float] = {"input": 3.00, "output": 15.00}


def calculate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """
    Calculate cost in USD for a given model and token counts.

    Args:
        model: Model identifier (e.g., "claude-sonnet-4")
        prompt_tokens: Number of input/prompt tokens
        completion_tokens: Number of output/completion tokens

    Returns:
        Cost in USD
    """
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)

    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]

    return input_cost + output_cost


def get_model_pricing(model: str) -> dict[str, float]:
    """
    Get pricing for a specific model.

    Args:
        model: Model identifier

    Returns:
        Dict with "input" and "output" prices per 1M tokens
    """
    return MODEL_PRICING.get(model, DEFAULT_PRICING)
