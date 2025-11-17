"""
News Summary Tab
Handles RSS feed management, news fetching, and summarization
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTreeWidget, QTreeWidgetItem, QTextEdit, QLineEdit,
                            QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
                            QSplitter, QFrame, QGroupBox, QLabel, QProgressBar)
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
from datetime import datetime
import feedparser
import requests
import google.generativeai as genai
from urllib.parse import urlparse
import logging

class NewsTab(QWidget):
    def __init__(self, db, scheduler, main_window):
        super().__init__()
        self.db = db
        self.scheduler = scheduler
        self.main_window = main_window
        self.setup_ui()
        self.load_feeds()
        self.load_news()
    
    def setup_ui(self):
        """Create the modern PyQt news tab UI"""
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
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
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
            QTextEdit {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 8px;
                color: white;
                padding: 10px;
            }
            QLineEdit {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 8px;
                color: white;
            }
            QLineEdit:focus {
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
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Feed management
        left_panel = QGroupBox("📡 RSS Feeds")
        left_layout = QVBoxLayout(left_panel)
        
        # Feed controls
        feed_controls = QFrame()
        feed_controls_layout = QHBoxLayout(feed_controls)
        feed_controls_layout.setSpacing(10)
        
        self.add_feed_btn = QPushButton("➕ Add Feed")
        self.add_feed_btn.clicked.connect(self.add_feed_dialog)
        feed_controls_layout.addWidget(self.add_feed_btn)
        
        self.edit_feed_btn = QPushButton("✏️ Edit Feed")
        self.edit_feed_btn.clicked.connect(self.edit_feed_dialog)
        feed_controls_layout.addWidget(self.edit_feed_btn)
        
        self.delete_feed_btn = QPushButton("🗑️ Delete Feed")
        self.delete_feed_btn.clicked.connect(self.delete_feed)
        feed_controls_layout.addWidget(self.delete_feed_btn)
        
        feed_controls_layout.addStretch()
        left_layout.addWidget(feed_controls)
        
        # Feed list
        self.feed_tree = QTreeWidget()
        self.feed_tree.setHeaderLabels(["Name", "URL"])
        self.feed_tree.setAlternatingRowColors(True)
        self.feed_tree.setRootIsDecorated(False)
        self.feed_tree.setColumnWidth(0, 150)
        self.feed_tree.setColumnWidth(1, 300)
        left_layout.addWidget(self.feed_tree)
        
        # News controls
        news_controls = QFrame()
        news_controls_layout = QHBoxLayout(news_controls)
        news_controls_layout.setSpacing(10)
        
        self.fetch_btn = QPushButton("🔄 Fetch News")
        self.fetch_btn.clicked.connect(self.fetch_all_news)
        news_controls_layout.addWidget(self.fetch_btn)
        
        self.send_discord_btn = QPushButton("📤 Send to Discord")
        self.send_discord_btn.clicked.connect(self.send_to_discord)
        news_controls_layout.addWidget(self.send_discord_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh View")
        self.refresh_btn.clicked.connect(self.load_news)
        news_controls_layout.addWidget(self.refresh_btn)
        
        news_controls_layout.addStretch()
        left_layout.addWidget(news_controls)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        splitter.addWidget(left_panel)
        
        # Right panel - News display
        right_panel = QGroupBox("📰 News Articles")
        right_layout = QVBoxLayout(right_panel)
        
        # News list
        self.news_tree = QTreeWidget()
        self.news_tree.setHeaderLabels(["Title", "Feed", "Date"])
        self.news_tree.setAlternatingRowColors(True)
        self.news_tree.setRootIsDecorated(False)
        self.news_tree.setColumnWidth(0, 300)
        self.news_tree.setColumnWidth(1, 100)
        self.news_tree.setColumnWidth(2, 120)
        self.news_tree.itemSelectionChanged.connect(self.show_news_details)
        right_layout.addWidget(self.news_tree)
        
        # News details
        self.news_details = QTextEdit()
        self.news_details.setReadOnly(True)
        self.news_details.setFont(QFont("Consolas", 10))
        self.news_details.setMaximumHeight(200)
        right_layout.addWidget(self.news_details)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        
        layout.addWidget(splitter)
    
    def load_feeds(self):
        """Load RSS feeds from database"""
        self.feed_tree.clear()
        feeds = self.db.get_feeds()
        
        for feed in feeds:
            item = QTreeWidgetItem([feed['name'], feed['url']])
            item.setData(0, Qt.ItemDataRole.UserRole, feed['id'])
            self.feed_tree.addTopLevelItem(item)
    
    def load_news(self):
        """Load news items from database"""
        self.news_tree.clear()
        news_items = self.db.get_news_items(limit=50)
        
        for item in news_items:
            # Format date
            date_str = ""
            if item['published']:
                try:
                    if 'T' in item['published']:
                        date_obj = datetime.fromisoformat(item['published'].replace('Z', '+00:00'))
                    else:
                        date_obj = datetime.strptime(item['published'], '%a, %d %b %Y %H:%M:%S %Z')
                    date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                except:
                    date_str = item['published'][:16] if len(item['published']) > 16 else item['published']
            
            tree_item = QTreeWidgetItem([
                item['title'][:60] + "..." if len(item['title']) > 60 else item['title'],
                item['feed_name'],
                date_str
            ])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item['id'])
            self.news_tree.addTopLevelItem(tree_item)
    
    def show_news_details(self):
        """Show details of selected news item"""
        current_item = self.news_tree.currentItem()
        if not current_item:
            self.news_details.clear()
            return
        
        news_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        # Get news item from database with feed name
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT n.*, f.name as feed_name 
            FROM news_items n 
            LEFT JOIN feeds f ON n.feed_id = f.id 
            WHERE n.id = ?
        """, (news_id,))
        news_item = cursor.fetchone()
        
        if not news_item:
            return
        
        # Display news details
        details = f"📰 {news_item['title']}\n\n"
        details += f"📡 Feed: {news_item['feed_name']}\n"
        if news_item['published']:
            details += f"📅 Published: {news_item['published']}\n"
        if news_item['link']:
            details += f"🔗 Link: {news_item['link']}\n"
        details += "\n"
        
        if news_item['summary']:
            details += f"📝 Summary:\n{news_item['summary']}\n\n"
        
        if news_item['description']:
            details += f"📄 Description:\n{news_item['description']}"
        
        self.news_details.setPlainText(details)
    
    def add_feed_dialog(self):
        """Show dialog to add new RSS feed"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add RSS Feed")
        dialog.setModal(True)
        dialog.resize(400, 150)
        
        layout = QFormLayout(dialog)
        
        name_edit = QLineEdit()
        layout.addRow("Name:", name_edit)
        
        url_edit = QLineEdit()
        layout.addRow("URL:", url_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            url = url_edit.text().strip()
            
            if not name or not url:
                QMessageBox.warning(self, "Error", "Please enter both name and URL")
                return
            
            try:
                self.db.add_feed(name, url)
                self.load_feeds()
                show_toast(self, "✅ RSS feed added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add feed: {e}")
    
    def edit_feed_dialog(self):
        """Show dialog to edit selected RSS feed"""
        current_item = self.feed_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a feed to edit")
            return
        
        feed_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit RSS Feed")
        dialog.setModal(True)
        dialog.resize(400, 150)
        
        layout = QFormLayout(dialog)
        
        name_edit = QLineEdit(current_item.text(0))
        layout.addRow("Name:", name_edit)
        
        url_edit = QLineEdit(current_item.text(1))
        layout.addRow("URL:", url_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            url = url_edit.text().strip()
            
            if not name or not url:
                QMessageBox.warning(self, "Error", "Please enter both name and URL")
                return
            
            try:
                self.db.update_feed(feed_id, name, url)
                self.load_feeds()
                show_toast(self, "✅ RSS feed updated successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update feed: {e}")
    
    def delete_feed(self):
        """Delete selected RSS feed"""
        current_item = self.feed_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a feed to delete")
            return
        
        feed_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        feed_name = current_item.text(0)
        
        reply = QMessageBox.question(self, "Confirm", f"Delete feed '{feed_name}'?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_feed(feed_id)
                self.load_feeds()
                self.load_news()
                show_toast(self, "✅ RSS feed deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete feed: {e}")
    
    def fetch_all_news(self):
        """Fetch news from all RSS feeds"""
        def fetch_in_thread():
            try:
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # Indeterminate progress
                
                feeds = self.db.get_feeds()
                news_count = 0
                
                for i, feed in enumerate(feeds):
                    try:
                        # Parse RSS feed
                        parsed_feed = feedparser.parse(feed['url'])
                        
                        for entry in parsed_feed.entries[:10]:  # Limit to 10 most recent per feed
                            # Check if item already exists
                            title = entry.get('title', 'No title')
                            link = entry.get('link', '')
                            
                            if self.db.news_item_exists(feed['id'], title, link):
                                continue
                            
                            # Get description
                            description = entry.get('description', '') or entry.get('summary', '')
                            
                            # Generate AI summary
                            summary = self.generate_summary(title, description)
                            
                            # Get published date
                            published = None
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                published = datetime(*entry.published_parsed[:6]).isoformat()
                            elif hasattr(entry, 'published'):
                                published = entry.published
                            
                            # Add to database
                            self.db.add_news_item(feed['id'], title, link, description, summary, published)
                            news_count += 1
                        
                    except Exception as e:
                        print(f"Failed to fetch from feed {feed['name']}: {e}")
                
                self.progress_bar.setVisible(False)
                self.load_news()
                show_toast(self, f"✅ Fetched {news_count} new news items!")
                
            except Exception as e:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(self, "Error", f"Failed to fetch news: {e}")
        
        threading.Thread(target=fetch_in_thread, daemon=True).start()
    
    def generate_summary(self, title, description):
        """Generate AI summary using Gemini API or fallback to truncation"""
        # If description is short, just use it as-is
        if len(description) <= 200:
            return description
        
        # Check if Gemini API is configured
        api_key = self.db.get_setting('gemini_api_key')
        if not api_key:
            # Fallback to simple truncation
            return description[:300] + "..." if len(description) > 300 else description
        
        try:
            import google.generativeai as genai
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Get selected model
            model_name = self.db.get_setting('gemini_model') or 'gemini-2.5-flash'
            model = genai.GenerativeModel(model_name)
            
            # Create summarization prompt
            prompt = f"""Please provide a concise summary of this news article in 2-3 sentences. Focus on the key facts and main points.

