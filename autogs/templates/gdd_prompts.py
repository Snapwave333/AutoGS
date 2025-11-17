"""
Prompt templates for GDD generation.
These prompts are used by the GDD Architect Bot when calling LLM APIs.
"""

CORE_LOOP_PROMPT = """
You are a game designer creating the core game loop for a {genre} game.

Game Brief:
- Title: {title}
- Concept: {concept}
- Target Keywords: {keywords}
- Theme: {theme}

Generate a core game loop with 5-7 sequential steps that the player will repeat.
Each step should be a verb that describes player action.
Format as numbered list with brief descriptions.
"""

MECHANICS_PROMPT = """
Design {num_mechanics} game mechanics for this game:

Title: {title}
Genre: {genre}
Core Theme: {theme}
Key Features: {features}

For each mechanic, provide:
1. Name
2. Description (2-3 sentences)
3. Core Systems (programming components needed)
4. Player Interactions (verbs/actions)
5. Dependencies (other mechanics it requires)
6. Priority (critical/high/medium/low)

Focus on mechanics that reinforce the {theme} theme and support {genre} gameplay.
"""

STORY_PROMPT = """
Create a 3-act story structure for:

Game: {title}
Genre: {genre}
Setting: {setting}
Theme: {theme}

For each act provide:
- Act number and title
- Summary (3-4 sentences)
- Key events (4-5 bullet points)
- Main locations
- Characters introduced

The story should support the core gameplay loop and integrate with mechanics naturally.
"""

QUEST_PROMPT = """
Generate {num_quests} quests for a {genre} game:

Title: {title}
Story Acts: {acts}
Mechanics: {mechanics}

For each quest:
- ID (unique identifier)
- Title
- Description
- Objectives (3-5 specific tasks)
- Rewards
- Prerequisites (if any)
- Act it belongs to
- Whether it's main quest or side quest

Ensure quests utilize the game's core mechanics and advance the story.
"""

ASSET_LIST_PROMPT = """
Generate a complete asset list for:

Game: {title}
Genre: {genre}
Setting: {setting}
Mechanics: {mechanics}

Categorize assets as:
1. 3D Models (characters, props, environment)
2. 2D Sprites/Textures
3. UI Elements
4. Sound Effects
5. Music Tracks
6. Animations

For each asset provide:
- Category
- Name
- Description
- Technical specifications (poly count, resolution, duration, etc.)
- Priority (critical/high/medium/low)

Focus on essential assets needed for a minimum viable product.
"""

CHARACTER_PROMPT = """
Create {num_characters} main characters for:

Game: {title}
Genre: {genre}
Story: {synopsis}
Theme: {theme}

For each character:
- Name
- Role (player, companion, antagonist, NPC)
- Physical description
- Personality traits
- Backstory (2-3 sentences)
- Character arc
- Key dialogue style

Characters should support the story and fit the {setting} setting.
"""

USP_PROMPT = """
Generate 5 Unique Selling Points for:

Game: {title}
Concept: {concept}
Genre: {genre}
Key Mechanics: {mechanics}

Each USP should:
- Be compelling and specific
- Differentiate from similar games
- Highlight a tangible benefit to players
- Be achievable within scope

Format as clear, marketing-ready statements.
"""
