#!/usr/bin/env python3
"""
Quick Start Example for AutoGS

This script demonstrates how to use the AutoGS pipeline programmatically.
"""

from pathlib import Path
from autogs import GamePipeline, PipelineConfig


def main():
    print("=== AutoGS Quick Start ===\n")

    # Step 1: Create configuration
    print("1. Creating pipeline configuration...")
    config = PipelineConfig()
    config.project_name = "SpaceColony"
    config.version = "0.1.0"
    config.paths.output_base = Path("./quick_start_output")
    config.dry_run = True  # Set to False for actual execution
    config.verbose = True

    # Configure which stages to run
    config.run_stages = [1, 2]  # Only run market research and GDD generation

    print(f"   Project: {config.project_name}")
    print(f"   Output: {config.paths.output_base}")
    print(f"   Stages: {config.run_stages}")
    print()

    # Step 2: Create pipeline
    print("2. Initializing pipeline...")
    pipeline = GamePipeline(config)
    print(f"   Pipeline created for: {pipeline.config.project_name}")
    print()

    # Step 3: Run pipeline
    print("3. Running pipeline...")
    print("=" * 50)
    results = pipeline.run()
    print("=" * 50)
    print()

    # Step 4: Examine results
    print("4. Pipeline Results:")
    for stage_num, result in results.items():
        stage_name = pipeline.STAGE_MAP.get(stage_num, ("Unknown", None))[0]
        print(f"\n   Stage {stage_num}: {stage_name}")

        if stage_num == 1 and result:
            # Trend Scout result (GameBrief)
            print(f"   Title: {result.title}")
            print(f"   Concept: {result.one_liner}")
            print(f"   Genre: {result.genre}")
            print(f"   Confidence: {result.confidence_score:.1%}")

        elif stage_num == 2 and result:
            # GDD Architect result (GameDesignDocument)
            print(f"   Mechanics: {len(result.mechanics)}")
            print(f"   Quests: {len(result.quests)}")
            print(f"   Total Assets: {result.asset_manifest.total_assets()}")

    print(f"\n   Full output saved to: {pipeline.output_dir}")
    print()

    # Step 5: Save configuration for later
    print("5. Saving configuration...")
    config_path = pipeline.output_dir / "pipeline_config.json"
    pipeline.save_config(config_path)
    print(f"   Saved to: {config_path}")
    print()

    print("=== Quick Start Complete ===")
    print("\nNext Steps:")
    print("1. Review the generated Game Brief and GDD")
    print("2. Modify the configuration with your API keys")
    print("3. Run the full pipeline: config.run_stages = [1,2,3,4,5]")
    print("4. Set config.dry_run = False for actual execution")


if __name__ == "__main__":
    main()
