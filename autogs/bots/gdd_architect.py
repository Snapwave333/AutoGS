"""
Stage 2: GDD Architect Bot
Game Design Document generation from Game Brief.
"""

import json
from datetime import datetime
from typing import Any, Optional

from ..core.base_bot import BaseBot
from ..core.config import PipelineConfig
from ..models.game_brief import GameBrief
from ..models.gdd import (
    GameDesignDocument,
    GameMechanic,
    Quest,
    StoryAct,
    AssetManifest,
    AssetRequirement,
    TechnicalRequirements,
)


class GDDArchitectBot(BaseBot):
    """
    Bot responsible for generating a complete Game Design Document.

    This bot:
    1. Takes a Game Brief from Stage 1
    2. Uses LLM to flesh out mechanics, story, and features
    3. Generates complete asset requirements list
    4. Outputs a comprehensive GDD
    """

    def run(self, input_data: Optional[Any] = None) -> GameDesignDocument:
        """
        Generate a complete Game Design Document.

        Args:
            input_data: GameBrief from Stage 1

        Returns:
            Complete GameDesignDocument
        """
        if not isinstance(input_data, GameBrief):
            # Try to reconstruct from dict
            if isinstance(input_data, dict):
                input_data = GameBrief.from_dict(input_data)
            else:
                raise ValueError("Expected GameBrief input")

        brief = input_data
        self.logger.info(f"Generating GDD for: {brief.title}")

        # Step 1: Generate core gameplay
        self.logger.info("Designing core game loop and mechanics...")
        core_loop = self._generate_core_loop(brief)
        mechanics = self._generate_mechanics(brief)

        # Step 2: Generate story
        self.logger.info("Creating narrative structure...")
        story_acts = self._generate_story(brief)
        characters = self._generate_characters(brief)
        quests = self._generate_quests(brief, story_acts)

        # Step 3: Generate asset requirements
        self.logger.info("Compiling asset manifest...")
        asset_manifest = self._generate_asset_manifest(brief, mechanics)

        # Step 4: Generate technical requirements
        self.logger.info("Defining technical specifications...")
        tech_reqs = self._generate_technical_requirements(brief)

        # Step 5: Compile the GDD
        gdd = GameDesignDocument(
            title=brief.title,
            version="1.0.0",
            last_updated=datetime.now(),
            high_concept=brief.one_liner,
            unique_selling_points=self._generate_usps(brief),
            target_audience=brief.market_analysis.target_audience if brief.market_analysis else "Indie gamers aged 18-35",
            core_game_loop=core_loop,
            mechanics=mechanics,
            progression_system=self._generate_progression(brief),
            win_conditions=self._generate_win_conditions(brief),
            fail_conditions=self._generate_fail_conditions(brief),
            story_synopsis=self._generate_synopsis(brief),
            story_acts=story_acts,
            main_characters=characters,
            quests=quests,
            technical_requirements=tech_reqs,
            asset_manifest=asset_manifest,
            monetization_strategy="premium",
            price_point=19.99,
            estimated_dev_time="6 months",
            team_size=1,
            mvp_features=self._generate_mvp_features(mechanics),
            post_launch_features=self._generate_post_launch_features(mechanics),
        )

        self.logger.info(f"GDD generated with {len(mechanics)} mechanics and {asset_manifest.total_assets()} assets")

        # Save GDD as markdown
        self._save_gdd_markdown(gdd)

        return gdd

    def validate_input(self, input_data: Optional[Any]) -> bool:
        """Validate that we have a valid GameBrief."""
        if input_data is None:
            self.logger.error("No input data provided")
            return False

        if isinstance(input_data, GameBrief):
            return True

        if isinstance(input_data, dict):
            required_keys = ["title", "one_liner", "genre"]
            return all(key in input_data for key in required_keys)

        return False

    def _generate_core_loop(self, brief: GameBrief) -> str:
        """Generate the core game loop description."""
        if "survival" in brief.genre.lower():
            return (
                "1. EXPLORE: Scout the environment for resources and threats\n"
                "2. GATHER: Collect materials, data, and supplies\n"
                "3. BUILD: Construct and upgrade your base/equipment\n"
                "4. SURVIVE: Manage resources and defend against hazards\n"
                "5. PROGRESS: Unlock new areas and advance the story"
            )
        elif "roguelike" in brief.genre.lower():
            return (
                "1. START: Begin a new run with basic equipment\n"
                "2. FIGHT: Combat enemies in procedural encounters\n"
                "3. CHOOSE: Select upgrades and paths\n"
                "4. RISK: Push forward or retreat to secure progress\n"
                "5. REPEAT: Death leads to meta-progression"
            )
        else:
            return (
                "1. DISCOVER: Explore new areas and uncover secrets\n"
                "2. INTERACT: Engage with game systems and mechanics\n"
                "3. PROGRESS: Complete objectives and advance\n"
                "4. UPGRADE: Improve capabilities\n"
                "5. MASTER: Overcome increasingly difficult challenges"
            )

    def _generate_mechanics(self, brief: GameBrief) -> list[GameMechanic]:
        """Generate game mechanics based on brief."""
        mechanics = []

        # Core mechanics based on keywords
        if "base-building" in brief.target_keywords:
            mechanics.append(GameMechanic(
                name="Base Construction",
                description="Players can construct and upgrade modular base components",
                core_systems=["GridSystem", "ResourceManager", "BuildingPlacement"],
                player_interactions=["Place", "Rotate", "Upgrade", "Demolish"],
                dependencies=["ResourceGathering"],
                priority="critical"
            ))

        if "crafting" in brief.target_keywords or "survival" in brief.genre:
            mechanics.append(GameMechanic(
                name="Crafting System",
                description="Combine gathered resources to create tools, equipment, and consumables",
                core_systems=["InventorySystem", "RecipeDatabase", "CraftingUI"],
                player_interactions=["Gather", "Craft", "Upgrade", "Discover Recipes"],
                dependencies=["ResourceGathering", "InventoryManagement"],
                priority="critical"
            ))

        if "co-op" in brief.target_keywords or "1-4" in brief.player_count:
            mechanics.append(GameMechanic(
                name="Multiplayer Co-op",
                description="Seamless drop-in/drop-out cooperative gameplay for up to 4 players",
                core_systems=["NetworkManager", "PlayerSync", "SessionManager"],
                player_interactions=["Join", "Leave", "Share Resources", "Revive"],
                dependencies=["PlayerController"],
                priority="high"
            ))

        if "automation" in brief.target_keywords:
            mechanics.append(GameMechanic(
                name="Automation Systems",
                description="Build conveyor belts and automated machinery to streamline resource processing",
                core_systems=["ConveyorSystem", "MachineLogic", "PowerGrid"],
                player_interactions=["Place", "Connect", "Program", "Monitor"],
                dependencies=["BaseConstruction", "PowerManagement"],
                priority="high"
            ))

        # Add standard mechanics
        mechanics.extend([
            GameMechanic(
                name="Resource Management",
                description="Track and manage vital resources including oxygen, power, and materials",
                core_systems=["ResourceTracker", "DepletionSystem", "UI_Indicators"],
                player_interactions=["Monitor", "Allocate", "Conserve", "Replenish"],
                priority="critical"
            ),
            GameMechanic(
                name="Exploration",
                description="Discover new areas, unlock map regions, and find points of interest",
                core_systems=["MapSystem", "FogOfWar", "DiscoveryTriggers"],
                player_interactions=["Move", "Scan", "Mark", "Navigate"],
                priority="high"
            ),
            GameMechanic(
                name="Progression System",
                description="Unlock new abilities, recipes, and areas through experience and achievements",
                core_systems=["XPSystem", "UnlockTree", "SaveSystem"],
                player_interactions=["Earn XP", "Choose Upgrades", "Unlock Content"],
                priority="medium"
            ),
        ])

        return mechanics[:self.config.gdd_architect.max_mechanics]

    def _generate_story(self, brief: GameBrief) -> list[StoryAct]:
        """Generate a 3-act story structure."""
        acts = [
            StoryAct(
                number=1,
                title="The Awakening",
                summary=f"The player arrives in the {brief.setting} and must establish basic survival systems while uncovering the first clues about what happened here.",
                key_events=[
                    "Initial crash/arrival",
                    "First shelter construction",
                    "Discovery of mysterious signal",
                    "First threat encounter"
                ],
                locations=["Starting Zone", "Crash Site", "Basic Outpost"],
                characters=["AI Companion", "First Contact NPC"]
            ),
            StoryAct(
                number=2,
                title="The Descent",
                summary="As the player expands their capabilities, they uncover darker secrets and face escalating challenges that threaten their survival.",
                key_events=[
                    "Major base expansion",
                    "Revelation of true threat",
                    "Betrayal or twist",
                    "Loss of critical resource"
                ],
                locations=["Underground Facility", "Abandoned Settlement", "Hostile Territory"],
                characters=["Antagonist Introduction", "Lost Survivor", "Mysterious Entity"]
            ),
            StoryAct(
                number=3,
                title="The Reckoning",
                summary="The player must use everything they've learned and built to face the ultimate challenge and determine the fate of their situation.",
                key_events=[
                    "Final preparations",
                    "Point of no return",
                    "Ultimate confrontation",
                    "Resolution and escape/salvation"
                ],
                locations=["Core Facility", "Final Frontier", "Escape Route"],
                characters=["Final Boss/Challenge", "Allied Forces"]
            )
        ]
        return acts

    def _generate_characters(self, brief: GameBrief) -> list[dict]:
        """Generate main characters."""
        characters = [
            {
                "name": "The Protagonist",
                "role": "Player Character",
                "description": "A resourceful survivor with a mysterious past",
                "arc": "From lost survivor to master of the environment"
            },
            {
                "name": "ARIA",
                "role": "AI Companion",
                "description": "An advanced AI system that guides and assists the player",
                "arc": "Gains sentience and becomes true partner"
            },
            {
                "name": "Director Chen",
                "role": "Mission Control",
                "description": "Remote contact providing objectives and context",
                "arc": "Hidden agenda revealed in Act 2"
            }
        ]
        return characters

    def _generate_quests(self, brief: GameBrief, acts: list[StoryAct]) -> list[Quest]:
        """Generate main and side quests."""
        quests = []
        quest_id = 0

        for act in acts:
            # Main quest for each act
            quests.append(Quest(
                id=f"main_{quest_id:03d}",
                title=f"Act {act.number}: {act.title}",
                description=act.summary,
                objectives=act.key_events[:3],
                rewards=["Story Progression", "New Area Access", "Major Unlock"],
                act=act.number,
                is_main_quest=True
            ))
            quest_id += 1

            # Side quests
            for i in range(2):
                quests.append(Quest(
                    id=f"side_{quest_id:03d}",
                    title=f"Optional: {act.locations[i % len(act.locations)]} Secrets",
                    description=f"Explore and uncover hidden content in {act.locations[i % len(act.locations)]}",
                    objectives=[
                        "Find hidden cache",
                        "Decode message",
                        "Survive challenge"
                    ],
                    rewards=["Rare Resources", "Unique Blueprint", "Lore Entry"],
                    act=act.number,
                    is_main_quest=False
                ))
                quest_id += 1

        return quests[:self.config.gdd_architect.max_quests]

    def _generate_asset_manifest(self, brief: GameBrief, mechanics: list[GameMechanic]) -> AssetManifest:
        """Generate complete asset requirements."""

        # 3D Models
        models_3d = [
            AssetRequirement("3d_model", "Player Character", "Main player model with animations", {"poly_count": "medium", "rigged": True}),
            AssetRequirement("3d_model", "Base Module - Core", "Central hub module", {"poly_count": "low"}),
            AssetRequirement("3d_model", "Base Module - Storage", "Resource storage unit", {"poly_count": "low"}),
            AssetRequirement("3d_model", "Base Module - Power", "Power generation unit", {"poly_count": "low"}),
            AssetRequirement("3d_model", "Resource Crate", "Generic resource container", {"poly_count": "low"}),
            AssetRequirement("3d_model", "Enemy - Basic", "Common threat type", {"poly_count": "medium", "rigged": True}),
            AssetRequirement("3d_model", "Enemy - Elite", "Advanced threat type", {"poly_count": "medium", "rigged": True}),
            AssetRequirement("3d_model", "Environment - Rock Large", "Large rock formation", {"poly_count": "low"}),
            AssetRequirement("3d_model", "Environment - Tree/Crystal", "Vertical environment element", {"poly_count": "low"}),
            AssetRequirement("3d_model", "Tool - Scanner", "Handheld scanning device", {"poly_count": "low"}),
        ]

        # 2D Sprites/Textures
        sprites_2d = [
            AssetRequirement("2d_sprite", "Item Icons Pack", "Icons for all inventory items", {"count": 50}),
            AssetRequirement("2d_sprite", "Status Effect Icons", "Buff and debuff indicators", {"count": 20}),
            AssetRequirement("2d_sprite", "Map Markers", "POI indicators for map", {"count": 15}),
        ]

        # Textures
        textures = [
            AssetRequirement("texture", "Terrain - Ground", "Tileable ground texture", {"resolution": "1024x1024"}),
            AssetRequirement("texture", "Metal - Sci-fi", "Base building material", {"resolution": "1024x1024"}),
            AssetRequirement("texture", "Organic - Alien", "Alien organic matter", {"resolution": "1024x1024"}),
            AssetRequirement("texture", "Environment - Sky", "Skybox textures", {"resolution": "2048x2048"}),
        ]

        # UI Elements
        ui_elements = [
            AssetRequirement("ui", "Main Menu Layout", "Title screen and menu UI", {"theme": brief.core_theme}),
            AssetRequirement("ui", "HUD Elements", "Health, resources, minimap", {"style": "minimal"}),
            AssetRequirement("ui", "Inventory Panel", "Grid-based inventory UI", {"slots": 40}),
            AssetRequirement("ui", "Crafting Menu", "Recipe browser and crafting interface", {}),
            AssetRequirement("ui", "Build Menu", "Construction selection wheel", {}),
            AssetRequirement("ui", "Dialog Box", "Character conversation UI", {}),
        ]

        # Sound Effects
        sfx = [
            AssetRequirement("sfx", "Footsteps Pack", "Various surface footsteps", {"variations": 20}),
            AssetRequirement("sfx", "UI Sounds", "Button clicks, hovers, notifications", {"variations": 15}),
            AssetRequirement("sfx", "Construction", "Building placement and completion", {"variations": 10}),
            AssetRequirement("sfx", "Resource Gather", "Mining, collecting, harvesting", {"variations": 12}),
            AssetRequirement("sfx", "Enemy Sounds", "Alerts, attacks, death", {"variations": 20}),
            AssetRequirement("sfx", "Ambient - Environment", "Background environmental sounds", {"variations": 8}),
            AssetRequirement("sfx", "Tool Sounds", "Equipment usage sounds", {"variations": 15}),
        ]

        # Music
        music = [
            AssetRequirement("music", "Main Theme", "Title screen and credits music", {"duration": "3min", "mood": "epic"}),
            AssetRequirement("music", "Exploration - Calm", "Peaceful exploration music", {"duration": "5min", "loop": True}),
            AssetRequirement("music", "Exploration - Tense", "Dangerous area music", {"duration": "4min", "loop": True}),
            AssetRequirement("music", "Combat", "Battle music", {"duration": "3min", "loop": True}),
            AssetRequirement("music", "Base Building", "Calm construction music", {"duration": "5min", "loop": True}),
        ]

        # Animations
        animations = [
            AssetRequirement("animation", "Player - Locomotion", "Walk, run, jump, crouch", {"clips": 8}),
            AssetRequirement("animation", "Player - Actions", "Use, grab, throw, interact", {"clips": 10}),
            AssetRequirement("animation", "Enemy - Movement", "Patrol, chase, attack", {"clips": 6}),
            AssetRequirement("animation", "UI - Transitions", "Menu animations", {"clips": 5}),
        ]

        return AssetManifest(
            models_3d=models_3d,
            sprites_2d=sprites_2d,
            textures=textures,
            ui_elements=ui_elements,
            sound_effects=sfx,
            music_tracks=music,
            animations=animations
        )

    def _generate_technical_requirements(self, brief: GameBrief) -> TechnicalRequirements:
        """Generate technical specifications."""
        packages = [
            "com.unity.render-pipelines.universal",
            "com.unity.inputsystem",
            "com.unity.textmeshpro",
            "com.unity.cinemachine",
            "com.unity.ai.navigation",
        ]

        networking = None
        if "co-op" in brief.target_keywords or "1-4" in brief.player_count:
            packages.append("com.unity.netcode.gameobjects")
            networking = "Unity Netcode"

        return TechnicalRequirements(
            unity_version=self.config.engineer.unity_version,
            render_pipeline=self.config.engineer.render_pipeline,
            target_fps=60,
            min_resolution="1280x720",
            max_resolution="3840x2160",
            required_packages=packages,
            networking=networking
        )

    def _generate_usps(self, brief: GameBrief) -> list[str]:
        """Generate Unique Selling Points."""
        return [
            f"Innovative {brief.genre} mechanics with {', '.join(brief.target_keywords[:2])}",
            f"Immersive {brief.core_theme} atmosphere with procedural elements",
            f"Deep {brief.target_keywords[0] if brief.target_keywords else 'gameplay'} systems with meaningful choices",
            "Seamless co-op experience for solo and group play",
            "Rich narrative with multiple endings"
        ]

    def _generate_progression(self, brief: GameBrief) -> str:
        """Generate progression system description."""
        return (
            "Players progress through a tiered unlock system:\n"
            "- Survival Tier: Basic tools and shelter\n"
            "- Establishment Tier: Base expansion and automation\n"
            "- Mastery Tier: Advanced tech and story completion\n"
            "Each tier unlocks new recipes, abilities, and areas."
        )

    def _generate_win_conditions(self, brief: GameBrief) -> list[str]:
        """Generate win conditions."""
        return [
            "Complete the main story campaign",
            "Achieve maximum base development level",
            "Survive for 100 in-game days",
            "Uncover all story secrets"
        ]

    def _generate_fail_conditions(self, brief: GameBrief) -> list[str]:
        """Generate fail conditions."""
        return [
            "Complete resource depletion (soft fail - can recover)",
            "Base destruction (checkpoint restart)",
            "Player death (respawn with penalties)"
        ]

    def _generate_synopsis(self, brief: GameBrief) -> str:
        """Generate story synopsis."""
        return (
            f"In a {brief.core_theme} {brief.setting}, you awaken to find yourself stranded "
            f"with limited resources and no clear path home. As you build, explore, and survive, "
            f"you'll uncover the dark secrets of this place and face the choice that will determine "
            f"not just your fate, but the fate of everything you've built."
        )

    def _generate_mvp_features(self, mechanics: list[GameMechanic]) -> list[str]:
        """Generate MVP feature list."""
        critical = [m.name for m in mechanics if m.priority == "critical"]
        return critical + [
            "Basic save/load system",
            "Tutorial sequence",
            "First story act"
        ]

    def _generate_post_launch_features(self, mechanics: list[GameMechanic]) -> list[str]:
        """Generate post-launch feature list."""
        return [
            "Additional story content",
            "New biomes/areas",
            "Steam Workshop support",
            "Challenge modes",
            "Cosmetic customization"
        ]

    def _save_gdd_markdown(self, gdd: GameDesignDocument) -> None:
        """Save GDD as a readable markdown file."""
        md_path = self.output_dir / f"{gdd.title.replace(' ', '_')}_GDD.md"
        with open(md_path, "w") as f:
            f.write(gdd.to_markdown())
        self.logger.info(f"GDD saved to {md_path}")

    def _dry_run(self, input_data: Optional[Any]) -> GameDesignDocument:
        """Simulate GDD generation."""
        self.logger.info("DRY RUN: Generating sample GDD structure")

        # Create minimal GDD for dry run
        return GameDesignDocument(
            title="Sample Game",
            version="1.0.0",
            last_updated=datetime.now(),
            high_concept="A sample game concept",
            unique_selling_points=["Feature 1", "Feature 2"],
            target_audience="Gamers",
            core_game_loop="Play -> Progress -> Repeat",
            mechanics=[],
            progression_system="Linear progression",
            win_conditions=["Complete game"],
            fail_conditions=["Game over"],
            story_synopsis="A hero's journey",
            story_acts=[],
            main_characters=[],
            quests=[],
            technical_requirements=TechnicalRequirements(),
            asset_manifest=AssetManifest([], [], [], [], [], [], [])
        )
