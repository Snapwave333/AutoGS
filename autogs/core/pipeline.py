"""Main pipeline orchestrator for AutoGS."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .config import PipelineConfig
from ..bots.trend_scout import TrendScoutBot
from ..bots.gdd_architect import GDDArchitectBot
from ..bots.asset_factory import AssetFactoryBot
from ..bots.engineer import EngineerBot
from ..bots.build_deploy import BuildDeployBot


class GamePipeline:
    """
    Main orchestrator for the Automated Game Studio pipeline.

    The pipeline consists of 5 stages:
    1. Trend Scout - Market research and niche finding
    2. GDD Architect - Game Design Document generation
    3. Asset Factory - AI-powered asset generation
    4. Engineer - Code generation and Unity project setup
    5. Build & Deploy - Compilation and distribution
    """

    STAGE_MAP = {
        1: ("TrendScout", TrendScoutBot),
        2: ("GDDArchitect", GDDArchitectBot),
        3: ("AssetFactory", AssetFactoryBot),
        4: ("Engineer", EngineerBot),
        5: ("BuildDeploy", BuildDeployBot),
    }

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the game development pipeline.

        Args:
            config: Pipeline configuration. Uses default if not provided.
        """
        self.config = config or PipelineConfig.create_default()
        self.logger = self._setup_logger()
        self.results: dict[int, Any] = {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.current_stage: int = 0

        # Initialize output directory
        self.output_dir = self.config.paths.output_base / self.config.project_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logger(self) -> logging.Logger:
        """Set up pipeline logger."""
        logger = logging.getLogger("GamePipeline")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] [Pipeline] %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG if self.config.verbose else logging.INFO)
        return logger

    def run(self, start_stage: int = 1, input_data: Optional[Any] = None) -> dict[int, Any]:
        """
        Execute the full pipeline.

        Args:
            start_stage: Stage to start from (1-5)
            input_data: Optional initial input data

        Returns:
            Dictionary mapping stage numbers to their results
        """
        self.logger.info(f"=== Starting AutoGS Pipeline for '{self.config.project_name}' ===")
        self.start_time = datetime.now()

        # Validate configuration
        errors = self.config.validate()
        if errors:
            self.logger.warning("Configuration warnings:")
            for error in errors:
                self.logger.warning(f"  - {error}")

        # Determine which stages to run
        stages_to_run = [s for s in self.config.run_stages if s >= start_stage]
        self.logger.info(f"Running stages: {stages_to_run}")

        # Execute each stage
        current_data = input_data
        for stage_num in stages_to_run:
            if stage_num not in self.STAGE_MAP:
                self.logger.error(f"Unknown stage: {stage_num}")
                continue

            self.current_stage = stage_num
            stage_name, bot_class = self.STAGE_MAP[stage_num]

            self.logger.info(f"\n{'='*50}")
            self.logger.info(f"STAGE {stage_num}: {stage_name}")
            self.logger.info(f"{'='*50}")

            try:
                # Create and execute the bot
                bot = bot_class(self.config, self.logger)
                current_data = bot.execute(current_data)
                self.results[stage_num] = current_data

                self.logger.info(f"Stage {stage_num} completed successfully")

            except Exception as e:
                self.logger.error(f"Stage {stage_num} failed: {str(e)}")
                self.results[stage_num] = {"error": str(e)}

                # Decide whether to continue or abort
                if not self._should_continue_on_error(stage_num):
                    self.logger.error("Pipeline aborted due to critical error")
                    break

        self.end_time = datetime.now()
        self._save_pipeline_report()

        duration = (self.end_time - self.start_time).total_seconds()
        self.logger.info(f"\n=== Pipeline completed in {duration:.2f} seconds ===")

        return self.results

    def run_single_stage(self, stage_num: int, input_data: Optional[Any] = None) -> Any:
        """
        Run a single pipeline stage.

        Args:
            stage_num: Stage number (1-5)
            input_data: Input data for the stage

        Returns:
            Output from the stage
        """
        if stage_num not in self.STAGE_MAP:
            raise ValueError(f"Unknown stage: {stage_num}")

        stage_name, bot_class = self.STAGE_MAP[stage_num]
        self.logger.info(f"Running single stage: {stage_name}")

        bot = bot_class(self.config, self.logger)
        result = bot.execute(input_data)
        self.results[stage_num] = result

        return result

    def _should_continue_on_error(self, failed_stage: int) -> bool:
        """
        Determine if pipeline should continue after a stage failure.

        Args:
            failed_stage: The stage that failed

        Returns:
            True if pipeline should continue, False to abort
        """
        # Critical stages that must succeed
        critical_stages = {1, 2}  # Trend Scout and GDD are critical
        return failed_stage not in critical_stages

    def _save_pipeline_report(self) -> None:
        """Save a report of the pipeline execution."""
        report = {
            "project_name": self.config.project_name,
            "version": self.config.version,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time
                else 0
            ),
            "stages_run": list(self.results.keys()),
            "stages_successful": [
                k for k, v in self.results.items() if not isinstance(v, dict) or "error" not in v
            ],
            "stages_failed": [
                k for k, v in self.results.items() if isinstance(v, dict) and "error" in v
            ],
            "configuration": {
                "run_stages": self.config.run_stages,
                "dry_run": self.config.dry_run,
                "save_intermediate": self.config.save_intermediate,
            },
        }

        report_path = self.output_dir / "pipeline_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Pipeline report saved to {report_path}")

    def load_stage_result(self, stage_num: int) -> Optional[Any]:
        """
        Load a previously saved stage result.

        Args:
            stage_num: Stage number to load

        Returns:
            The loaded result or None if not found
        """
        if stage_num not in self.STAGE_MAP:
            return None

        stage_name, _ = self.STAGE_MAP[stage_num]
        stage_dir = self.output_dir / stage_name

        if not stage_dir.exists():
            return None

        # Find the most recent result file
        result_files = sorted(stage_dir.glob("result_*.json"), reverse=True)
        if not result_files:
            return None

        with open(result_files[0], "r") as f:
            return json.load(f)

    def get_status(self) -> dict:
        """Get current pipeline status."""
        return {
            "project": self.config.project_name,
            "version": self.config.version,
            "current_stage": self.current_stage,
            "stages_completed": list(self.results.keys()),
            "is_running": self.start_time is not None and self.end_time is None,
            "output_directory": str(self.output_dir),
        }

    def clear_results(self) -> None:
        """Clear all cached results."""
        self.results.clear()
        self.start_time = None
        self.end_time = None
        self.current_stage = 0
        self.logger.info("Pipeline results cleared")

    @classmethod
    def from_config_file(cls, config_path: Path) -> "GamePipeline":
        """
        Create a pipeline from a configuration file.

        Args:
            config_path: Path to the JSON configuration file

        Returns:
            Configured GamePipeline instance
        """
        config = PipelineConfig.load(config_path)
        return cls(config)

    def save_config(self, path: Optional[Path] = None) -> None:
        """
        Save the current configuration to a file.

        Args:
            path: Path to save to. Uses default if not provided.
        """
        if path is None:
            path = self.output_dir / "config.json"

        self.config.save(path)
        self.logger.info(f"Configuration saved to {path}")
