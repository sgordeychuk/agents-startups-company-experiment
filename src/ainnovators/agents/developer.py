"""Developer Agent implementation."""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.anthropic import AnthropicChatCompletionClient

from ..config import config
from .base_agent import BaseAgent

if TYPE_CHECKING:
    from ..context.shared_context import CompanyContext

logger = logging.getLogger(__name__)

DEVELOPER_SYSTEM_MESSAGE = """You are a senior software developer and architect. Your role is to:
1. Design technical architectures for startup ideas
2. Create working prototypes demonstrating core value propositions
3. Assess technical feasibility and implementation challenges
4. Write clean, production-quality code

Access shared context to understand requirements and constraints.
Generate code that can actually run, not pseudocode."""


class DeveloperAgent(BaseAgent):
    """
    Developer Agent responsible for technical implementation.

    Competencies:
    - Architecture design
    - Code generation
    - API integration

    Authority:
    - Technical feasibility assessment
    - Implementation decisions
    """

    def __init__(self, context: CompanyContext | None = None) -> None:
        """Initialize the Developer agent."""
        super().__init__(
            name="Developer",
            role="Senior Software Developer",
            system_message=DEVELOPER_SYSTEM_MESSAGE,
            context=context,
        )
        # Set model name for statistics
        self._model_name = config.llm.primary_model

    def create_autogen_agent(
        self, model_client: AnthropicChatCompletionClient | None = None
    ) -> AssistantAgent:
        """
        Create the AutoGen agent instance using Anthropic Claude.

        Args:
            model_client: Anthropic model client (creates one if not provided)

        Returns:
            AutoGen AssistantAgent instance
        """
        # Create model client if not provided
        if model_client is None:
            model_client = AnthropicChatCompletionClient(
                model=config.llm.primary_model,
                api_key=config.llm.anthropic_api_key,
                max_tokens=8192,  # Increase from default 4096
            )

        # Get tools (async functions) - minimal set for context operations
        tools = [
            self._read_context_async,
            self._write_context_async,
        ]

        # Create the agent
        self._autogen_agent = AssistantAgent(
            name=self.name,
            model_client=model_client,
            tools=tools,
            system_message=self.system_message,
            max_tool_iterations=3,
            reflect_on_tool_use=False,  # Disable to reduce API calls
        )

        return self._autogen_agent

    def get_tools(self) -> list[dict[str, Any]]:
        """
        Get Developer-specific tools.

        Returns:
            List of tool definitions
        """
        return [
            *self.get_context_functions(),
            {
                "name": "generate_code",
                "description": "Generate code for a component",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "component": {"type": "string"},
                        "language": {"type": "string"},
                        "requirements": {"type": "string"},
                    },
                    "required": ["component", "language"],
                },
            },
            {
                "name": "design_architecture",
                "description": "Design system architecture",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "system_name": {"type": "string"},
                        "requirements": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["system_name"],
                },
            },
        ]

    def create_prototype(
        self,
        architecture: dict[str, Any],
        design: dict[str, Any],
        experiment_dir: str,
    ) -> dict[str, Any]:
        """
        Create a working prototype (sync wrapper).

        Args:
            architecture: Architecture spec from design_architecture()
            design: Design spec from Designer.create_design()
            experiment_dir: Path to experiment directory

        Returns:
            Prototype metadata including file paths
        """
        import asyncio

        return asyncio.run(self.create_prototype_async(architecture, design, experiment_dir))

    def assess_feasibility(self, requirements: list[str]) -> dict[str, Any]:
        """
        Assess technical feasibility.

        Args:
            requirements: List of requirements

        Returns:
            Feasibility assessment
        """
        # TODO: Implement feasibility assessment
        raise NotImplementedError("Feasibility assessment not yet implemented")

    def design_architecture(
        self, idea: dict[str, Any], research: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Design system architecture (sync wrapper).

        Args:
            idea: The startup idea
            research: Optional research findings

        Returns:
            Architecture design
        """
        import asyncio

        return asyncio.run(self.design_architecture_async(idea, research))

    def generate_implementation_summary(
        self, idea: dict[str, Any], architecture: dict[str, Any]
    ) -> str:
        """
        Generate a text summary explaining the implementation approach (sync wrapper).

        Args:
            idea: The startup idea
            architecture: The designed architecture

        Returns:
            Text summary of implementation approach
        """
        import asyncio

        return asyncio.run(self.generate_implementation_summary_async(idea, architecture))

    async def _read_context_async(self, key: str) -> str:
        """
        Read from shared context (async version).

        Args:
            key: The key to read from shared context

        Returns:
            JSON string of the value
        """
        value = self.read_context(key)
        return json.dumps(value, default=str)

    async def _write_context_async(self, key: str, value: str) -> str:
        """
        Write to shared context (async version).

        Args:
            key: The key to write to shared context
            value: JSON string of the value to write

        Returns:
            Confirmation message
        """
        try:
            # Parse JSON value
            parsed_value = json.loads(value)
            self.write_context(key, parsed_value)
            logger.info(f"[Developer] Successfully wrote {key} to context")
            return f"Successfully updated {key} in shared context"
        except json.JSONDecodeError as e:
            logger.error(f"[Developer] Failed to parse JSON for context write: {e}")
            return f"Failed to parse value as JSON: {e}"

    async def design_architecture_async(
        self, idea: dict[str, Any], research: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Design system architecture in a single LLM call (optimized).

        Args:
            idea: The startup idea
            research: Optional research findings

        Returns:
            Architecture design as dict
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        # Clear usage for fresh tracking
        self.clear_usage()

        logger.info("[Developer] Starting architecture design (single-call)")

        # Store inputs in context
        self.write_context("idea", idea)
        if research:
            self.write_context("research", research)

        system_name = idea.get("solution", idea.get("problem", "Startup MVP"))[:100]

        # Single comprehensive prompt combining all 3 former steps
        prompt = f"""Design a MINIMAL MVP architecture for this startup idea.

**Idea:**
- Problem: {idea.get("problem", "N/A")[:500]}
- Solution: {idea.get("solution", "N/A")[:500]}
- Value Proposition: {idea.get("value_proposition", "N/A")[:300]}

{f"**Market Research:** {json.dumps(research, indent=2)[:1000]}" if research else ""}

**Output a JSON architecture with this EXACT structure:**
```json
{{
  "system_name": "{system_name}",
  "tech_stack": {{
    "frontend": {{"framework": "React/Vue/etc", "language": "TypeScript", "rationale": "brief reason"}},
    "backend": {{"framework": "FastAPI/Express/etc", "language": "Python/Node", "rationale": "brief reason"}},
    "database": {{"primary": "PostgreSQL/MongoDB", "caching": "Redis/none", "rationale": "brief reason"}},
    "infrastructure": {{"hosting": "Vercel/AWS/Heroku", "rationale": "brief reason"}}
  }},
  "core_components": [
    {{"name": "ComponentName", "responsibility": "What it does", "technology": "Tech used", "key_features": ["feature1", "feature2"]}}
  ],
  "data_flows": [
    {{"flow_name": "User Journey Name", "steps": ["step1", "step2"], "components_involved": ["comp1", "comp2"]}}
  ],
  "api_structure": {{
    "base_url": "/api/v1",
    "endpoints": [
      {{"path": "/resource", "method": "GET", "purpose": "What it does"}}
    ],
    "authentication": "JWT"
  }},
  "implementation_notes": ["Note about MVP scope", "Key technical decision"],
  "mvp_scope_summary": {{
    "in_scope": ["Core feature 1", "Core feature 2"],
    "out_of_scope": ["Future feature 1"]
  }}
}}
```

**Guidelines:**
- 3-5 core components max for MVP
- 4-5 data flows (main user journeys only)
- 5-10 essential API endpoints
- Use proven, cost-effective technologies
- Design for 2-3 month MVP timeline

After creating the JSON, call _write_context_async("architecture", <json_string>) to save it."""

        response = await self._autogen_agent.run(task=prompt)
        self._record_usage(response)

        # Extract architecture from context
        architecture = self.read_context("architecture")

        if not architecture:
            logger.warning("[Developer] Architecture not in context, parsing response")
            try:
                response_text = ""
                if hasattr(response, "messages"):
                    for msg in response.messages:
                        if hasattr(msg, "content"):
                            response_text += str(msg.content)

                architecture = self._extract_json_from_text(response_text)
                if architecture:
                    self.write_context("architecture", architecture)
                    logger.info("[Developer] Architecture extracted and saved")
                else:
                    raise ValueError("No valid architecture JSON found")
            except Exception as e:
                logger.error(f"[Developer] Failed to parse architecture: {e}")
                raise

        logger.info("[Developer] Architecture design complete")
        return architecture

    async def generate_implementation_summary_async(
        self, idea: dict[str, Any], architecture: dict[str, Any]
    ) -> str:
        """
        Generate a text summary explaining the implementation approach.

        Args:
            idea: The startup idea
            architecture: The designed architecture

        Returns:
            Text summary explaining how to build the MVP
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        self.clear_usage()

        logger.info("[Developer] Generating implementation summary")

        system_name = architecture.get("system_name", idea.get("solution", "MVP")[:50])
        tech_stack = architecture.get("tech_stack", {})
        components = architecture.get("core_components", [])
        api_structure = architecture.get("api_structure", {})
        mvp_scope = architecture.get("mvp_scope_summary", {})

        prompt = f"""Based on the architecture design, write a clear implementation summary.

**System:** {system_name}
**Problem:** {idea.get("problem", "N/A")[:300]}
**Solution:** {idea.get("solution", "N/A")[:300]}

**Tech Stack:**
{json.dumps(tech_stack, indent=2)}

**Core Components:**
{json.dumps(components, indent=2)}

**API Structure:**
{json.dumps(api_structure, indent=2)}

**MVP Scope:**
- In Scope: {mvp_scope.get("in_scope", [])}
- Out of Scope: {mvp_scope.get("out_of_scope", [])}

Write a 300-500 word implementation summary that explains:
1. The overall technical approach and why these technologies were chosen
2. How the core components work together
3. The key data flows and user journeys
4. Implementation priorities and suggested build order
5. Potential technical challenges and how to address them

Write in clear, professional prose. This is for a technical audience who will implement the MVP.
Output ONLY the summary text, no JSON or additional formatting."""

        response = await self._autogen_agent.run(task=prompt)
        self._record_usage(response)

        summary = ""
        if hasattr(response, "messages"):
            for msg in response.messages:
                if hasattr(msg, "content") and msg.content:
                    summary = str(msg.content)
                    break

        self.write_context("implementation_summary", summary)
        logger.info("[Developer] Implementation summary complete")

        return summary

    def _extract_json_from_text(self, text: str) -> dict[str, Any] | None:
        """
        Extract architecture JSON from text response.

        Args:
            text: Text potentially containing JSON

        Returns:
            Parsed JSON dict or None
        """
        depth = 0
        start = -1
        candidates = []

        for i, char in enumerate(text):
            if char == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        json_str = text[start : i + 1]
                        obj = json.loads(json_str)

                        # Check if this looks like an architecture object
                        if isinstance(obj, dict) and any(
                            key in obj
                            for key in [
                                "system_name",
                                "tech_stack",
                                "core_components",
                                "data_flows",
                                "api_structure",
                            ]
                        ):
                            candidates.append(obj)
                    except json.JSONDecodeError:
                        pass

                    start = -1

        # Return the largest valid architecture object
        for obj in sorted(candidates, key=lambda x: len(str(x)), reverse=True):
            return obj

        return None

    async def create_prototype_async(
        self,
        architecture: dict[str, Any],
        design: dict[str, Any],
        experiment_dir: str,
    ) -> dict[str, Any]:
        """
        Generate prototype code from architecture and design specs.

        DISABLED: Code generation temporarily disabled for simplified pipeline.

        Args:
            architecture: Architecture spec from design_architecture()
            design: Design spec from Designer.create_design()
            experiment_dir: Path to experiment directory

        Returns:
            Prototype metadata including file paths and Docker status
        """
        # DISABLED: Code generation temporarily disabled for simplified pipeline
        # logger.warning("[Developer] create_prototype_async is DISABLED")
        # return {
        #     "directory": experiment_dir,
        #     "files_generated": 0,
        #     "status": "disabled",
        #     "message": "Code generation disabled for simplified pipeline",
        # }

        # DISABLED: Start of code generation logic
        if not self._autogen_agent:
            self.create_autogen_agent()

        # Clear usage for fresh tracking
        self.clear_usage()

        logger.info("[Developer] Starting prototype generation")

        prototype_dir = Path(experiment_dir) / "prototype"
        prototype_dir.mkdir(parents=True, exist_ok=True)

        files_generated = 0

        # Stage 1: Generate config files (Docker, package.json, requirements.txt)
        logger.info("[Developer] Stage 1: Generating config files")
        config_files = await self._generate_config_files(architecture, design)
        self._write_files(prototype_dir, config_files)
        files_generated += len(config_files)
        logger.info(f"[Developer] Config files generated: {len(config_files)}")

        # Stage 2: Generate backend code
        logger.info("[Developer] Stage 2: Generating backend code")
        backend_files = await self._generate_backend(architecture)
        self._write_files(prototype_dir / "backend", backend_files)
        files_generated += len(backend_files)
        logger.info(f"[Developer] Backend files generated: {len(backend_files)}")

        # Stage 3: Generate frontend code
        logger.info("[Developer] Stage 3: Generating frontend code")
        frontend_files = await self._generate_frontend(architecture, design)
        self._write_files(prototype_dir / "frontend", frontend_files)
        files_generated += len(frontend_files)
        logger.info(f"[Developer] Frontend files generated: {len(frontend_files)}")

        # Ensure public directory exists (required by Next.js standalone Dockerfile)
        (prototype_dir / "frontend" / "public").mkdir(parents=True, exist_ok=True)

        # Stage 4: Generate README
        readme = self._generate_readme(architecture, design)
        (prototype_dir / "README.md").write_text(readme)
        files_generated += 1

        prototype_data = {
            "directory": str(prototype_dir),
            "files_generated": files_generated,
            "tech_stack": architecture.get("tech_stack", {}),
            "endpoints": [
                ep.get("path") for ep in architecture.get("api_structure", {}).get("endpoints", [])
            ],
            "status": "generated",
        }

        # Store in context
        self.write_context("prototype", prototype_data)

        logger.info(f"[Developer] Prototype generation complete: {files_generated} files")
        return prototype_data
        # DISABLED: End of code generation logic

    async def _generate_config_files(
        self, architecture: dict[str, Any], design: dict[str, Any]
    ) -> dict[str, str]:
        """Generate Docker and project configuration files."""
        tech_stack = architecture.get("tech_stack", {})
        frontend = tech_stack.get("frontend", {})
        backend = tech_stack.get("backend", {})
        design_system = design.get("design_system", {})

        # Extract colors for Tailwind config
        colors = design_system.get("colors", {})
        primary_color = colors.get("primary", "#3B82F6")
        secondary_color = colors.get("secondary", "#10B981")

        prompt = f"""Generate Docker and project configuration files for this MVP prototype.

**Tech Stack:**
- Frontend: {frontend.get("framework", "Next.js")} with {frontend.get("language", "TypeScript")}
- Backend: {backend.get("framework", "FastAPI")} with {backend.get("language", "Python")}
- Database: SQLite (containerized)

**Design System Colors:**
- Primary: {primary_color}
- Secondary: {secondary_color}

**Output a JSON object with these files (filename as key, content as value):**

1. "docker-compose.yml" - Docker Compose config (NO volume mounts for frontend/backend - use built images only)
2. "Dockerfile.frontend" - Multi-stage Dockerfile for Next.js with standalone output
3. "Dockerfile.backend" - Dockerfile for FastAPI with uvicorn
4. "frontend/package.json" - Next.js 14 with Tailwind CSS, TypeScript
5. "frontend/tailwind.config.js" - Tailwind config with custom colors from design system
6. "frontend/next.config.js" - Next.js config with output: 'standalone'
7. "frontend/tsconfig.json" - TypeScript config for Next.js
8. "backend/requirements.txt" - FastAPI, uvicorn, SQLAlchemy, pydantic

**CRITICAL Requirements:**
- Backend on port 8000, frontend on port 3000
- SQLite database stored in /app/data/app.db
- Dockerfile.frontend MUST use 'npm install' (NOT 'npm ci') since no package-lock.json exists
- tsconfig.json paths MUST use "@/*": ["./*"] (NOT "./src/*") since files are in root, not src/
- docker-compose.yml MUST NOT have volume mounts that override /app (breaks standalone build)
- docker-compose.yml frontend should just have: build, ports, environment, depends_on (no volumes)
- Frontend should proxy API calls to backend via NEXT_PUBLIC_API_URL=http://backend:8000
- Use latest stable versions
- Include only essential dependencies

Output ONLY valid JSON, no explanation:
```json
{{
  "docker-compose.yml": "content...",
  ...
}}
```"""

        response = await self._autogen_agent.run(task=prompt)
        self._record_usage(response)
        return self._extract_files_from_response(response)

    async def _generate_backend(self, architecture: dict[str, Any]) -> dict[str, str]:
        """Generate FastAPI backend code."""
        api_structure = architecture.get("api_structure", {})
        endpoints = api_structure.get("endpoints", [])[:3]  # Limit to 3 endpoints
        components = architecture.get("core_components", [])[:3]

        prompt = f"""Generate FastAPI backend code for this MVP prototype.

**API Endpoints to implement:**
{json.dumps(endpoints, indent=2)}

**Core Components:**
{json.dumps(components, indent=2)}

**Output a JSON object with these files (filename as key, content as value):**

1. "app/__init__.py" - Empty init file
2. "app/main.py" - FastAPI app with CORS enabled for localhost:3000, startup event to create DB
3. "app/database.py" - SQLAlchemy setup with async SQLite, create_tables function
4. "app/models/__init__.py" - Empty init
5. "app/models/schemas.py" - Pydantic models for request/response based on components
6. "app/routers/__init__.py" - Empty init
7. "app/routers/api.py" - API router with 2-5 working endpoints returning placeholder data

**Requirements:**
- Use async SQLAlchemy with aiosqlite
- Include proper CORS configuration for http://localhost:3000
- Endpoints should return realistic placeholder data
- Include health check endpoint at /api/health
- Use proper type hints and docstrings
- Database file at /app/data/app.db

Output ONLY valid JSON, no explanation:
```json
{{
  "app/__init__.py": "",
  "app/main.py": "content...",
  ...
}}
```"""

        response = await self._autogen_agent.run(task=prompt)
        self._record_usage(response)
        return self._extract_files_from_response(response)

    async def _generate_frontend(
        self, architecture: dict[str, Any], design: dict[str, Any]
    ) -> dict[str, str]:
        """Generate Next.js frontend code."""
        design_system = design.get("design_system", {})
        wireframes = design.get("wireframes", [])[:2]  # Limit to 2 wireframes
        api_structure = architecture.get("api_structure", {})
        endpoints = api_structure.get("endpoints", [])[:3]

        colors = design_system.get("colors", {})
        typography = design_system.get("typography", {})

        prompt = f"""Generate Next.js 14 frontend code for this MVP prototype.

**Design System:**
- Colors: {json.dumps(colors, indent=2)}
- Typography: {json.dumps(typography, indent=2)}

**Wireframes to implement:**
{json.dumps(wireframes, indent=2)}

**API Endpoints available:**
{json.dumps(endpoints, indent=2)}

**Output a JSON object with these files (filename as key, content as value):**

1. "app/layout.tsx" - Root layout with Inter font, metadata, body with bg color
2. "app/page.tsx" - Landing/home page matching first wireframe, with hero section
3. "app/globals.css" - Tailwind directives (@tailwind base/components/utilities) + custom CSS variables for colors
4. "components/ui/Button.tsx" - Reusable button with primary/secondary/outline variants
5. "components/ui/Card.tsx" - Reusable card component with header, content, footer

**Requirements:**
- Use Tailwind CSS for styling with design system colors
- App Router (app/ directory structure)
- TypeScript with proper types
- Use design system colors as CSS variables
- Components should be properly typed with React.FC
- Include 'use client' directive where needed
- Landing page should have a hero section and feature cards
- Import components using @/components/ui/... paths (tsconfig paths: "@/*": ["./*"])

Output ONLY valid JSON, no explanation:
```json
{{
  "app/layout.tsx": "content...",
  ...
}}
```"""

        response = await self._autogen_agent.run(task=prompt)
        self._record_usage(response)
        return self._extract_files_from_response(response)

    def _extract_files_from_response(self, response: Any) -> dict[str, str]:
        """Extract file dictionary from LLM response."""
        response_text = ""
        if hasattr(response, "messages"):
            for msg in response.messages:
                if hasattr(msg, "content"):
                    response_text += str(msg.content)

        # Try to extract JSON from response
        files = self._extract_json_from_text_generic(response_text)

        if not files or not isinstance(files, dict):
            logger.warning("[Developer] Could not extract files from response")
            return {}

        # Filter to only string values (file contents)
        return {k: v for k, v in files.items() if isinstance(v, str)}

    def _extract_json_from_text_generic(self, text: str) -> dict[str, Any] | None:
        """Extract any JSON object from text."""
        depth = 0
        start = -1
        candidates = []

        for i, char in enumerate(text):
            if char == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        json_str = text[start : i + 1]
                        obj = json.loads(json_str)
                        if isinstance(obj, dict):
                            candidates.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start = -1

        # Return the largest valid object
        for obj in sorted(candidates, key=lambda x: len(str(x)), reverse=True):
            return obj

        return None

    def _write_files(self, base_dir: Path, files: dict[str, str]) -> None:
        """Write generated files to disk."""
        for filepath, content in files.items():
            full_path = base_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            logger.debug(f"[Developer] Wrote file: {full_path}")

    def _generate_readme(self, architecture: dict[str, Any], design: dict[str, Any]) -> str:
        """Generate README.md for the prototype."""
        tech_stack = architecture.get("tech_stack", {})
        system_name = architecture.get("system_name", "Prototype")
        endpoints = architecture.get("api_structure", {}).get("endpoints", [])

        endpoint_docs = "\n".join(
            f"- `{ep.get('method', 'GET')} {ep.get('path', '/')}` - {ep.get('purpose', 'N/A')}"
            for ep in endpoints[:5]
        )

        return f"""# {system_name}

Generated prototype for MVP validation.

## Tech Stack

- **Frontend:** {tech_stack.get("frontend", {}).get("framework", "Next.js")} with {tech_stack.get("frontend", {}).get("language", "TypeScript")}
- **Backend:** {tech_stack.get("backend", {}).get("framework", "FastAPI")} with {tech_stack.get("backend", {}).get("language", "Python")}
- **Database:** SQLite

## Quick Start

```bash
# Build and start containers
docker compose up --build

# Or run separately:
docker compose build
docker compose up -d
```

## Access

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## API Endpoints

{endpoint_docs}

## Stop

```bash
docker compose down
```

---
*Generated by AI Innovators Pipeline*
"""

    def fix_bugs(
        self,
        prototype: dict[str, Any],
        bugs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Fix bugs reported by QA (sync wrapper).

        Args:
            prototype: Prototype metadata with directory path
            bugs: List of bugs to fix (max 5 processed)

        Returns:
            Fix results including files modified
        """
        import asyncio

        return asyncio.run(self.fix_bugs_async(prototype, bugs))

    async def fix_bugs_async(
        self,
        prototype: dict[str, Any],
        bugs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Fix bugs reported by QA agent.

        DISABLED: Bug fixing temporarily disabled for simplified pipeline.

        Args:
            prototype: Prototype metadata with directory path
            bugs: List of bugs to fix (max 5 processed)

        Returns:
            Fix results including files modified and fix descriptions
        """
        # DISABLED: Bug fixing temporarily disabled for simplified pipeline
        logger.warning("[Developer] fix_bugs_async is DISABLED")
        return {
            "success": False,
            "fixes": [],
            "files_modified": [],
            "status": "disabled",
            "message": "Bug fixing disabled for simplified pipeline",
        }

        # DISABLED: Start of bug fixing logic
        # if not self._autogen_agent:
        #     self.create_autogen_agent()
        #
        # # Clear usage for fresh tracking
        # self.clear_usage()
        #
        # prototype_dir = Path(prototype.get("directory", ""))
        # if not prototype_dir.exists():
        #     logger.error(f"[Developer] Prototype directory not found: {prototype_dir}")
        #     return {"success": False, "error": "Prototype directory not found"}
        #
        # bugs_to_fix = bugs[:5]
        # logger.info(f"[Developer] Fixing {len(bugs_to_fix)} bugs")
        #
        # bugs_description = "\n".join(
        #     f"- [{b.get('severity', 'unknown').upper()}] {b.get('title', 'Unknown')}: "
        #     f"{b.get('description', 'No description')[:200]} "
        #     f"(Page: {b.get('affected_page', 'unknown')}, Category: {b.get('category', 'unknown')})"
        #     for b in bugs_to_fix
        # )
        #
        # relevant_files = await self._identify_relevant_files(prototype_dir, bugs_to_fix)
        # file_contents = {}
        # for filepath in relevant_files[:10]:
        #     try:
        #         content = filepath.read_text()
        #         rel_path = str(filepath.relative_to(prototype_dir))
        #         file_contents[rel_path] = content[:3000]
        #     except Exception as e:
        #         logger.warning(f"[Developer] Could not read {filepath}: {e}")
        #
        # files_context = "\n\n".join(
        #     f"**{name}:**\n```\n{content}\n```"
        #     for name, content in file_contents.items()
        # )
        #
        # prompt = f"""Fix the following bugs in the prototype code.
        #
        # **Bugs to fix:**
        # {bugs_description}
        #
        # **Current code files:**
        # {files_context}
        #
        # **Instructions:**
        # 1. Analyze each bug and identify the root cause
        # 2. Generate fixed code for affected files
        # 3. For styling bugs: ensure Tailwind classes are correct, layouts are proper
        # 4. For functional bugs: fix the logic, error handling, or API calls
        # 5. For API bugs: fix the backend endpoints or frontend API calls
        #
        # **Output a JSON object with:**
        # - "fixes": Array of fix descriptions (what was changed and why)
        # - "files": Object with relative filepath as key, full fixed file content as value
        #
        # Only include files that need changes. Output ONLY valid JSON:
        # ```json
        # {{
        #   "fixes": ["Fixed X by doing Y", ...],
        #   "files": {{
        #     "frontend/app/page.tsx": "full fixed content...",
        #     ...
        #   }}
        # }}
        # ```"""
        #
        # response = await self._autogen_agent.run(task=prompt)
        # self._record_usage(response)
        # result = self._extract_json_from_text_generic(
        #     "".join(str(msg.content) for msg in response.messages if hasattr(msg, "content"))
        # )
        #
        # if not result:
        #     logger.warning("[Developer] Could not parse fix response")
        #     return {"success": False, "error": "Could not parse fix response", "files_modified": []}
        #
        # files_to_write = result.get("files", {})
        # fixes = result.get("fixes", [])
        # files_modified = []
        #
        # for rel_path, content in files_to_write.items():
        #     if not isinstance(content, str):
        #         continue
        #     full_path = prototype_dir / rel_path
        #     try:
        #         full_path.parent.mkdir(parents=True, exist_ok=True)
        #         full_path.write_text(content)
        #         files_modified.append(rel_path)
        #         logger.info(f"[Developer] Fixed file: {rel_path}")
        #     except Exception as e:
        #         logger.error(f"[Developer] Failed to write {rel_path}: {e}")
        #
        # fix_result = {
        #     "success": len(files_modified) > 0,
        #     "fixes": fixes,
        #     "files_modified": files_modified,
        #     "bugs_addressed": len(bugs_to_fix),
        # }
        #
        # self.write_context("bug_fixes", fix_result)
        # logger.info(f"[Developer] Bug fixing complete: {len(files_modified)} files modified")
        #
        # return fix_result
        # DISABLED: End of bug fixing logic

    def fix_docker_issues(
        self,
        prototype: dict[str, Any],
        error_details: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Fix Docker configuration issues based on error details (sync wrapper).

        Args:
            prototype: Prototype metadata with directory path
            error_details: Docker error info (phase, stderr, stdout, etc.)

        Returns:
            Fix results including success status and files_modified
        """
        import asyncio

        return asyncio.run(self.fix_docker_issues_async(prototype, error_details))

    async def fix_docker_issues_async(
        self,
        prototype: dict[str, Any],
        error_details: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Fix Docker configuration issues (Dockerfile, docker-compose.yml, etc).

        Args:
            prototype: Prototype metadata with directory path
            error_details: Docker error info including phase, stderr, stdout

        Returns:
            Fix result with success status and files_modified
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        self.clear_usage()

        prototype_dir = Path(prototype.get("directory", ""))
        if not prototype_dir.exists():
            logger.error(f"[Developer] Prototype directory not found: {prototype_dir}")
            return {
                "success": False,
                "error": "Prototype directory not found",
                "files_modified": [],
            }

        docker_files = [
            "docker-compose.yml",
            "frontend/Dockerfile",
            "backend/Dockerfile",
            "frontend/package.json",
            "backend/requirements.txt",
        ]

        file_contents: dict[str, str] = {}
        for rel_path in docker_files:
            filepath = prototype_dir / rel_path
            if filepath.exists():
                try:
                    content = filepath.read_text()
                    file_contents[rel_path] = content[:5000]
                except Exception as e:
                    logger.warning(f"[Developer] Could not read {rel_path}: {e}")

        files_context = "\n\n".join(
            f"**{name}:**\n```\n{content}\n```" for name, content in file_contents.items()
        )

        error_phase = error_details.get("phase", "unknown")
        error_stderr = str(error_details.get("stderr", ""))[:3000]
        error_stdout = str(error_details.get("stdout", ""))[:1000]
        error_msg = error_details.get("error", "")

        logger.info(f"[Developer] Fixing Docker issues (phase: {error_phase})")

        prompt = f"""Fix the Docker configuration issues in this prototype.

**Error Phase:** {error_phase}

**Error Message:** {error_msg}

**Error Output (stderr):**
```
{error_stderr}
```

**Build Output (stdout):**
```
{error_stdout}
```

**Current Docker configuration files:**
{files_context}

**Instructions:**
1. Analyze the error output to identify the root cause
2. Common issues: missing dependencies, wrong base images, port conflicts, syntax errors, incompatible package versions
3. Fix the relevant configuration files
4. Ensure docker-compose.yml services are properly configured
5. Ensure Dockerfiles have correct base images and install commands

**Output a JSON object with:**
- "diagnosis": Brief explanation of what went wrong
- "files": Object with relative filepath as key, full fixed file content as value

Only include files that need changes. Output ONLY valid JSON:
```json
{{
  "diagnosis": "Brief explanation of the issue and fix",
  "files": {{
    "docker-compose.yml": "full fixed content...",
    "frontend/Dockerfile": "full fixed content..."
  }}
}}
```"""

        response = await self._autogen_agent.run(task=prompt)
        self._record_usage(response)

        response_text = "".join(
            str(msg.content) for msg in response.messages if hasattr(msg, "content")
        )
        result = self._extract_json_from_text_generic(response_text)

        if not result:
            logger.warning("[Developer] Could not parse Docker fix response")
            return {"success": False, "error": "Could not parse fix response", "files_modified": []}

        files_to_write = result.get("files", {})
        diagnosis = result.get("diagnosis", "Unknown issue")
        files_modified: list[str] = []

        logger.info(f"[Developer] Docker diagnosis: {diagnosis}")

        for rel_path, content in files_to_write.items():
            if not isinstance(content, str):
                continue
            full_path = prototype_dir / rel_path
            try:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                files_modified.append(rel_path)
                logger.info(f"[Developer] Fixed Docker file: {rel_path}")
            except Exception as e:
                logger.error(f"[Developer] Failed to write {rel_path}: {e}")

        return {
            "success": len(files_modified) > 0,
            "diagnosis": diagnosis,
            "files_modified": files_modified,
        }

    async def _identify_relevant_files(
        self,
        prototype_dir: Path,
        bugs: list[dict[str, Any]],
    ) -> list[Path]:
        """
        Identify files relevant to the bugs.

        Args:
            prototype_dir: Path to prototype directory
            bugs: List of bugs

        Returns:
            List of file paths to examine
        """
        relevant_files: list[Path] = []

        categories = {b.get("category", "") for b in bugs}
        pages = {b.get("affected_page", "").lower() for b in bugs}

        frontend_dir = prototype_dir / "frontend"
        backend_dir = prototype_dir / "backend"

        if "styling" in categories or "functional" in categories or "navigation" in categories:
            if frontend_dir.exists():
                for pattern in ["app/**/*.tsx", "app/**/*.css", "components/**/*.tsx"]:
                    relevant_files.extend(frontend_dir.glob(pattern))

        if "api" in categories:
            if backend_dir.exists():
                for pattern in ["app/**/*.py", "**/*.py"]:
                    relevant_files.extend(backend_dir.glob(pattern))

        for page in pages:
            if page and page != "unknown":
                page_file = frontend_dir / "app" / f"{page}" / "page.tsx"
                if page_file.exists():
                    relevant_files.append(page_file)

                if page in ("home", "/"):
                    home_file = frontend_dir / "app" / "page.tsx"
                    if home_file.exists():
                        relevant_files.append(home_file)

        return list(set(relevant_files))
