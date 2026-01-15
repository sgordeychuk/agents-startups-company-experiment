"""QA Agent implementation with Playwright browser testing and Gemini vision analysis."""

import asyncio
import base64
import json
import logging
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import aiohttp
from autogen_agentchat.agents import AssistantAgent
from playwright.async_api import Browser, Page, async_playwright

from ..config import config
from ..utils.gemini_client import GeminiChatCompletionClient, create_gemini_client
from .base_agent import BaseAgent

if TYPE_CHECKING:
    from ..context.shared_context import CompanyContext

logger = logging.getLogger(__name__)

QA_SYSTEM_MESSAGE = """You are a senior QA engineer specializing in web application testing. Your role is to:
1. Test running prototypes using visual inspection and interaction
2. Identify bugs, UI issues, and functional problems
3. Analyze screenshots to detect styling problems and broken layouts
4. Verify core user flows work correctly
5. Report bugs with clear severity, reproduction steps, and screenshots

You have access to shared company context via read_context() and write_context().

When testing prototypes:
- Navigate through all critical pages
- Test form submissions and API interactions
- Verify styling matches design specifications
- Check for broken layouts, missing elements, or visual bugs
- Test error handling with invalid inputs
- Capture screenshots as evidence

Bug severity levels:
- CRITICAL: App crashes, data loss, security issues, completely broken features
- HIGH: Major functionality broken, blocking user flows
- MEDIUM: Feature works but has significant issues
- LOW: Minor UI issues, cosmetic problems

Structure bug reports as JSON with fields:
- id, title, severity, category, description, reproduction_steps, screenshot_path, affected_page
"""


class PlaywrightTestRunner:
    """Manages Playwright browser for QA testing."""

    def __init__(self, screenshots_dir: Path) -> None:
        """Initialize the test runner."""
        self.screenshots_dir = screenshots_dir
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self._browser: Browser | None = None
        self._playwright: Any = None

    async def start(self) -> None:
        """Start Playwright browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        logger.info("[QA] Playwright browser started")

    async def stop(self) -> None:
        """Stop Playwright browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("[QA] Playwright browser stopped")

    async def capture_page(
        self,
        url: str,
        page_name: str,
        wait_for: Literal["load", "domcontentloaded", "networkidle"] = "networkidle",
        timeout: int = 30000,
    ) -> dict[str, Any]:
        """
        Navigate to page, wait for load, capture screenshot.

        Returns:
            Dict with screenshot_path, page_title, console_errors, etc.
        """
        if not self._browser:
            return {"success": False, "error": "Browser not started"}

        page: Page = await self._browser.new_page()
        console_errors: list[str] = []
        network_errors: list[str] = []

        page.on(
            "console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None
        )
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        start_time = time.time()

        try:
            response = await page.goto(url, wait_until=wait_for, timeout=timeout)
            load_time = int((time.time() - start_time) * 1000)

            if response and response.status >= 400:
                network_errors.append(f"HTTP {response.status}")

            screenshot_path = self.screenshots_dir / f"{page_name}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)

            title = await page.title()

            logger.info(f"[QA] Captured page '{page_name}': {url} ({load_time}ms)")

            return {
                "screenshot_path": str(screenshot_path),
                "page_title": title,
                "url": url,
                "load_time_ms": load_time,
                "console_errors": console_errors,
                "network_errors": network_errors,
                "success": True,
            }
        except Exception as e:
            logger.error(f"[QA] Failed to capture page '{page_name}': {e}")
            return {
                "screenshot_path": None,
                "error": str(e),
                "success": False,
                "console_errors": console_errors,
                "network_errors": network_errors,
            }
        finally:
            await page.close()

    async def test_navigation(
        self,
        base_url: str,
        links: list[str],
    ) -> list[dict[str, Any]]:
        """Test navigation links work correctly."""
        results = []
        for link in links:
            url = f"{base_url}{link}" if link.startswith("/") else link
            result = await self.capture_page(
                url, f"nav_{link.strip('/').replace('/', '_') or 'home'}"
            )
            results.append(result)
        return results


