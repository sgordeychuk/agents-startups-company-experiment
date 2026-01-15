"""Example: Testing the Researcher agent with various scenarios."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ainnovators.agents import ResearcherAgent
from src.ainnovators.context import CompanyContext
from src.ainnovators.utils import AgentTester


def test_researcher_tools() -> None:
    """Test Researcher agent tools availability."""
    print("\n" + "=" * 80)
    print("Test 1: Researcher Agent Tools")
    print("=" * 80)

    context = CompanyContext()
    researcher = ResearcherAgent(context=context)

    tester = AgentTester(output_dir=Path("./test_results"))
    result = tester.test_agent_tools(
        agent=researcher,
        test_name="researcher_tools_test",
        context=context,
    )

    print("\n✓ Test completed")
    print(f"  - Tools: {result['tool_count']}")
    print(f"  - Functions: {result['function_count']}")
    print(f"  - Tool names: {[t['name'] for t in result['tools']]}")


def test_researcher_research_idea() -> None:
    """Test Researcher comprehensive idea research."""
    print("\n" + "=" * 80)
    print("Test 2: Researcher Idea Research")
    print("=" * 80)

    context = CompanyContext()
    researcher = ResearcherAgent(context=context)

    tester = AgentTester(output_dir=Path("./test_results"))

    # Test input - realistic startup idea
    test_input = {
        "idea": {
            "problem": "Gen Z students struggle with financial literacy and lack accessible tools to learn money management",
            "solution": "AI-powered financial education app with gamified learning, personalized budgeting, and micro-investment features",
            "target_market": "Gen Z students and young professionals (ages 16-25) in the US",
            "value_proposition": "Learn financial skills through interactive games while building real savings habits",
            "novelty": "Combines behavioral psychology, AI personalization, and social features to make finance engaging for Gen Z",
        }
    }

    result = tester.test_agent(
        agent=researcher,
        test_name="researcher_research_idea",
        test_function="research_idea",
        test_input=test_input,
        context=context,
    )

    print(f"\n{'✓ Test PASSED' if result['success'] else '✗ Test FAILED'}")
    print(f"  - Execution time: {result['execution_time_ms']}ms")
    print(f"  - Context changes: {len(result['context_changes'])}")

    if result.get("output"):
        print("\n  Research Findings:")
        output = result["output"]

        if output.get("market_analysis"):
            print(f"    - Market Analysis: {str(output['market_analysis'])[:150]}...")

        if output.get("competitors"):
            print(f"    - Competitors Found: {len(output['competitors'])}")
            for comp in output["competitors"][:3]:
                if isinstance(comp, dict):
                    print(
                        f"      • {comp.get('name', 'Unknown')}: {str(comp.get('description', ''))[:80]}..."
                    )

        if output.get("market_size"):
            ms = output["market_size"]
            if isinstance(ms, dict):
                print("    - Market Size:")
                print(f"      • TAM: {ms.get('TAM', 'N/A')}")
                print(f"      • SAM: {ms.get('SAM', 'N/A')}")
                print(f"      • SOM: {ms.get('SOM', 'N/A')}")

        if output.get("risks"):
            print(f"    - Risks Identified: {len(output['risks'])}")

        if output.get("opportunities"):
            print(f"    - Opportunities: {len(output['opportunities'])}")

        if output.get("recommendation"):
            print(f"    - Recommendation: {output['recommendation']}")
            if output.get("reasoning"):
                print(f"    - Reasoning: {str(output['reasoning'])[:150]}...")

    if result.get("error"):
        print(f"\n  Error: {result['error']['message']}")


def test_researcher_analyze_competitors() -> None:
    """Test Researcher competitor analysis."""
    print("\n" + "=" * 80)
    print("Test 3: Researcher Competitor Analysis")
    print("=" * 80)

    context = CompanyContext()
    researcher = ResearcherAgent(context=context)

    tester = AgentTester(output_dir=Path("./test_results"))

    # Test input - market to analyze
    test_input = {"market": "AI-powered financial education apps for Gen Z"}

    result = tester.test_agent(
        agent=researcher,
        test_name="researcher_analyze_competitors",
        test_function="analyze_competitors",
        test_input=test_input,
        context=context,
    )

    print(f"\n{'✓ Test PASSED' if result['success'] else '✗ Test FAILED'}")
    print(f"  - Execution time: {result['execution_time_ms']}ms")

    if result.get("output"):
        competitors = result["output"]
        print(f"\n  Competitors Found: {len(competitors)}")

        for i, comp in enumerate(competitors[:5], 1):
            if isinstance(comp, dict):
                print(f"\n  {i}. {comp.get('name', 'Unknown')}")
                print(f"     Description: {str(comp.get('description', 'N/A'))[:100]}...")
                print(f"     Strengths: {str(comp.get('strengths', 'N/A'))[:80]}...")
                print(f"     Weaknesses: {str(comp.get('weaknesses', 'N/A'))[:80]}...")

    if result.get("error"):
        print(f"\n  Error: {result['error']['message']}")


def test_researcher_calculate_market_size() -> None:
    """Test Researcher market size calculation."""
    print("\n" + "=" * 80)
    print("Test 4: Researcher Market Size Calculation")
    print("=" * 80)

    context = CompanyContext()
    researcher = ResearcherAgent(context=context)

    tester = AgentTester(output_dir=Path("./test_results"))

    # Test input - market to size
    test_input = {"market": "Financial education apps for young adults in the United States"}

    result = tester.test_agent(
        agent=researcher,
        test_name="researcher_calculate_market_size",
        test_function="calculate_market_size",
        test_input=test_input,
        context=context,
    )

    print(f"\n{'✓ Test PASSED' if result['success'] else '✗ Test FAILED'}")
    print(f"  - Execution time: {result['execution_time_ms']}ms")

    if result.get("output"):
        market_size = result["output"]
        print("\n  Market Sizing:")

        if isinstance(market_size, dict):
            print(f"    - TAM: {market_size.get('TAM', 'N/A')}")
            print(f"    - SAM: {market_size.get('SAM', 'N/A')}")
            print(f"    - SOM: {market_size.get('SOM', 'N/A')}")

            if market_size.get("sources"):
                print(f"    - Sources: {str(market_size['sources'])[:150]}...")

            if market_size.get("growth_rate"):
                print(f"    - Growth Rate: {market_size['growth_rate']}")

            if market_size.get("notes"):
                print(f"    - Notes: {str(market_size['notes'])[:150]}...")

    if result.get("error"):
        print(f"\n  Error: {result['error']['message']}")


def test_researcher_assess_risks() -> None:
    """Test Researcher risk assessment."""
    print("\n" + "=" * 80)
    print("Test 5: Researcher Risk Assessment")
    print("=" * 80)

    context = CompanyContext()
    researcher = ResearcherAgent(context=context)

    tester = AgentTester(output_dir=Path("./test_results"))

    # Test input - idea to assess risks for
    test_input = {
        "idea": {
            "problem": "Gen Z students struggle with financial literacy",
            "solution": "AI-powered financial education app with gamified learning",
            "target_market": "Gen Z students and young professionals (ages 16-25)",
            "value_proposition": "Learn financial skills through interactive games",
            "novelty": "Combines behavioral psychology, AI personalization, and social features",
        }
    }

    result = tester.test_agent(
        agent=researcher,
        test_name="researcher_assess_risks",
        test_function="assess_risks",
        test_input=test_input,
        context=context,
    )

    print(f"\n{'✓ Test PASSED' if result['success'] else '✗ Test FAILED'}")
    print(f"  - Execution time: {result['execution_time_ms']}ms")

    if result.get("output"):
        risks = result["output"]
        print(f"\n  Risks Identified: {len(risks)}")

        # Group risks by category
        risk_categories = {}
        for risk in risks:
            if isinstance(risk, dict):
                category = risk.get("category", "Unknown")
                if category not in risk_categories:
                    risk_categories[category] = []
                risk_categories[category].append(risk)

        for category, category_risks in risk_categories.items():
            print(f"\n  {category}:")
            for risk in category_risks[:2]:  # Show first 2 per category
                print(f"    • {risk.get('description', 'N/A')[:100]}...")
                print(
                    f"      Severity: {risk.get('severity', 'N/A')} | Likelihood: {risk.get('likelihood', 'N/A')}"
                )
                if risk.get("mitigation"):
                    print(f"      Mitigation: {str(risk['mitigation'])[:80]}...")

    if result.get("error"):
        print(f"\n  Error: {result['error']['message']}")


def test_researcher_deep_research() -> None:
    """Test Researcher deep research tool directly."""
    print("\n" + "=" * 80)
    print("Test 6: Researcher Deep Research Tool")
    print("=" * 80)

    context = CompanyContext()
    researcher = ResearcherAgent(context=context)

    # Test the deep_research tool directly (sync version)
    print("\n  Testing shallow depth...")
    result_shallow = researcher._deep_research(
        topic="Gen Z financial literacy trends", depth="shallow"
    )
    print(f"  ✓ Shallow research completed ({len(result_shallow)} characters)")

    print("\n  Testing medium depth...")
    result_medium = researcher._deep_research(
        topic="Financial education app market", depth="medium"
    )
    print(f"  ✓ Medium research completed ({len(result_medium)} characters)")

    # Show a sample of the results
    print("\n  Sample output (first 300 chars):")
    print(f"  {result_medium[:300]}...")


def test_researcher_web_search() -> None:
    """Test Researcher web search tool directly."""
    print("\n" + "=" * 80)
    print("Test 7: Researcher Web Search Tool")
    print("=" * 80)

    context = CompanyContext()
    researcher = ResearcherAgent(context=context)

    # Test the web_search tool directly (sync version)
    query = "Gen Z financial literacy statistics 2025"
    print(f"\n  Searching for: {query}")

    result = researcher._web_search(query)

    print(f"  ✓ Search completed ({len(result)} characters)")
    print("\n  Sample output (first 400 chars):")
    print(f"  {result[:400]}...")


def main() -> None:
    """Run all Researcher agent tests."""
    print("\n" + "=" * 80)
    print("Researcher Agent Testing Suite")
    print("=" * 80)
    print("\nNOTE: Tests 2-7 require API keys (ANTHROPIC_API_KEY, SERPER_API_KEY)")
    print("and will make actual API calls. Comment out to skip.")

    try:
        # Test 1: Tools (no API call)
        test_researcher_tools()

        # Test 2: Research idea (requires API keys)
        # Uncomment to run:
        test_researcher_research_idea()

        # Test 3: Competitor analysis (requires API keys)
        # Uncomment to run:
        test_researcher_analyze_competitors()

        # Test 4: Market size calculation (requires API keys)
        # Uncomment to run:
        test_researcher_calculate_market_size()

        # Test 5: Risk assessment (requires API keys)
        # Uncomment to run:
        test_researcher_assess_risks()

        # Test 6: Deep research tool (requires SERPER_API_KEY)
        # Uncomment to run:
        test_researcher_deep_research()

        # Test 7: Web search tool (requires SERPER_API_KEY)
        # Uncomment to run:
        test_researcher_web_search()

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
