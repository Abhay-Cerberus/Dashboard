# Personal News & Gaming Dashboard

A Python-based desktop application that aggregates news, manages game libraries with completion tracking, handles to-do tasks, and stores configuration locally. Built with Tkinter for a native Windows experience with advanced game management features.

## Features

### 🖥️ System Tray Integration
- **Minimize to Tray**: App minimizes to system tray when closed instead of exiting
- **Right-Click Menu**: Access show/hide options and exit from tray icon
- **Background Operation**: Continues running scheduled tasks while minimized
- **Notification Support**: Shows tray notifications when minimized (platform dependent)

### 📰 News Summary
- **RSS Feed Management**: Add and manage multiple RSS feeds
- **AI-Powered Summarization**: Uses Google Gemini API to create concise 2-3 sentence summaries
- **Smart Fallback**: Falls back to description truncation if AI is unavailable
- **Automatic Fetching**: Hourly background updates
- **Discord Integration**: Send summaries to Discord channels via webhooks in batches
- **Local Storage**: All news items stored locally for offline access
- **Batch Messaging**: Automatically splits long messages to respect Discord's 2000 character limit

### 🎮 Enhanced Game Library
- **Completion Tracking**: Separate tabs for incomplete and completed games
- **Achievement Progress**: Shows completion percentage based on unlocked achievements
- **Steam Integration**: Import your Steam library with playtime and achievements
- **Epic Games Support**: Import Epic games via Legendary CLI with built-in authentication
- **Smart Game Launcher**: Launch games via Steam protocol (`steam://launch/{AppID}`) or Legendary
- **Random Game Selector**: Picks from incomplete games only to help you finish what you started
- **Advanced Sorting**: Sort by completion percentage, playtime, achievements, platform, or name
- **Game Management**: Mark games as completed/incomplete with right-click context menus
- **Detailed Game Info**: View comprehensive game statistics and launch directly from details

### ✅ To-Do Management
- **Task Creation**: Add tasks with due dates, priorities, and descriptions
- **Recurring Tasks**: Set up daily, weekly, or monthly recurring tasks
- **Discord Reminders**: Get notified about due tasks via Discord in batches
- **Priority System**: High, Medium, Low priority levels with visual indicators
- **Overdue Tracking**: Overdue tasks are highlighted in red
- **Batch Notifications**: Task reminders sent in multiple messages if needed

### ⚙️ Advanced Settings & Configuration
- **Gemini Model Selection**: Choose from 12+ Gemini models with quota tracking
- **API Usage Monitoring**: Track API calls, remaining quota, and usage warnings
- **Discord Webhooks**: Configure webhook URLs with connection testing
- **Legendary Authentication**: Built-in Epic Games authentication via browser
- **Path Configuration**: Set custom paths for Steam and other applications
- **Import/Export**: Backup and restore your settings
- **Connection Testing**: Test all integrations before saving
- **Usage Statistics**: Real-time API usage tracking with warnings at 80% limits

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows OS (designed for Windows, may work on other platforms)

### Required APIs and Tools
1. **Google Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey) (Required for AI news summarization)
2. **Steam Web API Key**: Get from [Steam Community](https://steamcommunity.com/dev/apikey)
3. **Discord Webhook URL**: Create in your Discord server settings
4. **Legendary CLI** (for Epic Games): Automatically installed via requirements.txt

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd personal-dashboard
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

4. **Configure your settings**:
   - Go to the Settings tab
   - Add your Google Gemini API key for AI news summarization
   - Add your Steam API key and Steam ID
   - Add your Discord webhook URL
   - Authenticate Legendary for Epic Games (built-in authentication)
   - Test connections to ensure everything works

## Usage

### First Time Setup

1. **Configure API Keys**:
   - Open Settings → API Keys tab
   - Enter your Google Gemini API key for AI news summarization
   - Enter your Steam API key and Steam ID for game library import
   - Test connections to verify they work

2. **Set up Epic Games**:
   - Open Settings → Paths tab
   - Click "Authenticate Legendary" to log into Epic Games
   - Follow the browser authentication process

3. **Set up Discord Integration**:
   - Open Settings → Discord tab
   - Add your Discord webhook URL
   - Test the webhook to ensure messages are sent

4. **Add RSS Feeds**:
   - Go to News Summary tab
   - Click "Add Feed" and enter your favorite news sources
   - The app will start fetching news automatically every hour

5. **Import Game Libraries**:
   - Go to Game Library tab
   - Click "Import Steam Library" to load your Steam games with achievement data
   - Click "Import Epic Library" to load Epic games (after authentication)
   - Games will be organized by completion status automatically

### Daily Usage

- **Check News**: View AI-summarized news in the News tab, send to Discord as needed
- **Manage Tasks**: Add, edit, and complete tasks in the To-Do tab
- **Launch Games**: Use the Game Library to launch games or get random suggestions
- **System Tray**: Close the app to minimize to system tray, right-click tray icon to show/hide
- **Background Operation**: The app runs scheduled tasks automatically (news fetching, task reminders)

## Configuration

### Database
- All data is stored in `dashboard.db` (SQLite database)
- Includes news items, game library, tasks, and settings
- Can be backed up by copying this file

### Scheduled Tasks
- **News Fetching**: Every hour
- **Task Reminders**: Daily at 9:00 AM
- **Recurring Tasks**: Processed daily at midnight

### File Structure
```
personal-dashboard/
├── main.py                 # Main application entry point
├── modules/
│   ├── database.py         # Database management
│   ├── news_tab.py         # News functionality
│   ├── games_tab.py        # Game library management
│   ├── todo_tab.py         # Task management
│   ├── settings_tab.py     # Configuration interface
│   └── scheduler.py        # Background task scheduler
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── dashboard.db           # SQLite database (created on first run)
```

## Troubleshooting

### Common Issues

1. **"Gemini API test failed"**:
   - Verify your API key is correct
   - Check your internet connection
   - Ensure you have API quota remaining

2. **"Steam API test failed"**:
   - Verify your Steam profile is public
   - Check that your Steam ID is correct (use steamidfinder.com)
   - Ensure your API key is valid

3. **"Legendary CLI not found"**:
   - Install Legendary: `pip install legendary-gl`
   - Authenticate: `legendary auth`
   - Ensure it's in your system PATH

4. **"Discord webhook test failed"**:
   - Verify the webhook URL is correct
   - Check that the Discord channel still exists
   - Ensure you have permission to send messages

### Performance Tips

- The app fetches news every hour by default
- Large game libraries may take time to import initially
- News summaries are cached locally to avoid re-processing
- Database grows over time; consider periodic cleanup of old news items

## Contributing

This is a personal project, but suggestions and improvements are welcome! Please feel free to:
- Report bugs or issues
- Suggest new features
- Submit pull requests
- Share your configuration tips

## License

This project is open source. Feel free to modify and distribute as needed.

## Acknowledgments

- Built with Python and Tkinter
- Uses Google Gemini API for news summarization
- Integrates with Steam Web API and Discord webhooks
- Epic Games support via Legendary CLI
- RSS parsing with feedparser library