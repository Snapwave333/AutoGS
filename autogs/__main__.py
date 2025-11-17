"""
Command-line interface for AutoGS - Automated Game Studio.

Usage:
    python -m autogs init [project_name]       Initialize a new project
    python -m autogs run [--stage N]           Run the full pipeline
    python -m autogs stage N                   Run a specific stage
    python -m autogs config                    Show/edit configuration
    python -m autogs status                    Show pipeline status
"""

import argparse
import json
import sys
from pathlib import Path

from . import GamePipeline, PipelineConfig, __version__


def main():
    """Main entry point for AutoGS CLI."""
    parser = argparse.ArgumentParser(
        description="AutoGS - Automated Game Studio Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m autogs init MyAwesomeGame      Create new project
  python -m autogs run                     Run full pipeline
  python -m autogs run --dry-run           Simulate pipeline
  python -m autogs stage 1                 Run only Trend Scout
  python -m autogs config --show           Show current config
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"AutoGS v{__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new project")
    init_parser.add_argument("name", nargs="?", default="MyGame", help="Project name")
    init_parser.add_argument(
        "--output", "-o", default="./output", help="Output directory"
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the pipeline")
    run_parser.add_argument(
        "--config", "-c", type=Path, help="Path to config file"
    )
    run_parser.add_argument(
        "--stages", "-s", nargs="+", type=int, help="Specific stages to run (1-5)"
    )
    run_parser.add_argument(
        "--start", type=int, default=1, help="Starting stage (default: 1)"
    )
    run_parser.add_argument(
        "--dry-run", action="store_true", help="Simulate without executing"
    )
    run_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Stage command
    stage_parser = subparsers.add_parser("stage", help="Run a specific stage")
    stage_parser.add_argument("number", type=int, choices=[1, 2, 3, 4, 5], help="Stage number")
    stage_parser.add_argument(
        "--config", "-c", type=Path, help="Path to config file"
    )
    stage_parser.add_argument(
        "--input", "-i", type=Path, help="Input data from previous stage"
    )
    stage_parser.add_argument(
        "--dry-run", action="store_true", help="Simulate without executing"
    )

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument(
        "--show", action="store_true", help="Show current configuration"
    )
    config_parser.add_argument(
        "--create", action="store_true", help="Create default config file"
    )
    config_parser.add_argument(
        "--validate", action="store_true", help="Validate configuration"
    )
    config_parser.add_argument(
        "--path", "-p", type=Path, default=Path("./autogs_config.json"),
        help="Config file path"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show pipeline status")
    status_parser.add_argument(
        "--project", "-p", type=Path, help="Project output directory"
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Show pipeline information")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute commands
    if args.command == "init":
        cmd_init(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "stage":
        cmd_stage(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "info":
        cmd_info(args)
    else:
        parser.print_help()


def cmd_init(args):
    """Initialize a new project."""
    print(f"🎮 Initializing AutoGS project: {args.name}")
    print(f"Output directory: {args.output}")

    # Create configuration
    config = PipelineConfig.create_default()
    config.project_name = args.name
    config.paths.output_base = Path(args.output)

    # Create output directory structure
    output_dir = Path(args.output) / args.name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save configuration
    config_path = output_dir / "config.json"
    config.save(config_path)

    print(f"✓ Created project directory: {output_dir}")
    print(f"✓ Created configuration: {config_path}")
    print()
    print("Next steps:")
    print(f"  1. Edit {config_path} to add API keys and settings")
    print(f"  2. Run: python -m autogs run --config {config_path}")
    print()
    print("Pipeline stages:")
    print("  Stage 1: Trend Scout - Market research and niche finding")
    print("  Stage 2: GDD Architect - Game Design Document generation")
    print("  Stage 3: Asset Factory - AI-powered asset generation")
    print("  Stage 4: Engineer - Code generation and Unity setup")
    print("  Stage 5: Build & Deploy - Compilation and packaging")


def cmd_run(args):
    """Run the full pipeline."""
    print("🚀 AutoGS Pipeline Starting...")
    print()

    # Load or create configuration
    if args.config and args.config.exists():
        config = PipelineConfig.load(args.config)
        print(f"Loaded configuration from {args.config}")
    else:
        config = PipelineConfig.create_default()
        print("Using default configuration")

    # Apply command-line overrides
    if args.stages:
        config.run_stages = args.stages
    if args.dry_run:
        config.dry_run = True
    if args.verbose:
        config.verbose = True

    # Create and run pipeline
    pipeline = GamePipeline(config)

    print(f"Project: {config.project_name}")
    print(f"Stages to run: {config.run_stages}")
    print(f"Dry run: {config.dry_run}")
    print()

    try:
        results = pipeline.run(start_stage=args.start)

        print("\n" + "=" * 50)
        print("PIPELINE COMPLETE")
        print("=" * 50)
        print(f"Stages completed: {list(results.keys())}")

        # Show brief results
        for stage, result in results.items():
            stage_name = pipeline.STAGE_MAP.get(stage, ("Unknown", None))[0]
            if isinstance(result, dict) and "error" in result:
                print(f"  Stage {stage} ({stage_name}): ❌ Failed")
            else:
                print(f"  Stage {stage} ({stage_name}): ✓ Success")

        print(f"\nOutput directory: {pipeline.output_dir}")

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline error: {str(e)}")
        sys.exit(1)


def cmd_stage(args):
    """Run a specific pipeline stage."""
    stage_names = {
        1: "Trend Scout (Market Research)",
        2: "GDD Architect (Pre-Production)",
        3: "Asset Factory (Asset Generation)",
        4: "Engineer (Code Generation)",
        5: "Build & Deploy (Distribution)",
    }

    print(f"🔧 Running Stage {args.number}: {stage_names.get(args.number)}")
    print()

    # Load configuration
    if args.config and args.config.exists():
        config = PipelineConfig.load(args.config)
    else:
        config = PipelineConfig.create_default()

    if args.dry_run:
        config.dry_run = True

    # Load input data if provided
    input_data = None
    if args.input and args.input.exists():
        with open(args.input, "r") as f:
            input_data = json.load(f)
        print(f"Loaded input from {args.input}")

    # Run single stage
    pipeline = GamePipeline(config)
    try:
        result = pipeline.run_single_stage(args.number, input_data)
        print(f"\n✓ Stage {args.number} completed successfully")
        print(f"Output directory: {pipeline.output_dir}")
    except Exception as e:
        print(f"\n❌ Stage {args.number} failed: {str(e)}")
        sys.exit(1)


def cmd_config(args):
    """Manage pipeline configuration."""
    if args.create:
        print(f"Creating default configuration at {args.path}")
        config = PipelineConfig.create_default()
        config.save(args.path)
        print(f"✓ Configuration saved to {args.path}")
        print("\nRemember to edit the file and add your API keys!")

    elif args.show:
        if args.path.exists():
            config = PipelineConfig.load(args.path)
            print(f"Configuration from {args.path}:")
            print("=" * 50)
            print(f"Project Name: {config.project_name}")
            print(f"Version: {config.version}")
            print(f"Output Base: {config.paths.output_base}")
            print(f"Stages to Run: {config.run_stages}")
            print(f"Dry Run: {config.dry_run}")
            print(f"Verbose: {config.verbose}")
            print()
            print("API Configuration:")
            print(f"  LLM Provider: {config.api.llm_provider}")
            print(f"  LLM Model: {config.api.llm_model}")
            print(f"  OpenAI Key: {'Set' if config.api.openai_api_key else 'Not set'}")
            print(f"  Anthropic Key: {'Set' if config.api.anthropic_api_key else 'Not set'}")
            print()
            print("Build Configuration:")
            print(f"  Target Platforms: {config.build.target_platforms}")
            print(f"  Development Build: {config.build.development_build}")
        else:
            print(f"Configuration file not found: {args.path}")
            print(f"Create one with: python -m autogs config --create --path {args.path}")

    elif args.validate:
        if args.path.exists():
            config = PipelineConfig.load(args.path)
            errors = config.validate()
            if errors:
                print("⚠️  Configuration warnings:")
                for error in errors:
                    print(f"  - {error}")
            else:
                print("✓ Configuration is valid")
        else:
            print(f"Configuration file not found: {args.path}")

    else:
        print("Use --show, --create, or --validate")


def cmd_status(args):
    """Show pipeline status."""
    print("📊 AutoGS Pipeline Status")
    print("=" * 50)

    if args.project and args.project.exists():
        project_dir = args.project
    else:
        project_dir = Path("./output")

    if not project_dir.exists():
        print("No project output directory found")
        return

    # List projects
    projects = [d for d in project_dir.iterdir() if d.is_dir()]
    if not projects:
        print("No projects found")
        return

    for project in projects:
        print(f"\nProject: {project.name}")
        print("-" * 40)

        # Check each stage
        stages = ["TrendScoutBot", "GDDArchitectBot", "AssetFactoryBot", "EngineerBot", "BuildDeployBot"]
        for i, stage_name in enumerate(stages, 1):
            stage_dir = project / stage_name
            if stage_dir.exists():
                result_files = list(stage_dir.glob("result_*.json"))
                if result_files:
                    latest = sorted(result_files)[-1]
                    print(f"  Stage {i} ({stage_name}): ✓ Completed")
                    print(f"    Latest: {latest.name}")
                else:
                    print(f"  Stage {i} ({stage_name}): ○ Directory exists, no results")
            else:
                print(f"  Stage {i} ({stage_name}): - Not run")

        # Check for pipeline report
        report = project / "pipeline_report.json"
        if report.exists():
            with open(report, "r") as f:
                data = json.load(f)
            print(f"\n  Last run: {data.get('end_time', 'Unknown')}")
            print(f"  Duration: {data.get('duration_seconds', 0):.2f}s")


def cmd_info(args):
    """Show pipeline information."""
    print("🎮 AutoGS - Automated Game Studio")
    print("=" * 50)
    print(f"Version: {__version__}")
    print()
    print("Pipeline Stages:")
    print("  1. Trend Scout Bot - Market research and niche finding")
    print("     • Scrapes Steam, itch.io, TikTok for trends")
    print("     • Analyzes sentiment and keyword velocity")
    print("     • Identifies high-demand, low-supply niches")
    print("     • Outputs: Game Brief")
    print()
    print("  2. GDD Architect Bot - Game Design Document generation")
    print("     • Takes Game Brief as input")
    print("     • Generates core mechanics and game loop")
    print("     • Creates story, quests, and characters")
    print("     • Compiles complete asset requirements")
    print("     • Outputs: 50+ page GDD")
    print()
    print("  3. Asset Factory Bot - AI-powered asset generation")
    print("     • Reads asset manifest from GDD")
    print("     • Calls AI APIs for each asset type:")
    print("       - Recraft/Midjourney for 2D art")
    print("       - Meshy for 3D models")
    print("       - ElevenLabs/Mubert for audio")
    print("     • Outputs: All game assets")
    print()
    print("  4. Engineer Bot - Code generation")
    print("     • Generates C# scripts from mechanics")
    print("     • Sets up Unity project structure")
    print("     • Creates scenes and configurations")
    print("     • Outputs: Complete Unity project")
    print()
    print("  5. Build & Deploy Bot - Compilation")
    print("     • Builds for configured platforms")
    print("     • Generates build scripts")
    print("     • Packages deployment artifacts")
    print("     • Outputs: .exe, .apk, etc.")
    print()
    print("Your Role:")
    print("  As the 'Director', you make creative decisions")
    print("  while the bots handle the manual labor.")
    print()
    print("Getting Started:")
    print("  python -m autogs init MyGame")
    print("  python -m autogs run --dry-run")
    print("  python -m autogs info")


if __name__ == "__main__":
    main()
