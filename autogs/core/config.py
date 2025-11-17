"""Configuration management for AutoGS pipeline."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class APIConfig:
    """Configuration for external API services."""

    # LLM APIs
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "openai"  # openai, anthropic, local
    llm_model: str = "gpt-4"

    # Asset Generation APIs
    recraft_api_key: str = ""
    meshy_api_key: str = ""
    elevenlabs_api_key: str = ""

    # Data Sources
    steam_api_key: str = ""


@dataclass
class PathConfig:
    """Configuration for file paths."""

    output_base: Path = field(default_factory=lambda: Path("./output"))
    templates_dir: Path = field(default_factory=lambda: Path("./autogs/templates"))
    unity_editor_path: str = ""
    project_path: Optional[Path] = None

    def __post_init__(self):
        if isinstance(self.output_base, str):
            self.output_base = Path(self.output_base)
        if isinstance(self.templates_dir, str):
            self.templates_dir = Path(self.templates_dir)
        if isinstance(self.project_path, str):
            self.project_path = Path(self.project_path)


@dataclass
class TrendScoutConfig:
    """Configuration for Trend Scout Bot."""

    sources: list[str] = field(default_factory=lambda: ["steam", "itch", "tiktok"])
    max_results: int = 100
    sentiment_threshold: float = 0.6
    velocity_threshold: float = 2.0  # 200% increase
    lookback_days: int = 30


@dataclass
class GDDArchitectConfig:
    """Configuration for GDD Architect Bot."""

    detail_level: str = "comprehensive"  # basic, standard, comprehensive
    include_monetization: bool = True
    include_analytics: bool = True
    max_mechanics: int = 10
    max_quests: int = 20


@dataclass
class AssetFactoryConfig:
    """Configuration for Asset Factory Bot."""

    default_2d_size: tuple = (512, 512)
    default_3d_poly: str = "low"
    max_concurrent_generations: int = 5
    retry_failed: bool = True
    max_retries: int = 3
    output_format_3d: str = "fbx"
    output_format_2d: str = "png"
    output_format_audio: str = "wav"


@dataclass
class EngineerConfig:
    """Configuration for Engineer Bot."""

    unity_version: str = "2022.3.0f1"
    render_pipeline: str = "URP"
    code_style: str = "standard"  # standard, minimal, verbose
    include_comments: bool = True
    include_tests: bool = False
    namespace_prefix: str = "Game"


@dataclass
class BuildConfig:
    """Configuration for Build Bot."""

    target_platforms: list[str] = field(
        default_factory=lambda: ["windows_64", "android"]
    )
    development_build: bool = False
    compression: str = "lz4"
    auto_increment_version: bool = True


@dataclass
class PipelineConfig:
    """Main configuration for the entire pipeline."""

    # Project
    project_name: str = "MyGame"
    version: str = "0.1.0"

    # Sub-configs
    api: APIConfig = field(default_factory=APIConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    trend_scout: TrendScoutConfig = field(default_factory=TrendScoutConfig)
    gdd_architect: GDDArchitectConfig = field(default_factory=GDDArchitectConfig)
    asset_factory: AssetFactoryConfig = field(default_factory=AssetFactoryConfig)
    engineer: EngineerConfig = field(default_factory=EngineerConfig)
    build: BuildConfig = field(default_factory=BuildConfig)

    # Pipeline behavior
    run_stages: list[int] = field(default_factory=lambda: [1, 2, 3, 4, 5])
    save_intermediate: bool = True
    verbose: bool = True
    dry_run: bool = False

    def save(self, path: Path) -> None:
        """Save configuration to JSON file."""
        config_dict = self._to_serializable_dict()
        with open(path, "w") as f:
            json.dump(config_dict, f, indent=2)

    def _to_serializable_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        result = asdict(self)
        # Convert Path objects to strings
        result["paths"]["output_base"] = str(self.paths.output_base)
        result["paths"]["templates_dir"] = str(self.paths.templates_dir)
        if self.paths.project_path:
            result["paths"]["project_path"] = str(self.paths.project_path)
        return result

    @classmethod
    def load(cls, path: Path) -> "PipelineConfig":
        """Load configuration from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)

        # Reconstruct nested configs
        api_config = APIConfig(**data.get("api", {}))
        paths_config = PathConfig(**data.get("paths", {}))
        trend_scout_config = TrendScoutConfig(**data.get("trend_scout", {}))
        gdd_architect_config = GDDArchitectConfig(**data.get("gdd_architect", {}))
        asset_factory_config = AssetFactoryConfig(**data.get("asset_factory", {}))
        engineer_config = EngineerConfig(**data.get("engineer", {}))
        build_config_data = data.get("build", {})
        build_config = BuildConfig(**build_config_data)

        return cls(
            project_name=data.get("project_name", "MyGame"),
            version=data.get("version", "0.1.0"),
            api=api_config,
            paths=paths_config,
            trend_scout=trend_scout_config,
            gdd_architect=gdd_architect_config,
            asset_factory=asset_factory_config,
            engineer=engineer_config,
            build=build_config,
            run_stages=data.get("run_stages", [1, 2, 3, 4, 5]),
            save_intermediate=data.get("save_intermediate", True),
            verbose=data.get("verbose", True),
            dry_run=data.get("dry_run", False),
        )

    @classmethod
    def create_default(cls) -> "PipelineConfig":
        """Create a default configuration."""
        return cls()

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # Check API keys based on what's needed
        if not self.api.openai_api_key and not self.api.anthropic_api_key:
            errors.append("No LLM API key configured (OpenAI or Anthropic)")

        # Check paths
        if not self.paths.unity_editor_path and 4 in self.run_stages:
            errors.append("Unity Editor path not set (required for code generation)")

        # Check stages
        if not self.run_stages:
            errors.append("No stages configured to run")

        return errors
