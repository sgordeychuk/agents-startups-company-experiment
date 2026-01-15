"""Validation utilities."""

from typing import Any


def meets_quality_threshold(data: dict[str, Any], threshold: float = 0.7) -> bool:
    """
    Check if data meets the quality threshold.

    Args:
        data: Data to validate
        threshold: Minimum quality score (0-1)

    Returns:
        True if quality threshold is met
    """
    # TODO: Implement proper quality assessment
    # This could use an LLM to evaluate quality

    if not data:
        return False

    # Placeholder: check for required fields
    required_fields = ["problem", "solution"]
    present_fields = sum(1 for f in required_fields if data.get(f))
    score = present_fields / len(required_fields) if required_fields else 0

    return score >= threshold


def validate_idea(idea: dict[str, Any]) -> dict[str, Any]:
    """
    Validate an idea structure.

    Args:
        idea: The idea to validate

    Returns:
        Validation result with scores
    """
    results = {
        "valid": True,
        "scores": {},
        "missing_fields": [],
        "warnings": [],
    }

    # Check required fields
    required = ["problem", "solution", "target_market"]
    for field in required:
        if not idea.get(field):
            results["missing_fields"].append(field)
            results["valid"] = False

    # TODO: Add more sophisticated validation
    # - Novelty check
    # - Problem-solution fit
    # - Market size validation

    return results


def validate_research(research: dict[str, Any]) -> dict[str, Any]:
    """
    Validate research structure.

    Args:
        research: The research to validate

    Returns:
        Validation result with scores
    """
    results = {
        "valid": True,
        "scores": {},
        "missing_fields": [],
        "warnings": [],
    }

    # Check for competitors
    competitors = research.get("competitors", [])
    if len(competitors) < 3:
        results["warnings"].append(f"Only {len(competitors)} competitors found, expected 3+")

    # Check for market sizing
    market_size = research.get("market_size", {})
    if not market_size.get("tam"):
        results["missing_fields"].append("TAM")
    if not market_size.get("sam"):
        results["missing_fields"].append("SAM")
    if not market_size.get("som"):
        results["missing_fields"].append("SOM")

    # Check for risks
    risks = research.get("risks", [])
    if not risks:
        results["warnings"].append("No risks identified")

    results["valid"] = len(results["missing_fields"]) == 0

    return results


def validate_prototype(prototype: dict[str, Any]) -> dict[str, Any]:
    """
    Validate prototype structure.

    Args:
        prototype: The prototype to validate

    Returns:
        Validation result with scores
    """
    results = {
        "valid": True,
        "scores": {},
        "missing_fields": [],
        "warnings": [],
    }

    # Check for architecture
    if not prototype.get("architecture"):
        results["missing_fields"].append("architecture")

    # Check for components
    components = prototype.get("components", [])
    if not components:
        results["warnings"].append("No components defined")

    # Check for code
    code = prototype.get("code", {})
    if not code:
        results["warnings"].append("No code generated")

    results["valid"] = len(results["missing_fields"]) == 0

    return results


def validate_pitch(pitch: dict[str, Any]) -> dict[str, Any]:
    """
    Validate pitch deck structure.

    Args:
        pitch: The pitch deck to validate

    Returns:
        Validation result with scores
    """
    results = {
        "valid": True,
        "scores": {},
        "missing_fields": [],
        "warnings": [],
    }

    # Required slides
    required_slides = [
        "title",
        "problem",
        "solution",
        "market",
        "business_model",
        "team",
        "ask",
    ]

    slides = pitch.get("slides", [])
    slide_types = {s.get("type") for s in slides if isinstance(s, dict)}

    for slide in required_slides:
        if slide not in slide_types:
            results["missing_fields"].append(f"slide:{slide}")

    results["valid"] = len(results["missing_fields"]) == 0

    return results
