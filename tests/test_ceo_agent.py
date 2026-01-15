"""Example: Testing the CEO agent with various scenarios."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ainnovators.agents import CEOAgent
from src.ainnovators.context import CompanyContext
from src.ainnovators.utils import AgentTester


def test_ceo_tools() -> None:
    """Test CEO agent tools availability."""
    print("\n" + "=" * 80)
    print("Test 1: CEO Agent Tools")
    print("=" * 80)

    context = CompanyContext()
    ceo = CEOAgent(context=context)

    tester = AgentTester(output_dir=Path("./test_results"))
    result = tester.test_agent_tools(
        agent=ceo,
        test_name="ceo_tools_test",
        context=context,
    )

    print("\n✓ Test completed")
    print(f"  - Tools: {result['tool_count']}")
    print(f"  - Functions: {result['function_count']}")
    print(f"  - Tool names: {[t['name'] for t in result['tools']]}")


def test_ceo_generate_ideas() -> None:
    """Test CEO idea generation."""
    print("\n" + "=" * 80)
    print("Test 2: CEO Idea Generation")
    print("=" * 80)

    context = CompanyContext()
    ceo = CEOAgent(context=context)

    tester = AgentTester(output_dir=Path("./test_results"))

    # Test input
    test_input = {
        "chairman_input": "Create a sustainable fishing platform that helps small fishermen"
    }

    result = tester.test_agent(
        agent=ceo,
        test_name="ceo_generate_ideas",
        test_function="generate_ideas",
        test_input=test_input,
        context=context,
    )

    print(f"\n{'✓ Test PASSED' if result['success'] else '✗ Test FAILED'}")
    print(f"  - Execution time: {result['execution_time_ms']}ms")
    print(f"  - Context changes: {len(result['context_changes'])}")

    if result.get("output"):
        print("\n  Generated Idea:")
        for key, value in result["output"].items():
            print(f"    - {key}: {str(value)[:100]}...")

    if result.get("error"):
        print(f"\n  Error: {result['error']['message']}")


def test_ceo_review_research() -> None:
    """Test CEO research review."""
    print("\n" + "=" * 80)
    print("Test 3: CEO Research Review")
    print("=" * 80)

    context = CompanyContext()
    ceo = CEOAgent(context=context)

    # Set up context with idea first
    context.update(
        "system",
        "idea",
        {
            "problem": "Small fishermen lack access to modern sales channels",
            "solution": "Digital marketplace for sustainable fishing",
            "target_market": "Small-scale fishermen and eco-conscious consumers",
        },
    )

    tester = AgentTester(output_dir=Path("./test_results"))

    # Mock research data
    test_input = {
        "research": {
            "competitors": [
                {"name": "FishMarket", "strength": "Established brand"},
                {"name": "OceanDirect", "strength": "Large user base"},
                {"name": "SustainableCatch", "strength": "Sustainability focus"},
            ],
            "market_size": {
                "tam": "$50B",
                "sam": "$5B",
                "som": "$100M",
            },
            "risks": [
                "Regulatory compliance",
                "Supply chain complexity",
                "User adoption",
            ],
        }
    }

    result = tester.test_agent(
        agent=ceo,
        test_name="ceo_review_research",
        test_function="review_research",
        test_input=test_input,
        context=context,
    )

    print(f"\n{'✓ Test PASSED' if result['success'] else '✗ Test FAILED'}")
    print(f"  - Execution time: {result['execution_time_ms']}ms")

    if result.get("output"):
        print("\n  Decision:")
        print(f"    - Decision: {result['output'].get('decision')}")
        print(f"    - Reasoning: {result['output'].get('reasoning', '')[:200]}...")
        print(f"    - Confidence: {result['output'].get('confidence')}")

    if result.get("error"):
        print(f"\n  Error: {result['error']['message']}")


def test_ceo_make_decision() -> None:
    """Test CEO decision making tool."""
    print("\n" + "=" * 80)
    print("Test 4: CEO Decision Making")
    print("=" * 80)

    context = CompanyContext()
    ceo = CEOAgent(context=context)

    # Test the make_decision tool directly
    decision = ceo._make_decision(
        decision="GO",
        reasoning="Strong market opportunity with $100M SOM, clear competitive advantages",
        confidence=0.85,
    )

    print(f"\n✓ Decision recorded: {decision}")

    # Check context
    decisions = context.get("decisions", [])
    if decisions:
        latest = decisions[-1]
        print(f"  - Decision: {latest['decision']}")
        print(f"  - Confidence: {latest['confidence']}")
        print(f"  - Reasoning: {latest['reasoning'][:100]}...")


def main() -> None:
    """Run all CEO agent tests."""
    print("\n" + "=" * 80)
    print("CEO Agent Testing Suite")
    print("=" * 80)

    try:
        # Test 1: Tools
        test_ceo_tools()

        # Test 2: Idea generation
        # Note: This requires API key and will make actual API calls
        # Uncomment to run:
        test_ceo_generate_ideas()

        # Test 3: Research review
        # Note: This requires API key and will make actual API calls
        # Uncomment to run:
        test_ceo_review_research()

        # Test 4: Decision making (no API call)
        test_ceo_make_decision()

        print("\n" + "=" * 80)
        print("All tests completed!")
        print("=" * 80)
        print("\nCheck ./test_results/ for detailed results and summaries")

    except Exception as e:
        print(f"\nError running tests: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
