"""
To-Do Tab
Handles task management with priorities, due dates, and recurrence
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTreeWidget, QTreeWidgetItem, QComboBox, QLabel,
                            QMessageBox, QDialog, QLineEdit, QTextEdit, 
                            QDateTimeEdit, QSplitter, QFrame, QGroupBox,
                            QFormLayout, QDialogButtonBox)
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta
import threading
import requests
import time

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

class TodoTab(QWidget):
    def __init__(self, db, main_window):
        super().__init__()
        self.db = db
        self.main_window = main_window
        self.setup_ui()
        self.load_tasks()
    
    def setup_ui(self):
        """Create the modern PyQt todo tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(1)
        
        # Apply modern styling to match games tab
        self.setStyleSheet("""
            QWidget {
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 60px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
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
            QTreeWidget {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 8px;
                color: white;
                selection-background-color: #0078d4;
                alternate-background-color: #454545;
            }
            QTreeWidget::item {
                padding: 4px;
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
                padding: 6px;
                border: none;
                border-right: 1px solid #666666;
                font-weight: bold;
                font-size: 11px;
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
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 2px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        # Compact controls in single row
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)
        
        # Task management buttons - smaller
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.clicked.connect(self.add_task_dialog)
        controls_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_task_dialog)
        controls_layout.addWidget(self.edit_btn)
        
        self.complete_btn = QPushButton("✅ Done")
        self.complete_btn.clicked.connect(self.complete_task)
        controls_layout.addWidget(self.complete_btn)
        
        self.delete_btn = QPushButton("🗑️ Del")
        self.delete_btn.clicked.connect(self.delete_task)
        controls_layout.addWidget(self.delete_btn)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.clicked.connect(self.load_tasks)
        controls_layout.addWidget(self.refresh_btn)
        
        # Status filter in same row
        controls_layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Pending", "Completed"])
        self.status_combo.setCurrentText("Pending")
        self.status_combo.currentTextChanged.connect(self.filter_tasks)
        controls_layout.addWidget(self.status_combo)
        
        controls_layout.addStretch()
        
        # Reminder buttons - smaller
        self.send_reminders_btn = QPushButton("📢 Remind")
        self.send_reminders_btn.clicked.connect(self.send_reminders)
        controls_layout.addWidget(self.send_reminders_btn)
        
        self.test_reminders_btn = QPushButton("🧪 Test")
        self.test_reminders_btn.clicked.connect(self.test_auto_reminders)
        controls_layout.addWidget(self.test_reminders_btn)
        
        layout.addWidget(controls_frame)
        
        # Main content with splitter - no extra spacing
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Task list
        left_panel = QGroupBox("📋 Tasks")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 8, 6, 6)
        left_layout.setSpacing(4)
        
        # Task tree
        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderLabels(["Task", "Due Date", "Priority", "Status", "Recurrence"])
        self.task_tree.setAlternatingRowColors(True)
        self.task_tree.setRootIsDecorated(False)
        self.task_tree.setSortingEnabled(True)
        
        # Set column widths - more compact
        self.task_tree.setColumnWidth(0, 250)
        self.task_tree.setColumnWidth(1, 100)
        self.task_tree.setColumnWidth(2, 70)
        self.task_tree.setColumnWidth(3, 90)
        self.task_tree.setColumnWidth(4, 90)
        
        # Connect signals
        self.task_tree.itemSelectionChanged.connect(self.show_task_details)
        self.task_tree.itemDoubleClicked.connect(self.edit_task_dialog)
        
        left_layout.addWidget(self.task_tree)
        splitter.addWidget(left_panel)
        
        # Right panel - Task details
        right_panel = QGroupBox("📝 Details")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 8, 6, 6)
        right_layout.setSpacing(4)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Consolas", 10))
        right_layout.addWidget(self.details_text)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 200])  # Very compact allocation
        
        layout.addWidget(splitter)
    
    def load_tasks(self):
        """Load tasks from database into the tree"""
        self.task_tree.clear()
        
        # Get filter value
        status_filter = self.status_combo.currentText()
        
        # Load tasks from database
        if status_filter == "All":
            tasks = self.db.get_tasks()
        else:
            tasks = self.db.get_tasks(status_filter)
        
        # Add tasks to tree
        for task in tasks:
            # Format due date
            due_date = task['due_date']
            if due_date:
                try:
                    due_dt = datetime.fromisoformat(due_date)
                    due_str = due_dt.strftime("%Y-%m-%d %H:%M")
                    
                    # Check if overdue
                    if due_dt.date() < datetime.now().date() and task['status'] == 'Pending':
                        due_str += " ⚠️"
                except:
                    due_str = due_date
            else:
                due_str = ""
            
            # Format recurrence
            recurrence = task['recurrence'] or ""
            
            # Format status with emoji
            status = task['status']
            if status == 'Completed':
                status = "✅ Completed"
            elif status == 'Pending':
                status = "⏳ Pending"
            
            # Create tree item
            item = QTreeWidgetItem([
                task['title'],
                due_str,
                task['priority'],
                status,
                recurrence
            ])
            
            # Store task ID in item data
            item.setData(0, Qt.ItemDataRole.UserRole, task['id'])
            
            # Color code based on priority and status
            if task['status'] == 'Completed':
                for i in range(5):
                    item.setBackground(i, QColor("#2d5a2d"))  # Dark green
            elif "⚠️" in due_str:  # Overdue
                for i in range(5):
                    item.setBackground(i, QColor("#5a2d2d"))  # Dark red
            elif task['priority'] == 'High':
                for i in range(5):
                    item.setBackground(i, QColor("#5a5a2d"))  # Dark yellow
            
            self.task_tree.addTopLevelItem(item)
    
    def filter_tasks(self):
        """Filter tasks by status"""
        self.load_tasks()
    
    def show_task_details(self):
        """Show details of selected task"""
        current_item = self.task_tree.currentItem()
        if not current_item:
            self.details_text.clear()
            return
        
        task_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        # Get task from database
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        
        if not task:
            return
        
        # Display task details
        details = f"📋 Title: {task['title']}\n\n"
        
        if task['description']:
            details += f"📝 Description:\n{task['description']}\n\n"
        
        if task['due_date']:
            details += f"📅 Due Date: {task['due_date']}\n"
        
        details += f"⚡ Priority: {task['priority']}\n"
        details += f"📊 Status: {task['status']}\n"
        
        if task['recurrence']:
            details += f"🔄 Recurrence: {task['recurrence']}\n"
        
        details += f"\n🕐 Created: {task['created_at']}\n"
        
        if task['updated_at'] != task['created_at']:
            details += f"🕑 Updated: {task['updated_at']}\n"
        
        if task['completed_at']:
            details += f"✅ Completed: {task['completed_at']}\n"
        
        self.details_text.setPlainText(details)
    
    def add_task_dialog(self):
        """Show dialog to add new task"""
        self.task_dialog(mode="add")
    
    def edit_task_dialog(self):
        """Show dialog to edit selected task"""
        current_item = self.task_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a task to edit")
            return
        
        task_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        self.task_dialog(mode="edit", task_id=task_id)
    
    def task_dialog(self, mode="add", task_id=None):
        """Show task add/edit dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Task" if mode == "add" else "Edit Task")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        # Apply styling to dialog
        dialog.setStyleSheet("""
            QDialog {
                background-color: #3c3c3c;
                color: #ffffff;
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
            QTextEdit {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 6px;
                color: white;
                padding: 8px;
            }
            QComboBox {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 8px;
                color: white;
                min-width: 120px;
            }
            QDateTimeEdit {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 6px;
                padding: 8px;
                color: white;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        
        layout = QFormLayout(dialog)
        
        # Title field
        title_edit = QLineEdit()
        title_edit.setPlaceholderText("Enter task title...")
        layout.addRow("Title:", title_edit)
        
        # Description field
        desc_edit = QTextEdit()
        desc_edit.setMaximumHeight(100)
        desc_edit.setPlaceholderText("Enter task description...")
        layout.addRow("Description:", desc_edit)
        
        # Due date field
        due_edit = QDateTimeEdit()
        due_edit.setDateTime(QDateTime.currentDateTime())
        due_edit.setCalendarPopup(True)
        layout.addRow("Due Date:", due_edit)
        
        # Priority field
        priority_combo = QComboBox()
        priority_combo.addItems(["Low", "Medium", "High"])
        priority_combo.setCurrentText("Medium")
        layout.addRow("Priority:", priority_combo)
        
        # Recurrence field
        recurrence_combo = QComboBox()
        recurrence_combo.addItems(["None", "Daily", "Weekly", "Monthly"])
        layout.addRow("Recurrence:", recurrence_combo)
        
        # Load existing data if editing
        if mode == "edit" and task_id:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()
            if task:
                title_edit.setText(task['title'])
                if task['description']:
                    desc_edit.setPlainText(task['description'])
                if task['due_date']:
                    due_dt = QDateTime.fromString(task['due_date'], Qt.DateFormat.ISODate)
                    due_edit.setDateTime(due_dt)
                priority_combo.setCurrentText(task['priority'])
                if task['recurrence']:
                    recurrence_combo.setCurrentText(task['recurrence'])
                else:
                    recurrence_combo.setCurrentText("None")
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = title_edit.text().strip()
            description = desc_edit.toPlainText().strip()
            due_date = due_edit.dateTime().toString(Qt.DateFormat.ISODate)
            priority = priority_combo.currentText()
            recurrence = recurrence_combo.currentText() if recurrence_combo.currentText() != "None" else None
            
            if not title:
                QMessageBox.warning(self, "Error", "Please enter a task title")
                return
            
            try:
                if mode == "add":
                    self.db.add_task(title, description, due_date, priority, recurrence)
                    show_toast(self, "✅ Task added successfully!")
                else:
                    self.db.update_task(task_id, title=title, description=description,
                                      due_date=due_date, priority=priority, recurrence=recurrence)
                    show_toast(self, "✅ Task updated successfully!")
                
                self.load_tasks()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save task: {e}")
    
    def complete_task(self):
        """Mark selected task as completed"""
        current_item = self.task_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a task to complete")
            return
        
        task_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        task_title = current_item.text(0)
        
        reply = QMessageBox.question(self, "Confirm", f"Mark task '{task_title}' as completed?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.complete_task(task_id)
                self.load_tasks()
                show_toast(self, "✅ Task marked as completed!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to complete task: {e}")
    
    def delete_task(self):
        """Delete selected task"""
        current_item = self.task_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a task to delete")
            return
        
        task_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        task_title = current_item.text(0)
        
        reply = QMessageBox.question(self, "Confirm", f"Delete task '{task_title}'?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_task(task_id)
                self.load_tasks()
                show_toast(self, "✅ Task deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete task: {e}")
    
    def send_reminders(self):
        """Send task reminders to Discord"""
        webhook_url = self.db.get_setting('discord_webhook_url')
        if not webhook_url:
            QMessageBox.warning(self, "Error", "No Discord webhook URL configured in Settings")
            return
        
        def send_in_thread():
            try:
                # Get pending tasks that are due today or overdue
                today = datetime.now().date()
                cursor = self.db.conn.cursor()
                cursor.execute('''
                    SELECT * FROM tasks 
                    WHERE status = 'Pending' AND due_date IS NOT NULL 
                    AND date(due_date) <= date('now')
                    ORDER BY due_date
                ''')
                due_tasks = cursor.fetchall()
                
                if not due_tasks:
                    QTimer.singleShot(0, lambda: QMessageBox.information(self, "Info", "No tasks due for reminders"))
                    return
                
                # Send task reminders in batches
                batches_sent = self.send_task_batches(webhook_url, due_tasks, today, "Task Reminder Bot", "⏰ **Task Reminders**")
                
                QTimer.singleShot(0, lambda: QMessageBox.information(self, "Success", f"Sent reminders for {len(due_tasks)} tasks in {batches_sent} message(s)!"))
                
            except Exception as e:
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Failed to send reminders: {e}"))
        
        threading.Thread(target=send_in_thread, daemon=True).start()
    
    def send_task_batches(self, webhook_url, due_tasks, today, username="Task Reminder Bot", header="⏰ **Task Reminders**"):
        """Send task reminders in batches to respect Discord's character limit"""
        # Get Discord user ID for pings
        discord_user_id = self.db.get_setting('discord_user_id', '')
        ping_text = f"<@{discord_user_id}> " if discord_user_id else ""
        
        batches = []
        current_batch = f"{ping_text}{header}\n\n"
        batch_count = 0
        
        for task in due_tasks:
            # Format task reminder
            due_date = datetime.fromisoformat(task['due_date']).date()
            if due_date < today:
                status_emoji = "🔴"
                status_text = "OVERDUE"
            else:
                status_emoji = "🟡"
                status_text = "DUE TODAY"
            
            task_text = f"{status_emoji} **{status_text}**: {task['title']}\n"
            if task['description']:
                desc = task['description']
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                task_text += f"   {desc}\n"
            task_text += f"   Priority: {task['priority']}\n\n"
            
            # Check if adding this task would exceed the limit
            if len(current_batch + task_text) > 1950:  # Leave some buffer
                # Save current batch and start new one
                batches.append(current_batch.strip())
                batch_count += 1
                current_batch = f"{ping_text}{header} (Part {batch_count + 1})\n\n{task_text}"
            else:
                current_batch += task_text
        
        # Add the last batch if it has content
        if current_batch.strip() != header.strip():
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
    
    def test_auto_reminders(self):
        """Test the automatic reminder system"""
        # Check if task webhook is configured
        task_webhook_url = self.db.get_setting('discord_task_webhook_url')
        news_webhook_url = self.db.get_setting('discord_webhook_url')
        webhook_url = task_webhook_url or news_webhook_url
        
        if not webhook_url:
            QMessageBox.warning(self, "Error", "No Discord webhook URL configured in Settings")
            return
        
        auto_reminders = str(self.db.get_setting('auto_task_reminders', 'true')).lower() == 'true'
        if not auto_reminders:
            QMessageBox.information(self, "Info", "Auto reminders are disabled in settings")
            return
        
        def test_in_thread():
            try:
                # Send a test reminder
                payload = {
                    "username": "Task Reminder Bot (Test)",
                    "content": "🧪 **Test Reminder**\n\nThis is a test of the automatic reminder system. If you see this message, reminders are working correctly!"
                }
                
                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                
                QTimer.singleShot(0, lambda: QMessageBox.information(self, "Success", "Test reminder sent successfully!"))
                
            except Exception as e:
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Failed to send test reminder: {e}"))
        
        threading.Thread(target=test_in_thread, daemon=True).start()