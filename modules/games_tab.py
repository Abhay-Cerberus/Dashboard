"""
Game Library Tab
Handles Steam and Epic Games library management
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTreeWidget, QTreeWidgetItem, QTextEdit, QLineEdit,
                            QMessageBox, QTabWidget, QFrame, QGroupBox, QLabel, 
                            QProgressBar, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor


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
import threading
import subprocess
import requests
import random
import json
import logging
import webbrowser
from datetime import datetime

class GamesTab(QWidget):
    # Signals for thread-safe UI updates
    update_import_status = pyqtSignal(str)
    show_import_status = pyqtSignal()
    hide_import_status = pyqtSignal()
    
    def __init__(self, db, main_window):
        super().__init__()
        self.db = db
        self.main_window = main_window
        self.setup_ui()
        self.load_games()
        
        # Connect signals to slots
        self.update_import_status.connect(self._update_import_status_slot)
        self.show_import_status.connect(self._show_import_status_slot)
        self.hide_import_status.connect(self._hide_import_status_slot)
    
    def _update_import_status_slot(self, text):
        """Slot to update import status label text"""
        self.import_status_label.setText(text)
        self.import_status_label.setVisible(True)
    
    def _show_import_status_slot(self):
        """Slot to show import status label"""
        self.import_status_label.setVisible(True)
    
    def _hide_import_status_slot(self):
        """Slot to hide import status label"""
        self.import_status_label.setVisible(False)
    
    def setup_ui(self):
        """Create the modern PyQt games tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
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
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton.danger {
                background-color: #d13438;
            }
            QPushButton.danger:hover {
                background-color: #b02a2e;
            }
            QPushButton.success {
                background-color: #107c10;
            }
            QPushButton.success:hover {
                background-color: #0e6b0e;
            }
            QTreeWidget {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 8px;
                color: white;
                selection-background-color: #0078d4;
                alternate-background-color: #454545;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #555555;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
            }
            QTreeWidget::item:hover {
                background-color: #505050;
            }
            QHeaderView::section {
                background-color: #505050;
                color: white;
                padding: 10px;
                border: none;
                border-right: 1px solid #666666;
                font-weight: bold;
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
            QComboBox {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 8px;
                color: white;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #0078d4;
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
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 6px;
                text-align: center;
                background-color: #404040;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 4px;
            }
        """)
        
        # Controls frame
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(10)
        
        # Left side - Import and utility buttons
        self.import_steam_btn = QPushButton("🎮 Import Steam Library")
        self.import_steam_btn.clicked.connect(self.import_steam_library)
        controls_layout.addWidget(self.import_steam_btn)
        
        self.import_epic_btn = QPushButton("🎯 Import Epic Library")
        self.import_epic_btn.clicked.connect(self.import_epic_library)
        controls_layout.addWidget(self.import_epic_btn)
        
        self.random_game_btn = QPushButton("🎲 Random Game")
        self.random_game_btn.setProperty("class", "success")
        self.random_game_btn.clicked.connect(self.select_random_game)
        controls_layout.addWidget(self.random_game_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_games)
        controls_layout.addWidget(self.refresh_btn)
        
        controls_layout.addStretch()
        
        # Right side - Clear buttons
        self.clear_steam_btn = QPushButton("🗑️ Clear Steam")
        self.clear_steam_btn.setProperty("class", "danger")
        self.clear_steam_btn.clicked.connect(self.clear_steam_games)
        controls_layout.addWidget(self.clear_steam_btn)
        
        self.clear_epic_btn = QPushButton("🗑️ Clear Epic")
        self.clear_epic_btn.setProperty("class", "danger")
        self.clear_epic_btn.clicked.connect(self.clear_epic_games)
        controls_layout.addWidget(self.clear_epic_btn)
        
        layout.addWidget(controls_frame)
        
        # Import status label
        self.import_status_label = QLabel("")
        self.import_status_label.setVisible(False)
        self.import_status_label.setStyleSheet("""
            QLabel {
                background-color: #404040;
                border: 2px solid #0078d4;
                border-radius: 6px;
                padding: 8px;
                color: #0078d4;
                font-weight: bold;
                text-align: center;
            }
        """)
        layout.addWidget(self.import_status_label)
        
        # Search and filter controls
        search_filter_frame = QFrame()
        search_filter_layout = QHBoxLayout(search_filter_frame)
        
        # Search box
        search_filter_layout.addWidget(QLabel("🔍 Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search games...")
        self.search_box.textChanged.connect(self.filter_games)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 8px;
                color: white;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        search_filter_layout.addWidget(self.search_box)
        
        search_filter_layout.addWidget(QLabel("Platform:"))
        self.platform_filter = QComboBox()
        self.platform_filter.addItems(["All", "Steam", "Epic"])
        self.platform_filter.currentTextChanged.connect(self.filter_games)
        search_filter_layout.addWidget(self.platform_filter)
        
        search_filter_layout.addWidget(QLabel("Sort by:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name", "Platform", "Playtime", "Achievements", "Achievement %"])
        self.sort_combo.currentTextChanged.connect(self.sort_games)
        search_filter_layout.addWidget(self.sort_combo)
        
        search_filter_layout.addStretch()
        layout.addWidget(search_filter_frame)
        
        # Tab widget for incomplete/complete/100% games
        self.games_tab_widget = QTabWidget()
        
        # Incomplete games tab
        incomplete_widget = QWidget()
        incomplete_layout = QVBoxLayout(incomplete_widget)
        
        # Multi-select controls for incomplete games
        incomplete_controls = QFrame()
        incomplete_controls_layout = QHBoxLayout(incomplete_controls)
        
        self.mark_complete_btn = QPushButton("✅ Mark as Complete")
        self.mark_complete_btn.setProperty("class", "success")
        self.mark_complete_btn.clicked.connect(self.mark_games_complete)
        self.mark_complete_btn.setEnabled(False)
        incomplete_controls_layout.addWidget(self.mark_complete_btn)
        
        incomplete_controls_layout.addStretch()
        incomplete_layout.addWidget(incomplete_controls)
        
        # Incomplete games tree
        self.incomplete_games_tree = QTreeWidget()
        self.incomplete_games_tree.setHeaderLabels(["Name", "Platform", "Playtime (hrs)", "Achievements"])
        self.incomplete_games_tree.setAlternatingRowColors(True)
        self.incomplete_games_tree.setRootIsDecorated(False)
        self.incomplete_games_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.incomplete_games_tree.setColumnWidth(0, 300)
        self.incomplete_games_tree.setColumnWidth(1, 100)
        self.incomplete_games_tree.setColumnWidth(2, 120)
        self.incomplete_games_tree.setColumnWidth(3, 120)
        self.incomplete_games_tree.itemSelectionChanged.connect(self.on_incomplete_selection_changed)
        self.incomplete_games_tree.itemDoubleClicked.connect(self.launch_selected_game)
        incomplete_layout.addWidget(self.incomplete_games_tree)
        
        # Complete games tab
        complete_widget = QWidget()
        complete_layout = QVBoxLayout(complete_widget)
        
        # Multi-select controls for complete games
        complete_controls = QFrame()
        complete_controls_layout = QHBoxLayout(complete_controls)
        
        self.mark_incomplete_btn = QPushButton("↩️ Mark as Incomplete")
        self.mark_incomplete_btn.clicked.connect(self.mark_games_incomplete)
        self.mark_incomplete_btn.setEnabled(False)
        complete_controls_layout.addWidget(self.mark_incomplete_btn)
        
        complete_controls_layout.addStretch()
        complete_layout.addWidget(complete_controls)
        
        # Complete games tree
        self.complete_games_tree = QTreeWidget()
        self.complete_games_tree.setHeaderLabels(["Name", "Platform", "Playtime (hrs)", "Achievements"])
        self.complete_games_tree.setAlternatingRowColors(True)
        self.complete_games_tree.setRootIsDecorated(False)
        self.complete_games_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.complete_games_tree.setColumnWidth(0, 300)
        self.complete_games_tree.setColumnWidth(1, 100)
        self.complete_games_tree.setColumnWidth(2, 120)
        self.complete_games_tree.setColumnWidth(3, 120)
        self.complete_games_tree.itemSelectionChanged.connect(self.on_complete_selection_changed)
        self.complete_games_tree.itemDoubleClicked.connect(self.launch_selected_game)
        complete_layout.addWidget(self.complete_games_tree)
        
        # 100% Achievement games tab
        hundred_percent_widget = QWidget()
        hundred_percent_layout = QVBoxLayout(hundred_percent_widget)
        
        # 100% games tree
        self.hundred_percent_tree = QTreeWidget()
        self.hundred_percent_tree.setHeaderLabels(["Name", "Platform", "Playtime (hrs)", "Achievements"])
        self.hundred_percent_tree.setAlternatingRowColors(True)
        self.hundred_percent_tree.setRootIsDecorated(False)
        self.hundred_percent_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.hundred_percent_tree.setColumnWidth(0, 300)
        self.hundred_percent_tree.setColumnWidth(1, 100)
        self.hundred_percent_tree.setColumnWidth(2, 120)
        self.hundred_percent_tree.setColumnWidth(3, 120)
        self.hundred_percent_tree.itemDoubleClicked.connect(self.launch_selected_game)
        hundred_percent_layout.addWidget(self.hundred_percent_tree)
        
        # Add tabs
        self.games_tab_widget.addTab(incomplete_widget, "📋 Incomplete Games")
        self.games_tab_widget.addTab(complete_widget, "✅ Complete Games")
        self.games_tab_widget.addTab(hundred_percent_widget, "🏆 100% Achievement")
        
        layout.addWidget(self.games_tab_widget)
    
    def on_incomplete_selection_changed(self):
        """Handle selection change in incomplete games tree"""
        selected_items = self.incomplete_games_tree.selectedItems()
        self.mark_complete_btn.setEnabled(len(selected_items) > 0)
    
    def on_complete_selection_changed(self):
        """Handle selection change in complete games tree"""
        selected_items = self.complete_games_tree.selectedItems()
        self.mark_incomplete_btn.setEnabled(len(selected_items) > 0)
    
    def mark_games_complete(self):
        """Mark selected games as complete"""
        selected_items = self.incomplete_games_tree.selectedItems()
        if not selected_items:
            return
        
        try:
            # Use a single transaction for all games
            cursor = self.db.conn.cursor()
            for item in selected_items:
                game_id = item.data(0, Qt.ItemDataRole.UserRole)
                if game_id:
                    cursor.execute("UPDATE games SET is_completed = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (True, game_id))
            self.db.conn.commit()
            
            self.load_games()
            show_toast(self, f"✅ Marked {len(selected_items)} game(s) as complete!")
            
        except Exception as e:
            try:
                self.db.conn.rollback()
            except:
                pass
            QMessageBox.critical(self, "Error", f"Failed to mark games as completed: {e}")
    
    def mark_games_incomplete(self):
        """Mark selected games as incomplete"""
        selected_items = self.complete_games_tree.selectedItems()
        if not selected_items:
            return
        
        try:
            # Use a single transaction for all games
            cursor = self.db.conn.cursor()
            for item in selected_items:
                game_id = item.data(0, Qt.ItemDataRole.UserRole)
                if game_id:
                    cursor.execute("UPDATE games SET is_completed = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (False, game_id))
            self.db.conn.commit()
            
            self.load_games()
            show_toast(self, f"✅ Marked {len(selected_items)} game(s) as incomplete!")
            
        except Exception as e:
            try:
                self.db.conn.rollback()
            except:
                pass
            QMessageBox.critical(self, "Error", f"Failed to mark games as incomplete: {e}")
        
        self.load_games()
        show_toast(self, f"↩️ Marked {len(selected_items)} game(s) as incomplete!")
    
    def load_games(self):
        """Load games from database"""
        self.incomplete_games_tree.clear()
        self.complete_games_tree.clear()
        self.hundred_percent_tree.clear()
        
        games = self.db.get_games()
        
        for game in games:
            # Format playtime (convert minutes to hours)
            playtime_hours = game['playtime'] / 60.0 if game['playtime'] else 0
            playtime = f"{playtime_hours:.1f}h" if playtime_hours else "0h"
            
            # Format achievements
            if game['achievements_total'] and game['achievements_total'] > 0:
                achievements = f"{game['achievements_unlocked']}/{game['achievements_total']}"
                completion_rate = (game['achievements_unlocked'] / game['achievements_total']) * 100
                achievements += f" ({completion_rate:.1f}%)"
                is_hundred_percent = completion_rate == 100.0
            else:
                achievements = "No achievements"
                completion_rate = 0
                is_hundred_percent = False
            
            # Create tree item
            item = QTreeWidgetItem([
                game['name'],
                game['platform'],
                playtime,
                achievements
            ])
            
            # Store game ID for database operations
            item.setData(0, Qt.ItemDataRole.UserRole, game['id'])
            
            # Check if game is marked as complete in database
            is_complete = game['is_completed'] if 'is_completed' in game.keys() else False
            
            # Add to 100% tab if it has 100% achievements
            if is_hundred_percent:
                hundred_item = QTreeWidgetItem([
                    game['name'],
                    game['platform'],
                    playtime,
                    achievements
                ])
                hundred_item.setData(0, Qt.ItemDataRole.UserRole, game['id'])
                self.hundred_percent_tree.addTopLevelItem(hundred_item)
                # Color 100% games gold
                for i in range(4):
                    hundred_item.setBackground(i, QColor("#5a4d2d"))  # Dark gold
            
            # Add to appropriate completion tree
            if is_complete:
                self.complete_games_tree.addTopLevelItem(item)
                # Color complete games green
                for i in range(4):
                    item.setBackground(i, QColor("#2d5a2d"))
            else:
                self.incomplete_games_tree.addTopLevelItem(item)
                # Color code incomplete games based on achievement completion
                if completion_rate >= 80:
                    for i in range(4):
                        item.setBackground(i, QColor("#5a5a2d"))  # Dark yellow for high completion
        
        # Apply current filters
        self.filter_games()
    
    def filter_games(self):
        """Filter games by search text and platform"""
        search_text = self.search_box.text().lower()
        platform_filter = self.platform_filter.currentText()
        
        # Filter incomplete games
        for i in range(self.incomplete_games_tree.topLevelItemCount()):
            item = self.incomplete_games_tree.topLevelItem(i)
            name_match = search_text in item.text(0).lower()
            platform_match = platform_filter == "All" or item.text(1) == platform_filter
            item.setHidden(not (name_match and platform_match))
        
        # Filter complete games
        for i in range(self.complete_games_tree.topLevelItemCount()):
            item = self.complete_games_tree.topLevelItem(i)
            name_match = search_text in item.text(0).lower()
            platform_match = platform_filter == "All" or item.text(1) == platform_filter
            item.setHidden(not (name_match and platform_match))
        
        # Filter 100% games
        for i in range(self.hundred_percent_tree.topLevelItemCount()):
            item = self.hundred_percent_tree.topLevelItem(i)
            name_match = search_text in item.text(0).lower()
            platform_match = platform_filter == "All" or item.text(1) == platform_filter
            item.setHidden(not (name_match and platform_match))
    
    def sort_games(self):
        """Sort games by selected criteria"""
        sort_by = self.sort_combo.currentText()
        
        if sort_by == "Achievement %":
            # Custom sort by achievement percentage
            self.sort_by_achievement_percentage()
        else:
            # Map sort criteria to column indices
            sort_columns = {
                "Name": 0,
                "Platform": 1,
                "Playtime": 2,
                "Achievements": 3
            }
            
            column = sort_columns.get(sort_by, 0)
            
            # Sort all trees
            self.incomplete_games_tree.sortItems(column, Qt.SortOrder.AscendingOrder)
            self.complete_games_tree.sortItems(column, Qt.SortOrder.AscendingOrder)
            self.hundred_percent_tree.sortItems(column, Qt.SortOrder.AscendingOrder)
    
    def sort_by_achievement_percentage(self):
        """Sort games by achievement completion percentage"""
        # Instead of moving items, just reload the games with custom sorting
        # This is safer and avoids Qt object deletion issues
        self.load_games_sorted_by_achievement_percentage()
    
    def load_games_sorted_by_achievement_percentage(self):
        """Load games sorted by achievement completion percentage"""
        self.incomplete_games_tree.clear()
        self.complete_games_tree.clear()
        self.hundred_percent_tree.clear()
        
        games = self.db.get_games()
        
        # Calculate achievement percentages and sort
        games_with_percentage = []
        for game in games:
            if game['achievements_total'] and game['achievements_total'] > 0:
                percentage = (game['achievements_unlocked'] / game['achievements_total']) * 100
            else:
                percentage = 0
            games_with_percentage.append((game, percentage))
        
        # Sort by percentage (descending - highest completion first)
        games_with_percentage.sort(key=lambda x: x[1], reverse=True)
        
        # Add games to appropriate trees
        for game, percentage in games_with_percentage:
            # Format playtime (convert minutes to hours)
            playtime_hours = game['playtime'] / 60.0 if game['playtime'] else 0
            playtime = f"{playtime_hours:.1f}h" if playtime_hours else "0h"
            
            # Format achievements
            if game['achievements_total'] and game['achievements_total'] > 0:
                achievements = f"{game['achievements_unlocked']}/{game['achievements_total']}"
                achievements += f" ({percentage:.1f}%)"
                is_hundred_percent = percentage == 100.0
            else:
                achievements = "No achievements"
                is_hundred_percent = False
            
            # Create tree item
            item = QTreeWidgetItem([
                game['name'],
                game['platform'],
                playtime,
                achievements
            ])
            
            # Store game ID for database operations
            item.setData(0, Qt.ItemDataRole.UserRole, game['id'])
            
            # Add to 100% tab if it has 100% achievements
            if is_hundred_percent:
                hundred_item = QTreeWidgetItem([
                    game['name'],
                    game['platform'],
                    playtime,
                    achievements
                ])
                hundred_item.setData(0, Qt.ItemDataRole.UserRole, game['id'])
                self.hundred_percent_tree.addTopLevelItem(hundred_item)
                # Color 100% games gold
                for i in range(4):
                    hundred_item.setBackground(i, QColor("#5a4d2d"))  # Dark gold
            
            # Check if game is marked as complete in database
            is_complete = game['is_completed'] if 'is_completed' in game.keys() else False
            
            # Add to appropriate completion tree
            if is_complete:
                self.complete_games_tree.addTopLevelItem(item)
                # Color complete games green
                for i in range(4):
                    item.setBackground(i, QColor("#2d5a2d"))
            else:
                self.incomplete_games_tree.addTopLevelItem(item)
                # Color code incomplete games based on achievement completion
                if percentage >= 80:
                    for i in range(4):
                        item.setBackground(i, QColor("#5a5a2d"))  # Dark yellow for high completion
        
        # Apply current filters
        self.filter_games()
    
    def import_steam_library(self):
        """Import Steam library"""
        steam_api_key = self.db.get_setting('steam_api_key')
        steam_id = self.db.get_setting('steam_id')
        
        if not steam_api_key or not steam_id:
            QMessageBox.warning(self, "Configuration Required", 
                              "Please configure Steam API key and Steam ID in Settings first.")
            return
        
        # Don't show initial fetching message, wait for count
        
        def import_in_thread():
            try:
                # Get owned games
                url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
                params = {
                    'key': steam_api_key,
                    'steamid': steam_id,
                    'format': 'json',
                    'include_appinfo': True,
                    'include_played_free_games': True
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'response' not in data or 'games' not in data['response']:
                    raise Exception("Invalid response from Steam API")
                
                games = data['response']['games']
                imported_count = 0
                total_games = len(games)
                processed_count = 0
                
                # Show initial count immediately
                self.update_import_status.emit(f"🔄 Processing Steam games: 0/{total_games}")
                
                for game in games:
                    processed_count += 1
                    # Update counter in main thread
                    self.update_import_status.emit(f"🔄 Processing Steam games: {processed_count}/{total_games}")
                    app_id = game['appid']
                    name = game['name']
                    playtime_minutes = game.get('playtime_forever', 0)
                    playtime_hours = playtime_minutes / 60.0
                    
                    # Get achievement data
                    achievements_unlocked = 0
                    achievements_total = 0
                    
                    try:
                        # Get player achievements
                        ach_url = "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/"
                        ach_params = {
                            'key': steam_api_key,
                            'steamid': steam_id,
                            'appid': app_id
                        }
                        
                        ach_response = requests.get(ach_url, params=ach_params, timeout=10)
                        if ach_response.status_code == 200:
                            ach_data = ach_response.json()
                            if 'playerstats' in ach_data and 'achievements' in ach_data['playerstats']:
                                achievements = ach_data['playerstats']['achievements']
                                achievements_total = len(achievements)
                                achievements_unlocked = sum(1 for ach in achievements if ach.get('achieved', 0) == 1)
                    except:
                        pass  # Achievement data is optional
                    
                    # Check if this is a new game
                    cursor = self.db.conn.cursor()
                    cursor.execute("SELECT id FROM games WHERE appid = ? AND platform = ?", (app_id, 'Steam'))
                    existing = cursor.fetchone()
                    
                    # Add or update game in database (playtime in minutes)
                    game_id = self.db.add_or_update_game(app_id, name, 'Steam', 
                                                        playtime=playtime_minutes,
                                                        achievements_unlocked=achievements_unlocked,
                                                        achievements_total=achievements_total,
                                                        has_achievements=(achievements_total > 0))
                    
                    # Only count as imported if it's a new game
                    if not existing and game_id:
                        imported_count += 1
                
                # Schedule UI updates in main thread
                self.update_import_status.emit(f"✅ Imported {imported_count} out of {total_games} Steam games!")
                QTimer.singleShot(2000, lambda: self.hide_import_status.emit())  # Hide after 2 seconds
                QTimer.singleShot(0, lambda: self.load_games())
                QTimer.singleShot(0, lambda: show_toast(self, f"✅ Imported {imported_count} new Steam games!"))
                
            except Exception as e:
                self.hide_import_status.emit()
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Failed to import Steam library: {e}"))
        
        threading.Thread(target=import_in_thread, daemon=True).start()
    
    def import_epic_library(self):
        """Import Epic Games library using legendary"""
        # Don't show initial fetching message, wait for count
        
        def import_in_thread():
            try:
                # Run legendary list command with shorter timeout
                result = subprocess.run(['legendary', 'list'], capture_output=True, text=True, 
                                       encoding='utf-8', errors='ignore', timeout=30)
                
                if result.returncode != 0:
                    raise Exception(f"Legendary command failed: {result.stderr}")
                
                # Parse legendary output
                lines = result.stdout.split('\n')
                imported_count = 0
                
                # Find valid game lines (start with ' * ' and contain 'App name:')
                valid_lines = [line for line in lines if line.strip().startswith('*') and 'App name:' in line]
                total_games = len(valid_lines)
                processed_count = 0
                
                # Show initial count immediately
                self.update_import_status.emit(f"🔄 Processing Epic games: 0/{total_games}")
                
                for line in lines:
                    if line.strip().startswith('*') and 'App name:' in line:
                        processed_count += 1
                        # Update counter in main thread
                        self.update_import_status.emit(f"🔄 Processing Epic games: {processed_count}/{total_games}")
                        
                        try:
                            # Parse format: * "Game Name" (App name: app_id | Version: version)
                            # Extract game name (between * and first parenthesis)
                            name_part = line.split('(App name:')[0].strip()
                            if name_part.startswith('*'):
                                name = name_part[1:].strip().strip('"')
                            
                            # Extract version info to check for UE assets
                            version_part = ""
                            if '| Version:' in line:
                                version_part = line.split('| Version:')[1].strip().rstrip(')')
                            
                            # Skip UE4/UE5 assets and engine content
                            skip_terms_name = [
                                'unreal engine', 'ue4', 'ue5', 'marketplace', 
                                'asset pack', 'content pack', 'sample project',
                                'lyra starter game', 'pixel streaming demo', 'stack o bot',
                                'slay animation sample', 'virtual studio', 'unreal learning kit'
                            ]
                            
                            skip_terms_version = [
                                '+++ue4+dev-marketplace', '+++ue5+dev-marketplace',
                                '+++ue4+release', '+++ue5+release',
                                'dev-marketplace-windows', 'release-5.', 'release-4.'
                            ]
                            
                            # Check name for skip terms
                            if any(skip_term in name.lower() for skip_term in skip_terms_name):
                                continue
                                
                            # Check version for UE marketplace/engine indicators
                            if any(skip_term in version_part.lower() for skip_term in skip_terms_version):
                                continue
                            
                            # Extract app_id (between 'App name:' and '|')
                            app_name_part = line.split('App name:')[1].split('|')[0].strip()
                            app_id = app_name_part
                            
                            # Check if this is a new game
                            cursor = self.db.conn.cursor()
                            cursor.execute("SELECT id FROM games WHERE appid = ? AND platform = ?", (app_id, 'Epic'))
                            existing = cursor.fetchone()
                            
                            # Epic Games doesn't provide playtime/achievement data via legendary
                            # So we'll use default values
                            game_id = self.db.add_or_update_game(app_id, name, 'Epic', 
                                                                playtime=0, 
                                                                achievements_unlocked=0, 
                                                                achievements_total=0,
                                                                has_achievements=False)
                            
                            # Only count as imported if it's a new game
                            if not existing and game_id:
                                imported_count += 1
                                
                        except Exception as e:
                            print(f"Error processing Epic game line: {e}")
                            continue
                
                # Schedule UI updates in main thread
                self.update_import_status.emit(f"✅ Imported {imported_count} out of {total_games} Epic games!")
                QTimer.singleShot(2000, lambda: self.hide_import_status.emit())  # Hide after 2 seconds
                QTimer.singleShot(0, lambda: self.load_games())
                QTimer.singleShot(0, lambda: show_toast(self, f"✅ Imported {imported_count} new Epic Games!"))
                
            except FileNotFoundError:
                self.hide_import_status.emit()
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", 
                                   "Legendary CLI not found. Please install legendary first:\npip install legendary-gl"))
            except Exception as e:
                self.hide_import_status.emit()
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Failed to import Epic library: {e}"))
        
        threading.Thread(target=import_in_thread, daemon=True).start()
    
    def select_random_game(self):
        """Select a random game from the library and offer to launch it"""
        # Get incomplete games only for random selection
        incomplete_games = self.db.get_games_by_completion(completed=False)
        if not incomplete_games:
            show_toast(self, "ℹ️ No incomplete games found in library. Import some games first!")
            return
        
        random_game = random.choice(incomplete_games)
        
        # Format playtime
        playtime_hours = random_game['playtime'] / 60.0 if random_game['playtime'] else 0
        playtime = f"{playtime_hours:.1f} hours" if playtime_hours else "No playtime recorded"
        
        # Format achievements
        if random_game['achievements_total'] and random_game['achievements_total'] > 0:
            completion = (random_game['achievements_unlocked'] / random_game['achievements_total']) * 100
            achievements = f"{random_game['achievements_unlocked']}/{random_game['achievements_total']} ({completion:.1f}%)"
        else:
            achievements = "No achievements"
        
        # Create message box with launch option
        message = f"� Racndom Game Selected!\n\n"
        message += f"🎮 Game: {random_game['name']}\n"
        message += f"🏷️ Platform: {random_game['platform']}\n"
        message += f"⏱️ Playtime: {playtime}\n"
        message += f"🏆 Achievements: {achievements}\n\n"
        message += "Would you like to launch this game?"
        
        reply = QMessageBox.question(self, "Random Game", message,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.launch_game(random_game)
        else:
            show_toast(self, f"🎲 Random game selected: {random_game['name']}")
    
    def launch_selected_game(self):
        """Launch the currently selected game"""
        # Determine which tree has the selection
        current_item = None
        if self.incomplete_games_tree.currentItem():
            current_item = self.incomplete_games_tree.currentItem()
        elif self.complete_games_tree.currentItem():
            current_item = self.complete_games_tree.currentItem()
        elif self.hundred_percent_tree.currentItem():
            current_item = self.hundred_percent_tree.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a game to launch")
            return
        
        game_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        # Get game from database
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM games WHERE id = ?", (game_id,))
        game = cursor.fetchone()
        
        if game:
            self.launch_game(game)
    
    def launch_game(self, game):
        """Launch a game based on its platform"""
        try:
            if game['platform'] == 'Steam':
                self.launch_steam_game(game['appid'])
            elif game['platform'] == 'Epic Games':
                self.launch_epic_game(game['appid'])
            else:
                QMessageBox.warning(self, "Warning", f"Launching {game['platform']} games is not supported yet")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch {game['name']}: {e}")
    
    def launch_steam_game(self, app_id):
        """Launch a Steam game using steam:// protocol"""
        steam_url = f"steam://launch/{app_id}"
        webbrowser.open(steam_url)
        show_toast(self, f"🚀 Launching Steam game (App ID: {app_id})")
    
    def launch_epic_game(self, app_id):
        """Launch an Epic Games game using legendary"""
        def launch_in_thread():
            try:
                # Use legendary to launch the game
                result = subprocess.run(['legendary', 'launch', app_id], 
                                       capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    QTimer.singleShot(0, lambda: show_toast(self, f"🚀 Launching Epic game: {app_id}"))
                else:
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", 
                                       f"Failed to launch Epic game: {error_msg[:200]}"))
                
            except FileNotFoundError:
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", 
                                   "Legendary CLI not found. Please install legendary first:\npip install legendary-gl"))
            except Exception as e:
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Failed to launch Epic game: {e}"))
        
        threading.Thread(target=launch_in_thread, daemon=True).start()
    
    def clear_steam_games(self):
        """Clear all Steam games from database"""
        reply = QMessageBox.question(self, "Confirm", "Delete all Steam games from library?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_all_games('Steam')
                self.load_games()
                show_toast(self, "✅ Steam games cleared successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear Steam games: {e}")
    
    def clear_epic_games(self):
        """Clear all Epic Games from database"""
        reply = QMessageBox.question(self, "Confirm", "Delete all Epic Games from library?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Clear both "Epic" and "Epic Games" to handle any inconsistencies
                cursor = self.db.conn.cursor()
                cursor.execute("DELETE FROM games WHERE platform IN ('Epic', 'Epic Games')")
                self.db.conn.commit()
                
                self.load_games()
                show_toast(self, "✅ Epic Games cleared successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear Epic Games: {e}")