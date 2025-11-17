# AutoGS - Automated Game Studio

A bot-driven pipeline for Unity game development that automates 90% of the development labor. Your role shifts from "artist" or "coder" to "Executive Producer" who directs a team of specialized AI bots.

## Overview

AutoGS implements a 5-stage pipeline that transforms market insights into deployable Unity games:

```
Market Research → Game Design → Asset Generation → Code Generation → Build & Deploy
```

**Important Note:** As of 2025, a single bot cannot autonomously create fun, cohesive games. The "fun" part—core game loop, system architecture, and cohesion—still requires a human "Director." AutoGS automates the manual labor while you make the creative decisions.

## The Five Stages

### Stage 1: Trend Scout Bot (Market Research)
**Goal:** Find a profitable, low-competition niche.

- Scrapes data from Steam, itch.io, and TikTok
- Analyzes sentiment and keyword velocity
- Identifies high-demand, low-supply combinations
- **Output:** Game Brief with market-validated concept

```
Example Output:
"High-demand, low-supply niche detected: '1-4 player co-op sci-fi survival
game with base-building'. Avoid 'zombies' (saturated); target 'alien planets'
(high-demand)."
```

### Stage 2: GDD Architect Bot (Pre-Production)
**Goal:** Transform the Game Brief into a complete Game Design Document.

- Generates core game loop and mechanics
- Designs story structure (3 acts) and quests
- Creates character profiles and narrative arcs
- Compiles complete asset requirements list
- **Output:** 50+ page comprehensive GDD

### Stage 3: Asset Factory Bot (Production)
**Goal:** Programmatically create every asset in the GDD.

Calls specialized AI APIs:
- **2D Art:** Recraft, Midjourney, DALL-E for textures, sprites, UI
- **3D Models:** Meshy for text-to-3D and image-to-3D generation
- **Audio:** ElevenLabs for SFX, Mubert for music
- **UI/UX:** Uizard for interface design
- **Output:** Complete asset library organized for Unity import

### Stage 4: Engineer Bot (Code Generation)
**Goal:** Write C# scripts and assemble the Unity project.

- Generates scripts for each mechanic in the GDD
- Creates Unity project structure
- Sets up scenes, configurations, and packages
- **Output:** Complete Unity project with all scripts

**Note:** AI writes the components; you integrate them. The AI cannot architect the full game's systems—it can only write components on command.

### Stage 5: Build & Deploy Bot (Distribution)
**Goal:** Compile final executables for all platforms.

- Executes Unity batch mode builds
- Packages for Windows, Mac, Linux, Android, iOS, WebGL
- Generates build scripts for manual use
- **Output:** Deployment-ready .exe, .apk, etc.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AutoGS.git
cd AutoGS

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

## Quick Start

### 1. Initialize a Project

```bash
python -m autogs init MyAwesomeGame
```

This creates:
- Project directory structure
- Default configuration file
- Output folders for each stage

### 2. Configure API Keys

Edit the generated `config.json`:

```json
{
  "api": {
    "openai_api_key": "your-key-here",
    "meshy_api_key": "your-key-here",
    "recraft_api_key": "your-key-here"
  }
}
```

### 3. Run the Pipeline

```bash
# Full pipeline
python -m autogs run --config ./output/MyAwesomeGame/config.json

# Dry run (simulation)
python -m autogs run --dry-run

# Specific stages only
python -m autogs run --stages 1 2

# Single stage
python -m autogs stage 2
```

### 4. Review Results

Each stage saves its output to the project directory:
- Stage 1: `TrendScoutBot/` - Market analysis and Game Brief
- Stage 2: `GDDArchitectBot/` - Complete GDD in Markdown
- Stage 3: `AssetFactoryBot/` - Generated assets organized by type
- Stage 4: `EngineerBot/` - Unity project with C# scripts
- Stage 5: `BuildDeployBot/` - Build artifacts and scripts

## Programmatic Usage

