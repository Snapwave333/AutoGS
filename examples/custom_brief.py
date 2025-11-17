#!/usr/bin/env python3
"""
Custom Game Brief Example

This example shows how to start the pipeline with your own Game Brief,
skipping the market research stage.
"""

from pathlib import Path
from autogs import GamePipeline, PipelineConfig
from autogs.models.game_brief import GameBrief


def main():
    print("=== Custom Game Brief Example ===\n")

    # Create your own Game Brief
    my_brief = GameBrief(
        title="Stellar Nomads",
        one_liner="A procedural space exploration game with base-building and trading",
        genre="exploration",
        sub_genres=["sci-fi", "sandbox", "survival-lite"],
        player_count="1-2 players",
        core_theme="cosmic-frontier",
        setting="Procedurally generated galaxy with unique solar systems",
        target_platforms=["PC", "Steam"],
        avoid_keywords=["combat-focused", "battle-royale", "competitive"],
        target_keywords=["exploration", "discovery", "trading", "base-building", "peaceful"],
        confidence_score=1.0  # High confidence since you defined it
    )

    print("Custom Game Brief:")
    print(my_brief)

    # Configure pipeline to start from Stage 2
    config = PipelineConfig()
    config.project_name = "StellarNomads"
    config.paths.output_base = Path("./custom_output")
    config.run_stages = [2, 3, 4]  # Skip trend scout, run GDD, Assets, Code
    config.dry_run = True
    config.verbose = True

    # Create pipeline
    pipeline = GamePipeline(config)

    # Run pipeline starting from Stage 2 with custom brief
    print("Running pipeline from Stage 2...")
    print("=" * 50)

    # Run Stage 2 (GDD Architect) with custom brief
    gdd_result = pipeline.run_single_stage(2, my_brief)

    print(f"\nGDD Generated: {gdd_result.title}")
    print(f"  Mechanics: {len(gdd_result.mechanics)}")
    print(f"  Quests: {len(gdd_result.quests)}")
    print(f"  Assets needed: {gdd_result.asset_manifest.total_assets()}")

    # You can continue with subsequent stages
    if 3 in config.run_stages:
        print("\nRunning Asset Factory...")
        assets = pipeline.run_single_stage(3, gdd_result)
        print(f"  Assets generated: {assets.total_assets()}")

    if 4 in config.run_stages:
        print("\nRunning Engineer Bot...")
        project = pipeline.run_single_stage(4, gdd_result)
        print(f"  Scripts generated: {project.total_scripts()}")

    print(f"\nOutput saved to: {pipeline.output_dir}")


if __name__ == "__main__":
    main()
