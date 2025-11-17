# AutoGS Unity Plugin

Complete Unity Editor integration for the AutoGS pipeline.

## Features

### 1. Unity Editor Window
Run the entire AutoGS pipeline from within Unity without leaving the editor.

**Features:**
- Configure AutoGS path and API keys
- Select which pipeline stages to run
- View real-time log output
- Import generated assets automatically
- Dry-run mode for testing

**Installation:**
1. Copy the `unity_plugin` folder to your Unity project's `Assets/` directory
2. Open Unity and navigate to `Window > AutoGS Pipeline`

### 2. Playtesting Metrics System
Automated gameplay metrics collection for data-driven game design.

**Tracked Metrics:**
- FPS (average, min, max)
- Player deaths with causes
- Quest completions with timing
- Items crafted
- Enemies defeated
- Custom events and actions

**Usage:**
```csharp
using AutoGS.Metrics;

// Track player death
PlaytestMetrics.Instance.RecordDeath("fall_damage");

// Track quest completion
PlaytestMetrics.Instance.RecordQuestComplete("quest_001", 45.2f);

// Track custom event
PlaytestMetrics.Instance.TrackEvent("boss_defeated", new Dictionary<string, object>
{
    { "boss_name", "Dragon Lord" },
    { "attempts", 3 }
});

// Export session data
string filepath = PlaytestMetrics.Instance.ExportSession();
```

**Output:**
Metrics are automatically exported to JSON files in `Application.persistentDataPath/Metrics/`

### 3. Steam Deployment Integration
One-click Steam deployment through the Unity Editor.

**Features:**
- Automated Steamworks SDK integration
- Multi-depot support for different platforms
- VDF script generation
- Build upload automation

**Requirements:**
- Steamworks SDK installed
- Steam Partner account
- Valid App ID

## File Structure

```
unity_plugin/
├── Editor/
│   └── AutoGSWindow.cs          # Unity Editor window
├── Runtime/
│   └── Metrics/
│       └── PlaytestMetrics.cs   # Metrics collection system
└── README.md                     # This file
```

## Configuration

### Setting up the Editor Window

1. **Python Path:** Path to your Python executable (e.g., `/usr/bin/python3`)
2. **AutoGS Path:** Path to your AutoGS installation directory
3. **API Key:** Your OpenAI or Anthropic API key
4. **Output Directory:** Where generated assets should be placed

### Setting up Steam Deployment

Configure in your AutoGS `config.json`:

```json
{
  "build": {
    "steamworks_sdk_path": "/path/to/steamworks_sdk",
    "steam_app_id": 480
  }
}
```

## Best Practices

### Metrics Collection

1. **Initialize Early:** PlaytestMetrics auto-initializes, but you can manually start it in your game manager
2. **Track Important Events:** Focus on events that matter for game balance and player experience
3. **Regular Exports:** Export session data periodically for long play sessions
4. **Analyze Trends:** Use the JSON exports to analyze gameplay patterns over time

### Editor Integration

1. **Test with Dry-Run:** Always test your pipeline configuration with dry-run mode first
2. **API Key Security:** Don't commit your API keys to version control
3. **Incremental Stages:** Run individual stages during development for faster iteration

## Troubleshooting

### Editor Window Issues

**Problem:** Pipeline doesn't start
- **Solution:** Check Python path and AutoGS directory are correctly configured
- **Solution:** Ensure API key is set (or run in dry-run mode)

**Problem:** Can't see output
- **Solution:** Check the Output Log section in the window - it updates in real-time

### Metrics Issues

**Problem:** Metrics not saving
- **Solution:** Check write permissions for `Application.persistentDataPath`
- **Solution:** Call `ExportSession()` manually if auto-export fails

### Steam Deployment Issues

**Problem:** Steamworks SDK not found
- **Solution:** Verify SDK path in configuration
- **Solution:** Download Steamworks SDK from Steamworks partner site

**Problem:** Upload fails
- **Solution:** Check Steam credentials
- **Solution:** Verify App ID is correct and active

## Examples

### Complete Workflow Example

1. **Configure the Pipeline:**
   ```
   Open Window > AutoGS Pipeline
   Set Python Path, AutoGS Path, API Key
   Click "Validate Configuration"
   ```

2. **Run Pipeline:**
   ```
   Select stages to run (or run all)
   Click "Run Full Pipeline"
   Monitor progress in Output Log
   ```

3. **Import Assets:**
   ```
   After pipeline completes, click "Import Generated Assets"
   Assets appear in your specified Output Directory
   ```

4. **Collect Metrics:**
   ```csharp
   // In your game code
   PlaytestMetrics.Instance.RecordDeath("lava");
   PlaytestMetrics.Instance.RecordQuestComplete("tutorial", 120f);
   ```

5. **Deploy to Steam:**
   ```python
   # In your AutoGS pipeline or standalone
   from autogs.bots.steam_deployer import SteamDeployerBot

   deployer = SteamDeployerBot(config)
   result = deployer.run({
       "game_name": "My Game",
       "build_paths": {
           "Windows": "Builds/Windows",
           "Linux": "Builds/Linux"
       }
   })
   ```

## API Reference

### PlaytestMetrics

#### Methods

- `RecordDeath(cause: string)` - Record player death with cause
- `RecordQuestComplete(questId: string, time: float)` - Record quest completion
- `RecordCraft(itemName: string, category: string)` - Record item crafted
- `RecordEnemyDefeated(enemyType: string, duration: float)` - Record enemy defeated
- `RecordAction(actionName: string)` - Record generic action
- `TrackEvent(eventName: string, data: Dictionary)` - Track custom event
- `GetSessionMetrics()` - Get current session metrics
- `ExportSession()` - Export session to JSON file
- `EndSession()` - End current session and start new one

## Support

For issues and questions:
- Check the main AutoGS documentation
- File issues on the GitHub repository
- Review example projects in the `examples/` directory

## License

MIT License - See main AutoGS LICENSE file
