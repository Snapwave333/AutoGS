"""Data models for Stage 5: Build & Deploy Bot output."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum


class BuildPlatform(Enum):
    """Target build platform."""

    WINDOWS_64 = "windows_64"
    WINDOWS_32 = "windows_32"
    MACOS = "macos"
    LINUX = "linux"
    ANDROID = "android"
    IOS = "ios"
    WEBGL = "webgl"


class BuildStatus(Enum):
    """Status of the build process."""

    PENDING = "pending"
    BUILDING = "building"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BuildConfig:
    """Configuration for a single build."""

    platform: BuildPlatform
    development_build: bool = False
    compression: str = "lz4"  # none, lz4, lz4hc
    il2cpp: bool = True
    strip_engine_code: bool = True
    build_app_bundle: bool = False  # For Android AAB
    keystore_path: Optional[str] = None
    custom_defines: list[str] = field(default_factory=list)
    scenes_to_include: list[str] = field(default_factory=list)

    def get_build_target(self) -> str:
        """Get Unity build target string."""
        mapping = {
            BuildPlatform.WINDOWS_64: "Win64",
            BuildPlatform.WINDOWS_32: "Win",
            BuildPlatform.MACOS: "OSXUniversal",
            BuildPlatform.LINUX: "Linux64",
            BuildPlatform.ANDROID: "Android",
            BuildPlatform.IOS: "iOS",
            BuildPlatform.WEBGL: "WebGL",
        }
        return mapping.get(self.platform, "Win64")

    def get_file_extension(self) -> str:
        """Get the output file extension."""
        extensions = {
            BuildPlatform.WINDOWS_64: ".exe",
            BuildPlatform.WINDOWS_32: ".exe",
            BuildPlatform.MACOS: ".app",
            BuildPlatform.LINUX: ".x86_64",
            BuildPlatform.ANDROID: ".apk" if not self.build_app_bundle else ".aab",
            BuildPlatform.IOS: ".ipa",
            BuildPlatform.WEBGL: "",
        }
        return extensions.get(self.platform, "")


@dataclass
class BuildResult:
    """Result of a single build."""

    config: BuildConfig
    status: BuildStatus
    output_path: Optional[Path] = None
    file_size: int = 0
    build_duration: float = 0.0  # seconds
    error_message: str = ""
    warnings: list[str] = field(default_factory=list)
    build_log: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class BuildOutput:
    """
    The output of Stage 5: Build & Deploy Bot.
    Complete build results for all platforms.
    """

    project_name: str
    version: str
    build_number: int
    builds: list[BuildResult] = field(default_factory=list)
    output_directory: Optional[Path] = None
    unity_path: str = ""
    project_path: Optional[Path] = None
    created_at: datetime = field(default_factory=datetime.now)

    def total_builds(self) -> int:
        """Get total number of builds."""
        return len(self.builds)

    def successful_builds(self) -> int:
        """Get number of successful builds."""
        return sum(1 for b in self.builds if b.status == BuildStatus.SUCCEEDED)

    def failed_builds(self) -> int:
        """Get number of failed builds."""
        return sum(1 for b in self.builds if b.status == BuildStatus.FAILED)

    def total_size(self) -> int:
        """Get total size of all builds in bytes."""
        return sum(b.file_size for b in self.builds if b.status == BuildStatus.SUCCEEDED)

    def total_build_time(self) -> float:
        """Get total build time in seconds."""
        return sum(b.build_duration for b in self.builds)

    def get_summary(self) -> str:
        """Get build output summary."""
        size_mb = self.total_size() / (1024 * 1024)
        time_min = self.total_build_time() / 60

        summary = f"""
=== BUILD OUTPUT: {self.project_name} v{self.version} ===
Build Number: {self.build_number}

Results:
- Total Builds: {self.total_builds()}
- Successful: {self.successful_builds()}
- Failed: {self.failed_builds()}

Total Size: {size_mb:.2f} MB
Total Build Time: {time_min:.1f} minutes

Platforms:
"""
        for build in self.builds:
            status_icon = "✓" if build.status == BuildStatus.SUCCEEDED else "✗"
            summary += f"  {status_icon} {build.config.platform.value}: {build.status.value}"
            if build.output_path:
                summary += f" -> {build.output_path.name}"
            summary += "\n"

        summary += f"""
Output Directory: {self.output_directory or 'Not set'}
Created: {self.created_at.strftime('%Y-%m-%d %H:%M')}
================================================
"""
        return summary

    def get_unity_build_script(self) -> str:
        """Generate Unity Editor build script."""
        script = """
using UnityEditor;
using UnityEditor.Build.Reporting;
using System.IO;

public static class AutoGSBuilder
{
    public static void BuildAll()
    {
        string[] scenes = EditorBuildSettings.scenes
            .Where(s => s.enabled)
            .Select(s => s.path)
            .ToArray();

        string buildPath = "Builds";

"""
        for build in self.builds:
            platform = build.config.platform.value.replace("_", "").title()
            target = build.config.get_build_target()
            ext = build.config.get_file_extension()

            script += f"""
        // Build for {platform}
        BuildPlayerOptions options_{platform} = new BuildPlayerOptions();
        options_{platform}.scenes = scenes;
        options_{platform}.locationPathName = Path.Combine(buildPath, "{platform}", "{self.project_name}{ext}");
        options_{platform}.target = BuildTarget.{target};
        options_{platform}.options = BuildOptions.None;
        BuildPipeline.BuildPlayer(options_{platform});
"""

        script += """
    }
}
"""
        return script