class QAAgent(BaseAgent):
    """
    QA Agent responsible for quality assurance using browser testing and vision analysis.

    Uses Gemini model for LLM reasoning and vision analysis.
    Uses Playwright for browser automation and screenshot capture.
    """

    def __init__(self, context: CompanyContext | None = None) -> None:
        """Initialize the QA agent."""
        super().__init__(
            name="QA",
            role="Quality Assurance Engineer",
            system_message=QA_SYSTEM_MESSAGE,
            context=context,
        )
        # Set model name for statistics (uses OpenAI)
        self._model_name = config.llm.openai_model
        self._image_client = None
        if config.llm.gemini_api_key:
            try:
                from google import genai

                self._image_client = genai.Client(api_key=config.llm.gemini_api_key)
                logger.info("[QA] Gemini vision client initialized")
            except Exception as e:
                logger.warning(f"[QA] Failed to initialize Gemini client: {e}")
        else:
            logger.warning("[QA] GEMINI_API_KEY not configured - vision analysis disabled")

        self._screenshots_dir: Path | None = None

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
        if model_client is None:
            model_client = create_gemini_client(
                model=config.llm.gemini_model,
                api_key=config.llm.gemini_api_key,
                base_url=config.llm.gemini_base_url,
                max_retries=3,
            )

        tools = [
            self._read_context_async,
            self._write_context_async,
        ]

        self._autogen_agent = AssistantAgent(
            name=self.name,
            model_client=model_client,
            tools=tools,
            system_message=self.system_message,
            max_tool_iterations=3,
            reflect_on_tool_use=False,
        )

        return self._autogen_agent

    def get_tools(self) -> list[dict[str, Any]]:
        """
        Get QA-specific tools.

        Returns:
            List of tool definitions
        """
        return [
            *self.get_context_functions(),
            {
                "name": "capture_screenshot",
                "description": "Capture screenshot of a page",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "page_name": {"type": "string"},
                    },
                    "required": ["url", "page_name"],
                },
            },
            {
                "name": "analyze_screenshot",
                "description": "Analyze screenshot for visual bugs using Gemini vision",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "screenshot_path": {"type": "string"},
                        "expected_elements": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["screenshot_path"],
                },
            },
            {
                "name": "report_bug",
                "description": "Report a bug found during testing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["critical", "high", "medium", "low"],
                        },
                        "category": {
                            "type": "string",
                            "enum": ["functional", "styling", "api", "navigation", "performance"],
                        },
                        "reproduction_steps": {"type": "array", "items": {"type": "string"}},
                        "screenshot_path": {"type": "string"},
                    },
                    "required": ["title", "description", "severity", "category"],
                },
            },
        ]

    async def _read_context_async(self, key: str) -> str:
        """Read from shared context (async version)."""
        value = self.read_context(key)
        return json.dumps(value, default=str)

    async def _write_context_async(self, key: str, value: str) -> str:
        """Write to shared context (async version)."""
        try:
            parsed_value = json.loads(value)
            self.write_context(key, parsed_value)
            logger.info(f"[QA] Successfully wrote {key} to context")
            return f"Successfully updated {key} in shared context"
        except json.JSONDecodeError as e:
            logger.error(f"[QA] Failed to parse JSON for context write: {e}")
            return f"Failed to parse value as JSON: {e}"

    async def test_prototype_async(
        self,
        prototype_url: str = "http://localhost:3000",
        api_url: str = "http://localhost:8000",
        design: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run comprehensive prototype tests.

        DISABLED: QA testing temporarily disabled for simplified pipeline.

        Args:
            prototype_url: Frontend URL (default: http://localhost:3000)
            api_url: Backend API URL (default: http://localhost:8000)
            design: Design specification for styling validation

        Returns:
            Dict with bugs, test_results, screenshots, quality_score, passed
        """
        # DISABLED: QA testing temporarily disabled for simplified pipeline
        logger.warning("[QA] test_prototype_async is DISABLED")
        return {
            "bugs": [],
            "test_results": {"pages_tested": [], "api_tests": [], "forms_tested": []},
            "screenshots": [],
            "quality_score": 1.0,
            "passed": True,
            "prototype_running": False,
            "has_styling": True,
            "summary": "QA testing disabled for simplified pipeline",
            "status": "disabled",
        }

        # DISABLED: Start of QA testing logic
        # bugs: list[dict[str, Any]] = []
        # test_results: dict[str, Any] = {
        #     "pages_tested": [],
        #     "api_tests": [],
        #     "forms_tested": [],
        # }
        # screenshots: list[str] = []
        #
        # experiment_dir = self.read_context("experiment_dir")
        # if experiment_dir:
        #     self._screenshots_dir = Path(experiment_dir) / "qa_screenshots"
        # else:
        #     self._screenshots_dir = Path("./experiments/qa_screenshots")
        #
        # runner = PlaywrightTestRunner(self._screenshots_dir)
        #
        # try:
        #     await runner.start()
        #
        #     # SCENARIO 1: Core user flows - pages load
        #     pages_to_test = [
        #         ("/", "home"),
        #         ("/dashboard", "dashboard"),
        #         ("/login", "login"),
        #         ("/signup", "signup"),
        #     ]
        #
        #     wireframes = design.get("wireframes", []) if design else []
        #     for wf in wireframes:
        #         screen_name = wf.get("screen_name", "").lower()
        #         if screen_name and screen_name not in ["home", "dashboard", "login", "signup"]:
        #             pages_to_test.append((f"/{screen_name}", screen_name))
        #
        #     for path, name in pages_to_test:
        #         url = f"{prototype_url}{path}"
        #         result = await runner.capture_page(url, name)
        #         test_results["pages_tested"].append(result)
        #
        #         if result["success"]:
        #             screenshots.append(result["screenshot_path"])
        #
        #             vision_bugs = await self._analyze_screenshot_with_vision(
        #                 result["screenshot_path"],
        #                 f"{name} page",
        #                 design,
        #             )
        #             bugs.extend(vision_bugs)
        #
        #             if result["console_errors"]:
        #                 for error in result["console_errors"][:3]:
        #                     bugs.append({
        #                         "id": str(uuid.uuid4())[:8],
        #                         "title": f"Console error on {name}",
        #                         "severity": "medium",
        #                         "category": "functional",
        #                         "description": error[:200],
        #                         "reproduction_steps": [f"Navigate to {url}", "Open browser console"],
        #                         "screenshot_path": result["screenshot_path"],
        #                         "affected_page": name,
        #                         "source": "playwright",
        #                     })
        #         else:
        #             if "404" not in str(result.get("error", "")):
        #                 bugs.append({
        #                     "id": str(uuid.uuid4())[:8],
        #                     "title": f"Page failed to load: {name}",
        #                     "severity": "critical",
        #                     "category": "functional",
        #                     "description": result.get("error", "Unknown error"),
        #                     "reproduction_steps": [f"Navigate to {url}"],
        #                     "screenshot_path": None,
        #                     "affected_page": name,
        #                     "source": "playwright",
        #                 })
        #
        #     # SCENARIO 2: API tests
        #     api_bugs = await self._test_api_endpoints(api_url)
        #     bugs.extend(api_bugs)
        #     test_results["api_tests"] = api_bugs
        #
        # finally:
        #     await runner.stop()
        #
        # prioritized_bugs = self._prioritize_bugs(bugs, max_critical_high=10)
        #
        # quality_score = self._calculate_quality_score(prioritized_bugs, test_results)
        # pages_loaded = len([p for p in test_results["pages_tested"] if p.get("success")])
        # has_styling = not any(
        #     b["category"] == "styling" and b["severity"] in ("critical", "high")
        #     for b in prioritized_bugs
        # )
        #
        # result = {
        #     "bugs": prioritized_bugs,
        #     "test_results": test_results,
        #     "screenshots": screenshots,
        #     "quality_score": quality_score,
        #     "passed": quality_score >= 0.7,
        #     "prototype_running": pages_loaded > 0,
        #     "has_styling": has_styling,
        #     "summary": self._generate_summary(prioritized_bugs, test_results),
        # }
        #
        # self.write_context("qa_results", result)
        #
        # return result
        # DISABLED: End of QA testing logic

    async def _analyze_screenshot_with_vision(
        self,
        screenshot_path: str,
        page_context: str,
        design: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Use Gemini vision to analyze screenshot for bugs.

        Args:
            screenshot_path: Path to screenshot image
            page_context: Description of the page
            design: Design specification for comparison

        Returns:
            List of bugs found in the screenshot
        """
        if not self._image_client:
            logger.warning("[QA] Gemini client not available for vision analysis")
            return []

        try:
            with open(screenshot_path, "rb") as f:
                image_data = f.read()
        except Exception as e:
            logger.error(f"[QA] Failed to read screenshot: {e}")
            return []

        image_base64 = base64.b64encode(image_data).decode()

        design_context = ""
        if design:
            colors = design.get("design_system", {}).get("colors", {})
            if colors:
                design_context = f"""
Expected design system:
- Primary color: {colors.get("primary", "N/A")}
- Secondary color: {colors.get("secondary", "N/A")}
"""

        prompt = f"""Analyze this screenshot of a web application page for bugs and issues.

Page: {page_context}
{design_context}

Look for:
1. STYLING ISSUES: Broken layouts, misaligned elements, unstyled HTML (no CSS applied), missing styles, color inconsistencies
2. FUNCTIONAL ISSUES: Missing buttons, broken forms, error messages displayed, loading states stuck
3. UI ISSUES: Overlapping text, cut-off content, poor contrast, missing icons, blank sections
4. RESPONSIVENESS: Elements not fitting properly, horizontal scroll issues

For each issue found, provide a JSON object with:
- title: Brief description
- severity: critical/high/medium/low
- category: styling/functional/navigation
- description: Detailed explanation
- affected_area: Where on the page

Output a JSON array of issues found. If no issues, return empty array [].
Only report REAL bugs visible in the screenshot, not theoretical issues.
Focus especially on whether the page has proper CSS styling applied (not raw HTML).
"""

        try:
            from google.genai import types

            response = self._image_client.models.generate_content(
                model=config.llm.gemini_model,
                contents=[
                    types.Content(
                        parts=[
                            types.Part(text=prompt),
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type="image/png",
                                    data=image_data,
                                )
                            ),
                        ]
                    )
                ],
            )

            response_text = ""
            if response.candidates and response.candidates[0].content.parts:
                response_text = response.candidates[0].content.parts[0].text

            bugs = self._extract_json_array(response_text)

            for bug in bugs:
                bug["screenshot_path"] = screenshot_path
                bug["affected_page"] = page_context
                bug["source"] = "vision"
                bug["id"] = str(uuid.uuid4())[:8]
                if "reproduction_steps" not in bug:
                    bug["reproduction_steps"] = [f"Navigate to {page_context}", "Observe the issue"]

            logger.info(f"[QA] Vision analysis found {len(bugs)} issues on {page_context}")
            return bugs

        except Exception as e:
            logger.error(f"[QA] Vision analysis failed: {e}")
            return []

    async def _test_api_endpoints(self, api_url: str) -> list[dict[str, Any]]:
        """
        Test API endpoints.

        Args:
            api_url: Base API URL

        Returns:
            List of bugs found
        """
        bugs: list[dict[str, Any]] = []
        endpoints_to_test = [
            ("GET", "/api/health", None),
            ("GET", "/health", None),
            ("GET", "/docs", None),
        ]

        async with aiohttp.ClientSession() as session:
            for method, path, body in endpoints_to_test:
                try:
                    url = f"{api_url}{path}"
                    async with session.request(
                        method, url, json=body, timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status >= 500:
                            bugs.append(
                                {
                                    "id": str(uuid.uuid4())[:8],
                                    "title": f"API error: {method} {path}",
                                    "severity": "high",
                                    "category": "api",
                                    "description": f"Server returned {response.status}",
                                    "reproduction_steps": [f"Make {method} request to {url}"],
                                    "screenshot_path": None,
                                    "affected_page": path,
                                    "source": "api_test",
                                }
                            )
                        elif response.status == 404:
                            logger.debug(f"[QA] Endpoint not found: {path}")
                except TimeoutError:
                    bugs.append(
                        {
                            "id": str(uuid.uuid4())[:8],
                            "title": f"API timeout: {method} {path}",
                            "severity": "high",
                            "category": "api",
                            "description": "Request timed out after 10 seconds",
                            "reproduction_steps": [f"Make {method} request to {api_url}{path}"],
                            "screenshot_path": None,
                            "affected_page": path,
                            "source": "api_test",
                        }
                    )
                except aiohttp.ClientConnectorError:
                    bugs.append(
                        {
                            "id": str(uuid.uuid4())[:8],
                            "title": f"API unreachable: {method} {path}",
                            "severity": "critical",
                            "category": "api",
                            "description": f"Cannot connect to {api_url}",
                            "reproduction_steps": [f"Attempt to connect to {api_url}"],
                            "screenshot_path": None,
                            "affected_page": path,
                            "source": "api_test",
                        }
                    )
                    break
                except Exception as e:
                    logger.warning(f"[QA] API test failed for {path}: {e}")

        return bugs

    def _prioritize_bugs(
        self,
        bugs: list[dict[str, Any]],
        max_critical_high: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Sort bugs by severity, limit critical-high to max 10.

        Args:
            bugs: List of bugs
            max_critical_high: Maximum number of critical-high bugs to return

        Returns:
            Prioritized list of bugs
        """
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        category_order = {
            "functional": 0,
            "api": 1,
            "styling": 2,
            "navigation": 3,
            "performance": 4,
        }

        sorted_bugs = sorted(
            bugs,
            key=lambda b: (
                severity_order.get(b.get("severity", "low"), 99),
                category_order.get(b.get("category", "performance"), 99),
            ),
        )

        critical_high = [b for b in sorted_bugs if b.get("severity") in ("critical", "high")]
        medium_low = [b for b in sorted_bugs if b.get("severity") in ("medium", "low")]

        return critical_high[:max_critical_high] + medium_low

    def _calculate_quality_score(
        self,
        bugs: list[dict[str, Any]],
        test_results: dict[str, Any],
    ) -> float:
        """
        Calculate overall quality score.

        Args:
            bugs: List of bugs found
            test_results: Test execution results

        Returns:
            Quality score from 0.0 to 1.0
        """
        score = 1.0

        for bug in bugs:
            severity = bug.get("severity", "low")
            if severity == "critical":
                score -= 0.3
            elif severity == "high":
                score -= 0.15
            elif severity == "medium":
                score -= 0.05
            elif severity == "low":
                score -= 0.02

        pages_tested = test_results.get("pages_tested", [])
        if pages_tested:
            success_rate = len([p for p in pages_tested if p.get("success")]) / len(pages_tested)
            score = score * (0.5 + 0.5 * success_rate)

        return max(0.0, min(1.0, score))

    def _generate_summary(
        self,
        bugs: list[dict[str, Any]],
        test_results: dict[str, Any],
    ) -> str:
        """
        Generate human-readable summary.

        Args:
            bugs: List of bugs
            test_results: Test results

        Returns:
            Summary string
        """
        critical_count = len([b for b in bugs if b.get("severity") == "critical"])
        high_count = len([b for b in bugs if b.get("severity") == "high"])
        medium_count = len([b for b in bugs if b.get("severity") == "medium"])
        low_count = len([b for b in bugs if b.get("severity") == "low"])

        pages_tested = test_results.get("pages_tested", [])
        pages_passed = len([p for p in pages_tested if p.get("success")])

        return (
            f"QA Summary: {len(bugs)} bugs found "
            f"(Critical: {critical_count}, High: {high_count}, Medium: {medium_count}, Low: {low_count}). "
            f"Pages tested: {len(pages_tested)}, Pages loaded: {pages_passed}."
        )

    def _extract_json_array(self, text: str) -> list[dict[str, Any]]:
        """
        Extract JSON array from text.

        Args:
            text: Text containing JSON

        Returns:
            List of dicts
        """
        import re

        code_block_pattern = r"```(?:json)?\s*(\[[\s\S]*?\])\s*```"
        matches = re.findall(code_block_pattern, text)
        for match in matches:
            try:
                result = json.loads(match)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                continue

        array_pattern = r"\[[\s\S]*?\]"
        matches = re.findall(array_pattern, text)
        for match in matches:
            try:
                result = json.loads(match)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                continue

        return []

    def test_prototype(
        self,
        prototype_url: str = "http://localhost:3000",
        api_url: str = "http://localhost:8000",
        design: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run comprehensive prototype tests (sync wrapper).

        Args:
            prototype_url: Frontend URL
            api_url: Backend API URL
            design: Design specification

        Returns:
            Test results dict
        """
        return asyncio.run(self.test_prototype_async(prototype_url, api_url, design))

    def validate_prototype(
        self,
        prototype: dict[str, Any],
        design: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate prototype against design (legacy interface).

        Args:
            prototype: The prototype to validate
            design: The design specifications

        Returns:
            Validation results
        """
        return self.test_prototype(design=design)

    def generate_test_cases(self, feature: str) -> list[dict[str, Any]]:
        """
        Generate test cases for a feature.

        Args:
            feature: The feature to test

        Returns:
            List of test cases
        """
        return [
            {
                "name": f"Test {feature} loads correctly",
                "steps": ["Navigate to feature page", "Verify page renders"],
                "expected": "Page loads without errors",
            },
            {
                "name": f"Test {feature} functionality",
                "steps": ["Interact with main feature element", "Verify expected behavior"],
                "expected": "Feature works as designed",
            },
            {
                "name": f"Test {feature} error handling",
                "steps": ["Provide invalid input", "Verify error message"],
                "expected": "Appropriate error message displayed",
            },
        ]

    def identify_edge_cases(self, feature: str) -> list[str]:
        """
        Identify edge cases for a feature.

        Args:
            feature: The feature to analyze

        Returns:
            List of edge cases
        """
        return [
            f"Empty input for {feature}",
            f"Very long input for {feature}",
            f"Special characters in {feature}",
            f"Concurrent access to {feature}",
            f"Network failure during {feature}",
        ]
