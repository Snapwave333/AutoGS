using UnityEngine;
using System;
using System.Collections.Generic;
using System.IO;

namespace AutoGS.Metrics
{
    /// <summary>
    /// Automated playtesting metrics collection system
    /// Tracks gameplay metrics and sends data for analysis
    /// </summary>
    public class PlaytestMetrics : MonoBehaviour
    {
        private static PlaytestMetrics _instance;
        public static PlaytestMetrics Instance
        {
            get
            {
                if (_instance == null)
                {
                    var go = new GameObject("PlaytestMetrics");
                    _instance = go.AddComponent<PlaytestMetrics>();
                    DontDestroyOnLoad(go);
                }
                return _instance;
            }
        }

        // Session data
        private string sessionId;
        private float sessionStartTime;
        private Dictionary<string, object> sessionData = new Dictionary<string, object>();

        // Performance metrics
        private List<float> fpssamples = new List<float>();
        private float lastFPSSampleTime;
        private const float FPS_SAMPLE_INTERVAL = 1.0f;

        // Gameplay metrics
        private int playerDeaths = 0;
        private int questsCompleted = 0;
        private int itemsCrafted = 0;
        private int enemiesDefeated = 0;
        private Dictionary<string, int> actionCounts = new Dictionary<string, int>();

        // Event tracking
        private List<GameEvent> events = new List<GameEvent>();

        [Serializable]
        public class GameEvent
        {
            public string eventName;
            public float timestamp;
            public Dictionary<string, object> data;

            public GameEvent(string name, float time)
            {
                eventName = name;
                timestamp = time;
                data = new Dictionary<string, object>();
            }
        }

        private void Awake()
        {
            if (_instance != null && _instance != this)
            {
                Destroy(gameObject);
                return;
            }

            _instance = this;
            DontDestroyOnLoad(gameObject);

            StartNewSession();
        }

        private void StartNewSession()
        {
            sessionId = Guid.NewGuid().ToString();
            sessionStartTime = Time.realtimeSinceStartup;
            lastFPSSampleTime = sessionStartTime;

            sessionData["session_id"] = sessionId;
            sessionData["start_time"] = DateTime.Now.ToString("o");
            sessionData["platform"] = Application.platform.ToString();
            sessionData["unity_version"] = Application.unityVersion;
            sessionData["game_version"] = Application.version;

            Debug.Log($"[PlaytestMetrics] Session started: {sessionId}");
        }

        private void Update()
        {
            // Sample FPS
            if (Time.realtimeSinceStartup - lastFPSSampleTime >= FPS_SAMPLE_INTERVAL)
            {
                float fps = 1.0f / Time.deltaTime;
                fpssamples.Add(fps);
                lastFPSSampleTime = Time.realtimeSinceStartup;

                // Keep only last 60 samples (1 minute at 1 sample/sec)
                if (fpssamples.Count > 60)
                {
                    fpssamples.RemoveAt(0);
                }
            }
        }

        /// <summary>
        /// Track a custom game event
        /// </summary>
        public void TrackEvent(string eventName, Dictionary<string, object> data = null)
        {
            var gameEvent = new GameEvent(eventName, Time.realtimeSinceStartup - sessionStartTime);

            if (data != null)
            {
                foreach (var kvp in data)
                {
                    gameEvent.data[kvp.Key] = kvp.Value;
                }
            }

            events.Add(gameEvent);
            Debug.Log($"[PlaytestMetrics] Event: {eventName}");
        }

        /// <summary>
        /// Record player death
        /// </summary>
        public void RecordDeath(string cause = "unknown")
        {
            playerDeaths++;
            TrackEvent("player_death", new Dictionary<string, object>
            {
                { "cause", cause },
                { "death_count", playerDeaths }
            });
        }

        /// <summary>
        /// Record quest completion
        /// </summary>
        public void RecordQuestComplete(string questId, float completionTime)
        {
            questsCompleted++;
            TrackEvent("quest_complete", new Dictionary<string, object>
            {
                { "quest_id", questId },
                { "completion_time", completionTime },
                { "total_completed", questsCompleted }
            });
        }

        /// <summary>
        /// Record item crafted
        /// </summary>
        public void RecordCraft(string itemName, string category = "unknown")
        {
            itemsCrafted++;
            TrackEvent("item_crafted", new Dictionary<string, object>
            {
                { "item", itemName },
                { "category", category },
                { "total_crafted", itemsCrafted }
            });
        }

