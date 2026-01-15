"""Test suite for Designer Agent."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ainnovators.agents.designer import DesignerAgent
from src.ainnovators.context.shared_context import CompanyContext


def test_designer_initialization():
    """Test Designer agent initialization."""
    print("\n" + "=" * 80)
    print("Test 1: Designer Agent Initialization")
    print("=" * 80)

    context = CompanyContext()
    designer = DesignerAgent(context=context)

    assert designer.name == "Designer"
    assert designer.role == "Product Designer"
    assert designer._context is context

    print("\n✓ Designer agent initialized successfully")
    print(f"  - Name: {designer.name}")
    print(f"  - Role: {designer.role}")
    print(f"  - Image client available: {designer._image_client is not None}")


def test_designer_tools():
    """Test Designer agent tools."""
    print("\n" + "=" * 80)
    print("Test 2: Designer Agent Tools")
    print("=" * 80)

    context = CompanyContext()
    designer = DesignerAgent(context=context)

    tools = designer.get_tools()

    print(f"\n✓ Designer has {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")

    # Verify expected tools exist
    tool_names = [t["name"] for t in tools]
    assert "generate_wireframe" in tool_names
    assert "analyze_design_requirements" in tool_names
    assert "read_context" in tool_names
    assert "write_context" in tool_names

    print("\n✓ All expected tools present")


def test_analyze_design_requirements():
    """Test design requirements analysis."""
    print("\n" + "=" * 80)
    print("Test 3: Analyze Design Requirements")
    print("=" * 80)

    context = CompanyContext()
    designer = DesignerAgent(context=context)

    # Set up test context
    test_idea = {
        "problem": "Small fishermen lack access to modern sales channels",
        "solution": "Digital marketplace for sustainable fishing",
        "target_market": "Small-scale fishermen and eco-conscious consumers",
        "value_proposition": "Direct connection between fishermen and consumers",
    }

    test_research = {
        "market_analysis": "Growing demand for sustainable seafood",
        "competitors": [
            {"name": "FishMarket", "strengths": "Established brand", "weaknesses": "High fees"},
            {
                "name": "OceanDirect",
                "strengths": "Wide reach",
                "weaknesses": "Poor user experience",
            },
        ],
        "market_size": {"TAM": "$50B", "SAM": "$5B", "SOM": "$500M"},
    }

    context.update("system", "idea", test_idea)
    context.update("system", "research", test_research)

    # Test requirement analysis
    import asyncio
    import json

    result = asyncio.run(designer._analyze_design_requirements_async())
    requirements = json.loads(result)

    print("\n✓ Requirements analyzed successfully:")
    print(f"  - Target users: {requirements.get('target_users')}")
    print(f"  - Key problems: {requirements.get('key_problems')[:50]}...")
    print(f"  - Competitive insights: {len(requirements.get('competitive_insights', []))}")
    print(f"  - User needs: {len(requirements.get('user_needs', []))}")
    print(f"  - Constraints: {len(requirements.get('constraints', []))}")

    assert "target_users" in requirements
    assert "key_problems" in requirements
    assert "competitive_insights" in requirements


def test_generate_wireframe_spec():
    """Test wireframe specification generation (without image)."""
    print("\n" + "=" * 80)
    print("Test 4: Generate Wireframe Specification")
    print("=" * 80)

    context = CompanyContext()
    designer = DesignerAgent(context=context)

    # Test wireframe generation
    import asyncio
    import json

    result = asyncio.run(
        designer._generate_wireframe_async(
            screen_name="Dashboard",
            description="Main dashboard showing user metrics, activity feed, and quick actions",
            components=["Header", "Sidebar", "MetricsCard", "ActivityFeed", "CTAButton"],
        )
    )

    wireframe_result = json.loads(result)

    print("\n✓ Wireframe specification generated:")
    print(f"  - Status: {wireframe_result.get('status')}")
    print(f"  - Message: {wireframe_result.get('message')}")

    if wireframe_result.get("wireframe"):
        wireframe = wireframe_result["wireframe"]
        print(f"  - Screen: {wireframe.get('screen_name')}")
        print(f"  - Components: {len(wireframe.get('components', []))}")
        print(f"  - Image generated: {wireframe.get('image_generated', False)}")

        if wireframe.get("filepath"):
            print(f"  - Filepath: {wireframe.get('filepath')}")

    assert wireframe_result.get("status") == "success"


def test_create_design_full():
    """Test full design creation workflow (requires GEMINI_API_KEY)."""
    print("\n" + "=" * 80)
    print("Test 5: Full Design Creation Workflow")
    print("=" * 80)

    from src.ainnovators.config import config

    if not config.llm.gemini_api_key:
        print("\n⚠ Skipped - GEMINI_API_KEY not configured")
        print("  Set GEMINI_API_KEY in .env to enable this test")
        return

    context = CompanyContext()
    designer = DesignerAgent(context=context)

    # Set up test data
    test_idea = {
        "problem": "Small fishermen lack modern sales channels and fair pricing",
        "solution": "Digital marketplace connecting fishermen directly to consumers",
        "target_market": "Small-scale fishermen and eco-conscious seafood consumers",
        "value_proposition": "Fair prices for fishermen, fresh sustainable seafood for consumers",
        "novelty": "Blockchain-verified supply chain for sustainability tracking",
    }

    test_research = {
        "market_analysis": "Growing demand for sustainable seafood and supply chain transparency",
        "competitors": [
            {
                "name": "FishMarket",
                "strengths": "Established brand and distribution",
                "weaknesses": "High fees (30%) and opaque pricing",
            },
            {
                "name": "OceanDirect",
                "strengths": "Wide geographic reach",
                "weaknesses": "Poor UX and limited sustainability info",
            },
        ],
        "market_size": {"TAM": "$50B", "SAM": "$5B", "SOM": "$500M"},
        "recommendation": "GO",
    }

    context.update("system", "idea", test_idea)
    context.update("system", "research", test_research)

    print("\n⏳ Creating design (this may take 30-60 seconds)...")

    try:
        # Run design creation
        design = designer.create_design(idea=test_idea, research=test_research)

        print("\n✓ Design created successfully!")
        print("\n  Design Structure:")
        print(f"    - Design system defined: {'design_system' in design}")
        print(f"    - User flows: {len(design.get('user_flows', []))}")
        print(f"    - Wireframes: {len(design.get('wireframes', []))}")
        print(f"    - Component library: {len(design.get('component_library', []))}")

        if design.get("design_system"):
            ds = design["design_system"]
            print("\n  Design System:")
            if ds.get("colors"):
                print(f"    - Colors: {list(ds['colors'].keys())}")
            if ds.get("typography"):
                print(f"    - Typography: {list(ds['typography'].keys())}")
            if ds.get("components"):
                print(f"    - Components: {len(ds['components'])} defined")

        if design.get("user_flows"):
            print("\n  User Flows:")
            for flow in design["user_flows"][:2]:  # Show first 2
                print(f"    - {flow.get('flow_name')}: {len(flow.get('steps', []))} steps")

        if design.get("wireframes"):
            print("\n  Wireframes:")
            for wf in design["wireframes"]:
                print(f"    - {wf.get('screen_name')}")
                if wf.get("filepath"):
                    print(f"      → {wf['filepath']}")

        if design.get("design_rationale"):
            rationale = design["design_rationale"]
            print(f"\n  Design Rationale: {len(rationale)} chars")
            print(f"    {rationale[:150]}...")

        # Verify design was saved to context
        saved_design = context.get("design")
        assert saved_design is not None, "Design not saved to context"
        print("\n✓ Design successfully saved to shared context")

    except Exception as e:
        print(f"\n✗ Design creation failed: {e}")
        import traceback

        traceback.print_exc()
        raise


def test_legacy_methods():
    """Test legacy methods for backward compatibility."""
    print("\n" + "=" * 80)
    print("Test 6: Legacy Methods")
    print("=" * 80)

    context = CompanyContext()
    designer = DesignerAgent(context=context)

    # Test design_user_flow
    flow = designer.design_user_flow("User Registration")
    print("\n✓ design_user_flow() works:")
    print(f"  - Flow name: {flow.get('flow_name')}")
    print(f"  - Steps: {len(flow.get('steps', []))}")

    # Test create_component_library
    lib = designer.create_component_library()
    print("\n✓ create_component_library() works:")
    print(f"  - Components: {len(lib.get('components', []))}")
    for comp in lib["components"][:2]:
        print(f"    - {comp.get('component_name')}")


def run_all_tests():
    """Run all Designer agent tests."""
    print("\n" + "=" * 80)
    print("Designer Agent Test Suite")
    print("=" * 80)

    tests = [
        ("Initialization", test_designer_initialization),
        ("Tools", test_designer_tools),
        ("Analyze Requirements", test_analyze_design_requirements),
        ("Generate Wireframe Spec", test_generate_wireframe_spec),
        ("Legacy Methods", test_legacy_methods),
        ("Full Design Creation", test_create_design_full),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ Test '{test_name}' failed: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
