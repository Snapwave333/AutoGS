"""Data models for Stage 4: Engineer Bot output."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum


class ScriptType(Enum):
    """Type of Unity C# script."""

    MONOBEHAVIOUR = "monobehaviour"
    SCRIPTABLE_OBJECT = "scriptable_object"
    EDITOR_SCRIPT = "editor"
    SHADER = "shader"
    STATIC_CLASS = "static"
    INTERFACE = "interface"
    DATA_CLASS = "data"


class CodeStatus(Enum):
    """Status of code generation."""

    PENDING = "pending"
    GENERATING = "generating"
    GENERATED = "generated"
    COMPILED = "compiled"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


@dataclass
class CodeComponent:
    """A single C# script or code component."""

    name: str
    script_type: ScriptType
    description: str
    namespace: str = "Game"
    dependencies: list[str] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)
    public_methods: list[dict] = field(default_factory=list)
    public_properties: list[dict] = field(default_factory=list)
    source_code: str = ""
    file_path: Optional[Path] = None
    status: CodeStatus = CodeStatus.PENDING
    generation_prompt: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def get_file_name(self) -> str:
        """Get the C# file name."""
        return f"{self.name}.cs"

    def get_full_path(self, base_path: Path) -> Path:
        """Get full path for the script."""
        return base_path / "Assets" / "Scripts" / self.namespace / self.get_file_name()


@dataclass
class UnityScene:
    """A Unity scene configuration."""

    name: str
    description: str
    scene_type: str  # menu, gameplay, loading, etc.
    required_objects: list[str] = field(default_factory=list)
    required_scripts: list[str] = field(default_factory=list)
    lighting_setup: str = "default"
    post_processing: bool = False


@dataclass
class UnityProject:
    """
    The output of Stage 4: Engineer Bot.
    Complete Unity project structure and code.
    """

    project_name: str
    unity_version: str = "2022.3.0f1"
    render_pipeline: str = "URP"

    # Code
    scripts: list[CodeComponent] = field(default_factory=list)
    scenes: list[UnityScene] = field(default_factory=list)

    # Configuration
    project_settings: dict = field(default_factory=dict)
    packages: list[str] = field(default_factory=list)
    layers: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    input_actions: dict = field(default_factory=dict)

    # Paths
    project_path: Optional[Path] = None
    created_at: datetime = field(default_factory=datetime.now)

    def total_scripts(self) -> int:
        """Get total number of scripts."""
        return len(self.scripts)

    def compiled_scripts(self) -> int:
        """Get number of successfully compiled scripts."""
        return sum(1 for s in self.scripts if s.status == CodeStatus.COMPILED)

    def failed_scripts(self) -> int:
        """Get number of failed scripts."""
        return sum(1 for s in self.scripts if s.status == CodeStatus.FAILED)

    def get_summary(self) -> str:
        """Get project summary."""
        return f"""
=== UNITY PROJECT: {self.project_name} ===
Unity Version: {self.unity_version}
Render Pipeline: {self.render_pipeline}

Scripts:
- Total: {self.total_scripts()}
- Compiled: {self.compiled_scripts()}
- Failed: {self.failed_scripts()}

Scenes: {len(self.scenes)}
Packages: {len(self.packages)}

Project Path: {self.project_path or 'Not set'}
Created: {self.created_at.strftime('%Y-%m-%d %H:%M')}
=========================================
"""

    def get_package_manifest(self) -> dict:
        """Generate package.json content for Unity."""
        return {
            "dependencies": {
                "com.unity.render-pipelines.universal": "14.0.8",
                "com.unity.inputsystem": "1.7.0",
                "com.unity.textmeshpro": "3.0.6",
                **{pkg: "latest" for pkg in self.packages},
            }
        }
