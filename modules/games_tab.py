"""
Game Library Tab
Handles Steam and Epic Games library management
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import requests
import random
import json
import logging
from datetime import datetime

class GamesTab:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        
        self.frame = ttk.Frame(parent)
        self.create_widgets()
        self.load_games()
    
    def create_widgets(self):
        """Create the games tab widgets"""
        # Main container
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left side - Import and utility buttons
        left_buttons = ttk.Frame(controls_frame)
        left_buttons.pack(side=tk.LEFT)
        
        ttk.Button(left_buttons, text="Import Steam Library", command=self.import_steam_library).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_buttons, text="Import Epic Library", command=self.import_epic_library).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_buttons, text="Random Game", command=self.select_random_game).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_buttons, text="Refresh", command=self.load_games).pack(side=tk.LEFT, padx=(0, 5))
        
        # Right side - Clear buttons
        right_buttons = ttk.Frame(controls_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        ttk.Button(right_buttons, text="Clear Steam Games", command=self.clear_steam_games).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(right_buttons, text="Clear Epic Games", command=self.clear_epic_games).pack(side=tk.LEFT, padx=(5, 0))
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(action_frame, text="Mark Selected as Completed", command=self.mark_game_completed).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Mark Selected as Incomplete", command=self.mark_game_incomplete).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Mark Selected as 100%", command=self.mark_game_hundred_percent).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(action_frame, text="(Use Ctrl+Click or Shift+Click to select multiple games)").pack(side=tk.LEFT, padx=(10, 0))
        
        # Filter frame
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Platform:").pack(side=tk.LEFT, padx=(0, 5))
        self.platform_var = tk.StringVar(value="All")
        platform_combo = ttk.Combobox(filter_frame, textvariable=self.platform_var, 
                                     values=["All", "Steam", "Epic"], state="readonly", width=10)
        platform_combo.pack(side=tk.LEFT, padx=(0, 10))
        platform_combo.bind("<<ComboboxSelected>>", self.filter_games)
        
        ttk.Label(filter_frame, text="Sort by:").pack(side=tk.LEFT, padx=(0, 5))
        self.sort_var = tk.StringVar(value="Completion")
        sort_combo = ttk.Combobox(filter_frame, textvariable=self.sort_var,
                                 values=["Name", "Platform", "Playtime", "Achievements", "Completion"], 
                                 state="readonly", width=12)
        sort_combo.pack(side=tk.LEFT, padx=(0, 10))
        sort_combo.bind("<<ComboboxSelected>>", self.sort_games)
        
        ttk.Button(filter_frame, text="Clear Filters", command=self.clear_filters).pack(side=tk.LEFT, padx=(10, 0))
        
        # Create notebook for incomplete/completed games
        self.games_notebook = ttk.Notebook(main_frame)
        self.games_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Incomplete games tab
        incomplete_frame = ttk.Frame(self.games_notebook)
        self.games_notebook.add(incomplete_frame, text="Incomplete Games")
        
        # Treeview for incomplete games
        columns = ("platform", "playtime", "achievements", "completion", "last_played")
        self.incomplete_tree = ttk.Treeview(incomplete_frame, columns=columns, show="tree headings", selectmode="extended")
        
        # Configure columns
        self.incomplete_tree.heading("#0", text="Game Name")
        self.incomplete_tree.heading("platform", text="Platform")
        self.incomplete_tree.heading("playtime", text="Playtime (hrs)")
        self.incomplete_tree.heading("achievements", text="Achievements")
        self.incomplete_tree.heading("completion", text="Completion %")
        self.incomplete_tree.heading("last_played", text="Last Played")
        
        self.incomplete_tree.column("#0", width=250)
        self.incomplete_tree.column("platform", width=80)
        self.incomplete_tree.column("playtime", width=100)
        self.incomplete_tree.column("achievements", width=120)
        self.incomplete_tree.column("completion", width=100)
        self.incomplete_tree.column("last_played", width=120)
        
        # Scrollbar for incomplete games
        incomplete_scroll = ttk.Scrollbar(incomplete_frame, orient=tk.VERTICAL, command=self.incomplete_tree.yview)
        self.incomplete_tree.configure(yscrollcommand=incomplete_scroll.set)
        
        self.incomplete_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        incomplete_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Completed games tab
        completed_frame = ttk.Frame(self.games_notebook)
        self.games_notebook.add(completed_frame, text="Completed Games")
        
        # Treeview for completed games
        self.completed_tree = ttk.Treeview(completed_frame, columns=columns, show="tree headings", selectmode="extended")
        
        # Configure columns (same as incomplete)
        self.completed_tree.heading("#0", text="Game Name")
        self.completed_tree.heading("platform", text="Platform")
        self.completed_tree.heading("playtime", text="Playtime (hrs)")
        self.completed_tree.heading("achievements", text="Achievements")
        self.completed_tree.heading("completion", text="Completion %")
        self.completed_tree.heading("last_played", text="Last Played")
        
        self.completed_tree.column("#0", width=250)
        self.completed_tree.column("platform", width=80)
        self.completed_tree.column("playtime", width=100)
        self.completed_tree.column("achievements", width=120)
        self.completed_tree.column("completion", width=100)
        self.completed_tree.column("last_played", width=120)
        
        # Scrollbar for completed games
        completed_scroll = ttk.Scrollbar(completed_frame, orient=tk.VERTICAL, command=self.completed_tree.yview)
        self.completed_tree.configure(yscrollcommand=completed_scroll.set)
        
        self.completed_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        completed_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 100% Games tab
        hundred_percent_frame = ttk.Frame(self.games_notebook)
        self.games_notebook.add(hundred_percent_frame, text="100% Games")
        
        # Treeview for 100% games
        self.hundred_percent_tree = ttk.Treeview(hundred_percent_frame, columns=columns, show="tree headings", selectmode="extended")
        
        # Configure columns (same as others)
        self.hundred_percent_tree.heading("#0", text="Game Name")
        self.hundred_percent_tree.heading("platform", text="Platform")
        self.hundred_percent_tree.heading("playtime", text="Playtime (hrs)")
        self.hundred_percent_tree.heading("achievements", text="Achievements")
        self.hundred_percent_tree.heading("completion", text="Completion %")
        self.hundred_percent_tree.heading("last_played", text="Last Played")
        
        self.hundred_percent_tree.column("#0", width=250)
        self.hundred_percent_tree.column("platform", width=80)
        self.hundred_percent_tree.column("playtime", width=100)
        self.hundred_percent_tree.column("achievements", width=120)
        self.hundred_percent_tree.column("completion", width=100)
        self.hundred_percent_tree.column("last_played", width=120)
        
        # Scrollbar for 100% games
        hundred_percent_scroll = ttk.Scrollbar(hundred_percent_frame, orient=tk.VERTICAL, command=self.hundred_percent_tree.yview)
        self.hundred_percent_tree.configure(yscrollcommand=hundred_percent_scroll.set)
        
        self.hundred_percent_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hundred_percent_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Context menus
        self.incomplete_menu = tk.Menu(self.frame, tearoff=0)
        self.incomplete_menu.add_command(label="Launch Game", command=self.launch_selected_game)
        self.incomplete_menu.add_separator()
        self.incomplete_menu.add_command(label="Mark as Completed", command=self.mark_game_completed)
        self.incomplete_menu.add_command(label="View Details", command=self.show_game_details)
        
        self.completed_menu = tk.Menu(self.frame, tearoff=0)
        self.completed_menu.add_command(label="Launch Game", command=self.launch_selected_game)
        self.completed_menu.add_separator()
        self.completed_menu.add_command(label="Mark as Incomplete", command=self.mark_game_incomplete)
        self.completed_menu.add_command(label="View Details", command=self.show_game_details)
        
        self.hundred_percent_menu = tk.Menu(self.frame, tearoff=0)
        self.hundred_percent_menu.add_command(label="Launch Game", command=self.launch_selected_game)
        self.hundred_percent_menu.add_separator()
        self.hundred_percent_menu.add_command(label="Mark as Incomplete", command=self.mark_game_incomplete)
        self.hundred_percent_menu.add_command(label="View Details", command=self.show_game_details)
        
        # Bind events
        self.incomplete_tree.bind("<Button-3>", lambda e: self.show_context_menu(e, "incomplete"))
        self.incomplete_tree.bind("<Double-1>", self.launch_selected_game)
        self.incomplete_tree.bind("<Return>", lambda e: self.mark_game_completed())  # Enter key to mark completed
        self.incomplete_tree.bind("<Delete>", lambda e: self.mark_game_completed())  # Delete key to mark completed
        
        self.completed_tree.bind("<Button-3>", lambda e: self.show_context_menu(e, "completed"))
        self.completed_tree.bind("<Double-1>", self.launch_selected_game)
        self.completed_tree.bind("<Return>", lambda e: self.mark_game_incomplete())  # Enter key to mark incomplete
        self.completed_tree.bind("<Delete>", lambda e: self.mark_game_incomplete())  # Delete key to mark incomplete
        
        self.hundred_percent_tree.bind("<Button-3>", lambda e: self.show_context_menu(e, "hundred_percent"))
        self.hundred_percent_tree.bind("<Double-1>", self.launch_selected_game)
        self.hundred_percent_tree.bind("<Return>", lambda e: self.mark_game_incomplete())  # Enter key to mark incomplete
        self.hundred_percent_tree.bind("<Delete>", lambda e: self.mark_game_incomplete())  # Delete key to mark incomplete
    
    def load_games(self):
        """Load games from database into all trees"""
        # Clear existing items
        for item in self.incomplete_tree.get_children():
            self.incomplete_tree.delete(item)
        for item in self.completed_tree.get_children():
            self.completed_tree.delete(item)
        for item in self.hundred_percent_tree.get_children():
            self.hundred_percent_tree.delete(item)
        
        # Get filter values
        platform_filter = self.platform_var.get()
        
        # Load games by category
        if platform_filter == "All":
            incomplete_games = self.db.get_games_by_completion(completed=False)
            completed_games = self.db.get_games_by_completion(completed=True)
            hundred_percent_games = self.db.get_hundred_percent_games()
        else:
            incomplete_games = self.db.get_games_by_completion(completed=False, platform=platform_filter)
            completed_games = self.db.get_games_by_completion(completed=True, platform=platform_filter)
            hundred_percent_games = self.db.get_hundred_percent_games(platform=platform_filter)
        
        # Sort games
        incomplete_games = self.sort_games_list(incomplete_games)
        completed_games = self.sort_games_list(completed_games)
        hundred_percent_games = self.sort_games_list(hundred_percent_games)
        
        # Add incomplete games to tree
        for game in incomplete_games:
            self.add_game_to_tree(game, self.incomplete_tree)
        
        # Add completed games to tree
        for game in completed_games:
            self.add_game_to_tree(game, self.completed_tree)
        
        # Add 100% games to tree
        for game in hundred_percent_games:
            self.add_game_to_tree(game, self.hundred_percent_tree)
    
    def add_game_to_tree(self, game, tree):
        """Add a game to the specified tree with proper formatting"""
        # Format playtime
        playtime_hours = game['playtime'] / 60 if game['playtime'] else 0
        playtime_str = f"{playtime_hours:.1f}" if playtime_hours > 0 else "0"
        
        # Format achievements and completion percentage
        completion_percentage = 0
        if game['has_achievements'] and game['achievements_total'] > 0:
            achievements_str = f"{game['achievements_unlocked']}/{game['achievements_total']}"
            completion_percentage = (game['achievements_unlocked'] / game['achievements_total']) * 100
        else:
            achievements_str = "N/A"
        
        completion_str = f"{completion_percentage:.1f}%" if game['has_achievements'] else "N/A"
        
        # Format last played
        last_played = game['last_played'] or "Never"
        if last_played != "Never":
            try:
                last_played = datetime.fromisoformat(last_played).strftime("%Y-%m-%d")
            except:
                pass
        
        tree.insert("", tk.END,
                   text=game['name'],
                   values=(game['platform'], playtime_str, achievements_str, completion_str, last_played),
                   tags=(game['id'], game['appid'], game['platform']))
    
    def sort_games_list(self, games):
        """Sort games list based on current sort selection"""
        sort_by = self.sort_var.get()
        
        if sort_by == "Name":
            return sorted(games, key=lambda x: x['name'].lower())
        elif sort_by == "Platform":
            return sorted(games, key=lambda x: (x['platform'], x['name'].lower()))
        elif sort_by == "Playtime":
            return sorted(games, key=lambda x: x['playtime'] or 0, reverse=True)
        elif sort_by == "Achievements":
            return sorted(games, key=lambda x: (x['achievements_unlocked'] or 0, x['name'].lower()), reverse=True)
        elif sort_by == "Completion":
            def completion_key(game):
                if game['has_achievements'] and game['achievements_total'] > 0:
                    return (game['achievements_unlocked'] / game['achievements_total']) * 100
                return 0
            return sorted(games, key=completion_key, reverse=True)
        else:
            return games
    
    def filter_games(self, event=None):
        """Filter games by platform"""
        self.load_games()
    
    def sort_games(self, event=None):
        """Sort games by selected criteria"""
        self.load_games()
    
    def clear_filters(self):
        """Clear all filters and sorting"""
        self.platform_var.set("All")
        self.sort_var.set("Completion")
        self.load_games()
    
    def mark_game_completed(self):
        """Mark selected games as completed"""
        # Determine which tree to use based on current tab or focus
        current_tab = self.games_notebook.index(self.games_notebook.select())
        if current_tab == 0:  # Incomplete games tab
            tree = self.incomplete_tree
            selection = tree.selection()
        else:
            # If we're on completed tab, check if incomplete tree has selection
            incomplete_selection = self.incomplete_tree.selection()
            if incomplete_selection:
                tree = self.incomplete_tree
                selection = incomplete_selection
            else:
                messagebox.showwarning("Warning", "Please go to Incomplete Games tab and select games to mark as completed")
                return
        
        if not selection:
            messagebox.showwarning("Warning", "Please select one or more games to mark as completed")
            return
        
        # Get selected games
        selected_games = []
        for item_id in selection:
            item = tree.item(item_id)
            game_name = item['text']
            game_id = item['tags'][0]
            selected_games.append((game_id, game_name))
        
        # Confirm action
        if len(selected_games) == 1:
            confirm_msg = f"Mark '{selected_games[0][1]}' as completed?"
        else:
            confirm_msg = f"Mark {len(selected_games)} games as completed?"
        
        if messagebox.askyesno("Confirm", confirm_msg):
            try:
                failed_games = []
                for game_id, game_name in selected_games:
                    try:
                        self.db.mark_game_completed(game_id, True)
                    except Exception as e:
                        failed_games.append(game_name)
                
                self.load_games()
                
                # Only show error if some games failed
                if failed_games:
                    messagebox.showerror("Error", f"Failed to mark these games as completed:\n" + "\n".join(failed_games))
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to mark games as completed: {e}")
    
    def mark_game_incomplete(self):
        """Mark selected games as incomplete"""
        # Determine which tree to use based on current tab or focus
        current_tab = self.games_notebook.index(self.games_notebook.select())
        if current_tab == 1:  # Completed games tab
            tree = self.completed_tree
            selection = tree.selection()
        else:
            # If we're on incomplete tab, check if completed tree has selection
            completed_selection = self.completed_tree.selection()
            if completed_selection:
                tree = self.completed_tree
                selection = completed_selection
            else:
                messagebox.showwarning("Warning", "Please go to Completed Games tab and select games to mark as incomplete")
                return
        
        if not selection:
            messagebox.showwarning("Warning", "Please select one or more games to mark as incomplete")
            return
        
        # Get selected games
        selected_games = []
        for item_id in selection:
            item = tree.item(item_id)
            game_name = item['text']
            game_id = item['tags'][0]
            selected_games.append((game_id, game_name))
        
        # Confirm action
        if len(selected_games) == 1:
            confirm_msg = f"Mark '{selected_games[0][1]}' as incomplete?"
        else:
            confirm_msg = f"Mark {len(selected_games)} games as incomplete?"
        
        if messagebox.askyesno("Confirm", confirm_msg):
            try:
                failed_games = []
                for game_id, game_name in selected_games:
                    try:
                        self.db.mark_game_completed(game_id, False)
                    except Exception as e:
                        failed_games.append(game_name)
                
                self.load_games()
                
                # Only show error if some games failed
                if failed_games:
                    messagebox.showerror("Error", f"Failed to mark these games as incomplete:\n" + "\n".join(failed_games))
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to mark games as incomplete: {e}")
    
    def import_steam_library(self):
        """Import Steam library using Steam Web API"""
        steam_api_key = self.db.get_setting('steam_api_key')
        steam_id = self.db.get_setting('steam_id')
        
        if not steam_api_key or not steam_id:
            messagebox.showerror("Error", "Steam API key and Steam ID must be configured in Settings")
            return
        
        def import_in_thread():
            try:
                # Get owned games
                url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
                params = {
                    'key': steam_api_key,
                    'steamid': steam_id,
                    'format': 'json',
                    'include_appinfo': 1,
                    'include_played_free_games': 1
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'response' not in data or 'games' not in data['response']:
                    raise Exception("No games found. Check if Steam profile is public.")
                
                games = data['response']['games']
                
                # Note: We no longer clear existing games to preserve completion status
                
                # Import each game
                for game in games:
                    appid = str(game['appid'])
                    name = game['name']
                    playtime = game.get('playtime_forever', 0)
                    has_stats = game.get('has_community_visible_stats', False)
                    
                    # Get achievements if available
                    achievements_total = 0
                    achievements_unlocked = 0
                    
                    if has_stats:
                        try:
                            # Get game achievements
                            ach_url = "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/"
                            ach_params = {
                                'appid': appid,
                                'key': steam_api_key,
                                'steamid': steam_id
                            }
                            
                            ach_response = requests.get(ach_url, params=ach_params)
                            if ach_response.status_code == 200:
                                ach_data = ach_response.json()
                                if 'playerstats' in ach_data and 'achievements' in ach_data['playerstats']:
                                    achievements = ach_data['playerstats']['achievements']
                                    achievements_total = len(achievements)
                                    achievements_unlocked = sum(1 for ach in achievements if ach.get('achieved', 0) == 1)
                        except:
                            pass  # Skip achievements if API call fails
                    
                    # Add to database
                    self.db.add_or_update_game(
                        appid=appid,
                        name=name,
                        platform='Steam',
                        playtime=playtime,
                        achievements_total=achievements_total,
                        achievements_unlocked=achievements_unlocked,
                        has_achievements=has_stats
                    )
                
                self.frame.after(0, lambda: messagebox.showinfo("Success", f"Imported {len(games)} Steam games!"))
                self.frame.after(0, self.load_games)
                
            except Exception as e:
                error_msg = str(e)
                self.frame.after(0, lambda: messagebox.showerror("Error", f"Failed to import Steam library: {error_msg}"))
        
        threading.Thread(target=import_in_thread, daemon=True).start()
    
    def import_epic_library(self):
        """Import Epic Games library using legendary CLI with stored auth code"""
        # Check if auth code is configured
        auth_code = self.db.get_setting('epic_auth_code')
        if not auth_code:
            messagebox.showerror("Error", 
                "Epic Games authentication not configured.\n\n"
                "Please go to Settings → API Keys tab and:\n"
                "1. Click 'Get Auth Code'\n"
                "2. Complete Epic Games login\n"
                "3. Copy and save the authorization code")
            return
        
        def import_in_thread():
            try:
                # Check if legendary is installed
                version_check = subprocess.run(['legendary', '--version'], capture_output=True, text=True, 
                                             encoding='utf-8', errors='ignore', timeout=10)
                if version_check.returncode != 0:
                    self.frame.after(0, lambda: messagebox.showerror("Error", 
                        "Legendary CLI not found. Please install legendary first:\n\n"
                        "pip install legendary-gl"))
                    return
                
                # Authenticate with stored auth code if needed
                auth_result = subprocess.run(['legendary', 'auth', '--code', auth_code], 
                                           capture_output=True, text=True, encoding='utf-8', 
                                           errors='ignore', timeout=30)
                
                # Try different commands to get games list
                list_result = None
                
                # Method 1: Try 'legendary list-games' first (cleaner output)
                try:
                    list_result = subprocess.run(['legendary', 'list-games'], capture_output=True, text=True, 
                                               encoding='utf-8', errors='ignore', timeout=30)
                    if list_result.returncode != 0:
                        list_result = None
                except:
                    list_result = None
                
                # Method 2: Fallback to 'legendary list'
                if list_result is None:
                    list_result = subprocess.run(['legendary', 'list'], capture_output=True, text=True, 
                                               encoding='utf-8', errors='ignore', timeout=30)
                
                if list_result.returncode != 0:
                    error_output = list_result.stderr or list_result.stdout or "Unknown error"
                    self.frame.after(0, lambda: messagebox.showerror("Error", 
                        f"Failed to get Epic Games library:\n{error_output[:300]}"))
                    return
                
                # Parse games from output
                games = []
                lines = list_result.stdout.split('\n')
                
                # Debug: Show what we're actually parsing
                print(f"DEBUG: Legendary output has {len(lines)} lines")
                for i, line in enumerate(lines[:10]):  # Show first 10 lines
                    print(f"DEBUG Line {i}: '{line.strip()}'")
                
                for line in lines:
                    line = line.strip()
                    
                    # Skip empty lines and obvious non-game entries
                    if not line or line.startswith('[') or line.startswith('Legendary') or line.startswith('INFO:'):
                        continue
                    
                    # Skip DLC entries (start with +) and non-game entries (start with -)
                    if line.startswith('+') or line.startswith('-'):
                        continue
                    
                    # Look for main game entries (start with *)
                    if line.startswith('* '):
                        # Format: * Game Name (App name: app_id | Version: version)
                        try:
                            # Remove the "* " prefix
                            content = line[2:]
                            
                            # Find the opening parenthesis for app info
                            paren_pos = content.rfind(' (App name: ')
                            if paren_pos == -1:
                                continue
                            
                            # Extract game name (everything before the parenthesis)
                            game_name = content[:paren_pos].strip()
                            
                            # Extract app info (everything after "App name: ")
                            app_info = content[paren_pos + 12:]  # 12 = len(' (App name: ')
                            
                            # Find the pipe separator in app info
                            pipe_pos = app_info.find(' | Version:')
                            if pipe_pos == -1:
                                continue
                            
                            # Extract app name (everything before " | Version:")
                            app_name = app_info[:pipe_pos].strip()
                            
                            # Filter out UE5 assets and development samples
                            skip_patterns = [
                                'UE5+Dev-Marketplace',
                                'UE5+Release',
                                'Animation Sample',
                                'Learning Kit',
                                'Virtual Studio',
                                'Stack O Bot',
                                'Teleportation and Portal',
                                'Slay Animation Sample'
                            ]
                            
                            # Check if this is a UE5 asset or development sample
                            is_ue_asset = any(pattern in content for pattern in skip_patterns)
                            
                            # Also check for version patterns that indicate UE5 assets
                            version_part = app_info[pipe_pos:] if pipe_pos != -1 else ""
                            is_ue_version = "+++UE5+" in version_part
                            
                            # Validate and add the game (skip UE5 assets)
                            if (game_name and app_name and len(game_name) > 1 and len(app_name) > 2 
                                and not is_ue_asset and not is_ue_version):
                                games.append((app_name, game_name))
                                print(f"DEBUG: Found game: {app_name} | {game_name}")
                            elif is_ue_asset or is_ue_version:
                                print(f"DEBUG: Skipped UE5 asset: {game_name}")
                            
                        except Exception as e:
                            print(f"DEBUG: Failed to parse line: {line[:100]}... Error: {e}")
                            continue
                
                # If no games found, try alternative parsing or show debug info
                if not games:
                    debug_msg = "No games found in Epic Games library.\n\n"
                    debug_msg += "This might be because:\n"
                    debug_msg += "1. No games are owned on Epic Games Store\n"
                    debug_msg += "2. Legendary output format is different than expected\n"
                    debug_msg += "3. Authentication issue\n\n"
                    debug_msg += f"Raw output (first 1000 chars):\n{list_result.stdout[:1000]}"
                    if len(list_result.stdout) > 1000:
                        debug_msg += "\n...(truncated)"
                    debug_msg += f"\n\nStderr: {list_result.stderr[:300] if list_result.stderr else 'None'}"
                    
                    self.frame.after(0, lambda msg=debug_msg: messagebox.showwarning("No Games Found", msg))
                    return
                
                # Import games to database
                imported_count = 0
                for app_name, game_name in games:
                    try:
                        self.db.add_or_update_game(
                            appid=app_name,
                            name=game_name,
                            platform='Epic',
                            playtime=0,
                            achievements_total=0,
                            achievements_unlocked=0,
                            has_achievements=False
                        )
                        imported_count += 1
                    except Exception as e:
                        print(f"Failed to import game {game_name}: {e}")
                        continue
                
                self.frame.after(0, lambda: messagebox.showinfo("Success", 
                    f"Successfully imported {imported_count} Epic games!"))
                self.frame.after(0, self.load_games)
                
            except subprocess.TimeoutExpired:
                self.frame.after(0, lambda: messagebox.showerror("Error", 
                    "Legendary command timed out. Please try again."))
            except Exception as e:
                error_msg = str(e)
                self.frame.after(0, lambda msg=error_msg: messagebox.showerror("Error", 
                    f"Failed to import Epic library: {msg}"))
        
        threading.Thread(target=import_in_thread, daemon=True).start()
    
    def mark_game_hundred_percent(self):
        """Mark selected games as 100% (only works for games with achievements)"""
        # Determine which tree to use based on current tab or focus
        current_tab = self.games_notebook.index(self.games_notebook.select())
        if current_tab == 0:  # Incomplete games tab
            tree = self.incomplete_tree
            selection = tree.selection()
        elif current_tab == 1:  # Completed games tab
            tree = self.completed_tree
            selection = tree.selection()
        else:  # 100% games tab or other
            incomplete_selection = self.incomplete_tree.selection()
            completed_selection = self.completed_tree.selection()
            if incomplete_selection:
                tree = self.incomplete_tree
                selection = incomplete_selection
            elif completed_selection:
                tree = self.completed_tree
                selection = completed_selection
            else:
                messagebox.showwarning("Warning", "Please select games from Incomplete or Completed tabs to mark as 100%")
                return
        
        if not selection:
            messagebox.showwarning("Warning", "Please select one or more games to mark as 100%")
            return
        
        # Get selected games and check if they have achievements
        selected_games = []
        games_without_achievements = []
        for item_id in selection:
            item = tree.item(item_id)
            game_name = item['text']
            game_id = item['tags'][0]
            
            # Get game details from database to check achievements
            game_details = self.db.get_games()
            game_data = next((g for g in game_details if str(g['id']) == str(game_id)), None)
            
            if game_data and game_data['has_achievements'] and game_data['achievements_total'] > 0:
                selected_games.append((game_id, game_name, game_data['achievements_total']))
            else:
                games_without_achievements.append(game_name)
        
        if games_without_achievements:
            messagebox.showwarning("Warning", 
                f"These games don't have achievements and can't be marked as 100%:\n" + 
                "\n".join(games_without_achievements[:5]) + 
                (f"\n... and {len(games_without_achievements) - 5} more" if len(games_without_achievements) > 5 else ""))
        
        if not selected_games:
            return
        
        # Confirm action
        if len(selected_games) == 1:
            confirm_msg = f"Mark '{selected_games[0][1]}' as 100% completed?\n\nThis will set achievements to {selected_games[0][2]}/{selected_games[0][2]} and mark as completed."
        else:
            confirm_msg = f"Mark {len(selected_games)} games as 100% completed?\n\nThis will set all achievements as unlocked and mark games as completed."
        
        if messagebox.askyesno("Confirm", confirm_msg):
            try:
                failed_games = []
                for game_id, game_name, total_achievements in selected_games:
                    try:
                        # Update achievements to 100%
                        cursor = self.db.conn.cursor()
                        cursor.execute('''
                            UPDATE games 
                            SET achievements_unlocked = achievements_total, 
                                is_completed = 1, 
                                updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        ''', (game_id,))
                        self.db.conn.commit()
                    except Exception as e:
                        failed_games.append(game_name)
                
                self.load_games()
                
                # Only show error if some games failed
                if failed_games:
                    messagebox.showerror("Error", f"Failed to mark these games as 100%:\n" + "\n".join(failed_games))
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to mark games as 100%: {e}")
    
    def clear_steam_games(self):
        """Clear all Steam Games entries from the database"""
        # Confirm the action
        result = messagebox.askyesno("Confirm Clear", 
                                   "Are you sure you want to remove ALL Steam Games from your library?\n\n"
                                   "This will delete all Steam Games entries including completion status.\n"
                                   "This action cannot be undone.")
        
        if result:
            try:
                self.db.delete_all_games('Steam')
                self.load_games()
                messagebox.showinfo("Success", "All Steam Games entries have been removed from your library.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear Steam Games: {e}")
    
    def clear_epic_games(self):
        """Clear all Epic Games entries from the database"""
        # Confirm the action
        result = messagebox.askyesno("Confirm Clear", 
                                   "Are you sure you want to remove ALL Epic Games from your library?\n\n"
                                   "This will delete all Epic Games entries including completion status.\n"
                                   "This action cannot be undone.")
        
        if result:
            try:
                self.db.delete_all_games('Epic')
                self.load_games()
                messagebox.showinfo("Success", "All Epic Games entries have been removed from your library.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear Epic Games: {e}")
    
    def select_random_game(self):
        """Select a random game from the incomplete games library"""
        games = []
        for item in self.incomplete_tree.get_children():
            games.append(self.incomplete_tree.item(item))
        
        if not games:
            messagebox.showinfo("Info", "No incomplete games in library")
            return
        
        # Select random game
        random_game = random.choice(games)
        game_name = random_game['text']
        platform = random_game['values'][0]
        
        # Switch to incomplete games tab and highlight the selected game
        self.games_notebook.select(0)  # Select incomplete games tab
        for item in self.incomplete_tree.get_children():
            if self.incomplete_tree.item(item)['text'] == game_name:
                self.incomplete_tree.selection_set(item)
                self.incomplete_tree.focus(item)
                self.incomplete_tree.see(item)
                break
        
        # Show message
        result = messagebox.askyesno("Random Game Selected", 
                                   f"Selected: {game_name} ({platform})\n\nWould you like to launch it?")
        if result:
            self.launch_selected_game()
    
    def launch_selected_game(self, event=None):
        """Launch the selected game"""
        # Determine which tree has the selection
        current_tab = self.games_notebook.index(self.games_notebook.select())
        if current_tab == 0:  # Incomplete games tab
            tree = self.incomplete_tree
        else:  # Completed games tab
            tree = self.completed_tree
        
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a game to launch")
            return
        
        item = tree.item(selection[0])
        game_name = item['text']
        appid = item['tags'][1]
        platform = item['tags'][2]
        
        try:
            if platform == 'Steam':
                # Launch via Steam protocol
                import webbrowser
                webbrowser.open(f"steam://launch/{appid}")
                messagebox.showinfo("Success", f"Launching {game_name} via Steam...")
                
            elif platform == 'Epic':
                # Launch via legendary
                subprocess.Popen(['legendary', 'launch', appid])
                messagebox.showinfo("Success", f"Launching {game_name} via Legendary...")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {game_name}: {e}")
    
    def show_context_menu(self, event, tab_type):
        """Show context menu on right click"""
        if tab_type == "incomplete":
            tree = self.incomplete_tree
            menu = self.incomplete_menu
        elif tab_type == "completed":
            tree = self.completed_tree
            menu = self.completed_menu
        else:  # hundred_percent
            tree = self.hundred_percent_tree
            menu = self.hundred_percent_menu
        
        # Handle selection for context menu
        item = tree.identify_row(event.y)
        if item:
            # If the clicked item is not in current selection, select only it
            # If it's already selected, keep the current multi-selection
            current_selection = tree.selection()
            if item not in current_selection:
                tree.selection_set(item)
            menu.post(event.x_root, event.y_root)
    
    def show_game_details(self):
        """Show detailed information about selected game"""
        # Determine which tree has the selection
        current_tab = self.games_notebook.index(self.games_notebook.select())
        if current_tab == 0:  # Incomplete games tab
            tree = self.incomplete_tree
        else:  # Completed games tab
            tree = self.completed_tree
        
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        game_id = item['tags'][0]
        
        # Get full game data from database
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM games WHERE id = ?", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            return
        
        # Create details window
        details_window = tk.Toplevel(self.frame)
        details_window.title(f"Game Details - {game['name']}")
        details_window.geometry("500x400")
        
        # Game info
        info_frame = ttk.LabelFrame(details_window, text="Game Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Name
        ttk.Label(info_frame, text="Name:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=game['name']).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Platform
        ttk.Label(info_frame, text="Platform:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=game['platform']).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # App ID
        ttk.Label(info_frame, text="App ID:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=game['appid']).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Playtime
        playtime_hours = game['playtime'] / 60 if game['playtime'] else 0
        ttk.Label(info_frame, text="Playtime:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"{playtime_hours:.1f} hours").grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Achievements
        if game['has_achievements']:
            ttk.Label(info_frame, text="Achievements:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, pady=2)
            achievement_text = f"{game['achievements_unlocked']}/{game['achievements_total']}"
            if game['achievements_total'] > 0:
                percentage = (game['achievements_unlocked'] / game['achievements_total']) * 100
                achievement_text += f" ({percentage:.1f}%)"
            ttk.Label(info_frame, text=achievement_text).grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Last played
        if game['last_played']:
            ttk.Label(info_frame, text="Last Played:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky=tk.W, pady=2)
            ttk.Label(info_frame, text=game['last_played']).grid(row=5, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Buttons
        button_frame = ttk.Frame(details_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Launch Game", 
                  command=lambda: self.launch_game_by_id(game_id)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Close", command=details_window.destroy).pack(side=tk.RIGHT)
    
    def launch_game_by_id(self, game_id):
        """Launch game by database ID"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM games WHERE id = ?", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            return
        
        try:
            if game['platform'] == 'Steam':
                steam_path = self.db.get_setting('steam_path', r"C:\Program Files (x86)\Steam\steam.exe")
                subprocess.Popen([steam_path, f"-applaunch", game['appid']])
                messagebox.showinfo("Success", f"Launching {game['name']} via Steam...")
                
            elif game['platform'] == 'Epic':
                subprocess.Popen(['legendary', 'launch', game['appid']])
                messagebox.showinfo("Success", f"Launching {game['name']} via Legendary...")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {game['name']}: {e}")