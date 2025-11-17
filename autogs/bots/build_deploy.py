"""
Stage 5: Build & Deploy Bot
Compilation and distribution automation.
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..core.base_bot import BaseBot
from ..core.config import PipelineConfig
from ..models.code import UnityProject
from ..models.build import (
    BuildConfig as BuildConfiguration,
    BuildPlatform,
    BuildStatus,
    BuildResult,
    BuildOutput,
)


class BuildDeployBot(BaseBot):
    """
    Bot responsible for building and packaging the Unity project.

    This bot:
    1. Reads Unity project configuration
    2. Executes Unity batch mode builds
    3. Packages for multiple platforms
    4. Generates deployment-ready artifacts
    """

    def run(self, input_data: Optional[Any] = None) -> BuildOutput:
        """
        Build the Unity project for configured platforms.

        Args:
            input_data: UnityProject from Stage 4

        Returns:
            BuildOutput with all build results
        """
        if isinstance(input_data, UnityProject):
            project = input_data
        elif isinstance(input_data, dict):
            # Basic project info
            project = UnityProject(
                project_name=input_data.get("project_name", "Game"),
                project_path=Path(input_data.get("project_path", self.output_dir / "Game")),
            )
        else:
            raise ValueError("Expected UnityProject or project metadata")

        self.logger.info(f"Building project: {project.project_name}")

        # Create build output
        build_output = BuildOutput(
            project_name=project.project_name,
            version=self.config.version,
            build_number=self._get_next_build_number(),
            output_directory=self.output_dir / "Builds",
            unity_path=self.config.paths.unity_editor_path,
            project_path=project.project_path,
        )
        build_output.output_directory.mkdir(parents=True, exist_ok=True)

        # Parse target platforms from config
        platforms = self._parse_platforms(self.config.build.target_platforms)

        self.logger.info(f"Building for {len(platforms)} platform(s)...")

        # Build for each platform
        for platform in platforms:
            self.logger.info(f"  Building for {platform.value}...")

            build_config = BuildConfiguration(
                platform=platform,
                development_build=self.config.build.development_build,
                compression=self.config.build.compression,
            )

            result = self._execute_build(build_config, build_output)
            build_output.builds.append(result)

            if result.status == BuildStatus.SUCCEEDED:
                self.logger.info(f"    ✓ {platform.value} build successful")
            else:
                self.logger.error(f"    ✗ {platform.value} build failed: {result.error_message}")

        # Generate build scripts for manual use
        self._generate_build_scripts(build_output)

        # Save build report
        self._save_build_report(build_output)

        self.logger.info(build_output.get_summary())

        return build_output

    def validate_input(self, input_data: Optional[Any]) -> bool:
        """Validate input data."""
        if input_data is None:
            self.logger.error("No project data provided")
            return False

        if isinstance(input_data, (UnityProject, dict)):
            return True

        return False

    def _parse_platforms(self, platform_strings: list[str]) -> list[BuildPlatform]:
        """Parse platform strings into BuildPlatform enums."""
        platforms = []
        for p_str in platform_strings:
            try:
                platform = BuildPlatform(p_str.lower())
                platforms.append(platform)
            except ValueError:
                self.logger.warning(f"Unknown platform: {p_str}")
        return platforms

    def _get_next_build_number(self) -> int:
        """Get the next build number."""
        build_num_file = self.output_dir / "build_number.txt"
        if build_num_file.exists():
            with open(build_num_file, "r") as f:
                current = int(f.read().strip())
        else:
            current = 0

        next_num = current + 1
        with open(build_num_file, "w") as f:
            f.write(str(next_num))

        return next_num

    def _execute_build(
        self, config: BuildConfiguration, build_output: BuildOutput
    ) -> BuildResult:
        """
        Execute a Unity build for a specific platform.

        In production, this would call Unity's batch mode.
        """
        result = BuildResult(
            config=config,
            status=BuildStatus.BUILDING,
            started_at=datetime.now(),
        )

        # Determine output path
        platform_dir = build_output.output_directory / config.platform.value
        platform_dir.mkdir(parents=True, exist_ok=True)

        output_file = (
            platform_dir / f"{build_output.project_name}{config.get_file_extension()}"
        )
        result.output_path = output_file

        # Check if Unity path is configured
        if not build_output.unity_path or self.config.dry_run:
            # Simulate build
            return self._simulate_build(result)

        # Build Unity command
        cmd = self._build_unity_command(config, build_output, output_file)

        try:
            # Execute build
            start_time = time.time()
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )

            result.build_duration = time.time() - start_time
            result.build_log = process.stdout + process.stderr

            if process.returncode == 0:
                result.status = BuildStatus.SUCCEEDED
                if output_file.exists():
                    result.file_size = output_file.stat().st_size
            else:
                result.status = BuildStatus.FAILED
                result.error_message = f"Build failed with code {process.returncode}"

        except subprocess.TimeoutExpired:
            result.status = BuildStatus.FAILED
            result.error_message = "Build timed out after 1 hour"
        except FileNotFoundError:
            result.status = BuildStatus.FAILED
            result.error_message = f"Unity not found at {build_output.unity_path}"
        except Exception as e:
            result.status = BuildStatus.FAILED
            result.error_message = str(e)

        result.completed_at = datetime.now()
        return result

    def _simulate_build(self, result: BuildResult) -> BuildResult:
        """Simulate a successful build for testing."""
        self.logger.debug(f"  Simulating build for {result.config.platform.value}")

        # Simulate build time
        time.sleep(0.5)

        result.status = BuildStatus.SUCCEEDED
        result.build_duration = 120.0  # Simulated 2 minutes
        result.file_size = 150 * 1024 * 1024  # Simulated 150 MB
        result.completed_at = datetime.now()
        result.build_log = f"[SIMULATED] Build successful for {result.config.platform.value}"

        # Create placeholder output info
        if result.output_path:
            result.output_path.parent.mkdir(parents=True, exist_ok=True)

        return result

    def _build_unity_command(
        self,
        config: BuildConfiguration,
        build_output: BuildOutput,
        output_file: Path,
    ) -> list[str]:
        """Build the Unity command line for batch mode build."""
        cmd = [
            build_output.unity_path,
            "-quit",
            "-batchmode",
            "-nographics",
            "-projectPath",
            str(build_output.project_path),
        ]

        # Add build target
        target_map = {
            BuildPlatform.WINDOWS_64: ["-buildWindows64Player", str(output_file)],
            BuildPlatform.WINDOWS_32: ["-buildWindowsPlayer", str(output_file)],
            BuildPlatform.MACOS: ["-buildOSXUniversalPlayer", str(output_file)],
            BuildPlatform.LINUX: ["-buildLinux64Player", str(output_file)],
            BuildPlatform.ANDROID: ["-buildTarget", "Android", "-executeMethod", "AutoGSBuilder.BuildAndroid"],
            BuildPlatform.IOS: ["-buildTarget", "iOS", "-executeMethod", "AutoGSBuilder.BuildiOS"],
            BuildPlatform.WEBGL: ["-buildTarget", "WebGL", "-executeMethod", "AutoGSBuilder.BuildWebGL"],
        }

        cmd.extend(target_map.get(config.platform, []))

        # Add development build flag if needed
        if config.development_build:
            cmd.extend(["-developmentBuild"])

        # Add log file
        log_file = output_file.parent / "build_log.txt"
        cmd.extend(["-logFile", str(log_file)])

        return cmd

    def _generate_build_scripts(self, build_output: BuildOutput) -> None:
        """Generate build scripts for manual execution."""

        # Windows batch script
        bat_script = self._generate_windows_build_script(build_output)
        bat_path = build_output.output_directory / "build_all.bat"
        with open(bat_path, "w") as f:
            f.write(bat_script)

        # Unix shell script
        sh_script = self._generate_unix_build_script(build_output)
        sh_path = build_output.output_directory / "build_all.sh"
        with open(sh_path, "w") as f:
            f.write(sh_script)

        # Make shell script executable
        sh_path.chmod(0o755)

        # Unity Editor script
        unity_script = build_output.get_unity_build_script()
        unity_script_path = (
            build_output.project_path / "Assets" / "Editor" / "AutoGSBuilder.cs"
        )
        if build_output.project_path:
            unity_script_path.parent.mkdir(parents=True, exist_ok=True)
            with open(unity_script_path, "w") as f:
                f.write(unity_script)

        self.logger.info(f"Generated build scripts in {build_output.output_directory}")

    def _generate_windows_build_script(self, build_output: BuildOutput) -> str:
        """Generate Windows batch script for builds."""
        default_unity = r'C:\Program Files\Unity\Hub\Editor\2022.3.0f1\Editor\Unity.exe'
        unity_path = build_output.unity_path or default_unity
        project_path_str = str(build_output.project_path) if build_output.project_path else 'PROJECT_PATH_HERE'
        build_path_str = str(build_output.output_directory)

        script = f'''@echo off
REM AutoGS Build Script for {build_output.project_name}
REM Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}

set UNITY_PATH="{unity_path}"
set PROJECT_PATH="{project_path_str}"
set BUILD_PATH="{build_path_str}"

echo Building {build_output.project_name} v{build_output.version}...
echo.

'''
        for build in build_output.builds:
            platform = build.config.platform.value
            ext = build.config.get_file_extension()
            build_target = f"%BUILD_PATH%\\\\{platform}\\\\{build_output.project_name}{ext}"
            log_file = f"%BUILD_PATH%\\\\{platform}\\\\build_log.txt"
            script += f'''
echo Building for {platform}...
%UNITY_PATH% -quit -batchmode -nographics -projectPath %PROJECT_PATH% -buildWindows64Player "{build_target}" -logFile "{log_file}"
if %ERRORLEVEL% EQU 0 (
    echo {platform} build successful!
) else (
    echo {platform} build failed!
)
echo.
'''

        script += '''
echo All builds complete!
pause
'''
        return script

    def _generate_unix_build_script(self, build_output: BuildOutput) -> str:
        """Generate Unix shell script for builds."""
        script = f'''#!/bin/bash
# AutoGS Build Script for {build_output.project_name}
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}

UNITY_PATH="{build_output.unity_path or '/Applications/Unity/Hub/Editor/2022.3.0f1/Unity.app/Contents/MacOS/Unity'}"
PROJECT_PATH="{build_output.project_path or 'PROJECT_PATH_HERE'}"
BUILD_PATH="{build_output.output_directory}"

echo "Building {build_output.project_name} v{build_output.version}..."
echo

'''
        for build in build_output.builds:
            platform = build.config.platform.value
            ext = build.config.get_file_extension()
            script += f'''
echo "Building for {platform}..."
"$UNITY_PATH" -quit -batchmode -nographics -projectPath "$PROJECT_PATH" -buildLinux64Player "$BUILD_PATH/{platform}/{build_output.project_name}{ext}" -logFile "$BUILD_PATH/{platform}/build_log.txt"
if [ $? -eq 0 ]; then
    echo "{platform} build successful!"
else
    echo "{platform} build failed!"
fi
echo
'''

        script += '''
echo "All builds complete!"
'''
        return script

    def _save_build_report(self, build_output: BuildOutput) -> None:
        """Save a detailed build report."""
        report = {
            "project": build_output.project_name,
            "version": build_output.version,
            "build_number": build_output.build_number,
            "created_at": build_output.created_at.isoformat(),
            "total_builds": build_output.total_builds(),
            "successful": build_output.successful_builds(),
            "failed": build_output.failed_builds(),
            "total_size_bytes": build_output.total_size(),
            "total_build_time_seconds": build_output.total_build_time(),
            "builds": [],
        }

        for build in build_output.builds:
            build_info = {
                "platform": build.config.platform.value,
                "status": build.status.value,
                "output_path": str(build.output_path) if build.output_path else None,
                "file_size_bytes": build.file_size,
                "build_duration_seconds": build.build_duration,
                "error": build.error_message if build.error_message else None,
                "started_at": build.started_at.isoformat() if build.started_at else None,
                "completed_at": build.completed_at.isoformat() if build.completed_at else None,
            }
            report["builds"].append(build_info)

        report_path = build_output.output_directory / "build_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Build report saved to {report_path}")

    def _dry_run(self, input_data: Optional[Any]) -> BuildOutput:
        """Simulate build process."""
        self.logger.info("DRY RUN: Simulating build process")

        return BuildOutput(
            project_name="SampleProject",
            version="1.0.0",
            build_number=1,
        )
