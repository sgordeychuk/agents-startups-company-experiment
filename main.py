#!/usr/bin/env python3
"""CLI entry point for AI Innovators."""

import json
import logging
import sys
from pathlib import Path

import click

from src.ainnovators.config import ModeConfig, config
from src.ainnovators.context import CompanyContext, ContextObserver
from src.ainnovators.orchestrator import StartupCompany, StartupPipeline
from src.ainnovators.utils import AgentTester

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.logging.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.logging.log_file),
        logging.StreamHandler() if config.logging.log_to_console else logging.NullHandler(),
    ],
)

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """AI Innovators - Multi-agent AI startup company simulation."""
    pass


@cli.command()
@click.option("--name", "-n", required=True, help="Experiment name")
def init(name: str) -> None:
    """Initialize a new experiment."""
    experiments_dir = config.storage.experiments_dir
    experiment_path = experiments_dir / name

    if experiment_path.exists():
        click.echo(f"Error: Experiment '{name}' already exists", err=True)
        sys.exit(1)

    experiment_path.mkdir(parents=True)
    (experiment_path / "context.json").write_text("{}")
    (experiment_path / "logs").mkdir()

    click.echo(f"Initialized experiment: {name}")
    click.echo(f"  Path: {experiment_path}")


@cli.command()
@click.option("--input", "-i", "input_text", required=True, help="Chairman input")
@click.option("--name", "-n", default="experiment", help="Experiment name prefix")
@click.option("--observe", "-o", is_flag=True, help="Enable verbose observation")
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["standard", "extended"]),
    default="standard",
    help="Execution mode: standard (fast, research-focused) or extended (full prototype, showcase quality)",
)
def run(input_text: str, name: str, observe: bool, mode: str) -> None:
    """Run the startup pipeline."""
    mode_config = ModeConfig.extended() if mode == "extended" else ModeConfig.standard()

    try:
        company = StartupCompany(name=name, mode_config=mode_config)
        click.echo(f"Starting experiment: {company.name}")
        click.echo(f"Execution mode: {mode.upper()}")
        click.echo(f"Experiment directory: {company.experiment_dir}")
        click.echo(f"Input: {input_text[:100]}...")

        result = company.run_experiment(chairman_input=input_text)

        if observe:
            click.echo("\n--- Context Snapshot ---")
            ContextObserver.print_context_tree(company.pipeline.context)

        click.echo("\n--- Pipeline Status ---")
        pipeline_status = company.pipeline.get_status()
        click.echo(f"Completed stages: {pipeline_status['completed_stages']}")
        click.echo(f"Current stage: {pipeline_status['current_stage']}")

        # Display pipeline statistics
        company.pipeline.print_statistics()

        click.echo(f"\nAll outputs saved to: {company.experiment_dir}")

    except NotImplementedError as e:
        click.echo(f"\nNote: Pipeline stages not yet implemented: {e}")
        click.echo("This is a skeleton project. Implement the stages to run the full pipeline.")


@cli.command()
@click.option("--experiment", "-e", required=True, help="Experiment name")
@click.option("--stage", "-s", help="Filter by stage")
def inspect(experiment: str, stage: str | None) -> None:
    """Inspect experiment context."""
    experiment_dir = config.storage.experiments_dir / experiment

    if not experiment_dir.exists():
        click.echo(f"Error: Experiment directory not found: {experiment_dir}", err=True)
        sys.exit(1)

    if stage:
        context_path = experiment_dir / f"context_{stage}.json"
    else:
        context_path = experiment_dir / "context_final.json"

    if not context_path.exists():
        click.echo(f"Error: Context file not found: {context_path}", err=True)
        sys.exit(1)

    context = CompanyContext.load_from_file(str(context_path))

    if stage:
        click.echo(f"\n--- Stage: {stage} ---")
        summary = ContextObserver.get_stage_summary(context, stage)
        click.echo(json.dumps(summary, indent=2, default=str))
    else:
        click.echo("\n--- Full Context ---")
        ContextObserver.print_context_tree(context)


