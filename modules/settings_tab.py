"""
Settings Tab
Handles configuration of API keys, webhooks, and other settings
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import requests
import os

class SettingsTab:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        
        self.frame = ttk.Frame(parent)
        self.create_widgets()
        self.load_settings()
    
    def create_widgets(self):
        """Create the settings tab widgets"""
        # Create notebook for settings categories
        self.settings_notebook = ttk.Notebook(self.frame)
        self.settings_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # API Keys tab
        self.create_api_tab()
        
        # Discord tab
        self.create_discord_tab()
        
        # Paths tab
        self.create_paths_tab()
        
        # Import/Export tab
        self.create_import_export_tab()
    
    def create_api_tab(self):
        """Create API keys configuration tab"""
        api_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(api_frame, text="API Keys")
        
        # Main container with scrollbar
        canvas = tk.Canvas(api_frame)
        scrollbar = ttk.Scrollbar(api_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create horizontal layout for API sections
        api_columns_frame = ttk.Frame(scrollable_frame)
        api_columns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left column - Gemini API
        left_column = ttk.Frame(api_columns_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        gemini_frame = ttk.LabelFrame(left_column, text="Google Gemini API", padding=10)
        gemini_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(gemini_frame, text="API Key:").pack(anchor=tk.W)
        self.gemini_key_var = tk.StringVar()
        gemini_entry = ttk.Entry(gemini_frame, textvariable=self.gemini_key_var, width=40, show="*")
        gemini_entry.pack(fill=tk.X, pady=(5, 10))
        
        # Model selection
        model_frame = ttk.Frame(gemini_frame)
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(model_frame, text="Model:").pack(anchor=tk.W)
        self.gemini_model_var = tk.StringVar(value="gemini-2.5-flash")
        
        # Define models with their quotas (RPM/TPM/RPD)
        self.gemini_models = {
            "gemini-2.0-flash-live": {"name": "Gemini 2.0 Flash Live", "rpm": "Unlimited", "tpm": "1M", "rpd": "Unlimited"},
            "gemini-2.5-flash-live": {"name": "Gemini 2.5 Flash Live", "rpm": "Unlimited", "tpm": "1M", "rpd": "Unlimited"},
            "gemini-2.5-flash-native-audio-dialog": {"name": "Gemini 2.5 Flash Audio Dialog", "rpm": "Unlimited", "tpm": "1M", "rpd": "Unlimited"},
            "gemini-2.0-flash-lite": {"name": "Gemini 2.0 Flash Lite", "rpm": "300", "tpm": "1M", "rpd": "200"},
            "gemini-2.0-flash": {"name": "Gemini 2.0 Flash", "rpm": "150", "tpm": "1M", "rpd": "200"},
            "gemini-2.5-flash-lite": {"name": "Gemini 2.5 Flash Lite", "rpm": "150", "tpm": "250K", "rpd": "1K"},
            "gemini-2.5-flash-tts": {"name": "Gemini 2.5 Flash TTS", "rpm": "30", "tpm": "10K", "rpd": "15"},
            "gemini-2.5-flash": {"name": "Gemini 2.5 Flash", "rpm": "100", "tpm": "250K", "rpd": "250"},
            "gemini-2.5-pro": {"name": "Gemini 2.5 Pro", "rpm": "20", "tpm": "125K", "rpd": "50"},
            "gemini-robotics-er-1.5-preview": {"name": "Gemini Robotics ER 1.5", "rpm": "100", "tpm": "250K", "rpd": "250"},
            "learnlm-2.0-flash-experimental": {"name": "LearnLM 2.0 Flash", "rpm": "15", "tpm": "N/A", "rpd": "1.5K"},
            "gemini-2.0-flash-exp": {"name": "Gemini 2.0 Flash Exp", "rpm": "N/A", "tpm": "N/A", "rpd": "50"}
        }
        
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.gemini_model_var, 
                                       values=list(self.gemini_models.keys()), 
                                       state="readonly", width=30)
        self.model_combo.pack(fill=tk.X, pady=(5, 0))
        self.model_combo.bind("<<ComboboxSelected>>", self.update_quota_display)
        
        # Quota display
        self.quota_label = ttk.Label(gemini_frame, text="", foreground="darkgreen", font=("Arial", 9))
        self.quota_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Usage display
        self.usage_label = ttk.Label(gemini_frame, text="", foreground="darkblue", font=("Arial", 9))
        self.usage_label.pack(anchor=tk.W, pady=(0, 10))
        
        gemini_buttons = ttk.Frame(gemini_frame)
        gemini_buttons.pack(fill=tk.X)
        ttk.Button(gemini_buttons, text="Test Connection", command=self.test_gemini).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gemini_buttons, text="Save", command=self.save_gemini).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gemini_buttons, text="Refresh Usage", command=self.refresh_usage).pack(side=tk.LEFT)
        
        ttk.Label(gemini_frame, text="Get your API key from: https://makersuite.google.com/app/apikey", 
                 foreground="blue").pack(anchor=tk.W, pady=(5, 0))
        
        # Update quota display initially
        self.update_quota_display()
        
        # Middle column - Steam API
        middle_column = ttk.Frame(api_columns_frame)
        middle_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 5))
        
        steam_frame = ttk.LabelFrame(middle_column, text="Steam Web API", padding=10)
        steam_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(steam_frame, text="API Key:").pack(anchor=tk.W)
        self.steam_key_var = tk.StringVar()
        steam_key_entry = ttk.Entry(steam_frame, textvariable=self.steam_key_var, width=40, show="*")
        steam_key_entry.pack(fill=tk.X, pady=(5, 10))
        
        ttk.Label(steam_frame, text="Steam ID:").pack(anchor=tk.W)
        self.steam_id_var = tk.StringVar()
        steam_id_entry = ttk.Entry(steam_frame, textvariable=self.steam_id_var, width=40)
        steam_id_entry.pack(fill=tk.X, pady=(5, 10))
        
        steam_buttons = ttk.Frame(steam_frame)
        steam_buttons.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(steam_buttons, text="Test", command=self.test_steam).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(steam_buttons, text="Save", command=self.save_steam).pack(side=tk.LEFT)
        
        ttk.Label(steam_frame, text="Get API key:", foreground="blue").pack(anchor=tk.W)
        ttk.Label(steam_frame, text="steamcommunity.com/dev/apikey", foreground="blue", font=("Arial", 8)).pack(anchor=tk.W)
        ttk.Label(steam_frame, text="Find Steam ID:", foreground="blue").pack(anchor=tk.W, pady=(5, 0))
        ttk.Label(steam_frame, text="steamidfinder.com", foreground="blue", font=("Arial", 8)).pack(anchor=tk.W)
        
        # Right column - Epic Games Authentication
        right_column = ttk.Frame(api_columns_frame)
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        epic_frame = ttk.LabelFrame(right_column, text="Epic Games (Legendary)", padding=10)
        epic_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(epic_frame, text="Authorization Code:").pack(anchor=tk.W)
        self.epic_auth_var = tk.StringVar()
        epic_auth_entry = ttk.Entry(epic_frame, textvariable=self.epic_auth_var, width=40, show="*")
        epic_auth_entry.pack(fill=tk.X, pady=(5, 10))
        
        epic_buttons = ttk.Frame(epic_frame)
        epic_buttons.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(epic_buttons, text="Get Code", command=self.get_epic_auth).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(epic_buttons, text="Test", command=self.test_epic).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(epic_buttons, text="Save", command=self.save_epic).pack(side=tk.LEFT)
        
        ttk.Label(epic_frame, text="1. Click 'Get Code'", foreground="blue", font=("Arial", 9)).pack(anchor=tk.W)
        ttk.Label(epic_frame, text="2. Login to Epic Games", foreground="blue", font=("Arial", 9)).pack(anchor=tk.W)
        ttk.Label(epic_frame, text="3. Copy authorizationCode", foreground="blue", font=("Arial", 9)).pack(anchor=tk.W)
        ttk.Label(epic_frame, text="4. Paste above & Save", foreground="blue", font=("Arial", 9)).pack(anchor=tk.W)
        
        ttk.Label(epic_frame, text="1. Click 'Get Auth Code' to open Epic Games login", 
                 foreground="blue").pack(anchor=tk.W, pady=(5, 0))
        ttk.Label(epic_frame, text="2. Login and copy the 'authorizationCode' from the JSON response", 
                 foreground="blue").pack(anchor=tk.W)
        ttk.Label(epic_frame, text="3. Paste the code above and click 'Save'", 
                 foreground="blue").pack(anchor=tk.W)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_discord_tab(self):
        """Create Discord webhook configuration tab"""
        discord_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(discord_frame, text="Discord")
        
        # News Webhook URL
        news_webhook_frame = ttk.LabelFrame(discord_frame, text="News Webhook", padding=10)
        news_webhook_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(news_webhook_frame, text="News Webhook URL:").pack(anchor=tk.W)
        self.webhook_url_var = tk.StringVar()
        news_webhook_entry = ttk.Entry(news_webhook_frame, textvariable=self.webhook_url_var, width=80)
        news_webhook_entry.pack(fill=tk.X, pady=(5, 10))
        
        news_webhook_buttons = ttk.Frame(news_webhook_frame)
        news_webhook_buttons.pack(fill=tk.X)
        ttk.Button(news_webhook_buttons, text="Test News Webhook", command=self.test_webhook).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(news_webhook_buttons, text="Save", command=self.save_webhook).pack(side=tk.LEFT)
        
        # Task Reminders Webhook URL
        task_webhook_frame = ttk.LabelFrame(discord_frame, text="Task Reminders Webhook", padding=10)
        task_webhook_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(task_webhook_frame, text="Task Reminders Webhook URL:").pack(anchor=tk.W)
        self.task_webhook_url_var = tk.StringVar()
        task_webhook_entry = ttk.Entry(task_webhook_frame, textvariable=self.task_webhook_url_var, width=80)
        task_webhook_entry.pack(fill=tk.X, pady=(5, 10))
        
        task_webhook_buttons = ttk.Frame(task_webhook_frame)
        task_webhook_buttons.pack(fill=tk.X)
        ttk.Button(task_webhook_buttons, text="Test Task Webhook", command=self.test_task_webhook).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(task_webhook_buttons, text="Test Auto-Reminders", command=self.test_auto_reminders).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(task_webhook_buttons, text="Save", command=self.save_task_webhook).pack(side=tk.LEFT)
        
        # Discord User ID for pings
        user_id_frame = ttk.LabelFrame(discord_frame, text="Discord Notifications", padding=10)
        user_id_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(user_id_frame, text="Your Discord User ID (for pings):").pack(anchor=tk.W)
        self.discord_user_id_var = tk.StringVar()
        user_id_entry = ttk.Entry(user_id_frame, textvariable=self.discord_user_id_var, width=30)
        user_id_entry.pack(fill=tk.X, pady=(5, 10))
        
        user_id_buttons = ttk.Frame(user_id_frame)
        user_id_buttons.pack(fill=tk.X)
        ttk.Button(user_id_buttons, text="Save User ID", command=self.save_discord_user_id).pack(side=tk.LEFT)
        
        # Auto-send settings
        auto_send_frame = ttk.LabelFrame(discord_frame, text="Automatic Notifications", padding=10)
        auto_send_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.auto_send_news_var = tk.BooleanVar()
        ttk.Checkbutton(auto_send_frame, text="Auto-send news updates every hour", 
                       variable=self.auto_send_news_var, command=self.save_auto_settings).pack(anchor=tk.W)
        
        self.auto_task_reminders_var = tk.BooleanVar()
        ttk.Checkbutton(auto_send_frame, text="Auto-send task reminders daily at 9 AM", 
                       variable=self.auto_task_reminders_var, command=self.save_auto_settings).pack(anchor=tk.W)
        
        # Instructions for auto-reminders
        reminder_info = ttk.Label(auto_send_frame, 
                                 text="• Task reminders will be sent automatically for overdue and due-today tasks\n"
                                      "• Uses separate task webhook if configured, otherwise falls back to news webhook\n"
                                      "• Test the system using the 'Test Auto-Reminders' button above",
                                 justify=tk.LEFT, foreground="darkblue", font=("Arial", 9))
        reminder_info.pack(anchor=tk.W, pady=(5, 0))
        
        # Instructions for getting user ID
        instructions_text = """How to get your Discord User ID:
