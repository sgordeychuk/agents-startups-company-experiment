"""Robust Gemini model client wrapper for AutoGen.

This module provides a wrapper around OpenAIChatCompletionClient that handles
the Gemini API's quirks, particularly empty or null 'choices' responses.
"""

import asyncio
import logging
from collections.abc import Mapping, Sequence
from typing import Any

from autogen_core.models import (
    CreateResult,
    LLMMessage,
    ModelInfo,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient

logger = logging.getLogger(__name__)


class GeminiChatCompletionClient(OpenAIChatCompletionClient):
    """
    A wrapper around OpenAIChatCompletionClient that handles Gemini API quirks.

    Gemini's OpenAI-compatible API sometimes returns HTTP 200 with empty or null
    'choices' array. This wrapper catches those cases and retries or raises
    meaningful errors.
    """

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str,
        model_info: ModelInfo | None = None,
        max_retries: int = 5,
        retry_delay: float = 2.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Gemini-safe client.

        Args:
            model: Model name (e.g., gemini-2.0-flash-exp)
            api_key: Gemini API key
            base_url: Gemini OpenAI-compatible base URL
            model_info: Model capabilities info
            max_retries: Number of retries on empty response
            retry_delay: Delay between retries in seconds
            **kwargs: Additional arguments for OpenAIChatCompletionClient
        """
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            model_info=model_info,
            **kwargs,
        )
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    async def create(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Any] = [],
        json_output: bool | type[Any] | None = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Any | None = None,
    ) -> CreateResult:
        """
        Create a chat completion with retry logic for empty responses.

        Args:
            messages: Input messages
            tools: Available tools
            json_output: JSON output mode
            extra_create_args: Additional API arguments
            cancellation_token: Cancellation token

        Returns:
            CreateResult from the model

        Raises:
            RuntimeError: If all retries fail with empty responses
        """
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                result = await super().create(
                    messages=messages,
                    tools=tools,
                    json_output=json_output,
                    extra_create_args=extra_create_args,
                    cancellation_token=cancellation_token,
                )
                return result

            except TypeError as e:
                if "'NoneType' object is not subscriptable" in str(e):
                    last_error = e
                    logger.warning(
                        f"[GeminiClient] Gemini returned empty response "
                        f"(attempt {attempt + 1}/{self._max_retries})"
                    )

                    if attempt < self._max_retries - 1:
                        # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                        await asyncio.sleep(self._retry_delay * (2**attempt))
                        continue
                else:
                    raise

            except Exception as e:
                logger.error(f"[GeminiClient] Unexpected error: {e}")
                raise

        error_msg = (
            f"Gemini API returned empty 'choices' after {self._max_retries} attempts. "
            "This usually indicates content filtering or an internal API error. "
            "Try simplifying the prompt or using a different model."
        )
        logger.error(f"[GeminiClient] {error_msg}")
        raise RuntimeError(error_msg) from last_error


def create_gemini_client(
    model: str,
    api_key: str,
    base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/",
    max_retries: int = 5,
) -> GeminiChatCompletionClient:
    """
    Factory function to create a Gemini-safe model client.

    Args:
        model: Gemini model name
        api_key: Gemini API key
        base_url: OpenAI-compatible endpoint URL
        max_retries: Number of retries on empty response

    Returns:
        GeminiChatCompletionClient instance
    """
    return GeminiChatCompletionClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
        model_info=ModelInfo(
            vision=True,
            function_calling=True,
            json_output=True,
            family="unknown",
            structured_output=True,
        ),
        max_retries=max_retries,
    )
