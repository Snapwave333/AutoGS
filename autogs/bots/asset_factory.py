"""
Stage 3: Asset Factory Bot
AI-powered asset generation from GDD requirements.
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..core.base_bot import BaseBot
from ..core.config import PipelineConfig
from ..models.gdd import GameDesignDocument, AssetRequirement
from ..models.assets import (
    AssetCollection,
    Asset2D,
    Asset3D,
    AudioAsset,
    UIAsset,
    AnimationAsset,
    AssetStatus,
)


class AssetFactoryBot(BaseBot):
    """
    Bot responsible for generating game assets using AI APIs.

    This bot:
    1. Reads asset manifest from GDD
    2. Calls specialized AI APIs for each asset type
    3. Manages concurrent generation
    4. Organizes assets for Unity import
    """

    def run(self, input_data: Optional[Any] = None) -> AssetCollection:
        """
        Generate all required assets from GDD.

        Args:
            input_data: GameDesignDocument from Stage 2

        Returns:
            AssetCollection with all generated assets
        """
        if not isinstance(input_data, GameDesignDocument):
            raise ValueError("Expected GameDesignDocument input")

        gdd = input_data
        self.logger.info(f"Generating assets for: {gdd.title}")
        self.logger.info(f"Total assets needed: {gdd.asset_manifest.total_assets()}")

        # Create asset collection
        collection = AssetCollection(
            project_name=gdd.title,
            output_directory=self.output_dir / "Assets"
        )
        collection.output_directory.mkdir(parents=True, exist_ok=True)

        # Generate assets by type
        self.logger.info("Generating 3D models...")
        collection.assets_3d = self._generate_3d_models(gdd.asset_manifest.models_3d)

        self.logger.info("Generating 2D assets...")
        collection.assets_2d = self._generate_2d_assets(gdd.asset_manifest.sprites_2d + gdd.asset_manifest.textures)

        self.logger.info("Generating UI elements...")
        collection.ui_assets = self._generate_ui_assets(gdd.asset_manifest.ui_elements)

        self.logger.info("Generating audio assets...")
        collection.audio_assets = self._generate_audio_assets(
            gdd.asset_manifest.sound_effects + gdd.asset_manifest.music_tracks
        )

        self.logger.info("Generating animations...")
        collection.animations = self._generate_animations(gdd.asset_manifest.animations)

        # Generate summary
        self.logger.info(collection.get_summary())

        # Save asset manifest
        self._save_asset_manifest(collection)

        return collection

    def validate_input(self, input_data: Optional[Any]) -> bool:
        """Validate that we have a valid GDD."""
        if input_data is None:
            self.logger.error("No input data provided")
            return False

        if isinstance(input_data, GameDesignDocument):
            return True

        return False

    def _generate_3d_models(self, requirements: list[AssetRequirement]) -> list[Asset3D]:
        """Generate 3D models using AI APIs."""
        assets = []

        for req in requirements:
            asset = Asset3D(
                id=str(uuid.uuid4()),
                name=req.name,
                description=req.description,
                poly_count=req.specifications.get("poly_count", "low"),
                textured=True,
                rigged=req.specifications.get("rigged", False),
                generation_prompt=self._create_3d_prompt(req),
                source_api="meshy",
            )

            # Simulate API call
            if self.config.dry_run:
                asset.status = AssetStatus.PENDING
            else:
                asset = self._call_3d_api(asset)

            assets.append(asset)
            self.logger.debug(f"  Generated: {asset.name} ({asset.status.value})")

        return assets

    def _call_3d_api(self, asset: Asset3D) -> Asset3D:
        """
        Call Meshy or similar API to generate 3D model.

        In production, this would:
        1. Call Meshy API with the prompt
        2. Wait for generation (can be async)
        3. Download the result
        4. Save to output directory
        """
        # Simulate successful generation
        asset.status = AssetStatus.COMPLETED
        asset.file_path = self.output_dir / "Assets" / "Models" / f"{asset.name.replace(' ', '_')}.fbx"
        asset.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create placeholder file info
        asset.metadata = {
            "api_response": "simulated",
            "generation_time": 30.0,
            "polygons": 5000 if asset.poly_count == "low" else 15000,
        }

        return asset

    def _create_3d_prompt(self, req: AssetRequirement) -> str:
        """Create a prompt for 3D model generation."""
        poly = req.specifications.get("poly_count", "low")
        return (
            f"Create a {poly}-poly 3D model of: {req.name}. "
            f"Description: {req.description}. "
            f"Style: game-ready, optimized for real-time rendering. "
            f"Format: FBX with PBR textures."
        )

    def _generate_2d_assets(self, requirements: list[AssetRequirement]) -> list[Asset2D]:
        """Generate 2D sprites and textures using AI APIs."""
        assets = []

        for req in requirements:
            asset = Asset2D(
                id=str(uuid.uuid4()),
                name=req.name,
                description=req.description,
                width=req.specifications.get("width", 512),
                height=req.specifications.get("height", 512),
                tileable=req.specifications.get("tileable", "tile" in req.name.lower()),
                generation_prompt=self._create_2d_prompt(req),
                source_api="recraft",
            )

            if self.config.dry_run:
                asset.status = AssetStatus.PENDING
            else:
                asset = self._call_2d_api(asset)

            assets.append(asset)
            self.logger.debug(f"  Generated: {asset.name} ({asset.status.value})")

        return assets

    def _call_2d_api(self, asset: Asset2D) -> Asset2D:
        """
        Call Recraft, Midjourney, or DALL-E API to generate 2D art.

        In production, this would call the actual API.
        """
        asset.status = AssetStatus.COMPLETED
        asset.file_path = self.output_dir / "Assets" / "Sprites" / f"{asset.name.replace(' ', '_')}.png"
        asset.file_path.parent.mkdir(parents=True, exist_ok=True)

        asset.metadata = {
            "api_response": "simulated",
            "generation_time": 10.0,
        }

        return asset

    def _create_2d_prompt(self, req: AssetRequirement) -> str:
        """Create a prompt for 2D asset generation."""
        return (
            f"Create a game asset: {req.name}. "
            f"Description: {req.description}. "
            f"Style: clean, game-ready, consistent art style. "
            f"Background: transparent where appropriate."
        )

    def _generate_ui_assets(self, requirements: list[AssetRequirement]) -> list[UIAsset]:
        """Generate UI elements using AI tools."""
        assets = []

        for req in requirements:
            asset = UIAsset(
                id=str(uuid.uuid4()),
                name=req.name,
                description=req.description,
                element_type=req.specifications.get("type", "panel"),
                theme=req.specifications.get("theme", "sci-fi"),
                generation_prompt=self._create_ui_prompt(req),
                source_api="uizard",
            )

            if self.config.dry_run:
                asset.status = AssetStatus.PENDING
            else:
                asset = self._call_ui_api(asset)

            assets.append(asset)
            self.logger.debug(f"  Generated: {asset.name} ({asset.status.value})")

        return assets

    def _call_ui_api(self, asset: UIAsset) -> UIAsset:
        """Call UI generation API."""
        asset.status = AssetStatus.COMPLETED
        asset.file_path = self.output_dir / "Assets" / "UI" / f"{asset.name.replace(' ', '_')}.png"
        asset.file_path.parent.mkdir(parents=True, exist_ok=True)

        asset.metadata = {
            "api_response": "simulated",
            "generation_time": 15.0,
        }

        return asset

    def _create_ui_prompt(self, req: AssetRequirement) -> str:
        """Create a prompt for UI generation."""
        return (
            f"Design a {req.specifications.get('theme', 'modern')} themed UI element: {req.name}. "
            f"Description: {req.description}. "
            f"Style: clean, readable, game UI best practices."
        )

    def _generate_audio_assets(self, requirements: list[AssetRequirement]) -> list[AudioAsset]:
        """Generate audio assets using AI."""
        assets = []

        for req in requirements:
            is_music = req.category == "music"

            asset = AudioAsset(
                id=str(uuid.uuid4()),
                name=req.name,
                description=req.description,
                is_music=is_music,
                duration=float(req.specifications.get("duration", "1").replace("min", "")) * (60 if "min" in str(req.specifications.get("duration", "")) else 1),
                loopable=req.specifications.get("loop", is_music),
                variations=req.specifications.get("variations", 1),
                generation_prompt=self._create_audio_prompt(req),
                source_api="elevenlabs" if not is_music else "mubert",
            )

            if self.config.dry_run:
                asset.status = AssetStatus.PENDING
            else:
                asset = self._call_audio_api(asset)

            assets.append(asset)
            self.logger.debug(f"  Generated: {asset.name} ({asset.status.value})")

        return assets

    def _call_audio_api(self, asset: AudioAsset) -> AudioAsset:
        """Call audio generation API."""
        asset.status = AssetStatus.COMPLETED

        folder = "Music" if asset.is_music else "SFX"
        asset.file_path = self.output_dir / "Assets" / "Audio" / folder / f"{asset.name.replace(' ', '_')}.wav"
        asset.file_path.parent.mkdir(parents=True, exist_ok=True)

        asset.metadata = {
            "api_response": "simulated",
            "generation_time": 20.0,
        }

        return asset

    def _create_audio_prompt(self, req: AssetRequirement) -> str:
        """Create a prompt for audio generation."""
        if req.category == "music":
            mood = req.specifications.get("mood", "ambient")
            return (
                f"Compose {mood} game music: {req.name}. "
                f"Description: {req.description}. "
                f"Requirements: seamless loop, appropriate intensity, high quality."
            )
        else:
            return (
                f"Generate game sound effect: {req.name}. "
                f"Description: {req.description}. "
                f"Variations needed: {req.specifications.get('variations', 1)}. "
                f"Requirements: clear, professional, game-ready."
            )

    def _generate_animations(self, requirements: list[AssetRequirement]) -> list[AnimationAsset]:
        """Generate animation clips."""
        assets = []

        for req in requirements:
            asset = AnimationAsset(
                id=str(uuid.uuid4()),
                name=req.name,
                description=req.description,
                target_model=req.specifications.get("target", ""),
                duration=float(req.specifications.get("duration", 1.0)),
                frame_rate=30,
                keyframes=req.specifications.get("clips", 1) * 10,
            )

            if self.config.dry_run:
                asset.status = AssetStatus.PENDING
            else:
                asset.status = AssetStatus.COMPLETED
                asset.file_path = self.output_dir / "Assets" / "Animations" / f"{asset.name.replace(' ', '_')}.anim"
                asset.file_path.parent.mkdir(parents=True, exist_ok=True)

            assets.append(asset)
            self.logger.debug(f"  Generated: {asset.name} ({asset.status.value})")

        return assets

    def _save_asset_manifest(self, collection: AssetCollection) -> None:
        """Save a manifest of all generated assets."""
        manifest = {
            "project": collection.project_name,
            "created_at": collection.created_at.isoformat(),
            "total_assets": collection.total_assets(),
            "completed": collection.completed_assets(),
            "failed": collection.failed_assets(),
            "assets": {
                "3d_models": [
                    {"name": a.name, "path": str(a.file_path), "status": a.status.value}
                    for a in collection.assets_3d
                ],
                "2d_assets": [
                    {"name": a.name, "path": str(a.file_path), "status": a.status.value}
                    for a in collection.assets_2d
                ],
                "ui_assets": [
                    {"name": a.name, "path": str(a.file_path), "status": a.status.value}
                    for a in collection.ui_assets
                ],
                "audio_assets": [
                    {"name": a.name, "path": str(a.file_path), "status": a.status.value}
                    for a in collection.audio_assets
                ],
                "animations": [
                    {"name": a.name, "path": str(a.file_path), "status": a.status.value}
                    for a in collection.animations
                ],
            },
        }

        manifest_path = self.output_dir / "asset_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        self.logger.info(f"Asset manifest saved to {manifest_path}")

    def _dry_run(self, input_data: Optional[Any]) -> AssetCollection:
        """Simulate asset generation."""
        self.logger.info("DRY RUN: Simulating asset generation")

        return AssetCollection(
            project_name="Sample Project",
            output_directory=self.output_dir / "Assets"
        )
