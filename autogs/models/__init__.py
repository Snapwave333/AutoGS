"""Data models for the AutoGS pipeline."""

from .game_brief import GameBrief, MarketAnalysis, TrendData
from .gdd import GameDesignDocument, GameMechanic, Quest, AssetManifest
from .assets import AssetCollection, Asset2D, Asset3D, AudioAsset, UIAsset
from .code import CodeComponent, UnityProject
from .build import BuildConfig, BuildOutput

__all__ = [
    "GameBrief",
    "MarketAnalysis",
    "TrendData",
    "GameDesignDocument",
    "GameMechanic",
    "Quest",
    "AssetManifest",
    "AssetCollection",
    "Asset2D",
    "Asset3D",
    "AudioAsset",
    "UIAsset",
    "CodeComponent",
    "UnityProject",
    "BuildConfig",
    "BuildOutput",
]