Title: {title}

Content: {description}

Summary:"""
            
            # Generate summary
            response = model.generate_content(prompt)
            
            if response.text:
                summary = response.text.strip()
                # Ensure summary isn't too long
                if len(summary) > 400:
                    summary = summary[:397] + "..."
                return summary
            else:
                # Fallback if no response
                return description[:300] + "..." if len(description) > 300 else description
                
        except Exception as e:
            logging.error(f"Failed to generate AI summary: {e}")
            # Fallback to simple truncation
            return description[:300] + "..." if len(description) > 300 else description
    
    def send_to_discord(self):
        """Send selected news items to Discord"""
        webhook_url = self.db.get_setting('discord_webhook_url')
        if not webhook_url:
            QMessageBox.critical(self, "Error", "No Discord webhook URL configured in Settings")
            return
        
        # Get unsent news items
        unsent_news = self.db.get_unsent_news_items(10)
        
        if not unsent_news:
            show_toast(self, "ℹ️ No unsent news items to send")
            return
        
        def send_in_thread():
            try:
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)
                
                # Send news in batches
                header = f"📰 **News Update** ({len(unsent_news)} items)"
                batches_sent = self.send_news_batches(webhook_url, unsent_news, "News Bot", header)
                
                # Mark items as sent
                news_ids = [item['id'] for item in unsent_news]
                self.db.mark_news_items_as_sent(news_ids)
                
                self.progress_bar.setVisible(False)
                show_toast(self, f"✅ Sent {len(unsent_news)} news items in {batches_sent} message(s)!")
                
            except Exception as e:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(self, "Error", f"Failed to send to Discord: {e}")
        
        threading.Thread(target=send_in_thread, daemon=True).start()
    
    def send_news_batches(self, webhook_url, news_items, username="News Bot", header="📰 **News Update**"):
        """Send news items in batches to respect Discord's character limit"""
        import time
        
        # Get Discord user ID for pings
        discord_user_id = self.db.get_setting('discord_user_id', '')
        ping_text = f"<@{discord_user_id}> " if discord_user_id else ""
        
        batches = []
        current_batch = f"{ping_text}{header}\n\n"
        batch_count = 0
        
        for item in news_items:
            # Format news item
            item_text = f"**{item['feed_name']}**: {item['title']}\n"
            if item['summary']:
                # Truncate summary if too long
                summary = item['summary']
                if len(summary) > 250:
                    summary = summary[:247] + "..."
                item_text += f"{summary}\n"
            if item['link']:
                item_text += f"🔗 {item['link']}\n"
            item_text += "\n"
            
            # Check if adding this item would exceed the limit
            if len(current_batch + item_text) > 1950:  # Leave some buffer
                # Save current batch and start new one
                batches.append(current_batch.strip())
                batch_count += 1
                current_batch = f"{ping_text}{header} (Part {batch_count + 1})\n\n{item_text}"
            else:
                current_batch += item_text
        
        # Add the last batch if it has content
        if current_batch.strip() != f"{ping_text}{header}".strip():
            batches.append(current_batch.strip())
        
        # Send each batch with a small delay
        for i, batch in enumerate(batches):
            payload = {
                "username": username,
                "content": batch
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            # Small delay between messages to avoid rate limiting
            if i < len(batches) - 1:
                time.sleep(1)
        
        return len(batches)