@cli.command()
@click.option("--experiment", "-e", required=True, help="Experiment name")
@click.option("--from-stage", "-f", required=True, help="Stage to start from")
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["standard", "extended"]),
    default="standard",
    help="Execution mode: standard (fast, research-focused) or extended (full prototype, showcase quality)",
)
def replay(experiment: str, from_stage: str, mode: str) -> None:
    """Replay experiment from a specific stage."""
    experiment_dir = config.storage.experiments_dir / experiment

    if not experiment_dir.exists():
        click.echo(f"Error: Experiment directory not found: {experiment_dir}", err=True)
        sys.exit(1)

    stage_order = ["idea_development", "prototyping", "pitch"]
    if from_stage not in stage_order:
        click.echo(f"Error: Unknown stage '{from_stage}'. Valid stages: {stage_order}", err=True)
        sys.exit(1)

    stage_index = stage_order.index(from_stage)
    if stage_index == 0:
        context_path = experiment_dir / "context_final.json"
        if not context_path.exists():
            click.echo("Error: Cannot replay from first stage without existing context", err=True)
            click.echo("Use 'run' command to start a new experiment instead", err=True)
            sys.exit(1)
    else:
        previous_stage = stage_order[stage_index - 1]
        context_path = experiment_dir / f"context_{previous_stage}.json"

    if not context_path.exists():
        click.echo(f"Error: Context file not found: {context_path}", err=True)
        sys.exit(1)

    mode_config = ModeConfig.extended() if mode == "extended" else ModeConfig.standard()

    click.echo(f"Replaying from stage: {from_stage}")
    click.echo(f"Execution mode: {mode.upper()}")

    try:
        pipeline = StartupPipeline(mode_config=mode_config)
        result = pipeline.run_from_stage(from_stage, str(context_path))

        click.echo("\n--- Pipeline Status ---")
        status = pipeline.get_status()
        click.echo(f"Completed stages: {status['completed_stages']}")

    except NotImplementedError as e:
        click.echo(f"\nNote: Pipeline stages not yet implemented: {e}")


@cli.command()
@click.option("--experiment", "-e", required=True, help="Experiment name")
@click.option("--format", "-f", "output_format", default="markdown", help="Output format")
@click.option("--output", "-o", help="Output file path")
def export(experiment: str, output_format: str, output: str | None) -> None:
    """Export experiment results."""
    experiment_dir = config.storage.experiments_dir / experiment

    if not experiment_dir.exists():
        click.echo(f"Error: Experiment directory not found: {experiment_dir}", err=True)
        sys.exit(1)

    context_path = experiment_dir / "context_final.json"
    if not context_path.exists():
        click.echo(f"Error: Context file not found: {context_path}", err=True)
        sys.exit(1)

    context = CompanyContext.load_from_file(str(context_path))

    if output_format == "markdown":
        content = _export_markdown(context)
    elif output_format == "json":
        content = json.dumps(context.snapshot(), indent=2, default=str)
    elif output_format == "timeline":
        output_file = output or f"{experiment}_timeline.json"
        ContextObserver.export_timeline(context, output_file)
        click.echo(f"Timeline exported to: {output_file}")
        return
    else:
        click.echo(f"Error: Unknown format: {output_format}", err=True)
        sys.exit(1)

    if output:
        Path(output).write_text(content)
        click.echo(f"Exported to: {output}")
    else:
        click.echo(content)


def _export_markdown(context: CompanyContext) -> str:
    """Export context to markdown format."""
    lines = [
        "# Experiment Results",
        "",
        "## Summary",
        f"- Completed stages: {context.get('completed_stages', [])}",
        f"- Total iterations: {context.get('iterations', 0)}",
        "",
        "## Idea",
        "```json",
        json.dumps(context.get("idea"), indent=2, default=str),
        "```",
        "",
        "## Research",
        "```json",
        json.dumps(context.get("research"), indent=2, default=str),
        "```",
        "",
        "## Prototype",
        "```json",
        json.dumps(context.get("prototype"), indent=2, default=str),
        "```",
        "",
        "## Decisions",
        "",
    ]

    for decision in context.get("decisions", []):
        lines.append(f"- {decision}")

    return "\n".join(lines)


