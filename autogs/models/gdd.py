"""Data models for Stage 2: GDD Architect Bot output."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class GameMechanic:
    """A single game mechanic."""

    name: str
    description: str
    core_systems: list[str]
    player_interactions: list[str]
    dependencies: list[str] = field(default_factory=list)
    priority: str = "medium"  # low, medium, high, critical


@dataclass
class Quest:
    """A game quest or mission."""

    id: str
    title: str
    description: str
    objectives: list[str]
    rewards: list[str]
    prerequisites: list[str] = field(default_factory=list)
    act: int = 1
    is_main_quest: bool = True


@dataclass
class StoryAct:
    """A story act in the game narrative."""

    number: int
    title: str
    summary: str
    key_events: list[str]
    locations: list[str]
    characters: list[str]


@dataclass
class AssetRequirement:
    """A single asset requirement."""

    category: str  # 3d_model, 2d_sprite, texture, ui, sfx, music
    name: str
    description: str
    specifications: dict = field(default_factory=dict)
    priority: str = "medium"
    quantity: int = 1


@dataclass
class AssetManifest:
    """Complete list of assets needed for the game."""

    models_3d: list[AssetRequirement]
    sprites_2d: list[AssetRequirement]
    textures: list[AssetRequirement]
    ui_elements: list[AssetRequirement]
    sound_effects: list[AssetRequirement]
    music_tracks: list[AssetRequirement]
    animations: list[AssetRequirement]

    def total_assets(self) -> int:
        """Get total number of assets."""
        return (
            len(self.models_3d)
            + len(self.sprites_2d)
            + len(self.textures)
            + len(self.ui_elements)
            + len(self.sound_effects)
            + len(self.music_tracks)
            + len(self.animations)
        )


@dataclass
class TechnicalRequirements:
    """Technical specifications for the game."""

    unity_version: str = "2022.3 LTS"
    render_pipeline: str = "URP"
    target_fps: int = 60
    min_resolution: str = "1280x720"
    max_resolution: str = "3840x2160"
    required_packages: list[str] = field(default_factory=list)
    networking: Optional[str] = None  # None, Netcode, Photon, etc.


@dataclass
class GameDesignDocument:
    """
    The output of Stage 2: GDD Architect Bot.
    A complete Game Design Document.
    """

    # Basic Info
    title: str
    version: str
    last_updated: datetime

    # Core Concept
    high_concept: str
    unique_selling_points: list[str]
    target_audience: str

    # Gameplay
    core_game_loop: str
    mechanics: list[GameMechanic]
    progression_system: str
    win_conditions: list[str]
    fail_conditions: list[str]

    # Story
    story_synopsis: str
    story_acts: list[StoryAct]
    main_characters: list[dict]
    quests: list[Quest]

    # Technical
    technical_requirements: TechnicalRequirements

    # Assets
    asset_manifest: AssetManifest

    # Monetization (optional)
    monetization_strategy: str = "premium"
    price_point: float = 0.0

    # Scope
    estimated_dev_time: str = "6 months"
    team_size: int = 1
    mvp_features: list[str] = field(default_factory=list)
    post_launch_features: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Export GDD as markdown."""
        md = f"""# {self.title} - Game Design Document

**Version:** {self.version}
**Last Updated:** {self.last_updated.strftime('%Y-%m-%d')}

---

## 1. High Concept

{self.high_concept}

### Unique Selling Points
"""
        for usp in self.unique_selling_points:
            md += f"- {usp}\n"

        md += f"""
### Target Audience
{self.target_audience}

---

## 2. Core Gameplay

### Core Game Loop
{self.core_game_loop}

### Mechanics
"""
        for mechanic in self.mechanics:
            md += f"""
#### {mechanic.name} (Priority: {mechanic.priority})
{mechanic.description}

**Core Systems:** {', '.join(mechanic.core_systems)}
**Player Interactions:** {', '.join(mechanic.player_interactions)}
"""

        md += f"""
### Progression System
{self.progression_system}

### Win Conditions
"""
        for condition in self.win_conditions:
            md += f"- {condition}\n"

        md += "\n### Fail Conditions\n"
        for condition in self.fail_conditions:
            md += f"- {condition}\n"

        md += f"""
---

## 3. Story & Narrative

### Synopsis
{self.story_synopsis}

### Story Structure
"""
        for act in self.story_acts:
            md += f"""
#### Act {act.number}: {act.title}
{act.summary}

**Key Events:** {', '.join(act.key_events)}
**Locations:** {', '.join(act.locations)}
"""

        md += "\n### Main Quests\n"
        for quest in [q for q in self.quests if q.is_main_quest]:
            md += f"""
#### {quest.title}
{quest.description}

**Objectives:**
"""
            for obj in quest.objectives:
                md += f"- {obj}\n"

        md += f"""
---

## 4. Technical Requirements

- **Unity Version:** {self.technical_requirements.unity_version}
- **Render Pipeline:** {self.technical_requirements.render_pipeline}
- **Target FPS:** {self.technical_requirements.target_fps}
- **Resolution Range:** {self.technical_requirements.min_resolution} - {self.technical_requirements.max_resolution}
- **Networking:** {self.technical_requirements.networking or 'None'}

### Required Packages
"""
        for pkg in self.technical_requirements.required_packages:
            md += f"- {pkg}\n"

        md += f"""
---

## 5. Asset Requirements

**Total Assets Needed:** {self.asset_manifest.total_assets()}

### 3D Models ({len(self.asset_manifest.models_3d)})
"""
        for asset in self.asset_manifest.models_3d[:10]:  # Show first 10
            md += f"- {asset.name}: {asset.description}\n"

        md += f"""
### 2D Sprites ({len(self.asset_manifest.sprites_2d)})
"""
        for asset in self.asset_manifest.sprites_2d[:10]:
            md += f"- {asset.name}: {asset.description}\n"

        md += f"""
### Sound Effects ({len(self.asset_manifest.sound_effects)})
"""
        for asset in self.asset_manifest.sound_effects[:10]:
            md += f"- {asset.name}: {asset.description}\n"

        md += f"""
### Music Tracks ({len(self.asset_manifest.music_tracks)})
"""
        for asset in self.asset_manifest.music_tracks:
            md += f"- {asset.name}: {asset.description}\n"

        md += f"""
---

## 6. Scope & Timeline

- **Estimated Development Time:** {self.estimated_dev_time}
- **Team Size:** {self.team_size}
- **Monetization:** {self.monetization_strategy}
- **Price Point:** ${self.price_point:.2f}

### MVP Features
"""
        for feature in self.mvp_features:
            md += f"- {feature}\n"

        md += "\n### Post-Launch Features\n"
        for feature in self.post_launch_features:
            md += f"- {feature}\n"

        return md
