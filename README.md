# Startup Company experiment 

Multi-agent AI system simulating a company which generated startups.
This project is build as part of the experiment written in this article:

⚠️IMPORTANT: this is not production-ready software. It is an experiment demonstrating multi-agent AI capabilities using AutoGen. 
It might not be stable and might not even work anymore as everything is evolving fast in this space.
Use at your own risk!

## Overview

"AI Innovators" is a multi-agent system where AI agents collaborate to create, validate, and prototype startup ideas. The system simulates a startup company with the following roles:

| Agent | Competency | Authority |
|-------|-----------|-----------|
| **CEO** | Strategic vision, resource allocation | Go/no-go decisions |
| **Researcher** | Market research, data synthesis | Validation recommendations |
| **Legal Advisor** | IP, regulatory, privacy, liability analysis | Legal risk assessment |
| **Developer** | Architecture, code generation | Technical feasibility |
| **Designer** | UI/UX design, visual prototyping | Design direction |
| **QA** | Testing, edge case identification | Quality gates |
| **Marketer** | Go-to-market strategy, channel analysis | Marketing direction |
| **Deck Strategist** | Pitch decks, storytelling | Final pitch narrative |

## Architecture

- **Framework**: AutoGen 0.4+ (autogen-agentchat + autogen-ext)
- **Pattern**: Hybrid Staged Pipeline (sequential stages with collaboration within stages)
- **Communication**: Shared Context Pool
- **Model Provider**: Anthropic Claude (via AnthropicChatCompletionClient)

### Project Structure

```
ainnovators/
├── src/ainnovators/          # Main package
│   ├── agents/               # Agent implementations
│   ├── context/              # Shared context pool
│   ├── stages/               # Pipeline stages
│   ├── utils/                # Utilities
│   ├── orchestrator.py       # Pipeline orchestration
│   └── config.py             # Configuration
├── frontend/                 # Svelte frontend dashboard
├── tests/                    # Test suite
└── main.py                   # CLI entry point
```

### Pipeline Stages

1. **Idea Development** - CEO and Researcher collaborate to generate and validate ideas through iterative refinement
2. **Prototyping** - Developer, Designer, and QA build prototypes
3. **Pitch** - Marketer and Deck Strategist create go-to-market strategy and pitch decks

### Stage Gates

Each stage has quality gates that must pass before proceeding:

1. **Idea Development**: Novelty, problem-solution fit, market size, competitor analysis, market sizing, risk assessment, legal readiness
2. **Prototyping**: Code quality, feature completeness, QA validation
3. **Pitch**: Marketing completeness, deck structure, clarity, go-to-market coverage

## Execution Modes

The pipeline supports two execution modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| `standard` | Research-focused, budget-friendly (~4 designs, no code gen) | Quick exploration, cost-effective runs |
| `extended` | Full showcase quality (8 screens + mobile, full prototype, enhanced slides) | Article showcases, demos, high-quality outputs |

**Extended mode includes:**
- 8 screens instead of 4 (with mobile variants)
- Full working prototype with Docker + QA iteration
- Enhanced design prompts for higher visual quality
- Additional pitch slides (business model, traction, roadmap)

## Installation

```bash
# Using uv
uv sync

# Or with pip
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required environment variables:
- `ANTHROPIC_API_KEY` - Required for Claude models
- `OPENAI_API_KEY` - Optional, for OpenAI fallback

## Usage

### Run the Full Pipeline

```bash
# Standard mode (default) - fast, research-focused
python main.py run --input "Create a startup for sustainable fishing"

# Extended mode - full prototype, showcase quality
python main.py run --input "Create a startup for sustainable fishing" --mode extended
```

### Initialize an Experiment

```bash
python main.py init --name "my-experiment"
```

### Run a Single Stage

```bash
# Basic stage run
python main.py run-stage --stage idea_development --input "Create a sustainable fishing app"

# Run with previous context
python main.py run-stage --stage prototyping --input "Build the prototype" --context path/to/context.json

# Export results to file (with extended mode)
python main.py run-stage --stage prototyping --input "Build prototype" --output results.json --format json --mode extended
```

### Inspect, Replay, and Export

```bash
# Inspect context from an experiment
python main.py inspect --experiment "my-experiment" --stage "idea_development"

# Replay from a checkpoint (standard mode)
python main.py replay --experiment "my-experiment" --from-stage "prototyping"

# Replay from a checkpoint (extended mode)
python main.py replay --experiment "my-experiment" --from-stage "prototyping" --mode extended

# Export results
python main.py export --experiment "my-experiment" --format "markdown"
```

### Test Individual Agents

The `test-agent` command allows you to test individual agents in isolation:

```bash
# Test agent tools
python main.py test-agent --agent ceo --test-tools

# Test specific method
python main.py test-agent --agent ceo --method generate_ideas \
  --input '{"chairman_input": "Create sustainable fishing platform"}'

# Test with conversation (from JSON file)
python main.py test-agent --agent ceo --conversation messages.json

# Specify output directory
python main.py test-agent --agent ceo --test-tools --output-dir ./my_tests
```

Test results are saved to:
- Full JSON results: `test_results/{test_name}_{timestamp}.json`
- Human-readable summary: `test_results/{test_name}_latest.txt`

### Test All Agents

Test tools for all agents at once:

```bash
# Test all agents
python main.py test-all-agents

# Specify output directory
python main.py test-all-agents --output-dir ./my_tests
```

### Run Docker Prototype

Manage Docker containers for generated prototypes:

```bash
# Build Docker images
python main.py docker --experiment "experiment-name" --action build

# Start the prototype
python main.py docker --experiment "experiment-name" --action start

# Check status
python main.py docker --experiment "experiment-name" --action status

# View logs (optionally filter by service)
python main.py docker --experiment "experiment-name" --action logs
python main.py docker --experiment "experiment-name" --action logs --service frontend --tail 50

# Stop / restart containers
python main.py docker --experiment "experiment-name" --action stop
python main.py docker --experiment "experiment-name" --action restart
```

After starting, the prototype is available at:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Frontend Dashboard

The project includes a Svelte-based results viewer dashboard.

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development

```bash
# Run tests
pytest

# Lint
ruff check .

# Type check
mypy src/
```

Requirements:
- Python 3.14+
- uv for package management
- AutoGen 0.4+ for multi-agent orchestration

## License

MIT