```python
from autogs import GamePipeline, PipelineConfig

# Create configuration
config = PipelineConfig()
config.project_name = "SpaceColony"
config.dry_run = True

# Initialize pipeline
pipeline = GamePipeline(config)

# Run full pipeline
results = pipeline.run()

# Or run individual stages
brief = pipeline.run_single_stage(1)  # Market research
gdd = pipeline.run_single_stage(2, brief)  # Generate GDD
assets = pipeline.run_single_stage(3, gdd)  # Create assets
```

See `examples/` for more detailed usage patterns.

## CLI Commands

```bash
# Initialize new project
python -m autogs init [project_name]

# Run pipeline
python -m autogs run [--config PATH] [--stages N...] [--dry-run]

# Run single stage
python -m autogs stage N [--input FILE]

# Manage configuration
python -m autogs config --show
python -m autogs config --create
python -m autogs config --validate

# Check status
python -m autogs status

# Show information
python -m autogs info
```

## Project Structure

```
AutoGS/
├── autogs/                 # Main package
│   ├── bots/              # Bot implementations
│   │   ├── trend_scout.py      # Stage 1
│   │   ├── gdd_architect.py    # Stage 2
│   │   ├── asset_factory.py    # Stage 3
│   │   ├── engineer.py         # Stage 4
│   │   └── build_deploy.py     # Stage 5
│   ├── core/              # Core infrastructure
│   │   ├── pipeline.py         # Main orchestrator
│   │   ├── config.py           # Configuration management
│   │   └── base_bot.py         # Base bot class
│   ├── models/            # Data models
│   │   ├── game_brief.py       # Stage 1 output
│   │   ├── gdd.py              # Stage 2 output
│   │   ├── assets.py           # Stage 3 output
│   │   ├── code.py             # Stage 4 output
│   │   └── build.py            # Stage 5 output
│   └── templates/         # LLM prompt templates
├── config/                # Configuration files
├── examples/              # Example usage scripts
├── scripts/               # Build and utility scripts
└── output/                # Generated project output
```

## Configuration

The pipeline is highly configurable. Key settings:

```json
{
  "project_name": "MyGame",
  "run_stages": [1, 2, 3, 4, 5],  // Which stages to run
  "dry_run": false,                // Simulate without executing
  "verbose": true,                 // Detailed logging

  "trend_scout": {
    "sources": ["steam", "itch", "tiktok"],
    "sentiment_threshold": 0.6,
    "velocity_threshold": 2.0
  },

  "gdd_architect": {
    "detail_level": "comprehensive",
    "max_mechanics": 10,
    "max_quests": 20
  },

  "engineer": {
    "unity_version": "2022.3.0f1",
    "render_pipeline": "URP"
  },

  "build": {
    "target_platforms": ["windows_64", "android"]
  }
}
```

## Your Role as Director

While the bots handle the manual labor, you are responsible for:

1. **Creative Vision** - Defining what makes your game unique
2. **Quality Control** - Reviewing and refining bot outputs
3. **Integration** - Connecting systems and ensuring cohesion
4. **Playtesting** - Validating that the game is actually fun
5. **Polish** - Adding the human touch that makes games special

## Current Limitations

- **No True Autonomy:** Bots execute predefined tasks, not creative decisions
- **API Dependencies:** Asset generation requires external AI service subscriptions
- **Integration Required:** Generated code needs human assembly and debugging
- **Fun Factor:** AI cannot guarantee the game will be enjoyable to play
- **Context Limits:** LLM context windows limit scope of generation

## Future Roadmap

- [ ] Real-time API integration with Steam, itch.io, TikTok
- [ ] LLM-powered mechanic generation with actual AI calls
- [ ] Async asset generation with progress tracking
- [ ] Unity Editor integration plugin
- [ ] Automated testing and quality metrics
- [ ] Steam/Play Store deployment automation

## License

MIT License

## Contributing

Contributions are welcome! Areas particularly in need:
- Real API integrations for data sources
- Enhanced code generation templates
- Unity Editor tooling
- Additional asset generation providers

## Acknowledgments

This project was inspired by the potential of AI-assisted game development and the vision of democratizing game creation. While we're not yet at "push button, receive game," we're building the tools that will get us there.

---

**Remember:** The goal isn't to replace human creativity—it's to amplify it. You're not just a user of AutoGS; you're the Director of your own AI-powered game studio.
