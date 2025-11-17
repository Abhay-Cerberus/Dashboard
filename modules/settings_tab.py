"""
Settings Tab
Handles configuration of API keys, webhooks, and other settings
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTabWidget, QLineEdit, QTextEdit, QLabel, QFrame,
                            QMessageBox, QFileDialog, QFormLayout, QGroupBox,
                            QComboBox, QCheckBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

def show_toast(parent, message):
    """Show a simple status message in the status bar instead of toast to avoid threading issues"""
    try:
        # Use the main_window reference from the parent tab
        if hasattr(parent, 'main_window') and hasattr(parent.main_window, 'show_success_message'):
            parent.main_window.show_success_message(message)
        else:
            print(f"Status: {message}")  # Fallback to console
    except Exception as e:
        print(f"Status: {message}")  # Fallback to console
import json
import requests
import os
import threading
import webbrowser

class SettingsTab(QWidget):
    def __init__(self, db, main_window):
        super().__init__()
        self.db = db
        self.main_window = main_window
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Create the modern PyQt settings tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Apply modern styling
        self.setStyleSheet("""
            QWidget {
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton.test {
                background-color: #107c10;
            }
            QPushButton.test:hover {
                background-color: #0e6b0e;
            }
            QLineEdit {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 8px;
                color: white;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
            QLineEdit[echoMode="2"] {
                lineedit-password-character: 42;
            }
            QTextEdit {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 8px;
                color: white;
                padding: 10px;
            }
            QComboBox {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 8px;
                color: white;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
            QTabWidget::pane {
                border: 2px solid #555555;
                border-radius: 8px;
                background-color: #404040;
            }
            QTabBar::tab {
                background-color: #505050;
                color: #ffffff;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
            QTabBar::tab:hover {
                background-color: #606060;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
            QCheckBox {
                color: white;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #555555;
                background-color: #404040;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            QCheckBox::indicator:checked {
                color: white;
                font-weight: bold;
            }
            QLabel {
                color: #ffffff;
            }
            QScrollArea {
                border: none;
                background-color: #3c3c3c;
            }
        """)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # API Keys tab
        self.create_api_tab()
        
        # Discord tab
        self.create_discord_tab()
        
        # Paths tab
        self.create_paths_tab()
        
        # Import/Export tab
        self.create_import_export_tab()
        
        layout.addWidget(self.tab_widget)
    
    def create_api_tab(self):
        """Create API keys configuration tab"""
        api_widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(api_widget)
        scroll.setWidgetResizable(True)
        
        layout = QVBoxLayout(api_widget)
        layout.setSpacing(30)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Gemini API Section
        gemini_group = QGroupBox("🤖 Google Gemini API")
        gemini_layout = QFormLayout(gemini_group)
        gemini_layout.setSpacing(15)
        gemini_layout.setContentsMargins(15, 20, 15, 15)
        
        self.gemini_key_edit = QLineEdit()
        self.gemini_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        gemini_layout.addRow("API Key:", self.gemini_key_edit)
        
        self.gemini_model_combo = QComboBox()
        self.gemini_model_combo.addItems([
            "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash",
            "gemini-2.0-flash-lite", "gemini-2.5-flash-lite"
        ])
        gemini_layout.addRow("Model:", self.gemini_model_combo)
        
        gemini_buttons = QFrame()
        gemini_btn_layout = QHBoxLayout(gemini_buttons)
        gemini_btn_layout.setContentsMargins(0, 0, 0, 0)
        
        test_gemini_btn = QPushButton("🧪 Test")
        test_gemini_btn.setProperty("class", "test")
        test_gemini_btn.clicked.connect(self.test_gemini)
        gemini_btn_layout.addWidget(test_gemini_btn)
        
        save_gemini_btn = QPushButton("💾 Save")
        save_gemini_btn.clicked.connect(self.save_gemini)
        gemini_btn_layout.addWidget(save_gemini_btn)
        
        gemini_btn_layout.addStretch()
        gemini_layout.addRow(gemini_buttons)
        
        info_label = QLabel("Get your API key from: https://makersuite.google.com/app/apikey")
        info_label.setStyleSheet("color: #0078d4; font-size: 10px;")
        gemini_layout.addRow(info_label)
        
        layout.addWidget(gemini_group)
        
        # Steam API Section
        steam_group = QGroupBox("🎮 Steam Web API")
        steam_layout = QFormLayout(steam_group)
        steam_layout.setSpacing(15)
        steam_layout.setContentsMargins(15, 20, 15, 15)
        
        self.steam_key_edit = QLineEdit()
        self.steam_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        steam_layout.addRow("API Key:", self.steam_key_edit)
        
        self.steam_id_edit = QLineEdit()
        steam_layout.addRow("Steam ID:", self.steam_id_edit)
        
        steam_buttons = QFrame()
        steam_btn_layout = QHBoxLayout(steam_buttons)
        steam_btn_layout.setContentsMargins(0, 0, 0, 0)
        
        test_steam_btn = QPushButton("🧪 Test")
        test_steam_btn.setProperty("class", "test")
        test_steam_btn.clicked.connect(self.test_steam)
        steam_btn_layout.addWidget(test_steam_btn)
        
        save_steam_btn = QPushButton("💾 Save")
        save_steam_btn.clicked.connect(self.save_steam)
        steam_btn_layout.addWidget(save_steam_btn)
        
        steam_btn_layout.addStretch()
        steam_layout.addRow(steam_buttons)
        
        steam_info = QLabel("Get API key: steamcommunity.com/dev/apikey\nFind Steam ID: steamidfinder.com")
        steam_info.setStyleSheet("color: #0078d4; font-size: 10px;")
        steam_layout.addRow(steam_info)
        
        layout.addWidget(steam_group)
        
        # Epic Games Section
        epic_group = QGroupBox("🎯 Epic Games (Legendary)")
        epic_layout = QFormLayout(epic_group)
        epic_layout.setSpacing(15)
        epic_layout.setContentsMargins(15, 20, 15, 15)
        
        self.epic_auth_edit = QLineEdit()
        self.epic_auth_edit.setEchoMode(QLineEdit.EchoMode.Password)
        epic_layout.addRow("Authorization Code:", self.epic_auth_edit)
        
        epic_buttons = QFrame()
        epic_btn_layout = QHBoxLayout(epic_buttons)
        epic_btn_layout.setContentsMargins(0, 0, 0, 0)
        
        get_code_btn = QPushButton("🔗 Get Code")
        get_code_btn.clicked.connect(self.get_epic_auth)
        epic_btn_layout.addWidget(get_code_btn)
        
        test_epic_btn = QPushButton("🧪 Test")
        test_epic_btn.setProperty("class", "test")
        test_epic_btn.clicked.connect(self.test_epic)
        epic_btn_layout.addWidget(test_epic_btn)
        
        save_epic_btn = QPushButton("💾 Save")
        save_epic_btn.clicked.connect(self.save_epic)
        epic_btn_layout.addWidget(save_epic_btn)
        
        epic_btn_layout.addStretch()
        epic_layout.addRow(epic_buttons)
        
        epic_info = QLabel("1. Click 'Get Code' → Login to Epic Games\n2. Copy authorizationCode from JSON\n3. Paste above & Save")
        epic_info.setStyleSheet("color: #0078d4; font-size: 10px;")
        epic_layout.addRow(epic_info)
        
        layout.addWidget(epic_group)
        layout.addStretch()
        
        self.tab_widget.addTab(scroll, "🔑 API Keys")
    
    def create_discord_tab(self):
        """Create Discord webhook configuration tab"""
        discord_widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(discord_widget)
        scroll.setWidgetResizable(True)
        
        layout = QVBoxLayout(discord_widget)
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # News Webhook Section
        news_group = QGroupBox("📰 News Webhook")
        news_layout = QFormLayout(news_group)
        news_layout.setSpacing(18)
        news_layout.setContentsMargins(20, 25, 20, 20)
        
        self.news_webhook_edit = QLineEdit()
        news_layout.addRow("Webhook URL:", self.news_webhook_edit)
        
        news_buttons = QFrame()
        news_btn_layout = QHBoxLayout(news_buttons)
        news_btn_layout.setContentsMargins(0, 0, 0, 0)
        
        test_news_btn = QPushButton("🧪 Test")
        test_news_btn.setProperty("class", "test")
        test_news_btn.clicked.connect(self.test_webhook)
        news_btn_layout.addWidget(test_news_btn)
        
        save_news_btn = QPushButton("💾 Save")
        save_news_btn.clicked.connect(self.save_webhook)
        news_btn_layout.addWidget(save_news_btn)
        
        news_btn_layout.addStretch()
        news_layout.addRow(news_buttons)
        
        layout.addWidget(news_group)
        
        # Task Webhook Section
        task_group = QGroupBox("✅ Task Reminders Webhook")
        task_layout = QFormLayout(task_group)
        task_layout.setSpacing(18)
        task_layout.setContentsMargins(20, 25, 20, 20)
        
        self.task_webhook_edit = QLineEdit()
        task_layout.addRow("Webhook URL:", self.task_webhook_edit)
        
        task_buttons = QFrame()
        task_btn_layout = QHBoxLayout(task_buttons)
        task_btn_layout.setContentsMargins(0, 0, 0, 0)
        
        test_task_btn = QPushButton("🧪 Test")
        test_task_btn.setProperty("class", "test")
        test_task_btn.clicked.connect(self.test_task_webhook)
        task_btn_layout.addWidget(test_task_btn)
        
        test_auto_btn = QPushButton("🤖 Test Auto-Reminders")
        test_auto_btn.setProperty("class", "test")
        test_auto_btn.clicked.connect(self.test_auto_reminders)
        task_btn_layout.addWidget(test_auto_btn)
        
        save_task_btn = QPushButton("💾 Save")
        save_task_btn.clicked.connect(self.save_task_webhook)
        task_btn_layout.addWidget(save_task_btn)
        
        task_btn_layout.addStretch()
        task_layout.addRow(task_buttons)
        
        layout.addWidget(task_group)
        
        # User ID Section
        user_group = QGroupBox("👤 Discord Notifications")
        user_layout = QFormLayout(user_group)
        user_layout.setSpacing(18)
        user_layout.setContentsMargins(20, 25, 20, 20)
        
        self.discord_user_id_edit = QLineEdit()
        user_layout.addRow("Your Discord User ID:", self.discord_user_id_edit)
        
        save_user_btn = QPushButton("💾 Save User ID")
        save_user_btn.clicked.connect(self.save_discord_user_id)
        user_layout.addRow(save_user_btn)
        
        user_info = QLabel("How to get User ID:\n1. Enable Developer Mode in Discord\n2. Right-click your username\n3. Click 'Copy User ID'")
        user_info.setStyleSheet("color: #0078d4; font-size: 10px;")
        user_layout.addRow(user_info)
        
        layout.addWidget(user_group)
        
        # Auto Settings Section
        auto_group = QGroupBox("🤖 Automatic Notifications")
        auto_layout = QVBoxLayout(auto_group)
        auto_layout.setSpacing(15)
        auto_layout.setContentsMargins(20, 25, 20, 20)
        
        self.auto_send_news_check = QCheckBox("Auto-send news updates every hour")
        self.auto_send_news_check.stateChanged.connect(self.save_auto_settings)
        auto_layout.addWidget(self.auto_send_news_check)
        
        self.auto_task_reminders_check = QCheckBox("Auto-send task reminders daily at 9 AM")
        self.auto_task_reminders_check.stateChanged.connect(self.save_auto_settings)
        auto_layout.addWidget(self.auto_task_reminders_check)
        
        auto_info = QLabel("• Task reminders sent for overdue and due-today tasks\n• Uses task webhook if configured, otherwise news webhook\n• Test the system using buttons above")
        auto_info.setStyleSheet("color: #0078d4; font-size: 10px; margin-top: 15px;")
        auto_layout.addWidget(auto_info)
        
        layout.addWidget(auto_group)
        
        # Instructions
        instructions_group = QGroupBox("ℹ️ How to get Discord Webhook URL")
        instructions_layout = QVBoxLayout(instructions_group)
        instructions_layout.setContentsMargins(20, 25, 20, 20)
        
        instructions_text = QLabel("""1. Go to your Discord server
2. Right-click on the channel where you want notifications
3. Select "Edit Channel"
4. Go to "Integrations" tab
5. Click "Create Webhook"
6. Copy the webhook URL and paste it above""")
        instructions_text.setStyleSheet("color: #cccccc; font-size: 11px; line-height: 1.4;")
        instructions_layout.addWidget(instructions_text)
        
        layout.addWidget(instructions_group)
        layout.addStretch()
        
        self.tab_widget.addTab(scroll, "💬 Discord")
    
    def create_paths_tab(self):
        """Create paths configuration tab"""
        paths_widget = QWidget()
        layout = QVBoxLayout(paths_widget)
        layout.setSpacing(20)
        
        # Steam Path Section
        steam_group = QGroupBox("🎮 Steam Installation")
        steam_layout = QFormLayout(steam_group)
        steam_layout.setSpacing(15)
        steam_layout.setContentsMargins(15, 20, 15, 15)
        
        steam_path_frame = QFrame()
        steam_path_layout = QHBoxLayout(steam_path_frame)
        steam_path_layout.setContentsMargins(0, 0, 0, 0)
        
        self.steam_path_edit = QLineEdit()
        steam_path_layout.addWidget(self.steam_path_edit)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self.browse_steam_path)
        steam_path_layout.addWidget(browse_btn)
        
        steam_layout.addRow("Steam Executable:", steam_path_frame)
        
        save_path_btn = QPushButton("💾 Save")
        save_path_btn.clicked.connect(self.save_steam_path)
        steam_layout.addRow(save_path_btn)
        
        layout.addWidget(steam_group)
        
        # Legendary Info Section
        legendary_group = QGroupBox("🎯 Epic Games (Legendary)")
        legendary_layout = QVBoxLayout(legendary_group)
        
        legendary_info = QLabel("""For Epic Games support, you need to install Legendary CLI:

1. Download from: https://github.com/derrod/legendary
2. Install using pip: pip install legendary-gl
3. Configure authentication in API Keys tab
4. The app will use legendary to import and launch Epic games

Note: Authentication testing is available in the API Keys tab.""")
        legendary_info.setStyleSheet("color: #cccccc; font-size: 11px;")
        legendary_layout.addWidget(legendary_info)
        
        layout.addWidget(legendary_group)
        layout.addStretch()
        
        self.tab_widget.addTab(paths_widget, "📂 Paths")
    
    def create_import_export_tab(self):
        """Create import/export configuration tab"""
        ie_widget = QWidget()
        layout = QVBoxLayout(ie_widget)
        layout.setSpacing(20)
        
        # Export Section
        export_group = QGroupBox("📤 Export Settings")
        export_layout = QVBoxLayout(export_group)
        
        export_info = QLabel("Export all settings to a JSON file for backup:")
        export_layout.addWidget(export_info)
        
        export_btn = QPushButton("📤 Export Settings")
        export_btn.clicked.connect(self.export_settings)
        export_layout.addWidget(export_btn)
        
        layout.addWidget(export_group)
        
        # Import Section
        import_group = QGroupBox("📥 Import Settings")
        import_layout = QVBoxLayout(import_group)
        
        import_info = QLabel("Import settings from a JSON backup file:")
        import_layout.addWidget(import_info)
        
        import_btn = QPushButton("📥 Import Settings")
        import_btn.clicked.connect(self.import_settings)
        import_layout.addWidget(import_btn)
        
        layout.addWidget(import_group)
        
        # Database Info Section
        db_group = QGroupBox("🗄️ Database Information")
        db_layout = QVBoxLayout(db_group)
        
        db_info = QLabel(f"""Database Location: {os.path.abspath(self.db.db_path)}

The database contains:
• RSS feeds and news items
• Game library data
• Tasks and to-do items
• All configuration settings

You can backup this file to preserve all your data.""")
        db_info.setStyleSheet("color: #cccccc; font-size: 11px;")
        db_layout.addWidget(db_info)
        
        layout.addWidget(db_group)
        layout.addStretch()
        
        self.tab_widget.addTab(ie_widget, "💾 Import/Export")
    
    def load_settings(self):
        """Load settings from database"""
        # Load API keys
        self.gemini_key_edit.setText(str(self.db.get_setting('gemini_api_key', '')))
        self.gemini_model_combo.setCurrentText(str(self.db.get_setting('gemini_model', 'gemini-2.5-flash')))
        self.steam_key_edit.setText(str(self.db.get_setting('steam_api_key', '')))
        self.steam_id_edit.setText(str(self.db.get_setting('steam_id', '')))
        self.epic_auth_edit.setText(str(self.db.get_setting('epic_auth_code', '')))
        
        # Load Discord settings
        self.news_webhook_edit.setText(str(self.db.get_setting('discord_webhook_url', '')))
        self.task_webhook_edit.setText(str(self.db.get_setting('discord_task_webhook_url', '')))
        self.discord_user_id_edit.setText(str(self.db.get_setting('discord_user_id', '')))
        
        # Load auto settings
        self.auto_send_news_check.setChecked(str(self.db.get_setting('auto_send_news', 'true')).lower() == 'true')
        self.auto_task_reminders_check.setChecked(str(self.db.get_setting('auto_task_reminders', 'true')).lower() == 'true')
        
        # Load paths
        default_steam_path = r"C:\Program Files (x86)\Steam\steam.exe"
        self.steam_path_edit.setText(str(self.db.get_setting('steam_path', default_steam_path)))
    
    def save_gemini(self):
        """Save Gemini API settings"""
        api_key = self.gemini_key_edit.text().strip()
        model = self.gemini_model_combo.currentText()
        
        if api_key and model:
            self.db.set_setting('gemini_api_key', api_key)
            self.db.set_setting('gemini_model', model)
            show_toast(self, "✅ Gemini API settings saved!")
        else:
            QMessageBox.warning(self, "Warning", "Please enter an API key and select a model")
    
    def test_gemini(self):
        """Test Gemini API connection"""
        api_key = self.gemini_key_edit.text().strip()
        model_name = self.gemini_model_combo.currentText()
        
        if not api_key or not model_name:
            QMessageBox.warning(self, "Warning", "Please enter an API key and select a model first")
            return
        
        def test_in_thread():
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                
                response = model.generate_content("Hello, this is a test.")
                
                show_toast(self, f"✅ Gemini API connection successful! Model: {model_name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gemini API test failed: {e}")
        
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def save_steam(self):
        """Save Steam API settings"""
        api_key = self.steam_key_edit.text().strip()
        steam_id = self.steam_id_edit.text().strip()
        
        if api_key and steam_id:
            self.db.set_setting('steam_api_key', api_key)
            self.db.set_setting('steam_id', steam_id)
            show_toast(self, "✅ Steam API settings saved!")
        else:
            QMessageBox.warning(self, "Warning", "Please enter both API key and Steam ID")
    
    def test_steam(self):
        """Test Steam API connection"""
        api_key = self.steam_key_edit.text().strip()
        steam_id = self.steam_id_edit.text().strip()
        
        if not api_key or not steam_id:
            QMessageBox.warning(self, "Warning", "Please enter both API key and Steam ID first")
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
                    show_toast(self, f"✅ Steam API connection successful! Found {game_count} games.")
                else:
                    QMessageBox.critical(self, "Error", "Steam API test failed: Invalid response")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Steam API test failed: {e}")
        
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def get_epic_auth(self):
        """Open Epic Games login page"""
        webbrowser.open("https://legendary.gl/epiclogin")
        QMessageBox.information(self, "Epic Games Login", 
                               "1. Complete the Epic Games login in your browser\n"
                               "2. Copy the 'authorizationCode' value from the JSON response\n"
                               "3. Paste it in the Authorization Code field above\n"
                               "4. Click 'Save'")
    
    def save_epic(self):
        """Save Epic Games authorization code"""
        auth_code = self.epic_auth_edit.text().strip()
        if auth_code:
            self.db.set_setting('epic_auth_code', auth_code)
            show_toast(self, "✅ Epic Games authorization code saved!")
        else:
            QMessageBox.warning(self, "Warning", "Please enter the authorization code")
    
    def test_epic(self):
        """Test Epic Games connection using legendary"""
        auth_code = self.epic_auth_edit.text().strip()
        if not auth_code:
            QMessageBox.warning(self, "Warning", "Please enter and save the authorization code first")
            return
        
        def test_in_thread():
            try:
                import subprocess
                result = subprocess.run(['legendary', 'list'], capture_output=True, text=True, 
                                       encoding='utf-8', errors='ignore', timeout=30)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    game_count = 0
                    for line in lines:
                        if '|' in line and not line.startswith('Legendary'):
                            game_count += 1
                    
                    show_toast(self, f"✅ Epic Games connection successful! Found {game_count} games.")
                else:
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    QMessageBox.critical(self, "Error", f"Epic Games test failed: {error_msg[:200]}")
                        
            except FileNotFoundError:
                QMessageBox.critical(self, "Error", "Legendary CLI not found. Please install legendary first:\npip install legendary-gl")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Epic Games test failed: {e}")
        
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def save_webhook(self):
        """Save Discord news webhook URL"""
        webhook_url = self.news_webhook_edit.text().strip()
        if webhook_url:
            self.db.set_setting('discord_webhook_url', webhook_url)
            show_toast(self, "✅ Discord webhook URL saved!")
        else:
            QMessageBox.warning(self, "Warning", "Please enter a webhook URL")
    
    def test_webhook(self):
        """Test Discord news webhook"""
        webhook_url = self.news_webhook_edit.text().strip()
        if not webhook_url:
            QMessageBox.warning(self, "Warning", "Please enter a webhook URL first")
            return
        
        def test_in_thread():
            try:
                discord_user_id = self.discord_user_id_edit.text().strip()
                ping_text = f"<@{discord_user_id}> " if discord_user_id else ""
                
                payload = {
                    "username": "Dashboard Test",
                    "content": f"{ping_text}🧪 This is a test message from your Personal Dashboard!"
                }
                
                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                
                ping_status = " (with ping)" if discord_user_id else " (no ping - add User ID for pings)"
                show_toast(self, f"✅ Discord webhook test successful{ping_status}!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Discord webhook test failed: {e}")
        
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def save_task_webhook(self):
        """Save Discord task webhook URL"""
        webhook_url = self.task_webhook_edit.text().strip()
        if webhook_url:
            self.db.set_setting('discord_task_webhook_url', webhook_url)
            show_toast(self, "✅ Discord task webhook URL saved!")
        else:
            QMessageBox.warning(self, "Warning", "Please enter a task webhook URL")
    
    def test_task_webhook(self):
        """Test Discord task webhook"""
        webhook_url = self.task_webhook_edit.text().strip()
        if not webhook_url:
            QMessageBox.warning(self, "Warning", "Please enter a task webhook URL first")
            return
        
        def test_in_thread():
            try:
                discord_user_id = self.discord_user_id_edit.text().strip()
                ping_text = f"<@{discord_user_id}> " if discord_user_id else ""
                
                payload = {
                    "username": "Task Reminder Test",
                    "content": f"{ping_text}⏰ This is a test message for task reminders from your Personal Dashboard!"
                }
                
                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                
                ping_status = " (with ping)" if discord_user_id else " (no ping - add User ID for pings)"
                show_toast(self, f"✅ Discord task webhook test successful{ping_status}!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Discord task webhook test failed: {e}")
        
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def test_auto_reminders(self):
        """Test the automatic task reminder system"""
        def test_in_thread():
            try:
                from modules.scheduler import SchedulerManager
                temp_scheduler = SchedulerManager(self.db)
                task_count = temp_scheduler.test_task_reminders()
                
                if task_count > 0:
                    QMessageBox.information(self, "Success", 
                        f"Auto-reminder test successful!\n"
                        f"Sent reminders for {task_count} due tasks.\n\n"
                        f"This is how automatic daily reminders at 9 AM will work.")
                else:
                    QMessageBox.information(self, "Info", 
                        "Auto-reminder test completed.\n"
                        "No tasks are currently due for reminders.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Auto-reminder test failed: {e}")
        
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def save_discord_user_id(self):
        """Save Discord user ID"""
        user_id = self.discord_user_id_edit.text().strip()
        if user_id:
            if user_id.isdigit() and 17 <= len(user_id) <= 19:
                self.db.set_setting('discord_user_id', user_id)
                show_toast(self, "✅ Discord User ID saved!")
            else:
                QMessageBox.warning(self, "Warning", "Invalid Discord User ID. Should be 17-19 digits.")
        else:
            QMessageBox.warning(self, "Warning", "Please enter your Discord User ID")
    
    def save_auto_settings(self):
        """Save automatic notification settings"""
        self.db.set_setting('auto_send_news', str(self.auto_send_news_check.isChecked()).lower())
        self.db.set_setting('auto_task_reminders', str(self.auto_task_reminders_check.isChecked()).lower())
    
    def browse_steam_path(self):
        """Browse for Steam executable"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Steam Executable", 
                                                  r"C:\Program Files (x86)\Steam", 
                                                  "Executable files (*.exe)")
        if file_path:
            self.steam_path_edit.setText(file_path)
    
    def save_steam_path(self):
        """Save Steam path"""
        steam_path = self.steam_path_edit.text().strip()
        if steam_path:
            self.db.set_setting('steam_path', steam_path)
            show_toast(self, "✅ Steam path saved!")
        else:
            QMessageBox.warning(self, "Warning", "Please enter a Steam path")
    
    def export_settings(self):
        """Export all settings to JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Settings", 
                                                  "dashboard_settings.json", 
                                                  "JSON files (*.json)")
        if file_path:
            try:
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT key, value FROM settings")
                settings = {row['key']: row['value'] for row in cursor.fetchall()}
                
                with open(file_path, 'w') as f:
                    json.dump(settings, f, indent=2)
                
                show_toast(self, f"✅ Settings exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export settings: {e}")
    
    def import_settings(self):
        """Import settings from JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Settings", 
                                                  "", "JSON files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    settings = json.load(f)
                
                for key, value in settings.items():
                    self.db.set_setting(key, value)
                
                self.load_settings()
                show_toast(self, f"✅ Settings imported from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import settings: {e}")