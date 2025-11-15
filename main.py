#!/usr/bin/env python3
"""
Personal News & Gaming Dashboard
Main application entry point with Tkinter GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os
from pathlib import Path
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("Warning: pystray not available. System tray functionality disabled.")
    print("Install with: pip install pystray pillow")

# Import our modules
from modules.database import DatabaseManager
from modules.news_tab import NewsTab
from modules.games_tab import GamesTab
from modules.todo_tab import TodoTab
from modules.settings_tab import SettingsTab
from modules.scheduler import SchedulerManager

class DashboardApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Personal News & Gaming Dashboard")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize database
        self.db = DatabaseManager()
        
        # Initialize scheduler
        self.scheduler = SchedulerManager(self.db)
        
        # System tray variables
        self.tray_icon = None
        self.is_hidden = False
        
        # Create GUI
        self.create_gui()
        
        # Setup system tray if available
        if TRAY_AVAILABLE:
            self.setup_system_tray()
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self.scheduler.start, daemon=True)
        self.scheduler_thread.start()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
    
    def create_gui(self):
        """Create the main GUI with tabbed interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.news_tab = NewsTab(self.notebook, self.db, self.scheduler)
        self.games_tab = GamesTab(self.notebook, self.db)
        self.todo_tab = TodoTab(self.notebook, self.db)
        self.settings_tab = SettingsTab(self.notebook, self.db)
        
        # Add tabs to notebook
        self.notebook.add(self.news_tab.frame, text="News Summary")
        self.notebook.add(self.games_tab.frame, text="Game Library")
        self.notebook.add(self.todo_tab.frame, text="To-Do")
        self.notebook.add(self.settings_tab.frame, text="Settings")
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def create_tray_icon(self):
        """Create a simple icon for the system tray"""
        # Create a simple icon (16x16 blue circle)
        image = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([2, 2, 14, 14], fill=(0, 120, 215, 255), outline=(0, 90, 180, 255))
        return image
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        if not TRAY_AVAILABLE:
            return
        
        # Create tray icon
        icon_image = self.create_tray_icon()
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Show Dashboard", self.show_window, default=True),
            pystray.MenuItem("Hide Dashboard", self.hide_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_application)
        )
        
        # Create tray icon
        self.tray_icon = pystray.Icon(
            "dashboard",
            icon_image,
            "Personal Dashboard",
            menu
        )
        
        # Start tray icon in background thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
    
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        self.root.after(0, self._show_window)
    
    def _show_window(self):
        """Internal method to show window (runs in main thread)"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_hidden = False
    
    def hide_window(self, icon=None, item=None):
        """Hide the main window to system tray"""
        if TRAY_AVAILABLE:
            self.root.withdraw()
            self.is_hidden = True
        else:
            messagebox.showinfo("Info", "System tray not available. Window will minimize normally.")
            self.root.iconify()
    
    def on_window_close(self):
        """Handle window close button - minimize to tray instead of closing"""
        if TRAY_AVAILABLE:
            self.hide_window()
            # Show notification on first minimize
            if not hasattr(self, '_first_minimize_shown'):
                self._first_minimize_shown = True
                if self.tray_icon:
                    try:
                        self.tray_icon.notify("Dashboard minimized to system tray", "Right-click the tray icon to show the dashboard")
                    except:
                        pass  # Notifications might not be supported
        else:
            self.quit_application()
    
    def quit_application(self, icon=None, item=None):
        """Completely quit the application"""
        try:
            self.scheduler.stop()
            self.db.close()
            if self.tray_icon:
                self.tray_icon.stop()
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Error during shutdown: {e}")
            sys.exit(1)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        app = DashboardApp()
        app.run()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()