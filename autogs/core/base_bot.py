"""Base class for all pipeline bots."""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .config import PipelineConfig


class BaseBot(ABC):
    """
    Abstract base class for all pipeline bots.
    Each bot represents one stage of the game development pipeline.
    """

    def __init__(self, config: PipelineConfig, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or self._setup_logger()
        self.stage_name = self.__class__.__name__
        self.output_dir = self._setup_output_dir()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.result: Optional[Any] = None

    def _setup_logger(self) -> logging.Logger:
        """Set up logging for this bot."""
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f"[%(asctime)s] [{self.__class__.__name__}] %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG if self.config.verbose else logging.INFO)
        return logger

    def _setup_output_dir(self) -> Path:
        """Set up output directory for this bot's stage."""
        stage_dir = self.config.paths.output_base / self.config.project_name / self.stage_name
        stage_dir.mkdir(parents=True, exist_ok=True)
        return stage_dir

    @abstractmethod
    def run(self, input_data: Optional[Any] = None) -> Any:
        """
        Execute the bot's main task.

        Args:
            input_data: Output from the previous stage (if any)

        Returns:
            Output data to be passed to the next stage
        """
        pass

    @abstractmethod
    def validate_input(self, input_data: Optional[Any]) -> bool:
        """
        Validate that the input data is suitable for this bot.

        Args:
            input_data: Input data to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def execute(self, input_data: Optional[Any] = None) -> Any:
        """
        Full execution flow with logging and error handling.

        Args:
            input_data: Output from the previous stage

        Returns:
            Output data for the next stage
        """
        self.logger.info(f"Starting {self.stage_name}...")
        self.start_time = datetime.now()

        try:
            # Validate input
            if not self.validate_input(input_data):
                raise ValueError(f"Invalid input data for {self.stage_name}")

            # Run the main task
            if self.config.dry_run:
                self.logger.info("DRY RUN MODE - Simulating execution")
                self.result = self._dry_run(input_data)
            else:
                self.result = self.run(input_data)

            # Save intermediate results if configured
            if self.config.save_intermediate and self.result is not None:
                self._save_result()

            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            self.logger.info(f"Completed {self.stage_name} in {duration:.2f} seconds")

            return self.result

        except Exception as e:
            self.logger.error(f"Error in {self.stage_name}: {str(e)}")
            self.end_time = datetime.now()
            raise

    def _dry_run(self, input_data: Optional[Any]) -> Any:
        """
        Simulate execution without actually running the bot.
        Override this in subclasses for more specific dry-run behavior.
        """
        self.logger.info(f"Would execute {self.stage_name} with input: {type(input_data)}")
        return None

    def _save_result(self) -> None:
        """Save the result to the output directory."""
        if self.result is None:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_path = self.output_dir / f"result_{timestamp}.json"

        try:
            # Try to serialize the result
            if hasattr(self.result, "to_dict"):
                data = self.result.to_dict()
            elif hasattr(self.result, "__dict__"):
                data = self._make_serializable(self.result.__dict__)
            else:
                data = {"result": str(self.result)}

            with open(result_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            self.logger.debug(f"Saved result to {result_path}")

        except Exception as e:
            self.logger.warning(f"Could not save result: {str(e)}")

    def _make_serializable(self, obj: Any) -> Any:
        """Make an object JSON serializable."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(v) for v in obj]
        elif isinstance(obj, (datetime, Path)):
            return str(obj)
        elif hasattr(obj, "__dict__"):
            return self._make_serializable(obj.__dict__)
        else:
            return obj

    def get_status(self) -> dict:
        """Get current status of the bot."""
        return {
            "stage": self.stage_name,
            "started": self.start_time.isoformat() if self.start_time else None,
            "ended": self.end_time.isoformat() if self.end_time else None,
            "has_result": self.result is not None,
            "output_dir": str(self.output_dir),
        }

    def cleanup(self) -> None:
        """Clean up any temporary resources. Override in subclasses if needed."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False
