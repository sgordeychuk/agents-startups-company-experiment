"""Designer Agent implementation."""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from autogen_agentchat.agents import AssistantAgent

from ..config import config
from ..utils.gemini_client import GeminiChatCompletionClient, create_gemini_client
from .base_agent import BaseAgent

if TYPE_CHECKING:
    from ..context.shared_context import CompanyContext

logger = logging.getLogger(__name__)

DESIGNER_SYSTEM_MESSAGE = """You are a senior product designer specializing in UX/UI for startup MVPs. Your role is to:
1. Create user-centered design systems and specifications based on product vision and research
2. Design intuitive user flows that solve real customer problems efficiently
3. Define comprehensive component libraries for consistent, scalable UI
4. Generate visual wireframes and mockups that provide clear implementation guidance
5. Ensure designs align with target market, user needs, and technical constraints

You have access to shared company context via read_context() and write_context().

IMPORTANT DESIGN PRINCIPLES:
- DESKTOP-FIRST: All designs are for desktop only (1440px viewport width). No mobile or tablet variants in MVP phase.
- VISUAL CONSISTENCY: Use the exact same colors, typography, and spacing across all screens. Reference the design system tokens in every screen.
- UNIFIED STYLE: All screens must feel like part of the same application - consistent navigation, headers, and component styling.

When creating designs:
- Start by understanding the idea, research findings, and technical architecture
- Define a cohesive design system (colors, typography, spacing, components)
- Map out critical user flows with clear steps and decision points
- Create DESKTOP-ONLY wireframes (1440px width) for key screens that demonstrate layout and interactions
- Specify reusable component libraries with clear props and usage guidelines
- Ensure all screens use the SAME color palette and typography from the design system

Structure design outputs as JSON with these fields:
- design_system: Design tokens (colors, typography, spacing, components) - these MUST be used consistently across all screens
- user_flows: Critical user journeys with steps, screens, and decision points
- wireframes: Desktop-only wireframe specifications (1440px width) with descriptions and components
- component_library: Reusable UI components with props and usage notes
- design_rationale: Explanation of key design decisions including how visual consistency is maintained
- implementation_notes: Practical guidance for developers

Focus on MVP delivery - prioritize essential flows and components. Keep designs practical and implementable.
Avoid over-engineering. Design for the target market based on research insights."""


