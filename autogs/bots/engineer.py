"""
Stage 4: Engineer Bot
Code generation and Unity project setup.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..core.base_bot import BaseBot
from ..core.config import PipelineConfig
from ..models.gdd import GameDesignDocument, GameMechanic
from ..models.code import (
    CodeComponent,
    UnityProject,
    UnityScene,
    ScriptType,
    CodeStatus,
)


class EngineerBot(BaseBot):
    """
    Bot responsible for generating C# scripts and Unity project structure.

    This bot:
    1. Reads mechanics from GDD
    2. Generates C# scripts for each system
    3. Creates Unity project structure
    4. Sets up scenes and configurations
    """

    def run(self, input_data: Optional[Any] = None) -> UnityProject:
        """
        Generate Unity project and C# scripts.

        Args:
            input_data: GameDesignDocument from Stage 2

        Returns:
            UnityProject with all generated code
        """
        if not isinstance(input_data, (GameDesignDocument, dict)):
            raise ValueError("Expected GameDesignDocument input")

        if isinstance(input_data, dict):
            # Reconstruct GDD from previous stage if needed
            self.logger.warning("Received dict instead of GDD, using as metadata")
            gdd = None
            project_name = input_data.get("title", "GeneratedGame")
        else:
            gdd = input_data
            project_name = gdd.title

        self.logger.info(f"Generating Unity project: {project_name}")

        # Create Unity project
        project = UnityProject(
            project_name=project_name.replace(" ", ""),
            unity_version=self.config.engineer.unity_version,
            render_pipeline=self.config.engineer.render_pipeline,
            project_path=self.output_dir / project_name.replace(" ", ""),
        )

        # Set up project structure
        self._setup_project_structure(project)

        # Generate scripts based on GDD
        if gdd:
            self.logger.info("Generating core scripts...")
            project.scripts = self._generate_scripts_from_gdd(gdd, project)

            self.logger.info("Setting up scenes...")
            project.scenes = self._generate_scenes(gdd)

            # Set up packages
            if gdd.technical_requirements:
                project.packages = gdd.technical_requirements.required_packages
        else:
            # Generate basic scripts without GDD
            project.scripts = self._generate_basic_scripts(project)
            project.scenes = self._generate_basic_scenes()

        # Generate project configuration files
        self._generate_project_files(project)

        self.logger.info(project.get_summary())

        return project

    def validate_input(self, input_data: Optional[Any]) -> bool:
        """Validate input data."""
        # Stage 4 can work with GDD or basic metadata
        if input_data is None:
            self.logger.warning("No input data, will generate basic project")
            return True
        return True

    def _setup_project_structure(self, project: UnityProject) -> None:
        """Create Unity project directory structure."""
        if project.project_path is None:
            project.project_path = self.output_dir / project.project_name

        base = project.project_path
        directories = [
            base / "Assets" / "Scripts" / "Core",
            base / "Assets" / "Scripts" / "Gameplay",
            base / "Assets" / "Scripts" / "UI",
            base / "Assets" / "Scripts" / "Networking",
            base / "Assets" / "Scripts" / "Data",
            base / "Assets" / "Prefabs",
            base / "Assets" / "Scenes",
            base / "Assets" / "Materials",
            base / "Assets" / "Resources",
            base / "Assets" / "Editor",
            base / "ProjectSettings",
            base / "Packages",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        self.logger.debug(f"Created project structure at {base}")

    def _generate_scripts_from_gdd(
        self, gdd: GameDesignDocument, project: UnityProject
    ) -> list[CodeComponent]:
        """Generate C# scripts based on GDD mechanics."""
        scripts = []

        # Generate core system scripts
        scripts.extend(self._generate_core_scripts(project))

        # Generate scripts for each mechanic
        for mechanic in gdd.mechanics:
            mechanic_scripts = self._generate_mechanic_scripts(mechanic, project)
            scripts.extend(mechanic_scripts)

        # Generate UI scripts
        scripts.extend(self._generate_ui_scripts(project))

        # Generate data scripts
        scripts.extend(self._generate_data_scripts(project))

        # Write all scripts to files
        for script in scripts:
            self._write_script(script, project)

        return scripts

    def _generate_core_scripts(self, project: UnityProject) -> list[CodeComponent]:
        """Generate core system scripts."""
        scripts = []

        # Game Manager
        scripts.append(CodeComponent(
            name="GameManager",
            script_type=ScriptType.MONOBEHAVIOUR,
            description="Central game state management",
            namespace=f"{project.project_name}.Core",
            public_methods=[
                {"name": "StartGame", "returns": "void", "params": []},
                {"name": "PauseGame", "returns": "void", "params": []},
                {"name": "ResumeGame", "returns": "void", "params": []},
                {"name": "EndGame", "returns": "void", "params": []},
            ],
            source_code=self._generate_game_manager_code(project.project_name),
            status=CodeStatus.GENERATED,
        ))

        # Player Controller
        scripts.append(CodeComponent(
            name="PlayerController",
            script_type=ScriptType.MONOBEHAVIOUR,
            description="Player movement and input handling",
            namespace=f"{project.project_name}.Gameplay",
            dependencies=["InputSystem"],
            public_methods=[
                {"name": "Move", "returns": "void", "params": ["Vector2 direction"]},
                {"name": "Jump", "returns": "void", "params": []},
                {"name": "Interact", "returns": "void", "params": []},
            ],
            source_code=self._generate_player_controller_code(project.project_name),
            status=CodeStatus.GENERATED,
        ))

        # Save System
        scripts.append(CodeComponent(
            name="SaveSystem",
            script_type=ScriptType.STATIC_CLASS,
            description="Save and load game state",
            namespace=f"{project.project_name}.Core",
            public_methods=[
                {"name": "Save", "returns": "void", "params": ["string slotName"]},
                {"name": "Load", "returns": "void", "params": ["string slotName"]},
                {"name": "DeleteSave", "returns": "void", "params": ["string slotName"]},
            ],
            source_code=self._generate_save_system_code(project.project_name),
            status=CodeStatus.GENERATED,
        ))

        return scripts

    def _generate_mechanic_scripts(
        self, mechanic: GameMechanic, project: UnityProject
    ) -> list[CodeComponent]:
        """Generate scripts for a specific game mechanic."""
        scripts = []

        # Generate main mechanic manager
        manager_name = mechanic.name.replace(" ", "") + "Manager"
        scripts.append(CodeComponent(
            name=manager_name,
            script_type=ScriptType.MONOBEHAVIOUR,
            description=mechanic.description,
            namespace=f"{project.project_name}.Gameplay",
            dependencies=mechanic.dependencies,
            source_code=self._generate_mechanic_manager_code(mechanic, project.project_name),
            status=CodeStatus.GENERATED,
        ))

        # Generate supporting scripts for core systems
        for system in mechanic.core_systems[:2]:  # Limit to first 2
            system_script = CodeComponent(
                name=system,
                script_type=ScriptType.MONOBEHAVIOUR,
                description=f"Component for {mechanic.name}: {system}",
                namespace=f"{project.project_name}.Gameplay",
                source_code=self._generate_system_code(system, project.project_name),
                status=CodeStatus.GENERATED,
            )
            scripts.append(system_script)

        return scripts

    def _generate_ui_scripts(self, project: UnityProject) -> list[CodeComponent]:
        """Generate UI management scripts."""
        scripts = []

        scripts.append(CodeComponent(
            name="UIManager",
            script_type=ScriptType.MONOBEHAVIOUR,
            description="Central UI management",
            namespace=f"{project.project_name}.UI",
            source_code=self._generate_ui_manager_code(project.project_name),
            status=CodeStatus.GENERATED,
        ))

        scripts.append(CodeComponent(
            name="HUDController",
            script_type=ScriptType.MONOBEHAVIOUR,
            description="In-game HUD display",
            namespace=f"{project.project_name}.UI",
            source_code=self._generate_hud_code(project.project_name),
            status=CodeStatus.GENERATED,
        ))

        return scripts

    def _generate_data_scripts(self, project: UnityProject) -> list[CodeComponent]:
        """Generate data structure scripts."""
        scripts = []

        scripts.append(CodeComponent(
            name="GameData",
            script_type=ScriptType.DATA_CLASS,
            description="Serializable game data container",
            namespace=f"{project.project_name}.Data",
            source_code=self._generate_game_data_code(project.project_name),
            status=CodeStatus.GENERATED,
        ))

        return scripts

    def _write_script(self, script: CodeComponent, project: UnityProject) -> None:
        """Write a script to the project directory."""
        if project.project_path is None:
            return

        # Determine directory based on namespace
        if "Core" in script.namespace:
            subdir = "Core"
        elif "Gameplay" in script.namespace:
            subdir = "Gameplay"
        elif "UI" in script.namespace:
            subdir = "UI"
        elif "Data" in script.namespace:
            subdir = "Data"
        else:
            subdir = "Misc"

        script_path = (
            project.project_path / "Assets" / "Scripts" / subdir / script.get_file_name()
        )
        script.file_path = script_path

        with open(script_path, "w") as f:
            f.write(script.source_code)

        self.logger.debug(f"  Written: {script.name}.cs")

    def _generate_scenes(self, gdd: GameDesignDocument) -> list[UnityScene]:
        """Generate Unity scenes based on GDD."""
        scenes = [
            UnityScene(
                name="MainMenu",
                description="Main menu and title screen",
                scene_type="menu",
                required_objects=["Canvas", "EventSystem", "Camera"],
                required_scripts=["UIManager"],
            ),
            UnityScene(
                name="Loading",
                description="Loading screen between scenes",
                scene_type="loading",
                required_objects=["Canvas", "LoadingBar"],
                required_scripts=["LoadingManager"],
            ),
            UnityScene(
                name="Gameplay",
                description="Main gameplay scene",
                scene_type="gameplay",
                required_objects=["Player", "GameManager", "Lighting", "Terrain"],
                required_scripts=["GameManager", "PlayerController"],
                lighting_setup="dynamic",
                post_processing=True,
            ),
        ]

        return scenes

    def _generate_basic_scripts(self, project: UnityProject) -> list[CodeComponent]:
        """Generate basic scripts when no GDD is available."""
        return self._generate_core_scripts(project)

    def _generate_basic_scenes(self) -> list[UnityScene]:
        """Generate basic scenes."""
        return [
            UnityScene(
                name="SampleScene",
                description="Default sample scene",
                scene_type="gameplay",
                required_objects=["Main Camera", "Directional Light"],
            )
        ]

    def _generate_project_files(self, project: UnityProject) -> None:
        """Generate Unity project configuration files."""
        if project.project_path is None:
            return

        # Generate package manifest
        packages_path = project.project_path / "Packages" / "manifest.json"
        with open(packages_path, "w") as f:
            json.dump(project.get_package_manifest(), f, indent=2)

        # Generate .gitignore
        gitignore_path = project.project_path / ".gitignore"
        with open(gitignore_path, "w") as f:
            f.write(self._get_unity_gitignore())

        # Generate README
        readme_path = project.project_path / "README.md"
        with open(readme_path, "w") as f:
            f.write(f"# {project.project_name}\n\n")
            f.write(f"Unity {project.unity_version} project generated by AutoGS\n\n")
            f.write(f"## Scripts\n\n")
            for script in project.scripts:
                f.write(f"- **{script.name}**: {script.description}\n")

        self.logger.debug("Generated project configuration files")

    # Code generation methods (simplified templates)
    def _generate_game_manager_code(self, namespace: str) -> str:
        return f'''using UnityEngine;

namespace {namespace}.Core
{{
    public class GameManager : MonoBehaviour
    {{
        public static GameManager Instance {{ get; private set; }}

        public enum GameState {{ MainMenu, Playing, Paused, GameOver }}
        public GameState CurrentState {{ get; private set; }}

        private void Awake()
        {{
            if (Instance != null && Instance != this)
            {{
                Destroy(gameObject);
                return;
            }}
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }}

        public void StartGame()
        {{
            CurrentState = GameState.Playing;
            Time.timeScale = 1f;
            Debug.Log("Game Started");
        }}

        public void PauseGame()
        {{
            CurrentState = GameState.Paused;
            Time.timeScale = 0f;
            Debug.Log("Game Paused");
        }}

        public void ResumeGame()
        {{
            CurrentState = GameState.Playing;
            Time.timeScale = 1f;
            Debug.Log("Game Resumed");
        }}

        public void EndGame()
        {{
            CurrentState = GameState.GameOver;
            Time.timeScale = 0f;
            Debug.Log("Game Over");
        }}
    }}
}}
'''

    def _generate_player_controller_code(self, namespace: str) -> str:
        return f'''using UnityEngine;
using UnityEngine.InputSystem;

namespace {namespace}.Gameplay
{{
    [RequireComponent(typeof(CharacterController))]
    public class PlayerController : MonoBehaviour
    {{
        [Header("Movement Settings")]
        [SerializeField] private float moveSpeed = 5f;
        [SerializeField] private float jumpForce = 5f;
        [SerializeField] private float gravity = -9.81f;

        private CharacterController controller;
        private Vector3 velocity;
        private bool isGrounded;

        private Vector2 moveInput;

        private void Awake()
        {{
            controller = GetComponent<CharacterController>();
        }}

        private void Update()
        {{
            isGrounded = controller.isGrounded;

            if (isGrounded && velocity.y < 0)
            {{
                velocity.y = -2f;
            }}

            Vector3 move = transform.right * moveInput.x + transform.forward * moveInput.y;
            controller.Move(move * moveSpeed * Time.deltaTime);

            velocity.y += gravity * Time.deltaTime;
            controller.Move(velocity * Time.deltaTime);
        }}

        public void Move(Vector2 direction)
        {{
            moveInput = direction;
        }}

        public void Jump()
        {{
            if (isGrounded)
            {{
                velocity.y = Mathf.Sqrt(jumpForce * -2f * gravity);
            }}
        }}

        public void Interact()
        {{
            // Raycast for interactable objects
            RaycastHit hit;
            if (Physics.Raycast(transform.position, transform.forward, out hit, 2f))
            {{
                var interactable = hit.collider.GetComponent<IInteractable>();
                interactable?.OnInteract(this);
            }}
        }}
    }}

    public interface IInteractable
    {{
        void OnInteract(PlayerController player);
    }}
}}
'''

    def _generate_save_system_code(self, namespace: str) -> str:
        return f'''using UnityEngine;
using System.IO;

namespace {namespace}.Core
{{
    public static class SaveSystem
    {{
        private static string SavePath => Application.persistentDataPath + "/saves/";

        public static void Save(string slotName)
        {{
            if (!Directory.Exists(SavePath))
            {{
                Directory.CreateDirectory(SavePath);
            }}

            var data = new Data.GameData();
            // Populate data from game state

            string json = JsonUtility.ToJson(data, true);
            File.WriteAllText(SavePath + slotName + ".json", json);

            Debug.Log($"Game saved to {{slotName}}");
        }}

        public static void Load(string slotName)
        {{
            string path = SavePath + slotName + ".json";

            if (File.Exists(path))
            {{
                string json = File.ReadAllText(path);
                var data = JsonUtility.FromJson<Data.GameData>(json);
                // Apply data to game state

                Debug.Log($"Game loaded from {{slotName}}");
            }}
            else
            {{
                Debug.LogWarning($"Save file {{slotName}} not found");
            }}
        }}

        public static void DeleteSave(string slotName)
        {{
            string path = SavePath + slotName + ".json";
            if (File.Exists(path))
            {{
                File.Delete(path);
                Debug.Log($"Save {{slotName}} deleted");
            }}
        }}
    }}
}}
'''

    def _generate_mechanic_manager_code(self, mechanic: GameMechanic, namespace: str) -> str:
        class_name = mechanic.name.replace(" ", "") + "Manager"
        return f'''using UnityEngine;
using System.Collections.Generic;

namespace {namespace}.Gameplay
{{
    /// <summary>
    /// {mechanic.description}
    /// </summary>
    public class {class_name} : MonoBehaviour
    {{
        public static {class_name} Instance {{ get; private set; }}

        [Header("Settings")]
        [SerializeField] private bool isEnabled = true;

        private void Awake()
        {{
            if (Instance != null && Instance != this)
            {{
                Destroy(gameObject);
                return;
            }}
            Instance = this;
        }}

        private void Start()
        {{
            Initialize();
        }}

        private void Initialize()
        {{
            Debug.Log("{mechanic.name} system initialized");
        }}

        private void Update()
        {{
            if (!isEnabled) return;

            // Update {mechanic.name} logic
        }}

        // Player interactions: {', '.join(mechanic.player_interactions)}
        public void OnPlayerAction(string action)
        {{
            switch (action)
            {{
{self._generate_action_cases(mechanic.player_interactions)}
            }}
        }}
    }}
}}
'''

    def _generate_action_cases(self, actions: list[str]) -> str:
        cases = ""
        for action in actions:
            cases += f'                case "{action}":\n'
            cases += f'                    // Handle {action}\n'
            cases += f'                    break;\n'
        return cases

    def _generate_system_code(self, system_name: str, namespace: str) -> str:
        return f'''using UnityEngine;

namespace {namespace}.Gameplay
{{
    public class {system_name} : MonoBehaviour
    {{
        [Header("Configuration")]
        [SerializeField] private bool debugMode = false;

        private void Awake()
        {{
            if (debugMode)
            {{
                Debug.Log("{system_name} initialized");
            }}
        }}

        // Implement {system_name} functionality
    }}
}}
'''

    def _generate_ui_manager_code(self, namespace: str) -> str:
        return f'''using UnityEngine;

namespace {namespace}.UI
{{
    public class UIManager : MonoBehaviour
    {{
        public static UIManager Instance {{ get; private set; }}

        [Header("UI Panels")]
        [SerializeField] private GameObject mainMenuPanel;
        [SerializeField] private GameObject gameplayHUD;
        [SerializeField] private GameObject pauseMenu;

        private void Awake()
        {{
            if (Instance != null && Instance != this)
            {{
                Destroy(gameObject);
                return;
            }}
            Instance = this;
        }}

        public void ShowMainMenu()
        {{
            mainMenuPanel?.SetActive(true);
            gameplayHUD?.SetActive(false);
            pauseMenu?.SetActive(false);
        }}

        public void ShowGameplayHUD()
        {{
            mainMenuPanel?.SetActive(false);
            gameplayHUD?.SetActive(true);
            pauseMenu?.SetActive(false);
        }}

        public void TogglePauseMenu()
        {{
            bool isPaused = pauseMenu != null && pauseMenu.activeSelf;
            pauseMenu?.SetActive(!isPaused);
        }}
    }}
}}
'''

    def _generate_hud_code(self, namespace: str) -> str:
        return f'''using UnityEngine;
using TMPro;

namespace {namespace}.UI
{{
    public class HUDController : MonoBehaviour
    {{
        [Header("UI Elements")]
        [SerializeField] private TextMeshProUGUI healthText;
        [SerializeField] private TextMeshProUGUI resourceText;
        [SerializeField] private TextMeshProUGUI objectiveText;

        public void UpdateHealth(float current, float max)
        {{
            if (healthText != null)
            {{
                healthText.text = $"Health: {{current:F0}}/{{max:F0}}";
            }}
        }}

        public void UpdateResources(int amount)
        {{
            if (resourceText != null)
            {{
                resourceText.text = $"Resources: {{amount}}";
            }}
        }}

        public void SetObjective(string objective)
        {{
            if (objectiveText != null)
            {{
                objectiveText.text = objective;
            }}
        }}
    }}
}}
'''

    def _generate_game_data_code(self, namespace: str) -> str:
        return f'''using System;

namespace {namespace}.Data
{{
    [Serializable]
    public class GameData
    {{
        public string playerName;
        public int level;
        public float playTime;
        public float[] playerPosition;
        public int[] inventoryItems;
        public string[] unlockedAreas;
        public string lastSaveTime;

        public GameData()
        {{
            playerName = "Player";
            level = 1;
            playTime = 0f;
            playerPosition = new float[3];
            inventoryItems = new int[0];
            unlockedAreas = new string[0];
            lastSaveTime = DateTime.Now.ToString();
        }}
    }}
}}
'''

    def _get_unity_gitignore(self) -> str:
        return '''# Unity generated
[Ll]ibrary/
[Tt]emp/
[Oo]bj/
[Bb]uild/
[Bb]uilds/
[Ll]ogs/
[Mm]emoryCaptures/

# Asset meta data
*.pidb.meta
*.pdb.meta
*.mdb.meta

# OS generated
.DS_Store
Thumbs.db

# Visual Studio
.vs/
*.csproj
*.unityproj
*.sln
*.suo
*.tmp
*.user
*.userprefs

# Builds
*.apk
*.aab
*.unitypackage
*.app

# Crashlytics
crashlytics-build.properties
'''

    def _dry_run(self, input_data: Optional[Any]) -> UnityProject:
        """Simulate project generation."""
        self.logger.info("DRY RUN: Simulating Unity project generation")

        return UnityProject(
            project_name="SampleProject",
            unity_version=self.config.engineer.unity_version,
            render_pipeline=self.config.engineer.render_pipeline,
        )
