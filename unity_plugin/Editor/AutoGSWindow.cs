using UnityEngine;
using UnityEditor;
using System;
using System.Diagnostics;
using System.IO;
using System.Collections.Generic;

namespace AutoGS.Editor
{
    /// <summary>
    /// Unity Editor Window for AutoGS pipeline integration
    /// Allows running the full AutoGS pipeline from within Unity
    /// </summary>
    public class AutoGSWindow : EditorWindow
    {
        private string pythonPath = "python";
        private string autoGSPath = "";
        private string apiKey = "";
        private bool useOpenAI = true;
        private Vector2 scrollPosition;
        private string logOutput = "";
        private Process currentProcess;
        private bool isRunning = false;

        // Pipeline stages
        private bool runStage1 = true;
        private bool runStage2 = true;
        private bool runStage3 = true;
        private bool runStage4 = true;
        private bool runStage5 = true;

        // Output directory
        private string outputDirectory = "Assets/AutoGS_Output";

        [MenuItem("Window/AutoGS Pipeline")]
        public static void ShowWindow()
        {
            var window = GetWindow<AutoGSWindow>("AutoGS Pipeline");
            window.minSize = new Vector2(400, 600);
        }

        private void OnEnable()
        {
            // Load saved preferences
            pythonPath = EditorPrefs.GetString("AutoGS_PythonPath", "python");
            autoGSPath = EditorPrefs.GetString("AutoGS_Path", "");
            apiKey = EditorPrefs.GetString("AutoGS_APIKey", "");
            useOpenAI = EditorPrefs.GetBool("AutoGS_UseOpenAI", true);
            outputDirectory = EditorPrefs.GetString("AutoGS_OutputDir", "Assets/AutoGS_Output");
        }

        private void OnDisable()
        {
            // Save preferences
            EditorPrefs.SetString("AutoGS_PythonPath", pythonPath);
            EditorPrefs.SetString("AutoGS_Path", autoGSPath);
            EditorPrefs.SetString("AutoGS_APIKey", apiKey);
            EditorPrefs.SetBool("AutoGS_UseOpenAI", useOpenAI);
            EditorPrefs.SetString("AutoGS_OutputDir", outputDirectory);

            // Clean up process
            if (currentProcess != null && !currentProcess.HasExited)
            {
                currentProcess.Kill();
                currentProcess.Dispose();
            }
        }

        private void OnGUI()
        {
            scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);

            GUILayout.Label("AutoGS Pipeline Configuration", EditorStyles.boldLabel);
            EditorGUILayout.Space();

            // Configuration Section
            DrawConfigurationSection();

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("", GUI.skin.horizontalSlider);
            EditorGUILayout.Space();

            // Pipeline Stages Section
            DrawPipelineStagesSection();

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("", GUI.skin.horizontalSlider);
            EditorGUILayout.Space();

            // Control Section
            DrawControlSection();

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("", GUI.skin.horizontalSlider);
            EditorGUILayout.Space();

            // Log Section
            DrawLogSection();

            EditorGUILayout.EndScrollView();
        }

        private void DrawConfigurationSection()
        {
            GUILayout.Label("Setup", EditorStyles.boldLabel);

            pythonPath = EditorGUILayout.TextField("Python Path:", pythonPath);

            EditorGUILayout.BeginHorizontal();
            autoGSPath = EditorGUILayout.TextField("AutoGS Path:", autoGSPath);
            if (GUILayout.Button("Browse", GUILayout.Width(60)))
            {
                string path = EditorUtility.OpenFolderPanel("Select AutoGS Directory", "", "");
                if (!string.IsNullOrEmpty(path))
                {
                    autoGSPath = path;
                }
            }
            EditorGUILayout.EndHorizontal();

            useOpenAI = EditorGUILayout.Toggle("Use OpenAI (vs Anthropic):", useOpenAI);
            apiKey = EditorGUILayout.PasswordField("API Key:", apiKey);

            outputDirectory = EditorGUILayout.TextField("Output Directory:", outputDirectory);

            if (GUILayout.Button("Validate Configuration"))
            {
                ValidateConfiguration();
            }
        }

        private void DrawPipelineStagesSection()
        {
            GUILayout.Label("Pipeline Stages", EditorStyles.boldLabel);

            runStage1 = EditorGUILayout.ToggleLeft("Stage 1: Trend Scout (Market Analysis)", runStage1);
            runStage2 = EditorGUILayout.ToggleLeft("Stage 2: GDD Architect (Game Design)", runStage2);
            runStage3 = EditorGUILayout.ToggleLeft("Stage 3: Asset Factory (Asset Generation)", runStage3);
            runStage4 = EditorGUILayout.ToggleLeft("Stage 4: Engineer Bot (Code Generation)", runStage4);
            runStage5 = EditorGUILayout.ToggleLeft("Stage 5: Build/Deploy (Unity Build)", runStage5);

            EditorGUILayout.HelpBox("Selected stages will be executed in sequence", MessageType.Info);
        }

        private void DrawControlSection()
        {
            GUILayout.Label("Pipeline Control", EditorStyles.boldLabel);

            EditorGUI.BeginDisabledGroup(isRunning || string.IsNullOrEmpty(autoGSPath));

            if (GUILayout.Button("Run Full Pipeline", GUILayout.Height(40)))
            {
                RunPipeline(false);
            }

            if (GUILayout.Button("Run Dry-Run (Test Configuration)", GUILayout.Height(30)))
            {
                RunPipeline(true);
            }

            EditorGUI.EndDisabledGroup();

            EditorGUI.BeginDisabledGroup(!isRunning);
            if (GUILayout.Button("Stop Pipeline", GUILayout.Height(30)))
            {
                StopPipeline();
            }
            EditorGUI.EndDisabledGroup();

            if (GUILayout.Button("Import Generated Assets"))
            {
                ImportGeneratedAssets();
            }
        }

