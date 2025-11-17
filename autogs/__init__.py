"""
AutoGS - Automated Game Studio

A bot-driven pipeline for Unity game development that automates 90% of the labor
while the human "Director" manages the creative vision.
"""

__version__ = "0.1.0"
__author__ = "AutoGS Team"

from .core.pipeline import GamePipeline
from .core.config import PipelineConfig

__all__ = ["GamePipeline", "PipelineConfig", "__version__"]