@cli.command()
def status() -> None:
    """Show system status."""
    click.echo("AI Innovators Status")
    click.echo("=" * 40)
    click.echo("Config loaded: Yes")
    click.echo(f"Primary model: {config.llm.primary_model}")
    click.echo(f"Secondary model: {config.llm.secondary_model}")
    click.echo(f"API key configured: {'Yes' if config.llm.anthropic_api_key else 'No'}")
    click.echo(f"Experiments dir: {config.storage.experiments_dir}")
    click.echo(f"Log level: {config.logging.log_level}")


@cli.command()
@click.option(
    "--stage",
    "-s",
    required=True,
    type=click.Choice(["idea_development", "prototyping", "documentation"]),
    help="Stage to run",
)
@click.option("--input", "-i", "input_text", required=True, help="Input for the stage")
@click.option(
    "--context",
    "-c",
    "context_file",
    help="Optional context file to load (for stages that need previous context)",
)
@click.option("--name", "-n", default="stage_run", help="Experiment name prefix")
@click.option(
    "--output",
    "-o",
    "output_file",
    help="Output file for results (default: saves to experiment dir)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    default="json",
    type=click.Choice(["json", "markdown"]),
    help="Output format",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["standard", "extended"]),
    default="standard",
    help="Execution mode: standard (fast) or extended (full prototype)",
)
def run_stage(
    stage: str,
    input_text: str,
    context_file: str | None,
    name: str,
    output_file: str | None,
    output_format: str,
    mode: str,
) -> None:
    """Run a single stage for debugging (isolates stage execution)."""
    from datetime import datetime

    click.echo(f"Running stage: {stage}")
    click.echo(f"Input: {input_text[:100]}...")

    mode_config = ModeConfig.extended() if mode == "extended" else ModeConfig.standard()
    click.echo(f"Execution mode: {mode.upper()}")

    try:
        # Create timestamped experiment directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_dir = config.storage.experiments_dir / f"{name}_{stage}_{timestamp}"

        # Initialize pipeline with experiment directory and mode config
        pipeline = StartupPipeline(experiment_dir=experiment_dir, mode_config=mode_config)

        # Start experiment logging (captures all output to logs folder)
        pipeline.experiment_logger.start()

        try:
            click.echo(f"Experiment directory: {experiment_dir}")

            # Load context if provided, otherwise use pipeline's context
            if context_file and Path(context_file).exists():
                click.echo(f"Loading context from: {context_file}")
                loaded_context = CompanyContext.load_from_file(context_file)
                # Copy loaded context state to pipeline's context
                pipeline.context.state = loaded_context.state
                pipeline.context.stage_contexts = loaded_context.stage_contexts
                pipeline.context.history = loaded_context.history
                # Re-set experiment_dir in context (may have been overwritten)
                pipeline.context.update("system", "experiment_dir", str(experiment_dir))
                pipeline.context.update("system", "experiment_name", experiment_dir.name)
            else:
                click.echo("Creating fresh context")

            # Store input in pipeline's context
            pipeline.context.update("system", "chairman_input", input_text)
            pipeline.context.update("system", "current_stage", stage)

            # Get the specific stage
            stage_instance = pipeline.get_stage(stage)
            if not stage_instance:
                click.echo(f"Error: Stage '{stage}' not found", err=True)
                sys.exit(1)

            # Run the stage
            click.echo(f"\n--- Running {stage} ---")
            try:
                success = stage_instance.run()
                click.echo(f"\nStage completed: {'✓ Success' if success else '✗ Failed'}")
            except NotImplementedError as e:
                click.echo(f"\nNote: Stage not yet implemented: {e}")
                success = False

            # Get results
            snapshot = pipeline.context.snapshot()
            stage_output = snapshot.get("stage_outputs", {}).get(stage, {})

            # Save context to experiment directory
            context_output = experiment_dir / f"context_{stage}.json"
            pipeline.context.save_to_file(str(context_output))
            click.echo(f"Context saved to: {context_output}")

            # Format output
            if output_format == "json":
                output_content = json.dumps(
                    {
                        "stage": stage,
                        "input": input_text,
                        "success": success,
                        "experiment_dir": str(experiment_dir),
                        "stage_output": stage_output,
                        "full_context": snapshot,
                    },
                    indent=2,
                    default=str,
                )
            else:  # markdown
                output_content = f"""# Stage: {stage}

## Experiment
Directory: {experiment_dir}

## Input
{input_text}

## Status
{"✓ Success" if success else "✗ Failed"}

## Stage Output
```json
{json.dumps(stage_output, indent=2, default=str)}
```

## Full Context
```json
{json.dumps(snapshot, indent=2, default=str)}
```
"""

            # Output results
            if output_file:
                Path(output_file).write_text(output_content)
                click.echo(f"\nResults saved to: {output_file}")
            else:
                # Save to experiment directory by default
                result_file = (
                    experiment_dir / f"results.{output_format if output_format == 'json' else 'md'}"
                )
                result_file.write_text(output_content)
                click.echo(f"\nResults saved to: {result_file}")

            click.echo(f"\nAll outputs saved to: {experiment_dir}")
            click.echo(f"Logs saved to: {pipeline.experiment_logger.log_path}")

        finally:
            # Stop experiment logging
            pipeline.experiment_logger.stop()

    except Exception as e:
        click.echo(f"\nError running stage: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option(
    "--agent",
    "-a",
    required=True,
    type=click.Choice(
        [
            "ceo",
            "researcher",
            "legal_advisor",
            "developer",
            "designer",
            "qa",
            "marketer",
            "deck_strategist",
            "tech_writer",
        ]
    ),
    help="Agent to test (tech_writer is alias for deck_strategist)",
)
@click.option(
    "--method",
    "-m",
    help="Method to test (e.g., 'generate_ideas', 'review_research')",
)
@click.option(
    "--input",
    "-i",
    "input_json",
    help='JSON input for the method (e.g., \'{"chairman_input": "Create a fintech app"}\')',
)
@click.option(
    "--test-tools",
    "-t",
    is_flag=True,
    help="Test agent tools instead of running a method",
)
@click.option(
    "--conversation",
    "-c",
    help="Test with conversation (JSON file with messages)",
)
@click.option(
    "--output-dir",
    "-o",
    default="./test_results",
    help="Output directory for test results",
)
def test_agent(
    agent: str,
    method: str | None,
    input_json: str | None,
    test_tools: bool,
    conversation: str | None,
    output_dir: str,
) -> None:
    """Test an individual agent for debugging."""
    click.echo(f"Testing agent: {agent}")

    try:
        # Create context
        context = CompanyContext()

        # Import and create the agent
        if agent == "ceo":
            from src.ainnovators.agents import CEOAgent

            agent_instance = CEOAgent(context=context)
        elif agent == "researcher":
            from src.ainnovators.agents import ResearcherAgent

            agent_instance = ResearcherAgent(context=context)
        elif agent == "legal_advisor":
            from src.ainnovators.agents import LegalAdvisorAgent

            agent_instance = LegalAdvisorAgent(context=context)
        elif agent == "developer":
            from src.ainnovators.agents import DeveloperAgent

            agent_instance = DeveloperAgent(context=context)
        elif agent == "designer":
            from src.ainnovators.agents import DesignerAgent

            agent_instance = DesignerAgent(context=context)
        elif agent == "qa":
            from src.ainnovators.agents import QAAgent

            agent_instance = QAAgent(context=context)
        elif agent == "marketer":
            from src.ainnovators.agents import MarketerAgent

            agent_instance = MarketerAgent(context=context)
        elif agent in ("deck_strategist", "tech_writer"):
            from src.ainnovators.agents import DeckStrategistAgent

            agent_instance = DeckStrategistAgent(context=context)
        else:
            click.echo(f"Error: Unknown agent: {agent}", err=True)
            sys.exit(1)

        # Create tester
        tester = AgentTester(output_dir=Path(output_dir))

        # Run appropriate test
        if test_tools:
            # Test tools
            click.echo(f"\n--- Testing {agent} tools ---")
            result = tester.test_agent_tools(
                agent=agent_instance,
                test_name=f"{agent}_tools",
                context=context,
            )
            click.echo("\n✓ Tools test completed")
            click.echo(f"  - Tools: {result.get('tool_count', 0)}")
            click.echo(f"  - Functions: {result.get('function_count', 0)}")

        elif conversation:
            # Test conversation
            click.echo(f"\n--- Testing {agent} conversation ---")
            with open(conversation) as f:
                messages = json.load(f)

            result = tester.test_agent_conversation(
                agent=agent_instance,
                test_name=f"{agent}_conversation",
                messages=messages,
                context=context,
            )
            click.echo(f"\n{'✓ Test PASSED' if result['success'] else '✗ Test FAILED'}")
            click.echo(f"  - Messages: {len(result.get('messages', []))}")
            click.echo(f"  - Responses: {len(result.get('responses', []))}")
            click.echo(f"  - Execution time: {result.get('execution_time_ms', 0)}ms")

        elif method:
            # Test specific method
            if not input_json:
                click.echo("Error: --input required when testing a method", err=True)
                sys.exit(1)

            click.echo(f"\n--- Testing {agent}.{method}() ---")

            # Parse input JSON
            try:
                test_input = json.loads(input_json)
            except json.JSONDecodeError as e:
                click.echo(f"Error: Invalid JSON input: {e}", err=True)
                sys.exit(1)

            result = tester.test_agent(
                agent=agent_instance,
                test_name=f"{agent}_{method}",
                test_function=method,
                test_input=test_input,
                context=context,
            )

            click.echo(f"\n{'✓ Test PASSED' if result['success'] else '✗ Test FAILED'}")
            click.echo(f"  - Execution time: {result.get('execution_time_ms', 0)}ms")
            click.echo(f"  - Context changes: {len(result.get('context_changes', []))}")

            if result.get("error"):
                click.echo(f"\nError: {result['error']['message']}")

        else:
            click.echo("Error: Must specify --method, --test-tools, or --conversation", err=True)
            sys.exit(1)

        # Show output location
        click.echo(f"\nResults saved to: {output_dir}")
        click.echo(f"  - Full results: {output_dir}/{result.get('test_name', 'test')}_*.json")
        click.echo(f"  - Summary: {output_dir}/{result.get('test_name', 'test')}_latest.txt")

    except Exception as e:
        click.echo(f"\nError running test: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command("test-all-agents")
@click.option(
    "--output-dir",
    "-o",
    default="./test_results",
    help="Output directory for test results",
)
def test_all_agents(output_dir: str) -> None:
    """Test tools for all agents at once."""
    from src.ainnovators.agents import (
        CEOAgent,
        DeckStrategistAgent,
        DesignerAgent,
        DeveloperAgent,
        LegalAdvisorAgent,
        MarketerAgent,
        QAAgent,
        ResearcherAgent,
    )

    click.echo("Testing all agents...")
    click.echo("=" * 60)

    context = CompanyContext()
    tester = AgentTester(output_dir=Path(output_dir))

    agents = [
        ("ceo", CEOAgent),
        ("researcher", ResearcherAgent),
        ("legal_advisor", LegalAdvisorAgent),
        ("developer", DeveloperAgent),
        ("designer", DesignerAgent),
        ("qa", QAAgent),
        ("marketer", MarketerAgent),
        ("deck_strategist", DeckStrategistAgent),
    ]

    results = []
    for agent_name, agent_class in agents:
        click.echo(f"\n--- Testing {agent_name} ---")
        try:
            agent_instance = agent_class(context=context)
            result = tester.test_agent_tools(
                agent=agent_instance,
                test_name=f"{agent_name}_tools",
                context=context,
            )
            results.append(
                {
                    "agent": agent_name,
                    "success": result.get("success", False),
                    "tools": result.get("tool_count", 0),
                    "functions": result.get("function_count", 0),
                    "error": result.get("error"),
                }
            )
            status = "✓" if result.get("success") else "✗"
            click.echo(
                f"  {status} Tools: {result.get('tool_count', 0)}, Functions: {result.get('function_count', 0)}"
            )
        except Exception as e:
            results.append(
                {
                    "agent": agent_name,
                    "success": False,
                    "error": str(e),
                }
            )
            click.echo(f"  ✗ Error: {e}")

    # Summary
    click.echo("\n" + "=" * 60)
    click.echo("SUMMARY")
    click.echo("=" * 60)
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    click.echo(f"Passed: {passed}/{len(results)}")
    click.echo(f"Failed: {failed}/{len(results)}")

    if failed > 0:
        click.echo("\nFailed agents:")
        for r in results:
            if not r["success"]:
                click.echo(f"  - {r['agent']}: {r.get('error', 'Unknown error')}")

    click.echo(f"\nResults saved to: {output_dir}")


@cli.command()
@click.option(
    "--experiment",
    "-e",
    required=True,
    help="Experiment directory path or name",
)
@click.option(
    "--action",
    "-a",
    required=True,
    type=click.Choice(["build", "start", "stop", "status", "logs", "restart"]),
    help="Docker action to perform",
)
@click.option(
    "--service",
    "-s",
    type=click.Choice(["frontend", "backend"]),
    help="Service for logs action (optional)",
)
@click.option(
    "--tail",
    "-t",
    default=100,
    help="Number of log lines to show",
)
def docker(experiment: str, action: str, service: str | None, tail: int) -> None:
    """Manage Docker containers for a prototype."""
    from src.ainnovators.utils.docker_manager import DockerManager

    # Resolve experiment path
    experiment_path = Path(experiment)
    if not experiment_path.is_absolute():
        # Try as experiment name in experiments directory
        experiment_path = config.storage.experiments_dir / experiment

    prototype_dir = experiment_path / "prototype"

    if not prototype_dir.exists():
        click.echo(f"Error: No prototype found at {prototype_dir}", err=True)
        click.echo("Make sure the prototyping stage has been run first.", err=True)
        sys.exit(1)

    manager = DockerManager(prototype_dir)

    if action == "build":
        click.echo(f"Building Docker images for {experiment}...")
        if manager.build():
            click.echo("Build completed successfully.")
        else:
            click.echo("Build failed. Check logs above.", err=True)
            sys.exit(1)

    elif action == "start":
        click.echo(f"Starting containers for {experiment}...")
        if manager.start():
            click.echo("\nPrototype started successfully!")
            click.echo("  Frontend: http://localhost:3000")
            click.echo("  Backend:  http://localhost:8000")
            click.echo("  API Docs: http://localhost:8000/docs")
        else:
            click.echo("Failed to start containers. Try running 'build' first.", err=True)
            sys.exit(1)

    elif action == "stop":
        click.echo(f"Stopping containers for {experiment}...")
        if manager.stop():
            click.echo("Containers stopped successfully.")
        else:
            click.echo("Failed to stop containers.", err=True)
            sys.exit(1)

    elif action == "status":
        status = manager.status()
        click.echo(f"Prototype status for {experiment}:")
        click.echo(f"  Running: {'Yes' if status['running'] else 'No'}")

        if status.get("services"):
            click.echo("  Services:")
            for svc in status["services"]:
                name = svc.get("Service") or svc.get("Name", "unknown")
                state = svc.get("State") or svc.get("Status", "unknown")
                click.echo(f"    - {name}: {state}")

        if status.get("error"):
            click.echo(f"  Error: {status['error']}")

    elif action == "logs":
        click.echo(f"Fetching logs (tail={tail})...")
        logs = manager.logs(service=service, tail=tail)
        click.echo(logs)

    elif action == "restart":
        click.echo(f"Restarting containers for {experiment}...")
        if manager.restart():
            click.echo("\nPrototype restarted successfully!")
            click.echo("  Frontend: http://localhost:3000")
            click.echo("  Backend:  http://localhost:8000")
        else:
            click.echo("Failed to restart containers.", err=True)
            sys.exit(1)


if __name__ == "__main__":
    cli()