1. Enable Developer Mode in Discord Settings → Advanced
2. Right-click your username/avatar in any chat
3. Click "Copy User ID"
4. Paste the ID above and save"""
        
        ttk.Label(user_id_frame, text=instructions_text, justify=tk.LEFT, foreground="blue", font=("Arial", 9)).pack(anchor=tk.W, pady=(10, 0))
        
        # Instructions
        instructions = ttk.LabelFrame(discord_frame, text="How to get Discord Webhook URL", padding=10)
        instructions.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        instruction_text = """1. Go to your Discord server
2. Right-click on the channel where you want notifications
3. Select "Edit Channel"
4. Go to "Integrations" tab
5. Click "Create Webhook"
6. Copy the webhook URL and paste it above"""
        
        ttk.Label(instructions, text=instruction_text, justify=tk.LEFT).pack(anchor=tk.W)
    
    def create_paths_tab(self):
        """Create paths configuration tab"""
        paths_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(paths_frame, text="Paths")
        
        # Steam path
        steam_path_frame = ttk.LabelFrame(paths_frame, text="Steam Installation", padding=10)
        steam_path_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(steam_path_frame, text="Steam Executable Path:").pack(anchor=tk.W)
        
        path_frame = ttk.Frame(steam_path_frame)
        path_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.steam_path_var = tk.StringVar()
        steam_path_entry = ttk.Entry(path_frame, textvariable=self.steam_path_var, width=60)
        steam_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(path_frame, text="Browse", command=self.browse_steam_path).pack(side=tk.RIGHT)
        
        ttk.Button(steam_path_frame, text="Save", command=self.save_steam_path).pack(anchor=tk.W)
        
        # Legendary info
        legendary_frame = ttk.LabelFrame(paths_frame, text="Epic Games (Legendary)", padding=10)
        legendary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        legendary_text = """For Epic Games support, you need to install Legendary CLI:

