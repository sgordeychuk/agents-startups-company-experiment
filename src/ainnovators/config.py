"""Configuration management for AI Innovators."""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class LLMConfig:
    """LLM configuration settings."""

    primary_model: str = "claude-sonnet-4"
    secondary_model: str = "claude-3-5-haiku-latest"
    openai_model: str = "gpt-5.2"
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    serper_api_key: str = field(default_factory=lambda: os.getenv("SERPER_API_KEY", ""))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_pro_model: str = "gemini-2.5-pro"
    gemini_image_model: str = "gemini-3-pro-image-preview"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"


@dataclass
class PipelineConfig:
    """Pipeline execution configuration."""

    max_turns_per_stage: int = 5
    stage_timeout_minutes: int = 30
    max_iterations: int = 3


@dataclass
class CostConfig:
    """Cost control configuration."""

    max_budget_per_experiment: float = 10.00
    track_token_usage: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""

    log_level: str = "INFO"
    log_file: str = "startup_company.log"
    log_to_console: bool = True


@dataclass
class StorageConfig:
    """Storage configuration."""

    experiments_dir: Path = field(default_factory=lambda: Path("./experiments"))
    snapshots_dir: Path = field(default_factory=lambda: Path("./snapshots"))


class ExecutionMode(str, Enum):
    """Pipeline execution mode."""

    STANDARD = "standard"
    EXTENDED = "extended"


@dataclass
class ModeConfig:
    """Mode-specific configuration for standard vs extended execution."""

    mode: ExecutionMode = ExecutionMode.STANDARD

    # Prototyping settings
    enable_code_generation: bool = False
    enable_qa_iteration: bool = False
    enable_docker: bool = False

    # Design settings
    design_screen_count: int = 4
    enable_mobile_variants: bool = False
    enhanced_design_prompts: bool = False

    # Pitch settings
    enhanced_slides_content: bool = False
    include_all_design_images: bool = False

    @classmethod
    def standard(cls) -> ModeConfig:
        """Create standard mode configuration (research-focused, budget-friendly)."""
        return cls(mode=ExecutionMode.STANDARD)

    @classmethod
    def extended(cls) -> ModeConfig:
        """Create extended mode configuration (full prototype, showcase quality)."""
        return cls(
            mode=ExecutionMode.EXTENDED,
            enable_code_generation=True,
            enable_qa_iteration=True,
            enable_docker=True,
            design_screen_count=8,
            enable_mobile_variants=True,
            enhanced_design_prompts=True,
            enhanced_slides_content=True,
            include_all_design_images=True,
        )


@dataclass
class Config:
    """Main configuration container."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    cost: CostConfig = field(default_factory=CostConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    execution: ModeConfig = field(default_factory=ModeConfig)

    @classmethod
    def from_env(cls) -> Config:
        """Create configuration from environment variables."""
        return cls(
            llm=LLMConfig(
                primary_model=os.getenv("PRIMARY_MODEL", "claude-sonnet-4"),
                secondary_model=os.getenv("SECONDARY_MODEL", "claude-3-5-haiku-latest"),
                openai_model=os.getenv("OPENAI_MODEL", "gpt-5.2"),
            ),
            pipeline=PipelineConfig(
                max_turns_per_stage=int(os.getenv("MAX_TURNS_PER_STAGE", "5")),
                stage_timeout_minutes=int(os.getenv("STAGE_TIMEOUT_MINUTES", "30")),
            ),
            cost=CostConfig(
                max_budget_per_experiment=float(os.getenv("MAX_BUDGET_PER_EXPERIMENT", "10.00")),
            ),
            logging=LoggingConfig(
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                log_file=os.getenv("LOG_FILE", "startup_company.log"),
            ),
            storage=StorageConfig(
                experiments_dir=Path(os.getenv("EXPERIMENTS_DIR", "./experiments")),
            ),
        )


# Global config instance
config = Config.from_env()