        /// <summary>
        /// Record enemy defeated
        /// </summary>
        public void RecordEnemyDefeated(string enemyType, float battleDuration)
        {
            enemiesDefeated++;
            TrackEvent("enemy_defeated", new Dictionary<string, object>
            {
                { "enemy_type", enemyType },
                { "battle_duration", battleDuration },
                { "total_defeated", enemiesDefeated }
            });
        }

        /// <summary>
        /// Record generic player action
        /// </summary>
        public void RecordAction(string actionName)
        {
            if (!actionCounts.ContainsKey(actionName))
            {
                actionCounts[actionName] = 0;
            }
            actionCounts[actionName]++;
        }

        /// <summary>
        /// Get current session metrics
        /// </summary>
        public Dictionary<string, object> GetSessionMetrics()
        {
            float sessionDuration = Time.realtimeSinceStartup - sessionStartTime;

            var metrics = new Dictionary<string, object>
            {
                { "session_id", sessionId },
                { "session_duration", sessionDuration },
                { "player_deaths", playerDeaths },
                { "quests_completed", questsCompleted },
                { "items_crafted", itemsCrafted },
                { "enemies_defeated", enemiesDefeated },
                { "total_events", events.Count },
                { "fps_average", GetAverageFPS() },
                { "fps_min", GetMinFPS() },
                { "fps_max", GetMaxFPS() },
                { "action_counts", actionCounts },
                { "end_time", DateTime.Now.ToString("o") }
            };

            return metrics;
        }

        /// <summary>
        /// Export session data to JSON file
        /// </summary>
        public string ExportSession()
        {
            var metrics = GetSessionMetrics();

            string json = JsonUtility.ToJson(new SerializableMetrics(metrics), true);
            string filename = $"playtest_session_{sessionId}_{DateTime.Now:yyyyMMdd_HHmmss}.json";
            string filepath = Path.Combine(Application.persistentDataPath, "Metrics", filename);

            Directory.CreateDirectory(Path.GetDirectoryName(filepath));
            File.WriteAllText(filepath, json);

            Debug.Log($"[PlaytestMetrics] Session exported to: {filepath}");
            return filepath;
        }

        /// <summary>
        /// End current session and start a new one
        /// </summary>
        public void EndSession()
        {
            ExportSession();

            // Reset for new session
            playerDeaths = 0;
            questsCompleted = 0;
            itemsCrafted = 0;
            enemiesDefeated = 0;
            actionCounts.Clear();
            events.Clear();
            fpssamples.Clear();

            StartNewSession();
        }

        private float GetAverageFPS()
        {
            if (fpssamples.Count == 0) return 0f;

            float sum = 0f;
            foreach (float fps in fpssamples)
            {
                sum += fps;
            }
            return sum / fpssamples.Count;
        }

        private float GetMinFPS()
        {
            if (fpssamples.Count == 0) return 0f;

            float min = float.MaxValue;
            foreach (float fps in fpssamples)
            {
                if (fps < min) min = fps;
            }
            return min;
        }

        private float GetMaxFPS()
        {
            if (fpssamples.Count == 0) return 0f;

            float max = 0f;
            foreach (float fps in fpssamples)
            {
                if (fps > max) max = fps;
            }
            return max;
        }

        [Serializable]
        private class SerializableMetrics
        {
            public string session_id;
            public float session_duration;
            public int player_deaths;
            public int quests_completed;
            public int items_crafted;
            public int enemies_defeated;
            public int total_events;
            public float fps_average;
            public float fps_min;
            public float fps_max;

            public SerializableMetrics(Dictionary<string, object> metrics)
            {
                session_id = metrics["session_id"] as string;
                session_duration = (float)metrics["session_duration"];
                player_deaths = (int)metrics["player_deaths"];
                quests_completed = (int)metrics["quests_completed"];
                items_crafted = (int)metrics["items_crafted"];
                enemies_defeated = (int)metrics["enemies_defeated"];
                total_events = (int)metrics["total_events"];
                fps_average = (float)metrics["fps_average"];
                fps_min = (float)metrics["fps_min"];
                fps_max = (float)metrics["fps_max"];
            }
        }

        private void OnApplicationQuit()
        {
            // Auto-export on quit
            ExportSession();
        }
    }
}