1. Download from: https://github.com/derrod/legendary
2. Install using pip: pip install legendary-gl
3. Configure authentication in API Keys tab
4. The app will use legendary to import and launch Epic games

Note: Authentication testing is available in the API Keys tab."""
        
        ttk.Label(legendary_frame, text=legendary_text, justify=tk.LEFT).pack(anchor=tk.W)
    
    def create_import_export_tab(self):
        """Create import/export configuration tab"""
        ie_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(ie_frame, text="Import/Export")
        
        # Export settings
        export_frame = ttk.LabelFrame(ie_frame, text="Export Settings", padding=10)
        export_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(export_frame, text="Export all settings to a JSON file for backup:").pack(anchor=tk.W, pady=(0, 10))
        ttk.Button(export_frame, text="Export Settings", command=self.export_settings).pack(anchor=tk.W)
        
        # Import settings
        import_frame = ttk.LabelFrame(ie_frame, text="Import Settings", padding=10)
        import_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(import_frame, text="Import settings from a JSON backup file:").pack(anchor=tk.W, pady=(0, 10))
        ttk.Button(import_frame, text="Import Settings", command=self.import_settings).pack(anchor=tk.W)
        
        # Database info
        db_frame = ttk.LabelFrame(ie_frame, text="Database Information", padding=10)
        db_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        db_info = f"""Database Location: {os.path.abspath(self.db.db_path)}

