"""
Stage 2: GDD Architect Bot
Game Design Document generation from Game Brief with LLM integration.
"""

import json
from datetime import datetime
from typing import Any, Optional

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

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
from ..templates.gdd_prompts import (
    CORE_LOOP_PROMPT,
    MECHANICS_PROMPT,
    STORY_PROMPT,
    QUEST_PROMPT,
    CHARACTER_PROMPT,
    USP_PROMPT,
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

    def __init__(self, config: Optional[PipelineConfig] = None, dry_run: bool = False):
        """Initialize GDDArchitectBot with LLM client setup."""
        super().__init__(config, dry_run)
        self._openai_client = None
        self._anthropic_client = None
        self._llm_available = False
        self._setup_llm_client()

    def _setup_llm_client(self) -> None:
        """Set up the LLM client based on configuration."""
        # Try OpenAI first
        if HAS_OPENAI and self.config.api.openai_api_key:
            try:
                self._openai_client = openai.OpenAI(api_key=self.config.api.openai_api_key)
                self._llm_available = True
                self.logger.info("OpenAI LLM client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize OpenAI client: {e}")

        # Try Anthropic as fallback
        if not self._llm_available and HAS_ANTHROPIC and self.config.api.anthropic_api_key:
            try:
                self._anthropic_client = anthropic.Anthropic(api_key=self.config.api.anthropic_api_key)
                self._llm_available = True
                self.logger.info("Anthropic LLM client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Anthropic client: {e}")

        if not self._llm_available:
            self.logger.info("No LLM API available, using template-based generation")

    def _call_llm(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Call the configured LLM and return the response."""
        if not self._llm_available:
            return None

        try:
            if self._openai_client:
                response = self._openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional game designer helping create game design documents."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content

            elif self._anthropic_client:
                response = self._anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    system="You are a professional game designer helping create game design documents."
                )
                return response.content[0].text

        except Exception as e:
            self.logger.warning(f"LLM call failed: {e}")
            return None

        return None

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
        self.logger.info(f"LLM Available: {self._llm_available}")

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

        # Save GDD as JSON
        self._save_gdd_json(gdd)

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
        """Generate the core game loop description using LLM or templates."""
        if self._llm_available:
            prompt = CORE_LOOP_PROMPT.format(
                genre=brief.genre,
                title=brief.title,
                concept=brief.one_liner,
                keywords=", ".join(brief.target_keywords[:5]),
                theme=brief.core_theme
            )
            result = self._call_llm(prompt, max_tokens=500)
            if result:
                self.logger.debug("Core loop generated via LLM")
                return result

        # Fallback to template-based generation
        return self._template_core_loop(brief)

    def _template_core_loop(self, brief: GameBrief) -> str:
        """Template-based core loop generation."""
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
        elif "deckbuilder" in brief.genre.lower():
            return (
                "1. DRAW: Select cards from your deck\n"
                "2. PLAN: Strategize your turn based on available cards\n"
                "3. PLAY: Execute card combinations and actions\n"
                "4. RESOLVE: Process effects and enemy actions\n"
                "5. EVOLVE: Add new cards and thin your deck"
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
        """Generate game mechanics based on brief using LLM or templates."""
        mechanics = []

        # Try LLM generation first
        if self._llm_available:
            prompt = MECHANICS_PROMPT.format(
                num_mechanics=self.config.gdd_architect.max_mechanics,
                title=brief.title,
                genre=brief.genre,
                theme=brief.core_theme,
                features=", ".join(brief.target_keywords[:5])
            )
            result = self._call_llm(prompt, max_tokens=3000)
            if result:
                parsed_mechanics = self._parse_mechanics_response(result, brief)
                if parsed_mechanics:
                    self.logger.debug(f"Generated {len(parsed_mechanics)} mechanics via LLM")
                    return parsed_mechanics[:self.config.gdd_architect.max_mechanics]

        # Fallback to template-based generation
        return self._template_mechanics(brief)

    def _parse_mechanics_response(self, response: str, brief: GameBrief) -> list[GameMechanic]:
        """Parse LLM response into GameMechanic objects."""
        mechanics = []

        # Simple parsing: look for numbered sections
        sections = response.split("\n\n")

        current_mechanic = {}
        for section in sections:
            lines = section.strip().split("\n")
            if not lines:
                continue

            # Try to extract mechanic information
            name = ""
            description = ""
            core_systems = []
            player_interactions = []
            dependencies = []
            priority = "medium"

            for line in lines:
                line_lower = line.lower()
                if "name:" in line_lower or (lines.index(line) == 0 and not line.startswith("-")):
                    name = line.replace("Name:", "").replace("**", "").strip()
                    # Remove numbering
                    if name and name[0].isdigit():
                        name = name.split(".", 1)[-1].strip()
                        name = name.split(")", 1)[-1].strip()
                elif "description:" in line_lower:
                    description = line.split(":", 1)[-1].strip()
                elif "core system" in line_lower or "system" in line_lower:
                    systems_text = line.split(":", 1)[-1].strip()
                    core_systems = [s.strip() for s in systems_text.split(",")]
                elif "player interaction" in line_lower or "interaction" in line_lower:
                    interactions_text = line.split(":", 1)[-1].strip()
                    player_interactions = [i.strip() for i in interactions_text.split(",")]
                elif "dependenc" in line_lower:
                    deps_text = line.split(":", 1)[-1].strip()
                    dependencies = [d.strip() for d in deps_text.split(",")]
                elif "priority:" in line_lower:
                    priority = line.split(":", 1)[-1].strip().lower()
                elif description == "" and len(line) > 20:
                    description = line.strip()

            if name:
                # Provide defaults if parsing didn't get everything
                if not core_systems:
                    core_systems = ["CoreSystem", "Manager"]
                if not player_interactions:
                    player_interactions = ["Interact", "Use"]

                mechanics.append(GameMechanic(
                    name=name,
                    description=description if description else f"Mechanic for {name}",
                    core_systems=core_systems,
                    player_interactions=player_interactions,
                    dependencies=dependencies,
                    priority=priority if priority in ["critical", "high", "medium", "low"] else "medium"
                ))

        return mechanics

    def _template_mechanics(self, brief: GameBrief) -> list[GameMechanic]:
        """Template-based mechanics generation."""
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

        if "deckbuilder" in brief.genre.lower():
            mechanics.append(GameMechanic(
                name="Card System",
                description="Collect, upgrade, and strategize with cards that represent abilities and actions",
                core_systems=["DeckManager", "CardDatabase", "CombatResolver"],
                player_interactions=["Draw", "Play", "Upgrade", "Remove"],
                dependencies=["TurnSystem"],
                priority="critical"
            ))

        if "roguelike" in brief.genre.lower():
            mechanics.append(GameMechanic(
                name="Procedural Generation",
                description="Each run features randomly generated levels and encounters",
                core_systems=["LevelGenerator", "SeedManager", "EnemySpawner"],
                player_interactions=["Explore", "Adapt", "Risk"],
                dependencies=[],
                priority="critical"
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
        """Generate a 3-act story structure using LLM or templates."""
        if self._llm_available:
            prompt = STORY_PROMPT.format(
                title=brief.title,
                genre=brief.genre,
                setting=brief.setting,
                theme=brief.core_theme
            )
            result = self._call_llm(prompt, max_tokens=2000)
            if result:
                parsed_acts = self._parse_story_response(result, brief)
                if parsed_acts:
                    self.logger.debug("Story acts generated via LLM")
                    return parsed_acts

        # Fallback to template
        return self._template_story(brief)

    def _parse_story_response(self, response: str, brief: GameBrief) -> list[StoryAct]:
        """Parse LLM story response into StoryAct objects."""
        acts = []

        # Split by "Act" keyword
        act_sections = []
        current_section = ""

        for line in response.split("\n"):
            if line.strip().lower().startswith("act") and ("1" in line or "2" in line or "3" in line):
                if current_section:
                    act_sections.append(current_section)
                current_section = line + "\n"
            else:
                current_section += line + "\n"

        if current_section:
            act_sections.append(current_section)

        for i, section in enumerate(act_sections[:3], 1):
            lines = section.strip().split("\n")
            title = f"Act {i}"
            summary = ""
            key_events = []
            locations = []
            characters = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.lower().startswith("act"):
                    # Extract title
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        title = parts[1].strip().replace("**", "")
                    else:
                        title = line.replace("**", "").strip()
                elif "summary" in line.lower():
                    summary = line.split(":", 1)[-1].strip()
                elif line.startswith("-") or line.startswith("•"):
                    event = line.lstrip("-•").strip()
                    if len(key_events) < 5:
                        key_events.append(event)
                elif "location" in line.lower():
                    locs = line.split(":", 1)[-1].strip()
                    locations = [l.strip() for l in locs.split(",")]
                elif "character" in line.lower():
                    chars = line.split(":", 1)[-1].strip()
                    characters = [c.strip() for c in chars.split(",")]
                elif len(summary) == 0 and len(line) > 30:
                    summary = line

            if not key_events:
                key_events = [f"Event {j}" for j in range(1, 5)]
            if not locations:
                locations = ["Location A", "Location B"]
            if not characters:
                characters = ["Character A"]

            acts.append(StoryAct(
                number=i,
                title=title,
                summary=summary if summary else f"Act {i} of the story",
                key_events=key_events,
                locations=locations,
                characters=characters
            ))

        return acts if len(acts) == 3 else []

    def _template_story(self, brief: GameBrief) -> list[StoryAct]:
        """Template-based story generation."""
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
        """Generate main characters using LLM or templates."""
        if self._llm_available:
            prompt = CHARACTER_PROMPT.format(
                num_characters=3,
                title=brief.title,
                genre=brief.genre,
                synopsis=brief.one_liner,
                theme=brief.core_theme,
                setting=brief.setting
            )
            result = self._call_llm(prompt, max_tokens=1500)
            if result:
                parsed_chars = self._parse_characters_response(result)
                if parsed_chars:
                    self.logger.debug("Characters generated via LLM")
                    return parsed_chars

        # Fallback to template
        return self._template_characters(brief)

    def _parse_characters_response(self, response: str) -> list[dict]:
        """Parse LLM character response."""
        characters = []

        # Split by double newline or numbered items
        sections = response.split("\n\n")

        for section in sections:
            if not section.strip():
                continue

            char = {
                "name": "Unknown",
                "role": "NPC",
                "description": "",
                "arc": ""
            }

            lines = section.strip().split("\n")
            for line in lines:
                line_lower = line.lower()
                if "name:" in line_lower:
                    char["name"] = line.split(":", 1)[-1].strip().replace("**", "")
                elif "role:" in line_lower:
                    char["role"] = line.split(":", 1)[-1].strip()
                elif "description:" in line_lower or "physical:" in line_lower:
                    char["description"] = line.split(":", 1)[-1].strip()
                elif "arc:" in line_lower or "character arc:" in line_lower:
                    char["arc"] = line.split(":", 1)[-1].strip()
                elif "personality:" in line_lower:
                    char["personality"] = line.split(":", 1)[-1].strip()
                elif "backstory:" in line_lower:
                    char["backstory"] = line.split(":", 1)[-1].strip()
                elif lines.index(line) == 0 and ":" not in line:
                    # First line might be the name
                    potential_name = line.replace("**", "").strip()
                    if potential_name and len(potential_name) < 50:
                        char["name"] = potential_name

            if char["name"] != "Unknown":
                characters.append(char)

        return characters if characters else None

    def _template_characters(self, brief: GameBrief) -> list[dict]:
        """Template-based character generation."""
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
        """Generate main and side quests using LLM or templates."""
        if self._llm_available:
            prompt = QUEST_PROMPT.format(
                num_quests=self.config.gdd_architect.max_quests,
                genre=brief.genre,
                title=brief.title,
                acts=[f"Act {a.number}: {a.title}" for a in acts],
                mechanics=", ".join(brief.target_keywords[:5])
            )
            result = self._call_llm(prompt, max_tokens=3000)
            if result:
                parsed_quests = self._parse_quests_response(result, acts)
                if parsed_quests:
                    self.logger.debug(f"Generated {len(parsed_quests)} quests via LLM")
                    return parsed_quests[:self.config.gdd_architect.max_quests]

        # Fallback to template
        return self._template_quests(brief, acts)

    def _parse_quests_response(self, response: str, acts: list[StoryAct]) -> list[Quest]:
        """Parse LLM quest response."""
        quests = []
        quest_id = 0

        sections = response.split("\n\n")

        for section in sections:
            if not section.strip():
                continue

            lines = section.strip().split("\n")
            title = ""
            description = ""
            objectives = []
            rewards = []
            act_num = 1
            is_main = False

            for line in lines:
                line_lower = line.lower()
                if "title:" in line_lower or (lines.index(line) == 0 and ":" not in line):
                    title = line.split(":", 1)[-1].strip().replace("**", "")
                    if title and title[0].isdigit():
                        title = title.split(".", 1)[-1].strip()
                elif "description:" in line_lower:
                    description = line.split(":", 1)[-1].strip()
                elif "objective" in line_lower:
                    obj_text = line.split(":", 1)[-1].strip()
                    objectives = [o.strip() for o in obj_text.split(",")]
                elif line.strip().startswith("-"):
                    objectives.append(line.lstrip("-").strip())
                elif "reward" in line_lower:
                    rew_text = line.split(":", 1)[-1].strip()
                    rewards = [r.strip() for r in rew_text.split(",")]
                elif "act" in line_lower:
                    for i in range(1, 4):
                        if str(i) in line:
                            act_num = i
                            break
                elif "main" in line_lower:
                    is_main = True
                elif "side" in line_lower:
                    is_main = False

            if title:
                if not objectives:
                    objectives = ["Complete objective"]
                if not rewards:
                    rewards = ["Experience", "Resources"]

                quest_type = "main" if is_main else "side"
                quests.append(Quest(
                    id=f"{quest_type}_{quest_id:03d}",
                    title=title,
                    description=description if description else f"Quest: {title}",
                    objectives=objectives[:5],
                    rewards=rewards,
                    act=act_num,
                    is_main_quest=is_main
                ))
                quest_id += 1

        return quests if quests else None

    def _template_quests(self, brief: GameBrief, acts: list[StoryAct]) -> list[Quest]:
        """Template-based quest generation."""
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
        """Generate Unique Selling Points using LLM or templates."""
        if self._llm_available:
            prompt = USP_PROMPT.format(
                title=brief.title,
                concept=brief.one_liner,
                genre=brief.genre,
                mechanics=", ".join(brief.target_keywords[:5])
            )
            result = self._call_llm(prompt, max_tokens=500)
            if result:
                usps = [line.strip().lstrip("1234567890.-) ") for line in result.strip().split("\n") if line.strip()]
                if usps:
                    self.logger.debug("USPs generated via LLM")
                    return usps[:5]

        # Fallback to template
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
        self.logger.info(f"GDD markdown saved to {md_path}")

    def _save_gdd_json(self, gdd: GameDesignDocument) -> None:
        """Save GDD as JSON for programmatic access."""
        json_path = self.output_dir / f"{gdd.title.replace(' ', '_')}_GDD.json"

        gdd_dict = {
            "title": gdd.title,
            "version": gdd.version,
            "last_updated": gdd.last_updated.isoformat(),
            "high_concept": gdd.high_concept,
            "unique_selling_points": gdd.unique_selling_points,
            "target_audience": gdd.target_audience,
            "core_game_loop": gdd.core_game_loop,
            "mechanics": [
                {
                    "name": m.name,
                    "description": m.description,
                    "core_systems": m.core_systems,
                    "player_interactions": m.player_interactions,
                    "dependencies": m.dependencies,
                    "priority": m.priority
                }
                for m in gdd.mechanics
            ],
            "story_synopsis": gdd.story_synopsis,
            "story_acts": [
                {
                    "number": a.number,
                    "title": a.title,
                    "summary": a.summary,
                    "key_events": a.key_events,
                    "locations": a.locations,
                    "characters": a.characters
                }
                for a in gdd.story_acts
            ],
            "main_characters": gdd.main_characters,
            "quests": [
                {
                    "id": q.id,
                    "title": q.title,
                    "description": q.description,
                    "objectives": q.objectives,
                    "rewards": q.rewards,
                    "act": q.act,
                    "is_main_quest": q.is_main_quest
                }
                for q in gdd.quests
            ],
            "monetization_strategy": gdd.monetization_strategy,
            "price_point": gdd.price_point,
            "estimated_dev_time": gdd.estimated_dev_time,
            "team_size": gdd.team_size
        }

        with open(json_path, "w") as f:
            json.dump(gdd_dict, f, indent=2)

        self.logger.info(f"GDD JSON saved to {json_path}")

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

    def cleanup(self) -> None:
        """Clean up resources."""
        self._openai_client = None
        self._anthropic_client = None
        super().cleanup()