        private void DrawLogSection()
        {
            GUILayout.Label("Output Log", EditorStyles.boldLabel);

            EditorGUILayout.BeginVertical(GUI.skin.box);
            EditorGUILayout.TextArea(logOutput, GUILayout.Height(200));
            EditorGUILayout.EndVertical();

            if (GUILayout.Button("Clear Log"))
            {
                logOutput = "";
            }
        }

        private void ValidateConfiguration()
        {
            logOutput += "\n=== Validating Configuration ===\n";

            // Check Python
            if (!File.Exists(pythonPath) && !CheckCommandExists(pythonPath))
            {
                logOutput += "WARNING: Python path may be invalid\n";
            }
            else
            {
                logOutput += "✓ Python found\n";
            }

            // Check AutoGS path
            if (string.IsNullOrEmpty(autoGSPath) || !Directory.Exists(autoGSPath))
            {
                logOutput += "ERROR: AutoGS path is invalid\n";
            }
            else
            {
                logOutput += "✓ AutoGS directory found\n";
            }

            // Check API key
            if (string.IsNullOrEmpty(apiKey))
            {
                logOutput += "WARNING: No API key provided (will use template-based generation)\n";
            }
            else
            {
                logOutput += "✓ API key configured\n";
            }

            logOutput += "=== Validation Complete ===\n";
        }

        private bool CheckCommandExists(string command)
        {
            try
            {
                var process = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = command,
                        Arguments = "--version",
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        UseShellExecute = false,
                        CreateNoWindow = true
                    }
                };
                process.Start();
                process.WaitForExit();
                return process.ExitCode == 0;
            }
            catch
            {
                return false;
            }
        }

        private void RunPipeline(bool dryRun)
        {
            if (string.IsNullOrEmpty(autoGSPath))
            {
                EditorUtility.DisplayDialog("Error", "Please set the AutoGS path first", "OK");
                return;
            }

            isRunning = true;
            logOutput += $"\n=== Starting Pipeline {(dryRun ? "(DRY RUN)" : "")} ===\n";

            // Build command
            string arguments = $"-m autogs run";

            if (dryRun)
            {
                arguments += " --dry-run";
            }

            // Add stages
            List<string> stages = new List<string>();
            if (runStage1) stages.Add("1");
            if (runStage2) stages.Add("2");
            if (runStage3) stages.Add("3");
            if (runStage4) stages.Add("4");
            if (runStage5) stages.Add("5");

            if (stages.Count > 0 && stages.Count < 5)
            {
                arguments += " --stage " + string.Join(",", stages);
            }

            // Set environment variables
            var envVars = new Dictionary<string, string>();

            if (!string.IsNullOrEmpty(apiKey))
            {
                if (useOpenAI)
                {
                    envVars["OPENAI_API_KEY"] = apiKey;
                }
                else
                {
                    envVars["ANTHROPIC_API_KEY"] = apiKey;
                }
            }

            // Start process
            currentProcess = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = pythonPath,
                    Arguments = arguments,
                    WorkingDirectory = autoGSPath,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                }
            };

            // Set environment variables
            foreach (var kvp in envVars)
            {
                currentProcess.StartInfo.EnvironmentVariables[kvp.Key] = kvp.Value;
            }

            currentProcess.OutputDataReceived += (sender, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    logOutput += e.Data + "\n";
                }
            };

            currentProcess.ErrorDataReceived += (sender, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    logOutput += "ERROR: " + e.Data + "\n";
                }
            };

            currentProcess.Exited += (sender, e) =>
            {
                isRunning = false;
                logOutput += "\n=== Pipeline Complete ===\n";
            };

            currentProcess.EnableRaisingEvents = true;

            try
            {
                currentProcess.Start();
                currentProcess.BeginOutputReadLine();
                currentProcess.BeginErrorReadLine();

                logOutput += $"Pipeline started with PID: {currentProcess.Id}\n";
            }
            catch (Exception ex)
            {
                logOutput += $"ERROR: Failed to start pipeline: {ex.Message}\n";
                isRunning = false;
            }
        }

        private void StopPipeline()
        {
            if (currentProcess != null && !currentProcess.HasExited)
            {
                try
                {
                    currentProcess.Kill();
                    logOutput += "\nPipeline stopped by user\n";
                }
                catch (Exception ex)
                {
                    logOutput += $"\nERROR stopping pipeline: {ex.Message}\n";
                }
                finally
                {
                    isRunning = false;
                }
            }
        }

        private void ImportGeneratedAssets()
        {
            if (!Directory.Exists(outputDirectory))
            {
                EditorUtility.DisplayDialog("Error", "Output directory not found. Run the pipeline first.", "OK");
                return;
            }

            logOutput += "\n=== Importing Generated Assets ===\n";

            // Refresh asset database
            AssetDatabase.Refresh();

            logOutput += "Asset database refreshed\n";
            logOutput += $"Check {outputDirectory} for generated assets\n";

            EditorUtility.DisplayDialog("Import Complete",
                $"Assets have been imported. Check {outputDirectory} folder.", "OK");
        }

        private void Update()
        {
            // Repaint to update UI if process is running
            if (isRunning)
            {
                Repaint();
            }
        }
    }
}