The database contains:
- RSS feeds and news items
- Game library data
- Tasks and to-do items
- All configuration settings

You can backup this file to preserve all your data."""
        
        ttk.Label(db_frame, text=db_info, justify=tk.LEFT).pack(anchor=tk.W)
    
    def load_settings(self):
        """Load settings from database"""
        # Load API keys
        self.gemini_key_var.set(self.db.get_setting('gemini_api_key', ''))
        self.gemini_model_var.set(self.db.get_setting('gemini_model', 'gemini-2.5-flash'))
        self.steam_key_var.set(self.db.get_setting('steam_api_key', ''))
        self.steam_id_var.set(self.db.get_setting('steam_id', ''))
        self.epic_auth_var.set(self.db.get_setting('epic_auth_code', ''))
        
        # Load Discord webhooks
        self.webhook_url_var.set(self.db.get_setting('discord_webhook_url', ''))
        self.task_webhook_url_var.set(self.db.get_setting('discord_task_webhook_url', ''))
        self.discord_user_id_var.set(self.db.get_setting('discord_user_id', ''))
        
        # Load auto-send settings
        self.auto_send_news_var.set(self.db.get_setting('auto_send_news', 'true').lower() == 'true')
        self.auto_task_reminders_var.set(self.db.get_setting('auto_task_reminders', 'true').lower() == 'true')
        
        # Load paths
        default_steam_path = r"C:\Program Files (x86)\Steam\steam.exe"
        self.steam_path_var.set(self.db.get_setting('steam_path', default_steam_path))
        
        # Update quota display
        self.update_quota_display()
    
    def save_gemini(self):
        """Save Gemini API key and model"""
        api_key = self.gemini_key_var.get().strip()
        model = self.gemini_model_var.get().strip()
        
        if api_key and model:
            self.db.set_setting('gemini_api_key', api_key)
            self.db.set_setting('gemini_model', model)
            messagebox.showinfo("Success", "Gemini API settings saved!")
        else:
            messagebox.showwarning("Warning", "Please enter an API key and select a model")
    
    def test_gemini(self):
        """Test Gemini API connection"""
        api_key = self.gemini_key_var.get().strip()
        model_name = self.gemini_model_var.get().strip()
        
        if not api_key or not model_name:
            messagebox.showwarning("Warning", "Please enter an API key and select a model first")
            return
        
        def test_in_thread():
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                
                response = model.generate_content("Hello, this is a test.")
                
                self.frame.after(0, lambda: messagebox.showinfo("Success", f"Gemini API connection successful!\nModel: {model_name}\nResponse: {response.text[:100]}..."))
                
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Error", f"Gemini API test failed: {e}"))
        
        import threading
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def update_quota_display(self, event=None):
        """Update the quota display based on selected model"""
        model_key = self.gemini_model_var.get()
        if model_key in self.gemini_models:
            model_info = self.gemini_models[model_key]
            quota_text = f"Quota Limits - RPM: {model_info['rpm']}, TPM: {model_info['tpm']}, RPD: {model_info['rpd']}"
            
            # Add usage estimation
            rpm = model_info['rpm']
            if rpm != "Unlimited" and rpm != "N/A":
                try:
                    rpm_int = int(rpm)
                    hourly_limit = rpm_int * 60
                    daily_limit = min(hourly_limit * 24, int(model_info['rpd']) if model_info['rpd'] not in ["Unlimited", "N/A"] else hourly_limit * 24)
                    quota_text += f"\nEstimated Usage: ~{hourly_limit} requests/hour, ~{daily_limit} requests/day"
                except:
                    pass
            
            self.quota_label.config(text=quota_text)
            
            # Update usage statistics
            self.update_usage_display(model_key)
        else:
            self.quota_label.config(text="")
            self.usage_label.config(text="")
    
    def update_usage_display(self, model_key):
        """Update the usage display with current statistics"""
        try:
            stats = self.db.get_api_usage_stats('gemini', model_key)
            usage_text = f"Current Usage - Last Hour: {stats['hour']}, Last 24h: {stats['day']}, Total: {stats['total']}"
            
            # Calculate remaining quota if applicable
            if model_key in self.gemini_models:
                model_info = self.gemini_models[model_key]
                rpm = model_info['rpm']
                rpd = model_info['rpd']
                
                if rpm not in ["Unlimited", "N/A"] and rpd not in ["Unlimited", "N/A"]:
                    try:
                        rpm_int = int(rpm)
                        rpd_int = int(rpd.replace('K', '000').replace('M', '000000'))
                        
                        # Calculate remaining for today
                        remaining_daily = max(0, rpd_int - stats['day'])
                        usage_text += f"\nRemaining Today: {remaining_daily} requests"
                        
                        # Warning if approaching limits
                        if stats['day'] > rpd_int * 0.8:  # 80% of daily limit
                            usage_text += " ⚠️ Approaching daily limit!"
                        elif stats['hour'] > rpm_int * 0.8:  # 80% of per-minute limit
                            usage_text += " ⚠️ High usage rate!"
                    except:
                        pass
            
            self.usage_label.config(text=usage_text)
        except Exception as e:
            self.usage_label.config(text=f"Usage tracking error: {e}")
    
    def refresh_usage(self):
        """Refresh the usage statistics display"""
        self.update_quota_display()
    
    def save_steam(self):
        """Save Steam API settings"""
        api_key = self.steam_key_var.get().strip()
        steam_id = self.steam_id_var.get().strip()
        
        if api_key and steam_id:
            self.db.set_setting('steam_api_key', api_key)
            self.db.set_setting('steam_id', steam_id)
            messagebox.showinfo("Success", "Steam API settings saved!")
        else:
            messagebox.showwarning("Warning", "Please enter both API key and Steam ID")
    
    def test_steam(self):
        """Test Steam API connection"""
        api_key = self.steam_key_var.get().strip()
        steam_id = self.steam_id_var.get().strip()
        
        if not api_key or not steam_id:
            messagebox.showwarning("Warning", "Please enter both API key and Steam ID first")
            return
        
        def test_in_thread():
            try:
                url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
                params = {
                    'key': api_key,
                    'steamid': steam_id,
                    'format': 'json'
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'response' in data:
                    game_count = len(data['response'].get('games', []))
                    self.frame.after(0, lambda: messagebox.showinfo("Success", 
                        f"Steam API connection successful! Found {game_count} games."))
                else:
                    self.frame.after(0, lambda: messagebox.showerror("Error", 
                        "Steam API test failed: Invalid response"))
                
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Error", f"Steam API test failed: {e}"))
        
        import threading
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def get_epic_auth(self):
        """Open Epic Games login page"""
        import webbrowser
        auth_url = "https://legendary.gl/epiclogin"
        webbrowser.open(auth_url)
        messagebox.showinfo("Epic Games Login", 
                           "1. Complete the Epic Games login in your browser\n"
                           "2. Copy the 'authorizationCode' value from the JSON response\n"
                           "3. Paste it in the Authorization Code field above\n"
                           "4. Click 'Save'")
    
    def save_epic(self):
        """Save Epic Games authorization code"""
        auth_code = self.epic_auth_var.get().strip()
        if auth_code:
            self.db.set_setting('epic_auth_code', auth_code)
            messagebox.showinfo("Success", "Epic Games authorization code saved!")
        else:
            messagebox.showwarning("Warning", "Please enter the authorization code")
    
    def test_epic(self):
        """Test Epic Games connection using legendary"""
        auth_code = self.epic_auth_var.get().strip()
        if not auth_code:
            messagebox.showwarning("Warning", "Please enter and save the authorization code first")
            return
        
        def test_in_thread():
            try:
                import subprocess
                # Test legendary connection
                result = subprocess.run(['legendary', 'list'], capture_output=True, text=True, 
                                       encoding='utf-8', errors='ignore', timeout=30)
                
                if result.returncode == 0:
                    # Count games in output
                    lines = result.stdout.split('\n')
                    game_count = 0
                    for line in lines:
                        if '|' in line and not line.startswith('Legendary'):
                            game_count += 1
                    
                    self.frame.after(0, lambda: messagebox.showinfo("Success", 
                        f"Epic Games connection successful! Found {game_count} games."))
                else:
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    self.frame.after(0, lambda: messagebox.showerror("Error", 
                        f"Epic Games test failed: {error_msg[:200]}"))
                        
            except FileNotFoundError:
                self.frame.after(0, lambda: messagebox.showerror("Error", 
                    "Legendary CLI not found. Please install legendary first:\npip install legendary-gl"))
            except Exception as e:
                error_msg = str(e)
                self.frame.after(0, lambda msg=error_msg: messagebox.showerror("Error", f"Epic Games test failed: {msg}"))
        
        import threading
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def save_webhook(self):
        """Save Discord webhook URL"""
        webhook_url = self.webhook_url_var.get().strip()
        if webhook_url:
            self.db.set_setting('discord_webhook_url', webhook_url)
            messagebox.showinfo("Success", "Discord webhook URL saved!")
        else:
            messagebox.showwarning("Warning", "Please enter a webhook URL")
    
    def save_discord_user_id(self):
        """Save Discord user ID for pings"""
        user_id = self.discord_user_id_var.get().strip()
        if user_id:
            # Validate that it's a valid Discord user ID (should be numeric and 17-19 digits)
            if user_id.isdigit() and 17 <= len(user_id) <= 19:
                self.db.set_setting('discord_user_id', user_id)
                messagebox.showinfo("Success", "Discord User ID saved!")
            else:
                messagebox.showwarning("Warning", "Invalid Discord User ID. Should be 17-19 digits.")
        else:
            messagebox.showwarning("Warning", "Please enter your Discord User ID")
    
    def save_task_webhook(self):
        """Save Discord task webhook URL"""
        webhook_url = self.task_webhook_url_var.get().strip()
        if webhook_url:
            self.db.set_setting('discord_task_webhook_url', webhook_url)
            messagebox.showinfo("Success", "Discord task webhook URL saved!")
        else:
            messagebox.showwarning("Warning", "Please enter a task webhook URL")
    
    def test_task_webhook(self):
        """Test Discord task webhook"""
        webhook_url = self.task_webhook_url_var.get().strip()
        if not webhook_url:
            messagebox.showwarning("Warning", "Please enter a task webhook URL first")
            return
        
        def test_in_thread():
            try:
                # Get Discord user ID for ping test
                discord_user_id = self.discord_user_id_var.get().strip()
                ping_text = f"<@{discord_user_id}> " if discord_user_id else ""
                
                payload = {
                    "username": "Task Reminder Test",
                    "content": f"{ping_text}⏰ This is a test message for task reminders from your Personal Dashboard!"
                }
                
                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                
                ping_status = " (with ping)" if discord_user_id else " (no ping - add User ID for pings)"
                self.frame.after(0, lambda: messagebox.showinfo("Success", f"Discord task webhook test successful{ping_status}!"))
                
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Error", f"Discord task webhook test failed: {e}"))
        
        import threading
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def test_auto_reminders(self):
        """Test the automatic task reminder system"""
        def test_in_thread():
            try:
                # Import scheduler here to avoid circular imports
                from modules.scheduler import SchedulerManager
                
                # Create a temporary scheduler instance for testing
                temp_scheduler = SchedulerManager(self.db)
                
                # Test the task reminders
                task_count = temp_scheduler.test_task_reminders()
                
                if task_count > 0:
                    self.frame.after(0, lambda: messagebox.showinfo("Success", 
                        f"Auto-reminder test successful!\n"
                        f"Sent reminders for {task_count} due tasks.\n\n"
                        f"This is how automatic daily reminders at 9 AM will work."))
                else:
                    self.frame.after(0, lambda: messagebox.showinfo("Info", 
                        "Auto-reminder test completed.\n"
                        "No tasks are currently due for reminders."))
                
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Error", f"Auto-reminder test failed: {e}"))
        
        import threading
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def save_auto_settings(self):
        """Save automatic notification settings"""
        self.db.set_setting('auto_send_news', str(self.auto_send_news_var.get()).lower())
        self.db.set_setting('auto_task_reminders', str(self.auto_task_reminders_var.get()).lower())
    
    def test_webhook(self):
        """Test Discord webhook"""
        webhook_url = self.webhook_url_var.get().strip()
        if not webhook_url:
            messagebox.showwarning("Warning", "Please enter a webhook URL first")
            return
        
        def test_in_thread():
            try:
                # Get Discord user ID for ping test
                discord_user_id = self.discord_user_id_var.get().strip()
                ping_text = f"<@{discord_user_id}> " if discord_user_id else ""
                
                payload = {
                    "username": "Dashboard Test",
                    "content": f"{ping_text}🧪 This is a test message from your Personal Dashboard!"
                }
                
                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                
                ping_status = " (with ping)" if discord_user_id else " (no ping - add User ID for pings)"
                self.frame.after(0, lambda: messagebox.showinfo("Success", f"Discord webhook test successful{ping_status}!"))
                
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Error", f"Discord webhook test failed: {e}"))
        
        import threading
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def browse_steam_path(self):
        """Browse for Steam executable"""
        filename = filedialog.askopenfilename(
            title="Select Steam Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")],
            initialdir="C:\\Program Files (x86)\\Steam\\"
        )
        if filename:
            self.steam_path_var.set(filename)
    
    def save_steam_path(self):
        """Save Steam path"""
        steam_path = self.steam_path_var.get().strip()
        if steam_path:
            self.db.set_setting('steam_path', steam_path)
            messagebox.showinfo("Success", "Steam path saved!")
        else:
            messagebox.showwarning("Warning", "Please enter a Steam path")
    
    
    def export_settings(self):
        """Export all settings to JSON file"""
        filename = filedialog.asksaveasfilename(
            title="Export Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Get all settings from database
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT key, value FROM settings")
                settings = {row['key']: row['value'] for row in cursor.fetchall()}
                
                # Export to JSON file
                with open(filename, 'w') as f:
                    json.dump(settings, f, indent=2)
                
                messagebox.showinfo("Success", f"Settings exported to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export settings: {e}")
    
    def import_settings(self):
        """Import settings from JSON file"""
        filename = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Load settings from JSON file
                with open(filename, 'r') as f:
                    settings = json.load(f)
                
                # Import each setting
                for key, value in settings.items():
                    self.db.set_setting(key, value)
                
                # Reload settings in UI
                self.load_settings()
                
                messagebox.showinfo("Success", f"Settings imported from {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import settings: {e}")