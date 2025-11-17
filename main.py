#!/usr/bin/env python3
"""
Personal News & Gaming Dashboard
Main application entry point with PyQt6 GUI
"""

import sys
import os
import threading
from pathlib import Path

from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QVBoxLayout, 
                            QWidget, QStatusBar, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush

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

class DashboardApp(QMainWindow):
    # Signal for thread-safe status messages
    status_message_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Initialize database
        self.db = DatabaseManager()
        
        # Initialize scheduler
        self.scheduler = SchedulerManager(self.db)
        
        # System tray variables
        self.tray_icon = None
        self.is_hidden = False
        
        # Setup UI
        self.setup_ui()
        
        # Setup system tray if available
        if TRAY_AVAILABLE:
            self.setup_system_tray()
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self.scheduler.start, daemon=True)
        self.scheduler_thread.start()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("Personal News & Gaming Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # Apply modern dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #3c3c3c;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
            QStatusBar {
                background-color: #404040;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
        """)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs one 
        self.news_tab = NewsTab(self.db, self.scheduler, self)
        self.games_tab = GamesTab(self.db, self)
        self.todo_tab = TodoTab(self.db, self)
        self.settings_tab = SettingsTab(self.db, self)
        
        # Add tabs to widget
        self.tab_widget.addTab(self.news_tab, "📰 News Summary")
        self.tab_widget.addTab(self.games_tab, "🎮 Game Library")
        self.tab_widget.addTab(self.todo_tab, "✅ To-Do")
        self.tab_widget.addTab(self.settings_tab, "⚙️ Settings")
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Connect signal for thread-safe status updates
        self.status_message_signal.connect(self._show_success_message_impl)
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_bar.showMessage(message)
    
    def show_success_message(self, message):
        """Show a temporary success message in status bar (thread-safe)"""
        # Emit signal to ensure this runs in the main thread
        self.status_message_signal.emit(message)
    
    def _show_success_message_impl(self, message):
        """Internal implementation that runs in main thread"""
        self.status_bar.showMessage(f"✅ {message}", 5000)  # Show for 5 seconds
    
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
        QTimer.singleShot(0, self._show_window)
    
    def _show_window(self):
        """Internal method to show window (runs in main thread)"""
        self.show()
        self.raise_()
        self.activateWindow()
        self.is_hidden = False
    
    def hide_window(self, icon=None, item=None):
        """Hide the main window to system tray"""
        if TRAY_AVAILABLE:
            self.hide()
            self.is_hidden = True
        else:
            QMessageBox.information(self, "Info", "System tray not available. Window will minimize normally.")
            self.showMinimized()
    
    def closeEvent(self, event):
        """Handle window close button - minimize to tray instead of closing"""
        if TRAY_AVAILABLE:
            event.ignore()
            self.hide_window()
            # Show notification on first minimize
            if not hasattr(self, '_first_minimize_shown'):
                self._first_minimize_shown = True
                if self.tray_icon:
                    try:
                        self.tray_icon.notify("Dashboard minimized to system tray", 
                                            "Right-click the tray icon to show the dashboard")
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
            QApplication.quit()
        except Exception as e:
            print(f"Error during shutdown: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Personal Dashboard")
    app.setApplicationVersion("2.0")
    
    # Set application style
    app.setStyle('Fusion')
    
    try:
        dashboard = DashboardApp()
        dashboard.show()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()