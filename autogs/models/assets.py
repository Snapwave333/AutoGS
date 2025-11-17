"""Data models for Stage 3: Asset Factory Bot output."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum


class AssetStatus(Enum):
    """Status of asset generation."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


@dataclass
class BaseAsset:
    """Base class for all assets."""

    id: str
    name: str
    description: str
    file_path: Optional[Path] = None
    status: AssetStatus = AssetStatus.PENDING
    generation_prompt: str = ""
    generation_params: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class Asset2D(BaseAsset):
    """2D art asset (textures, sprites, UI elements)."""

    width: int = 512
    height: int = 512
    format: str = "png"
    style: str = "stylized"
    transparency: bool = False
    tileable: bool = False
    source_api: str = "recraft"  # recraft, midjourney, dalle, etc.


@dataclass
class Asset3D(BaseAsset):
    """3D model asset."""

    poly_count: str = "low"  # low, medium, high
    format: str = "fbx"  # fbx, obj, glb
    textured: bool = True
    rigged: bool = False
    animated: bool = False
    lod_levels: int = 1
    source_api: str = "meshy"  # meshy, point-e, etc.


@dataclass
class AudioAsset(BaseAsset):
    """Audio asset (SFX or music)."""

    duration: float = 1.0  # seconds
    format: str = "wav"
    sample_rate: int = 44100
    is_music: bool = False
    loopable: bool = False
    variations: int = 1
    source_api: str = "elevenlabs"  # elevenlabs, mubert, etc.


@dataclass
class UIAsset(BaseAsset):
    """UI/UX element."""

    element_type: str = "button"  # button, panel, icon, etc.
    width: int = 256
    height: int = 64
    states: list[str] = field(default_factory=lambda: ["normal"])
    theme: str = "sci-fi"
    source_api: str = "uizard"


@dataclass
class AnimationAsset(BaseAsset):
    """Animation clip."""

    target_model: str = ""
    duration: float = 1.0
    frame_rate: int = 30
    format: str = "anim"
    keyframes: int = 0


@dataclass
class AssetCollection:
    """
    The output of Stage 3: Asset Factory Bot.
    Collection of all generated assets.
    """

    project_name: str
    assets_2d: list[Asset2D] = field(default_factory=list)
    assets_3d: list[Asset3D] = field(default_factory=list)
    audio_assets: list[AudioAsset] = field(default_factory=list)
    ui_assets: list[UIAsset] = field(default_factory=list)
    animations: list[AnimationAsset] = field(default_factory=list)
    output_directory: Optional[Path] = None
    created_at: datetime = field(default_factory=datetime.now)

    def total_assets(self) -> int:
        """Get total number of assets."""
        return (
            len(self.assets_2d)
            + len(self.assets_3d)
            + len(self.audio_assets)
            + len(self.ui_assets)
            + len(self.animations)
        )

    def completed_assets(self) -> int:
        """Get number of completed assets."""
        count = 0
        for asset_list in [
            self.assets_2d,
            self.assets_3d,
            self.audio_assets,
            self.ui_assets,
            self.animations,
        ]:
            count += sum(1 for a in asset_list if a.status == AssetStatus.COMPLETED)
        return count

    def failed_assets(self) -> int:
        """Get number of failed assets."""
        count = 0
        for asset_list in [
            self.assets_2d,
            self.assets_3d,
            self.audio_assets,
            self.ui_assets,
            self.animations,
        ]:
            count += sum(1 for a in asset_list if a.status == AssetStatus.FAILED)
        return count

    def progress_percentage(self) -> float:
        """Get overall progress as percentage."""
        total = self.total_assets()
        if total == 0:
            return 100.0
        return (self.completed_assets() / total) * 100

    def get_summary(self) -> str:
        """Get a summary of the asset collection."""
        return f"""
=== ASSET COLLECTION: {self.project_name} ===
Total Assets: {self.total_assets()}
Completed: {self.completed_assets()}
Failed: {self.failed_assets()}
Progress: {self.progress_percentage():.1f}%

Breakdown:
- 2D Assets: {len(self.assets_2d)}
- 3D Models: {len(self.assets_3d)}
- Audio: {len(self.audio_assets)}
- UI Elements: {len(self.ui_assets)}
- Animations: {len(self.animations)}

Output Directory: {self.output_directory or 'Not set'}
Created: {self.created_at.strftime('%Y-%m-%d %H:%M')}
==========================================
"""