class DesignerAgent(BaseAgent):
    """
    Designer Agent responsible for UI/UX design.

    Competencies:
    - UI/UX design
    - Visual prototyping
    - User flows
    - Component library creation

    Authority:
    - Design direction
    - User experience decisions
    """

    def __init__(self, context: CompanyContext | None = None) -> None:
        """Initialize the Designer agent."""
        super().__init__(
            name="Designer",
            role="Product Designer",
            system_message=DESIGNER_SYSTEM_MESSAGE,
            context=context,
        )
        # Set model name for statistics (uses OpenAI)
        self._model_name = config.llm.openai_model
        # Initialize Google Generative AI for image generation
        self._image_client = None
        if config.llm.gemini_api_key:
            try:
                from google import genai

                self._image_client = genai.Client(api_key=config.llm.gemini_api_key)
                logger.info("[Designer] Nano Banana Pro (Gemini image model) initialized")
            except Exception as e:
                logger.warning(
                    f"[Designer] Failed to initialize Gemini image client: {e}. "
                    "Wireframe generation will use text descriptions only."
                )
        else:
            logger.warning(
                "[Designer] GEMINI_API_KEY not configured. "
                "Wireframe generation will use text descriptions only."
            )

    def create_autogen_agent(
        self, model_client: GeminiChatCompletionClient | None = None
    ) -> AssistantAgent:
        """
        Create the AutoGen agent instance using Gemini via OpenAI-compatible API.

        Args:
            model_client: Gemini model client (creates one with retry logic if not provided)

        Returns:
            AutoGen AssistantAgent instance
        """
        # Create Gemini model client with retry logic for empty responses
        if model_client is None:
            model_client = create_gemini_client(
                model=config.llm.gemini_model,
                api_key=config.llm.gemini_api_key,
                base_url=config.llm.gemini_base_url,
                max_retries=3,
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
            max_tool_iterations=3,  # Reduced from 5
            reflect_on_tool_use=False,  # Disable to reduce API calls
        )

        return self._autogen_agent

    def get_tools(self) -> list[dict[str, Any]]:
        """
        Get Designer-specific tools.

        Returns:
            List of tool definitions
        """
        return [
            *self.get_context_functions(),
            {
                "name": "generate_wireframe",
                "description": "Generate a wireframe/mockup for a screen or component",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "screen_name": {
                            "type": "string",
                            "description": "Name of the screen/page (e.g., 'Dashboard', 'Login')",
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of wireframe content and layout",
                        },
                        "components": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of UI components to include",
                        },
                    },
                    "required": ["screen_name", "description"],
                },
            },
            {
                "name": "analyze_design_requirements",
                "description": "Analyze idea and research to extract design requirements",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific areas to analyze (e.g., 'target users')",
                        }
                    },
                    "required": [],
                },
            },
        ]

    async def _generate_wireframe_async(
        self,
        screen_name: str,
        description: str,
        components: list[str] | None = None,
        design_system: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a wireframe/mockup (async version).

        Args:
            screen_name: Name of the screen
            description: Detailed description for wireframe
            components: Optional list of UI components
            design_system: Design system with colors and typography for consistency

        Returns:
            Wireframe specification or filepath if image generated
        """
        logger.info(f"[Designer] Generating wireframe for: {screen_name}")

        # Build wireframe specification
        component_text = f" including: {', '.join(components)}" if components else ""
        wireframe_spec = {
            "screen_name": screen_name,
            "description": description,
            "components": components or [],
            "layout": "TBD - describe layout structure",
        }

        # Extract colors from design_system for consistent styling
        colors = design_system.get("colors", {}) if design_system else {}
        typography = design_system.get("typography", {}) if design_system else {}
        primary_color = colors.get("primary", "#3B82F6")
        secondary_color = colors.get("secondary", "#10B981")
        accent_color = colors.get("accent", "#F59E0B")
        font_family = typography.get("font_families", {}).get("body", "Inter")

        # Try to generate actual image if Nano Banana Pro is available
        if self._image_client:
            try:
                # Build comprehensive prompt for Nano Banana Pro with desktop-only and consistent styling
                prompt = f"""Create a clean, professional DESKTOP wireframe mockup for: {screen_name}

VIEWPORT: Desktop only - 1440px width. NO mobile or tablet variants.

{description}{component_text}

STYLING (use these exact colors):
- Primary Color: {primary_color} (for buttons, links, key interactive elements)
- Secondary Color: {secondary_color} (for secondary actions, accents)
- Accent Color: {accent_color} (for highlights, notifications)
- Font Family: {font_family}
- Background: Light neutral (#F9FAFB or white)

REQUIREMENTS:
- Modern, minimalist wireframe with clear UI elements
- Desktop layout only (1440px width) - NO mobile designs
- Show layout structure, component placement, and content hierarchy
- Use the specified colors for consistency across all screens
- Professional design mockup suitable for developer handoff
- Include a consistent navigation/header area"""

                # Generate image using Nano Banana Pro
                response = self._image_client.models.generate_content(
                    model=config.llm.gemini_image_model, contents=prompt
                )

                # Get experiment directory from context, fallback to default
                experiment_dir = self.read_context("experiment_dir")
                if experiment_dir:
                    output_dir = Path(experiment_dir) / "wireframes"
                else:
                    output_dir = Path("./experiments/wireframes")
                output_dir.mkdir(parents=True, exist_ok=True)

                filename = f"{screen_name.replace(' ', '_').lower()}.png"
                filepath = output_dir / filename

                # Extract and save image from response
                if (
                    response.candidates
                    and response.candidates[0].content.parts
                    and hasattr(response.candidates[0].content.parts[0], "inline_data")
                ):
                    image_data = response.candidates[0].content.parts[0].inline_data.data
                    with open(filepath, "wb") as f:
                        f.write(image_data)

                    logger.info(f"[Designer] Wireframe image saved: {filepath}")
                    wireframe_spec["filepath"] = str(filepath)
                    wireframe_spec["image_generated"] = True
                    return json.dumps(
                        {
                            "status": "success",
                            "message": f"Wireframe generated: {filepath}",
                            "wireframe": wireframe_spec,
                        }
                    )
                else:
                    logger.warning("[Designer] No image in Nano Banana Pro response")

            except Exception as e:
                logger.error(f"[Designer] Wireframe image generation failed: {e}")

        # Fallback to text-only wireframe specification
        wireframe_spec["image_generated"] = False
        wireframe_spec["note"] = "Text description only - visual wireframe requires GEMINI_API_KEY"

        logger.info(f"[Designer] Wireframe spec created (text only): {screen_name}")
        return json.dumps(
            {"status": "success", "message": "Wireframe spec created", "wireframe": wireframe_spec}
        )

    async def _analyze_design_requirements_async(self, focus_areas: list[str] | None = None) -> str:
        """
        Analyze idea and research to extract design requirements (async version).

        Args:
            focus_areas: Specific areas to focus on

        Returns:
            JSON string with design requirements
        """
        logger.info("[Designer] Analyzing design requirements from context")

        try:
            # Read from context
            idea = self.read_context("idea", {})
            research = self.read_context("research", {})

            # Extract key design requirements
            requirements = {
                "target_users": idea.get("target_market", "Unknown"),
                "key_problems": idea.get("problem", ""),
                "value_proposition": idea.get("value_proposition", ""),
                "competitive_insights": [],
                "user_needs": [],
                "constraints": [],
            }

            # Extract insights from research
            if research:
                competitors = research.get("competitors", [])
                for comp in competitors[:3]:  # Top 3 competitors
                    requirements["competitive_insights"].append(
                        {
                            "competitor": comp.get("name", "Unknown"),
                            "strength": comp.get("strengths", ""),
                            "gap_opportunity": comp.get("weaknesses", ""),
                        }
                    )

            # Infer user needs from problem statement
            problem = idea.get("problem", "")
            if problem:
                requirements["user_needs"].append(f"Solve: {problem[:200]}")

            # Add MVP constraint
            requirements["constraints"].append(
                "MVP scope - focus on core value proposition and essential features"
            )

            logger.info("[Designer] Design requirements extracted successfully")
            return json.dumps(requirements, indent=2)

        except Exception as e:
            logger.error(f"[Designer] Requirements analysis failed: {e}")
            return json.dumps({"error": str(e)})

    async def _read_context_async(self, key: str) -> str:
        """Read from shared context (async version)."""
        value = self.read_context(key)
        return json.dumps(value, default=str)

    async def _write_context_async(self, key: str, value: str) -> str:
        """Write to shared context (async version)."""
        try:
            parsed_value = json.loads(value)
            self.write_context(key, parsed_value)
            logger.info(f"[Designer] Successfully wrote {key} to context")
            return f"Successfully updated {key} in shared context"
        except json.JSONDecodeError as e:
            logger.error(f"[Designer] Failed to parse JSON for context write: {e}")
            return f"Failed to parse value as JSON: {e}"

    async def create_design_async(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
        architecture: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create comprehensive UI/UX design in a single LLM call (optimized).

        Args:
            idea: The startup idea
            research: Research findings
            architecture: Optional technical architecture from Developer

        Returns:
            Complete design specification
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        # Clear usage for fresh tracking
        self.clear_usage()

        logger.info("[Designer] Starting design creation (single-call)")

        # Store inputs in context
        self.write_context("idea", idea)
        self.write_context("research", research)
        if architecture:
            self.write_context("architecture", architecture)

        product_name = idea.get("solution", idea.get("problem", "Product"))[:80]

        # Single comprehensive prompt
        prompt = f"""Create a complete UI/UX design specification for this startup.

**Product:** {product_name}
**Problem:** {idea.get("problem", "N/A")[:400]}
**Solution:** {idea.get("solution", "N/A")[:400]}
**Target Users:** {research.get("target_audience", "General users")[:200] if isinstance(research, dict) else "General users"}

{f"**Tech Stack:** {architecture.get('tech_stack', {}).get('frontend', {}).get('framework', 'React')}" if architecture else ""}

**Output a JSON design specification with this EXACT structure:**
```json
{{
  "design_system": {{
    "colors": {{
      "primary": "#3B82F6",
      "secondary": "#10B981",
      "accent": "#F59E0B",
      "neutral": {{"50": "#F9FAFB", "100": "#F3F4F6", "900": "#111827"}},
      "semantic": {{"success": "#10B981", "warning": "#F59E0B", "error": "#EF4444"}}
    }},
    "typography": {{
      "font_families": {{"heading": "Inter", "body": "Inter", "mono": "JetBrains Mono"}},
      "sizes": {{"xs": "12px", "sm": "14px", "base": "16px", "lg": "18px", "xl": "20px", "2xl": "24px"}},
      "weights": {{"normal": 400, "medium": 500, "semibold": 600, "bold": 700}}
    }},
    "spacing": {{
      "base_unit": "8px",
      "scale": [4, 8, 12, 16, 24, 32, 48, 64]
    }},
    "components": ["Button", "Card", "Input", "Navbar", "Modal", "Avatar"]
  }},
  "user_flows": [
    {{
      "flow_name": "User Onboarding",
      "description": "New user signup and initial setup",
      "steps": ["Landing page", "Sign up form", "Email verification", "Profile setup", "Dashboard"],
      "screens": ["Landing", "SignUp", "Verify", "ProfileSetup", "Dashboard"]
    }}
  ],
  "wireframes": [
    {{
      "screen_name": "Dashboard",
      "description": "Main dashboard with key metrics and actions - DESKTOP ONLY (1440px width)",
      "components": ["header", "sidebar", "stats-cards", "activity-feed"],
      "layout": "Desktop: Sidebar navigation (240px) with main content area (1200px)",
      "interactions": ["Click card to expand", "Filter by date range"],
      "viewport": "desktop-1440px"
    }},
    {{
      "screen_name": "Profile",
      "description": "User profile with settings and preferences - DESKTOP ONLY (1440px width)",
      "components": ["avatar", "form-fields", "save-button"],
      "layout": "Desktop: Centered card (800px) with form on neutral background",
      "interactions": ["Edit fields inline", "Upload avatar"],
      "viewport": "desktop-1440px"
    }},
    {{
      "screen_name": "Landing",
      "description": "Marketing landing page with signup CTA - DESKTOP ONLY (1440px width)",
      "components": ["hero", "features-grid", "testimonials", "cta-section"],
      "layout": "Desktop: Full-width sections (max 1200px content) stacked vertically",
      "interactions": ["Scroll animations", "CTA buttons"],
      "viewport": "desktop-1440px"
    }}
  ],
  "component_library": [
    {{
      "component_name": "PrimaryButton",
      "description": "Main call-to-action button",
      "props": {{"size": ["sm", "md", "lg"], "variant": ["solid", "outline"]}},
      "states": ["default", "hover", "active", "disabled"]
    }},
    {{
      "component_name": "Card",
      "description": "Content container with optional header and footer",
      "props": {{"padding": ["sm", "md", "lg"], "shadow": ["none", "sm", "md"]}},
      "states": ["default", "hover"]
    }}
  ],
  "design_rationale": "Brief explanation of key design decisions for this product",
  "implementation_notes": "1) Set up Tailwind with custom theme, 2) Build atomic components first, 3) Implement responsive layouts, 4) Add micro-interactions"
}}
```

**Guidelines:**
- Choose colors appropriate for the product type - these MUST be used consistently across ALL screens
- Include 3-5 wireframes for critical screens - ALL wireframes are DESKTOP ONLY (1440px width)
- NO mobile or tablet variants - only desktop layouts
- Define 2-4 core user flows
- List 4-8 essential components that use the design system colors
- All screens must have consistent navigation/header using the same styling
- Keep the design minimal and implementable for MVP

After creating the JSON, call _write_context_async("design", <json_string>) to save it."""

        response = await self._autogen_agent.run(task=prompt)
        self._record_usage(response)

        # Extract design from context
        design = self.read_context("design")

        if not design:
            logger.warning("[Designer] Design not in context, parsing response")
            try:
                response_text = ""
                if hasattr(response, "messages"):
                    for msg in response.messages:
                        if hasattr(msg, "content"):
                            response_text += str(msg.content)

                logger.info(f"[Designer] Response text length: {len(response_text)}")

                # Try extraction strategies
                design = self._extract_json_from_text(response_text)
                if not design:
                    design = self._extract_any_json(response_text)

                if design:
                    self.write_context("design", design)
                    logger.info("[Designer] Design extracted and saved")
                else:
                    logger.error(f"[Designer] Response sample: {response_text[:1000]}")
                    raise ValueError("No valid design JSON found in response")
            except Exception as e:
                logger.error(f"[Designer] Failed to parse design: {e}")
                raise

        logger.info("[Designer] Design creation complete")

        # Generate wireframe images for each wireframe in the design
        await self._generate_wireframe_images(design)

        return design

    async def _generate_wireframe_images(self, design: dict[str, Any]) -> None:
        """
        Generate wireframe images for all wireframes in the design.

        Args:
            design: The design specification containing wireframes and design_system
        """
        wireframes = design.get("wireframes", [])
        if not wireframes:
            logger.info("[Designer] No wireframes in design to generate images for")
            return

        if not self._image_client:
            logger.warning(
                "[Designer] Gemini image client not available - skipping wireframe image generation"
            )
            return

        # Extract design_system for consistent styling across all wireframes
        design_system = design.get("design_system", {})

        logger.info(
            f"[Designer] Generating images for {len(wireframes)} wireframes with unified styling"
        )

        for wireframe in wireframes:
            screen_name = wireframe.get("screen_name", "Unknown")
            description = wireframe.get("description", "")
            components = wireframe.get("components", [])
            layout = wireframe.get("layout", "")

            # Build full description including layout
            full_description = f"{description}"
            if layout:
                full_description += f"\nLayout: {layout}"

            try:
                result = await self._generate_wireframe_async(
                    screen_name=screen_name,
                    description=full_description,
                    components=components if isinstance(components, list) else [],
                    design_system=design_system,
                )
                logger.info(f"[Designer] Wireframe generated for: {screen_name}")
            except Exception as e:
                logger.error(f"[Designer] Failed to generate wireframe for {screen_name}: {e}")

    async def create_final_designs_async(
        self,
        design: dict[str, Any],
        experiment_dir: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generate polished, production-ready design images.

        Combines wireframe specifications with the design system (styling guide)
        to create visually consistent final designs using Nano Banana Pro.

        Args:
            design: Complete design specification including design_system and wireframes
            experiment_dir: Directory to save design images

        Returns:
            List of generated design metadata with file paths
        """
        wireframes = design.get("wireframes", [])
        if not wireframes:
            logger.info("[Designer] No wireframes in design to generate final designs for")
            return []

        if not self._image_client:
            logger.warning(
                "[Designer] Gemini image client not available - skipping final design generation"
            )
            return []

        # Extract design_system for consistent styling
        design_system = design.get("design_system", {})
        colors = design_system.get("colors", {})
        typography = design_system.get("typography", {})

        # Get color values
        primary_color = colors.get("primary", "#3B82F6")
        secondary_color = colors.get("secondary", "#10B981")
        accent_color = colors.get("accent", "#F59E0B")
        neutral_colors = colors.get("neutral", {})
        background_color = neutral_colors.get("50", "#F9FAFB")
        text_color = neutral_colors.get("900", "#111827")

        # Get typography values
        font_families = typography.get("font_families", {})
        heading_font = font_families.get("heading", "Inter")
        body_font = font_families.get("body", "Inter")

        # Setup output directory
        if experiment_dir:
            output_dir = Path(experiment_dir) / "designs"
        else:
            exp_dir = self.read_context("experiment_dir")
            if exp_dir:
                output_dir = Path(exp_dir) / "designs"
            else:
                output_dir = Path("./experiments/designs")
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"[Designer] Generating {len(wireframes)} polished final designs with unified styling"
        )

        final_designs = []

        for wireframe in wireframes:
            screen_name = wireframe.get("screen_name", "Unknown")
            description = wireframe.get("description", "")
            components = wireframe.get("components", [])
            layout = wireframe.get("layout", "")
            interactions = wireframe.get("interactions", [])

            # Build comprehensive prompt for polished design
            components_text = ", ".join(components) if components else "standard UI components"
            interactions_text = "; ".join(interactions) if interactions else "standard interactions"

            prompt = f"""Create a polished, production-ready UI design for: {screen_name}

## Design System (USE THESE EXACT VALUES):
- Primary Color: {primary_color} (for primary buttons, links, key interactive elements)
- Secondary Color: {secondary_color} (for secondary actions, success states)
- Accent Color: {accent_color} (for highlights, notifications, warnings)
- Background Color: {background_color} (main page background)
- Text Color: {text_color} (headings and body text)
- Heading Font: {heading_font}
- Body Font: {body_font}

## Screen Specification:
{description}

Layout: {layout}
Components: {components_text}
Interactions: {interactions_text}

## CRITICAL Requirements:
- DESKTOP ONLY - 1440px viewport width, NO mobile or tablet versions
- HIGH-FIDELITY UI - This is a FINAL DESIGN, NOT a wireframe
- Use the EXACT colors specified above - do not substitute
- Professional, modern, polished aesthetic
- Include realistic placeholder content (real text, not lorem ipsum)
- Consistent navigation/header that would match other screens in this app
- Clean visual hierarchy with proper spacing
- Modern UI patterns (shadows, rounded corners, proper whitespace)
- Ready for developer implementation"""

            try:
                response = self._image_client.models.generate_content(
                    model=config.llm.gemini_image_model, contents=prompt
                )

                filename = f"{screen_name.replace(' ', '_').lower()}_final.png"
                filepath = output_dir / filename

                # Extract and save image from response
                if (
                    response.candidates
                    and response.candidates[0].content.parts
                    and hasattr(response.candidates[0].content.parts[0], "inline_data")
                ):
                    image_data = response.candidates[0].content.parts[0].inline_data.data
                    with open(filepath, "wb") as f:
                        f.write(image_data)

                    logger.info(f"[Designer] Final design saved: {filepath}")

                    final_designs.append(
                        {
                            "screen_name": screen_name,
                            "filepath": str(filepath),
                            "design_type": "final",
                            "viewport": "desktop-1440px",
                            "colors_used": {
                                "primary": primary_color,
                                "secondary": secondary_color,
                                "accent": accent_color,
                            },
                        }
                    )
                else:
                    logger.warning(f"[Designer] No image in response for {screen_name}")
                    final_designs.append(
                        {
                            "screen_name": screen_name,
                            "filepath": None,
                            "error": "No image generated",
                        }
                    )

            except Exception as e:
                logger.error(f"[Designer] Failed to generate final design for {screen_name}: {e}")
                final_designs.append(
                    {
                        "screen_name": screen_name,
                        "filepath": None,
                        "error": str(e),
                    }
                )

        logger.info(
            f"[Designer] Final design generation complete: {len([d for d in final_designs if d.get('filepath')])} images created"
        )
        return final_designs

    async def create_final_designs_light_async(
        self,
        idea: dict[str, Any],
        design_system: dict[str, Any],
        architecture: dict[str, Any] | None = None,
        experiment_dir: str | None = None,
        mode_config: Any | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generate final design images using a light approach (no wireframe specs needed).

        Auto-derives core screens from the idea and generates consistent
        final design images using the design system colors.

        In extended mode:
        - Generates more screens (8 instead of 4)
        - Includes mobile variants
        - Uses enhanced prompts for higher quality

        Args:
            idea: The startup idea
            design_system: Design system with colors, typography, spacing
            architecture: Optional technical architecture
            experiment_dir: Directory to save design images
            mode_config: Execution mode configuration

        Returns:
            List of generated design metadata with file paths
        """
        from ..config import ExecutionMode, ModeConfig

        mode_config = mode_config or ModeConfig.standard()
        if not self._image_client:
            logger.warning(
                "[Designer] Gemini image client not available - skipping final design generation"
            )
            return []

        if not self._autogen_agent:
            self.create_autogen_agent()

        # Extract design system values
        colors = design_system.get("colors", {})
        typography = design_system.get("typography", {})

        primary_color = colors.get("primary", "#3B82F6")
        secondary_color = colors.get("secondary", "#10B981")
        accent_color = colors.get("accent", "#F59E0B")
        neutral_colors = colors.get("neutral", {})
        background_color = neutral_colors.get("50", "#F9FAFB")
        text_color = neutral_colors.get("900", "#111827")

        font_families = typography.get("font_families", {})
        heading_font = font_families.get("heading", "Inter")
        body_font = font_families.get("body", "Inter")

        # Setup output directory
        if experiment_dir:
            output_dir = Path(experiment_dir) / "designs"
        else:
            exp_dir = self.read_context("experiment_dir")
            if exp_dir:
                output_dir = Path(exp_dir) / "designs"
            else:
                output_dir = Path("./experiments/designs")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Derive screens from idea using LLM
        product_name = idea.get("solution", idea.get("problem", "Product"))[:80]
        problem = idea.get("problem", "N/A")[:300]
        solution = idea.get("solution", "N/A")[:300]

        # Use screen count from mode config
        screen_count = mode_config.design_screen_count
        is_extended = mode_config.mode == ExecutionMode.EXTENDED

        derive_prompt = f"""Based on this startup idea, list exactly {screen_count} core screens needed for the MVP.

Product: {product_name}
Problem: {problem}
Solution: {solution}

Output a JSON array with exactly {screen_count} screens. Each screen should have:
- screen_name: Short name (e.g., "Dashboard", "Landing Page")
- description: Brief description of what this screen shows and its purpose

{"Extended mode: Include comprehensive screens covering the full user journey - landing, authentication, main features, settings, and admin views." if is_extended else "Focus on the 4 most critical screens for MVP."}

Example format:
```json
[
  {{"screen_name": "Landing Page", "description": "Marketing page with hero section, features, and signup CTA"}},
  {{"screen_name": "Dashboard", "description": "Main user dashboard showing key metrics and actions"}},
  {{"screen_name": "Settings", "description": "User settings and preferences page"}},
  {{"screen_name": "Detail View", "description": "Detailed view of the main feature/content"}}
]
```

Output ONLY the JSON array, no other text."""

        logger.info("[Designer] Deriving core screens from idea")

        response = await self._autogen_agent.run(task=derive_prompt)
        self._record_usage(response)

        # Extract screens from response
        screens = []
        response_text = ""
        if hasattr(response, "messages"):
            for msg in response.messages:
                if hasattr(msg, "content"):
                    response_text += str(msg.content)

        extracted_json = self._extract_any_json_array(response_text)
        if extracted_json:
            screens = extracted_json
        else:
            logger.warning("[Designer] Could not extract screens, using defaults")
            default_screens = [
                {
                    "screen_name": "Landing Page",
                    "description": "Marketing page with hero section and signup",
                },
                {"screen_name": "Dashboard", "description": "Main user dashboard with key metrics"},
                {"screen_name": "Profile", "description": "User profile and settings"},
                {
                    "screen_name": "Main Feature",
                    "description": f"Core feature screen for {product_name}",
                },
            ]
            if is_extended:
                default_screens.extend(
                    [
                        {
                            "screen_name": "Login",
                            "description": "User authentication and login page",
                        },
                        {"screen_name": "Registration", "description": "New user signup flow"},
                        {
                            "screen_name": "Analytics",
                            "description": "Detailed analytics and reporting",
                        },
                        {
                            "screen_name": "Admin Panel",
                            "description": "Administrative controls and management",
                        },
                    ]
                )
            screens = default_screens[:screen_count]

        logger.info(
            f"[Designer] Generating {len(screens)} final design images with unified styling"
        )

        # Step 2: Generate images for each screen with strict consistency
        final_designs = []

        # Enhanced quality prompt additions for extended mode
        enhanced_quality_prompt = """
## ENHANCED QUALITY REQUIREMENTS (SHOWCASE MODE)
This is a PREMIUM, SHOWCASE-QUALITY design that must be exceptional:

1. VISUAL POLISH
   - Ultra-high visual polish - museum-quality design
   - Subtle micro-interactions indicated (hover states shown as tooltips)
   - Perfect pixel alignment and spacing throughout
   - Professional photography-quality image placeholders
   - Subtle gradients and depth where appropriate

2. REALISTIC CONTENT
   - All placeholder text must be realistic and contextual
   - Real company names, product features, and descriptions
   - Actual metrics and data visualizations with real numbers
   - No "Lorem ipsum" or placeholder text anywhere

3. ACCESSIBILITY
   - WCAG AA contrast compliance for all text
   - Clear visual hierarchy with proper heading structure
   - Touch-friendly target sizes (minimum 44px)
   - Clear focus states for interactive elements

4. ATTENTION TO DETAIL
   - Consistent 8px grid alignment
   - Careful attention to typography scale
   - Thoughtful empty states and loading indicators
   - Error states and validation feedback shown

5. MODERN AESTHETICS
   - Glass morphism effects where appropriate
   - Subtle shadows with multiple layers
   - Smooth color transitions and gradients
   - Contemporary icon style throughout
"""

        for screen in screens:
            screen_name = screen.get("screen_name", "Unknown")
            description = screen.get("description", "")

            # Build comprehensive prompt with consistency requirements
            base_prompt = f"""Create a polished, production-ready UI design for: {screen_name}

## PRODUCT CONTEXT
Product: {product_name}
Screen Purpose: {description}

## DESIGN SYSTEM (USE THESE EXACT VALUES)
- Primary Color: {primary_color} (for primary buttons, links, key interactive elements)
- Secondary Color: {secondary_color} (for secondary actions, success states)
- Accent Color: {accent_color} (for highlights, notifications, warnings)
- Background Color: {background_color} (main page background)
- Text Color: {text_color} (headings and body text)
- Heading Font: {heading_font}
- Body Font: {body_font}

## CRITICAL CONSISTENCY REQUIREMENTS
All screens in this application MUST look like they belong together:

1. HEADER: Use a navigation bar at the top with:
   - Logo "{product_name}" on the left using {primary_color}
   - Navigation links in the center
   - User avatar on the right
   - Height: 64px
   - Background: white with subtle bottom border

2. LAYOUT: Desktop layout (1440px viewport) with:
   - Content max-width: 1200px (centered)
   - Main content area with consistent padding (24px)
   - Clean whitespace between sections

3. COMPONENTS: All use design system tokens:
   - Primary buttons: {primary_color} background, white text, 8px border-radius
   - Secondary buttons: white background, {primary_color} border and text
   - Cards: White background, subtle shadow, 12px border-radius
   - Text: {text_color} for headings, lighter gray for body

4. FOOTER: Consistent footer at bottom with:
   - Dark background ({text_color})
   - White text for links and copyright
   - Simple layout with key links

## REQUIREMENTS
- DESKTOP ONLY - 1440px viewport width
- HIGH-FIDELITY UI - This is a FINAL DESIGN, NOT a wireframe
- Use the EXACT colors specified above - do not substitute
- Professional, modern, polished aesthetic
- Include realistic placeholder content (real text, not lorem ipsum)
- Clean visual hierarchy with proper spacing
- Modern UI patterns (shadows, rounded corners, proper whitespace)
- Ready for developer implementation

This screen MUST match the exact same visual style as other screens in this app."""

            # Add enhanced quality requirements for extended mode
            if mode_config.enhanced_design_prompts:
                prompt = base_prompt + enhanced_quality_prompt
            else:
                prompt = base_prompt

            try:
                response = self._image_client.models.generate_content(
                    model=config.llm.gemini_image_model, contents=prompt
                )

                filename = f"{screen_name.replace(' ', '_').lower()}_final.png"
                filepath = output_dir / filename

                # Extract and save image from response
                if (
                    response.candidates
                    and response.candidates[0].content.parts
                    and hasattr(response.candidates[0].content.parts[0], "inline_data")
                ):
                    image_data = response.candidates[0].content.parts[0].inline_data.data
                    with open(filepath, "wb") as f:
                        f.write(image_data)

                    logger.info(f"[Designer] Final design saved: {filepath}")

                    final_designs.append(
                        {
                            "screen_name": screen_name,
                            "description": description,
                            "filepath": str(filepath),
                            "design_type": "final",
                            "viewport": "desktop-1440px",
                            "colors_used": {
                                "primary": primary_color,
                                "secondary": secondary_color,
                                "accent": accent_color,
                            },
                        }
                    )

                    # Generate mobile variant in extended mode
                    if mode_config.enable_mobile_variants:
                        mobile_filepath = await self._generate_mobile_variant(
                            screen_name,
                            description,
                            product_name,
                            primary_color,
                            secondary_color,
                            accent_color,
                            background_color,
                            text_color,
                            heading_font,
                            body_font,
                            output_dir,
                            mode_config.enhanced_design_prompts,
                        )
                        if mobile_filepath:
                            final_designs.append(
                                {
                                    "screen_name": f"{screen_name} (Mobile)",
                                    "description": f"Mobile variant of {description}",
                                    "filepath": str(mobile_filepath),
                                    "design_type": "final",
                                    "viewport": "mobile-375px",
                                    "colors_used": {
                                        "primary": primary_color,
                                        "secondary": secondary_color,
                                        "accent": accent_color,
                                    },
                                }
                            )
                else:
                    logger.warning(f"[Designer] No image in response for {screen_name}")
                    final_designs.append(
                        {
                            "screen_name": screen_name,
                            "description": description,
                            "filepath": None,
                            "error": "No image generated",
                        }
                    )

            except Exception as e:
                logger.error(f"[Designer] Failed to generate final design for {screen_name}: {e}")
                final_designs.append(
                    {
                        "screen_name": screen_name,
                        "description": description,
                        "filepath": None,
                        "error": str(e),
                    }
                )

        logger.info(
            f"[Designer] Light design generation complete: {len([d for d in final_designs if d.get('filepath')])} images created"
        )
        return final_designs

    async def _generate_mobile_variant(
        self,
        screen_name: str,
        description: str,
        product_name: str,
        primary_color: str,
        secondary_color: str,
        accent_color: str,
        background_color: str,
        text_color: str,
        heading_font: str,
        body_font: str,
        output_dir: Path,
        enhanced: bool = False,
    ) -> Path | None:
        """
        Generate a mobile variant of a screen design.

        Args:
            screen_name: Name of the screen
            description: Screen description
            product_name: Product name
            primary_color, secondary_color, etc.: Design system colors
            output_dir: Directory to save the image
            enhanced: Whether to use enhanced prompts

        Returns:
            Path to the generated mobile image, or None if generation failed
        """
        mobile_prompt = f"""Create a mobile-responsive UI design for: {screen_name} (Mobile Version)

## PRODUCT CONTEXT
Product: {product_name}
Screen Purpose: {description}

## DESIGN SYSTEM (USE THESE EXACT VALUES)
- Primary Color: {primary_color}
- Secondary Color: {secondary_color}
- Accent Color: {accent_color}
- Background Color: {background_color}
- Text Color: {text_color}
- Heading Font: {heading_font}
- Body Font: {body_font}

## MOBILE-SPECIFIC REQUIREMENTS
- MOBILE VIEWPORT: 375px width (iPhone standard)
- MOBILE NAVIGATION: Hamburger menu icon in header
- TOUCH-FRIENDLY: All buttons minimum 44px height
- STACKED LAYOUT: Content flows vertically
- SIMPLIFIED: Reduce content density for mobile
- THUMB-ZONE: Important actions within easy thumb reach

## MOBILE HEADER
- Height: 56px
- Logo on left
- Hamburger menu icon on right
- No navigation links (hidden in menu)

## MOBILE LAYOUT
- Full-width content (no side margins except 16px padding)
- Larger touch targets
- Simplified navigation
- Single-column layout
- Bottom navigation bar if appropriate

## REQUIREMENTS
- HIGH-FIDELITY UI - This is a FINAL MOBILE DESIGN
- Use EXACT colors from design system
- Modern mobile patterns (bottom sheets, swipe gestures indicated)
- Realistic placeholder content
- Ready for mobile development"""

        if enhanced:
            mobile_prompt += """

## ENHANCED MOBILE QUALITY
- Pixel-perfect mobile design
- Consider safe areas (notch, home indicator)
- Smooth animations indicated
- Native mobile feel (not just scaled desktop)
- Platform-appropriate patterns"""

        try:
            response = self._image_client.models.generate_content(
                model=config.llm.gemini_image_model, contents=mobile_prompt
            )

            filename = f"{screen_name.replace(' ', '_').lower()}_mobile.png"
            filepath = output_dir / filename

            if (
                response.candidates
                and response.candidates[0].content.parts
                and hasattr(response.candidates[0].content.parts[0], "inline_data")
            ):
                image_data = response.candidates[0].content.parts[0].inline_data.data
                with open(filepath, "wb") as f:
                    f.write(image_data)

                logger.info(f"[Designer] Mobile variant saved: {filepath}")
                return filepath
            else:
                logger.warning(f"[Designer] No mobile image generated for {screen_name}")
                return None

        except Exception as e:
            logger.error(f"[Designer] Failed to generate mobile variant for {screen_name}: {e}")
            return None

    def _extract_any_json_array(self, text: str) -> list[dict[str, Any]] | None:
        """
        Extract a JSON array from text.

        Args:
            text: Text potentially containing JSON array

        Returns:
            Parsed JSON array or None
        """
        import re

        # Look for JSON in code blocks first
        code_block_pattern = r"```(?:json)?\s*(\[[\s\S]*?\])\s*```"
        matches = re.findall(code_block_pattern, text)

        for match in matches:
            try:
                obj = json.loads(match)
                if isinstance(obj, list) and len(obj) > 0:
                    return obj
            except json.JSONDecodeError:
                continue

        # Try bracket matching for arrays
        depth = 0
        start = -1

        for i, char in enumerate(text):
            if char == "[":
                if depth == 0:
                    start = i
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        json_str = text[start : i + 1]
                        obj = json.loads(json_str)
                        if isinstance(obj, list) and len(obj) > 0:
                            return obj
                    except json.JSONDecodeError:
                        pass
                    start = -1

        return None

    def create_final_designs_light(
        self,
        idea: dict[str, Any],
        design_system: dict[str, Any],
        architecture: dict[str, Any] | None = None,
        experiment_dir: str | None = None,
        mode_config: Any | None = None,
    ) -> list[dict[str, Any]]:
        """Create final designs using light approach (sync wrapper)."""
        import asyncio

        return asyncio.run(
            self.create_final_designs_light_async(
                idea, design_system, architecture, experiment_dir, mode_config
            )
        )

    def create_final_designs(
        self,
        design: dict[str, Any],
        experiment_dir: str | None = None,
    ) -> list[dict[str, Any]]:
        """Create final designs (sync wrapper)."""
        import asyncio

        return asyncio.run(self.create_final_designs_async(design, experiment_dir))

    def create_design(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
        architecture: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create comprehensive UI/UX design (sync wrapper)."""
        import asyncio

        return asyncio.run(self.create_design_async(idea, research, architecture))

    def create_design_system_only(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
        architecture: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create design system only - no wireframes or user flows (sync wrapper)."""
        import asyncio

        return asyncio.run(self.create_design_system_only_async(idea, research, architecture))

    async def create_design_system_only_async(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
        architecture: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create ONLY the design system (colors, typography, spacing).

        NO wireframes, NO user flows, NO final designs.

        Args:
            idea: The startup idea
            research: Research findings
            architecture: Optional technical architecture

        Returns:
            Design system dict with colors, typography, spacing only
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        self.clear_usage()

        logger.info("[Designer] Creating design system only (no wireframes/user flows)")

        self.write_context("idea", idea)
        self.write_context("research", research)
        if architecture:
            self.write_context("architecture", architecture)

        product_name = idea.get("solution", idea.get("problem", "Product"))[:80]
        target_audience = "General users"
        if isinstance(research, dict):
            target_audience = str(research.get("target_audience", "General users"))[:150]

        prompt = f"""Create a design system for this startup product. Output ONLY colors, typography, and spacing - NO wireframes, NO user flows.

**Product:** {product_name}
**Problem:** {idea.get("problem", "N/A")[:300]}
**Solution:** {idea.get("solution", "N/A")[:300]}
**Target Users:** {target_audience}

**Output a JSON design system with this EXACT structure:**
```json
{{
  "colors": {{
    "primary": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "neutral": {{"50": "#F9FAFB", "100": "#F3F4F6", "900": "#111827"}},
    "semantic": {{"success": "#10B981", "warning": "#F59E0B", "error": "#EF4444"}}
  }},
  "typography": {{
    "font_families": {{"heading": "Font Name", "body": "Font Name", "mono": "Font Name"}},
    "sizes": {{"xs": "12px", "sm": "14px", "base": "16px", "lg": "18px", "xl": "20px", "2xl": "24px"}},
    "weights": {{"normal": 400, "medium": 500, "semibold": 600, "bold": 700}}
  }},
  "spacing": {{
    "base_unit": "8px",
    "scale": [4, 8, 12, 16, 24, 32, 48, 64]
  }},
  "component_tokens": ["Button", "Card", "Input", "Navbar", "Modal"]
}}
```

**Guidelines:**
- Choose colors appropriate for the product type and target audience
- Use professional, accessible color combinations
- Ensure sufficient contrast for readability
- This is ONLY the design system - no wireframes or layouts

After creating the JSON, call _write_context_async("design_system", <json_string>) to save it."""

        response = await self._autogen_agent.run(task=prompt)
        self._record_usage(response)

        design_system = self.read_context("design_system")

        if not design_system:
            logger.warning("[Designer] Design system not in context, parsing response")
            try:
                response_text = ""
                if hasattr(response, "messages"):
                    for msg in response.messages:
                        if hasattr(msg, "content"):
                            response_text += str(msg.content)

                design_system = self._extract_any_json(response_text)
                if design_system:
                    self.write_context("design_system", design_system)
                    logger.info("[Designer] Design system extracted and saved")
                else:
                    raise ValueError("No valid design system JSON found")
            except Exception as e:
                logger.error(f"[Designer] Failed to parse design system: {e}")
                raise

        logger.info("[Designer] Design system creation complete (no wireframes)")
        return design_system

    def _extract_any_json(self, text: str) -> dict[str, Any] | None:
        """
        Extract any valid JSON object from text.

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
                        if isinstance(obj, dict):
                            candidates.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start = -1

        for obj in sorted(candidates, key=lambda x: len(str(x)), reverse=True):
            return obj

        return None

    def _extract_json_from_text(self, text: str) -> dict[str, Any] | None:
        """
        Extract valid JSON object from text.

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

                        # Check if this looks like a design object
                        if isinstance(obj, dict) and any(
                            key in obj
                            for key in [
                                "design_system",
                                "user_flows",
                                "wireframes",
                                "component_library",
                            ]
                        ):
                            candidates.append(obj)
                    except json.JSONDecodeError:
                        pass

                    start = -1

        # Return the largest valid design object
        for obj in sorted(candidates, key=lambda x: len(str(x)), reverse=True):
            if self._is_valid_design(obj):
                logger.info("[Designer] Extracted valid design from text")
                return obj

        return None

    def _extract_any_json(self, text: str) -> dict[str, Any] | None:
        """
        Extract any valid JSON object from text (more flexible fallback).

        Args:
            text: Text potentially containing JSON

        Returns:
            Parsed JSON dict or None
        """
        # Try to find JSON code blocks first
        import re

        # Look for JSON in code blocks
        code_block_pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"
        matches = re.findall(code_block_pattern, text)

        for match in matches:
            try:
                obj = json.loads(match)
                if self._is_valid_design(obj):
                    logger.info("[Designer] Extracted valid design JSON from code block")
                    return obj
            except json.JSONDecodeError:
                continue

        # Try the bracket matching approach but without strict key requirements
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

        # Sort candidates by size and prefer design-like objects
        for obj in sorted(candidates, key=lambda x: len(str(x)), reverse=True):
            if self._is_valid_design(obj):
                logger.info(f"[Designer] Extracted valid design with keys: {list(obj.keys())}")
                return obj

        # If no valid design found, try the largest object with at least 3 keys
        for obj in sorted(candidates, key=lambda x: len(str(x)), reverse=True):
            if len(obj) >= 3:
                logger.warning(
                    f"[Designer] Using fallback JSON (not validated as design): {list(obj.keys())}"
                )
                return obj

        return None

    def _is_valid_design(self, obj: dict[str, Any]) -> bool:
        """
        Check if a JSON object looks like a valid design specification.

        Args:
            obj: JSON object to validate

        Returns:
            True if it looks like a design spec
        """
        if not isinstance(obj, dict):
            return False

        # Must have at least one of the core design keys
        core_keys = ["design_system", "user_flows", "wireframes", "component_library"]
        has_core_key = any(key in obj for key in core_keys)

        if not has_core_key:
            return False

        # If it has design_system, it should have some content
        if "design_system" in obj:
            ds = obj["design_system"]
            if isinstance(ds, dict) and len(ds) > 0:
                return True

        # If it has user_flows, should be a list with content
        if "user_flows" in obj:
            flows = obj["user_flows"]
            if isinstance(flows, list) and len(flows) > 0:
                return True

        # If it has wireframes, should be a list
        if "wireframes" in obj:
            wf = obj["wireframes"]
            if isinstance(wf, list) and len(wf) > 0:
                return True

        # Has a core key but all values are empty - still valid structure
        return has_core_key

    # Additional helper methods for compatibility

    def design_user_flow(self, feature: str) -> dict[str, Any]:
        """
        Design user flow for a feature (legacy method).

        Args:
            feature: The feature to design

        Returns:
            User flow design
        """
        # This is a simplified version - for full design use create_design()
        logger.info(f"[Designer] Designing user flow for: {feature}")

        return {
            "flow_name": feature,
            "steps": ["Step 1: User entry", "Step 2: Main action", "Step 3: Completion"],
            "screens": ["Entry Screen", "Main Screen", "Completion Screen"],
            "note": "For complete design specification, use create_design() method",
        }

    def create_component_library(self) -> dict[str, Any]:
        """
        Create a component library (legacy method).

        Returns:
            Basic component library
        """
        logger.info("[Designer] Creating basic component library")

        return {
            "components": [
                {
                    "component_name": "Button",
                    "props": {"size": ["sm", "md", "lg"], "variant": ["solid", "outline"]},
                },
                {
                    "component_name": "Card",
                    "props": {"padding": ["sm", "md", "lg"], "elevation": [0, 1, 2, 3]},
                },
                {
                    "component_name": "Input",
                    "props": {"type": ["text", "email", "password"], "size": ["sm", "md", "lg"]},
                },
            ],
            "note": "For complete design specification, use create_design() method",
        }
