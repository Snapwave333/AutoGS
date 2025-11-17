"""
Steam Deployment Bot
One-click Steam deployment with Steamworks SDK integration.
"""

import json
import subprocess
import shutil
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime

from ..core.base_bot import BaseBot
from ..core.config import PipelineConfig


class SteamDeployerBot(BaseBot):
    """
    Bot responsible for automated Steam deployment.

    This bot:
    1. Configures Steamworks SDK
    2. Manages depots and builds
    3. Uploads build to Steam
    4. Sets build live (optional)
    """

    def __init__(self, config: Optional[PipelineConfig] = None, dry_run: bool = False):
        """Initialize SteamDeployerBot."""
        super().__init__(config, dry_run)
        self.steamworks_sdk_path = None
        self.steamcmd_path = None

    def run(self, input_data: Optional[Any] = None) -> Dict[str, Any]:
        """
        Deploy build to Steam.

        Args:
            input_data: Build information (game name, build paths, etc.)

        Returns:
            Deployment result with status and build ID
        """
        if not isinstance(input_data, dict):
            raise ValueError("Expected dict with build information")

        build_info = input_data
        game_name = build_info.get("game_name", "MyGame")
        build_paths = build_info.get("build_paths", {})

        self.logger.info(f"Deploying {game_name} to Steam...")

        # Step 1: Validate Steamworks setup
        if not self._validate_steamworks_setup():
            self.logger.error("Steamworks SDK not configured properly")
            return self._create_result(False, "Steamworks SDK not found")

        # Step 2: Generate Steam config files
        self.logger.info("Generating Steam configuration files...")
        app_id = self._get_or_create_app_id(game_name)
        depot_configs = self._generate_depot_configs(build_paths, app_id)

        # Step 3: Build VDF scripts
        self.logger.info("Creating VDF build scripts...")
        vdf_path = self._create_vdf_script(game_name, app_id, depot_configs)

        # Step 4: Upload to Steam
        self.logger.info("Uploading build to Steam...")
        if self.dry_run:
            result = self._simulate_upload(vdf_path)
        else:
            result = self._upload_to_steam(vdf_path)

        # Step 5: Generate deployment report
        self._save_deployment_report(result, game_name, app_id)

        return result

    def validate_input(self, input_data: Optional[Any]) -> bool:
        """Validate input data."""
        if input_data is None:
            return False

        if not isinstance(input_data, dict):
            return False

        # Check for required fields
        required = ["game_name"]
        return all(key in input_data for key in required)

    def _validate_steamworks_setup(self) -> bool:
        """Validate that Steamworks SDK is properly configured."""
        # Check for Steamworks SDK path in config or environment
        sdk_paths = [
            self.config.build.get("steamworks_sdk_path") if hasattr(self.config, "build") else None,
            Path.home() / "steamworks_sdk",
            Path("C:/steamworks_sdk") if Path("C:/").exists() else None,
            Path("/opt/steamworks_sdk"),
        ]

        for path in sdk_paths:
            if path and Path(path).exists():
                self.steamworks_sdk_path = Path(path)
                self.logger.info(f"Found Steamworks SDK at: {path}")
                break

        if not self.steamworks_sdk_path:
            self.logger.warning("Steamworks SDK not found. Set 'steamworks_sdk_path' in config.")
            return False

        # Look for SteamCMD
        steamcmd_executable = "steamcmd.exe" if self._is_windows() else "steamcmd.sh"
        steamcmd = self.steamworks_sdk_path / "tools" / "ContentBuilder" / steamcmd_executable

        if steamcmd.exists():
            self.steamcmd_path = steamcmd
            return True

        self.logger.warning(f"SteamCMD not found at expected location: {steamcmd}")
        return False

    def _get_or_create_app_id(self, game_name: str) -> int:
        """
        Get or create Steam App ID.

        In production, this would:
        1. Check if app is already registered with Steamworks
        2. Use configured App ID from config
        3. Warn if app not found

        For now, returns a placeholder that user must replace.
        """
        # Check config first
        if hasattr(self.config, "steam_app_id") and self.config.steam_app_id:
            return self.config.steam_app_id

        # Return placeholder
        self.logger.warning(
            "No Steam App ID configured. Using placeholder 480 (SpaceWar).\n"
            "Replace this with your actual App ID before production deployment!"
        )
        return 480  # SpaceWar test app

    def _generate_depot_configs(self, build_paths: Dict[str, str], app_id: int) -> List[Dict]:
        """Generate depot configurations for each platform."""
        depots = []
        depot_id_base = app_id + 1

        platform_mapping = {
            "Windows": {"depot_id": depot_id_base, "os": "windows"},
            "macOS": {"depot_id": depot_id_base + 1, "os": "macos"},
            "Linux": {"depot_id": depot_id_base + 2, "os": "linux"},
        }

        for platform, build_path in build_paths.items():
            if platform not in platform_mapping:
                continue

            depot = {
                "depot_id": platform_mapping[platform]["depot_id"],
                "platform": platform,
                "os": platform_mapping[platform]["os"],
                "content_path": build_path,
            }
            depots.append(depot)

        return depots

    def _create_vdf_script(self, game_name: str, app_id: int, depot_configs: List[Dict]) -> Path:
        """Create VDF build script for SteamCMD."""
        output_path = self.output_dir / "steam_build"
        output_path.mkdir(parents=True, exist_ok=True)

        # Create app build script
        app_build_vdf = output_path / f"app_build_{app_id}.vdf"

        vdf_content = f'"AppBuild"\n{{\n'
        vdf_content += f'    "AppID" "{app_id}"\n'
        vdf_content += f'    "Desc" "{game_name} build {datetime.now():%Y%m%d_%H%M%S}"\n'
        vdf_content += f'    "BuildOutput" "{output_path / "output"}"\n'
        vdf_content += f'    "ContentRoot" "{output_path / "content"}"\n'
        vdf_content += f'    "SetLive" ""\n'  # Empty = don't set live automatically
        vdf_content += f'    "Preview" "0"\n'
        vdf_content += f'    "Local" ""\n'

        # Add depots
        vdf_content += '    "Depots"\n    {\n'
        for depot in depot_configs:
            depot_id = depot["depot_id"]
            vdf_content += f'        "{depot_id}"\n'
            vdf_content += '        {\n'
            vdf_content += f'            "FileMapping"\n'
            vdf_content += '            {\n'
            vdf_content += f'                "LocalPath" "{depot["content_path"]}/*"\n'
            vdf_content += f'                "DepotPath" "."\n'
            vdf_content += f'                "recursive" "1"\n'
            vdf_content += '            }\n'
            vdf_content += '        }\n'

            # Create depot build VDF
            depot_vdf_path = output_path / f"depot_build_{depot_id}.vdf"
            depot_vdf = f'"DepotBuildConfig"\n{{\n'
            depot_vdf += f'    "DepotID" "{depot_id}"\n'
            depot_vdf += f'    "ContentRoot" "{depot["content_path"]}"\n'
            depot_vdf += f'    "FileMapping"\n'
            depot_vdf += '    {\n'
            depot_vdf += f'        "LocalPath" "*"\n'
            depot_vdf += f'        "DepotPath" "."\n'
            depot_vdf += f'        "recursive" "1"\n'
            depot_vdf += '    }\n'
            depot_vdf += '}\n'

            with open(depot_vdf_path, "w") as f:
                f.write(depot_vdf)

        vdf_content += '    }\n'
        vdf_content += '}\n'

        with open(app_build_vdf, "w") as f:
            f.write(vdf_content)

        self.logger.info(f"Created VDF build script: {app_build_vdf}")
        return app_build_vdf

    def _upload_to_steam(self, vdf_path: Path) -> Dict[str, Any]:
        """Upload build to Steam using SteamCMD."""
        if not self.steamcmd_path:
            return self._create_result(False, "SteamCMD not available")

        try:
            # Build steamcmd command
            # Note: User must configure Steam credentials separately
            cmd = [
                str(self.steamcmd_path),
                "+login", "username", "password",  # Replace with actual credentials
                "+run_app_build", str(vdf_path),
                "+quit"
            ]

            self.logger.info(f"Running SteamCMD: {' '.join(cmd)}")

            # Execute SteamCMD
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout for uploads
            )

            if result.returncode == 0:
                build_id = self._extract_build_id(result.stdout)
                return self._create_result(True, "Upload successful", build_id)
            else:
                return self._create_result(False, f"Upload failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            return self._create_result(False, "Upload timeout")
        except Exception as e:
            return self._create_result(False, f"Upload error: {e}")

    def _simulate_upload(self, vdf_path: Path) -> Dict[str, Any]:
        """Simulate Steam upload for dry-run mode."""
        self.logger.info(f"DRY RUN: Would upload using VDF: {vdf_path}")
        return self._create_result(
            True,
            "Dry-run simulation successful",
            build_id="DRY_RUN_12345"
        )

    def _extract_build_id(self, output: str) -> str:
        """Extract build ID from SteamCMD output."""
        # Parse SteamCMD output for build ID
        # This is a simplified version - real implementation would parse properly
        for line in output.split("\n"):
            if "BuildID" in line or "build ID" in line.lower():
                # Extract number from line
                import re
                match = re.search(r'\d+', line)
                if match:
                    return match.group()

        # Return timestamp-based ID if not found
        return f"BUILD_{datetime.now():%Y%m%d_%H%M%S}"

    def _create_result(self, success: bool, message: str, build_id: str = None) -> Dict[str, Any]:
        """Create deployment result dictionary."""
        return {
            "success": success,
            "message": message,
            "build_id": build_id,
            "timestamp": datetime.now().isoformat(),
            "platform": "Steam"
        }

    def _save_deployment_report(self, result: Dict[str, Any], game_name: str, app_id: int) -> None:
        """Save deployment report to output directory."""
        report_path = self.output_dir / "steam_deployment_report.json"

        report = {
            "game_name": game_name,
            "app_id": app_id,
            "deployment_result": result,
            "steamworks_sdk": str(self.steamworks_sdk_path) if self.steamworks_sdk_path else None,
        }

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Deployment report saved to: {report_path}")

    def _is_windows(self) -> bool:
        """Check if running on Windows."""
        import platform
        return platform.system() == "Windows"

    def _dry_run(self, input_data: Optional[Any]) -> Dict[str, Any]:
        """Simulate deployment."""
        self.logger.info("DRY RUN: Simulating Steam deployment")
        return self._create_result(True, "Dry-run complete", "DRY_RUN_BUILD")
