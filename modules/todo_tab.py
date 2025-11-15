"""
To-Do Tab
Handles task management with priorities, due dates, and recurrence
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import threading
import requests

class TodoTab:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        
        self.frame = ttk.Frame(parent)
        self.create_widgets()
        self.load_tasks()
    
    def create_widgets(self):
        """Create the todo tab widgets"""
        # Main container with paned window
        paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Task list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=2)
        
        # Task controls
        controls_frame = ttk.Frame(left_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(controls_frame, text="Add Task", command=self.add_task_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Edit Task", command=self.edit_task_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Complete Task", command=self.complete_task).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Delete Task", command=self.delete_task).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Refresh", command=self.load_tasks).pack(side=tk.LEFT, padx=(0, 5))
        
        # Filter controls
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_var = tk.StringVar(value="Pending")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var,
                                   values=["All", "Pending", "Completed"], state="readonly", width=10)
        status_combo.pack(side=tk.LEFT, padx=(0, 10))
        status_combo.bind("<<ComboboxSelected>>", self.filter_tasks)
        
        ttk.Button(filter_frame, text="Send Reminders Now", command=self.send_reminders).pack(side=tk.RIGHT, padx=(0, 5))
        ttk.Button(filter_frame, text="Test Auto-Reminders", command=self.test_auto_reminders).pack(side=tk.RIGHT)
        
        # Task list
        list_frame = ttk.LabelFrame(left_frame, text="Tasks", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for tasks
        columns = ("due_date", "priority", "status", "recurrence")
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings")
        
        # Configure columns
        self.task_tree.heading("#0", text="Task")
        self.task_tree.heading("due_date", text="Due Date")
        self.task_tree.heading("priority", text="Priority")
        self.task_tree.heading("status", text="Status")
        self.task_tree.heading("recurrence", text="Recurrence")
        
        self.task_tree.column("#0", width=250)
        self.task_tree.column("due_date", width=100)
        self.task_tree.column("priority", width=80)
        self.task_tree.column("status", width=80)
        self.task_tree.column("recurrence", width=100)
        
        # Scrollbar
        task_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=task_scroll.set)
        
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        task_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right panel - Task details
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        details_frame = ttk.LabelFrame(right_frame, text="Task Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Task details text
        self.details_text = tk.Text(details_frame, wrap=tk.WORD, state=tk.DISABLED)
        details_scroll = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scroll.set)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.task_tree.bind("<<TreeviewSelect>>", self.show_task_details)
        self.task_tree.bind("<Double-1>", self.edit_task_dialog)
    
    def load_tasks(self):
        """Load tasks from database into the tree"""
        # Clear existing items
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Get filter value
        status_filter = self.status_var.get()
        
        # Load tasks from database
        if status_filter == "All":
            tasks = self.db.get_tasks()
        else:
            tasks = self.db.get_tasks(status_filter)
        
        # Add to tree
        for task in tasks:
            # Format due date
            due_date = task['due_date']
            if due_date:
                try:
                    due_dt = datetime.fromisoformat(due_date)
                    due_str = due_dt.strftime("%Y-%m-%d")
                    
                    # Check if overdue
                    if due_dt.date() < datetime.now().date() and task['status'] == 'Pending':
                        due_str += " (OVERDUE)"
                except:
                    due_str = due_date
            else:
                due_str = ""
            
            # Format recurrence
            recurrence = task['recurrence'] or ""
            
            # Add to tree with color coding
            item_id = self.task_tree.insert("", tk.END,
                                          text=task['title'],
                                          values=(due_str, task['priority'], task['status'], recurrence),
                                          tags=(task['id'],))
            
            # Color code based on priority and status
            if task['status'] == 'Completed':
                self.task_tree.set(item_id, "status", "✓ Completed")
            elif "OVERDUE" in due_str:
                self.task_tree.item(item_id, tags=("overdue",))
            elif task['priority'] == 'High':
                self.task_tree.item(item_id, tags=("high_priority",))
        
        # Configure tags for colors
        self.task_tree.tag_configure("overdue", background="#ffcccc")
        self.task_tree.tag_configure("high_priority", background="#fff2cc")
    
    def filter_tasks(self, event=None):
        """Filter tasks by status"""
        self.load_tasks()
    
    def show_task_details(self, event=None):
        """Show details of selected task"""
        selection = self.task_tree.selection()
        if not selection:
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            self.details_text.config(state=tk.DISABLED)
            return
        
        task_id = self.task_tree.item(selection[0])['tags'][0]
        
        # Get task from database
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        
        if not task:
            return
        
        # Display task details
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        details = f"Title: {task['title']}\n\n"
        
        if task['description']:
            details += f"Description:\n{task['description']}\n\n"
        
        if task['due_date']:
            details += f"Due Date: {task['due_date']}\n"
        
        details += f"Priority: {task['priority']}\n"
        details += f"Status: {task['status']}\n"
        
        if task['recurrence']:
            details += f"Recurrence: {task['recurrence']}\n"
        
        details += f"\nCreated: {task['created_at']}\n"
        
        if task['updated_at'] != task['created_at']:
            details += f"Updated: {task['updated_at']}\n"
        
        if task['completed_at']:
            details += f"Completed: {task['completed_at']}\n"
        
        self.details_text.insert(1.0, details)
        self.details_text.config(state=tk.DISABLED)
    
    def add_task_dialog(self):
        """Show dialog to add new task"""
        self.task_dialog(mode="add")
    
    def edit_task_dialog(self, event=None):
        """Show dialog to edit selected task"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task to edit")
            return
        
        task_id = self.task_tree.item(selection[0])['tags'][0]
        self.task_dialog(mode="edit", task_id=task_id)
    
    def task_dialog(self, mode="add", task_id=None):
        """Show task add/edit dialog"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add Task" if mode == "add" else "Edit Task")
        dialog.geometry("500x400")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Load existing task data if editing
        task_data = None
        if mode == "edit" and task_id:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task_data = cursor.fetchone()
        
        # Form fields
        # Title
        ttk.Label(dialog, text="Title:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        title_entry = ttk.Entry(dialog, width=60)
        title_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Description
        ttk.Label(dialog, text="Description:").pack(anchor=tk.W, padx=10, pady=(0, 5))
        desc_text = tk.Text(dialog, height=6, wrap=tk.WORD)
        desc_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Due date frame
        date_frame = ttk.Frame(dialog)
        date_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(date_frame, text="Due Date:").pack(side=tk.LEFT)
        
        # Due date entries
        due_year = tk.StringVar()
        due_month = tk.StringVar()
        due_day = tk.StringVar()
        due_hour = tk.StringVar(value="23")
        due_minute = tk.StringVar(value="59")
        
        ttk.Entry(date_frame, textvariable=due_year, width=6).pack(side=tk.LEFT, padx=(10, 2))
        ttk.Label(date_frame, text="-").pack(side=tk.LEFT)
        ttk.Entry(date_frame, textvariable=due_month, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(date_frame, text="-").pack(side=tk.LEFT)
        ttk.Entry(date_frame, textvariable=due_day, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(date_frame, text=" ").pack(side=tk.LEFT, padx=5)
        ttk.Entry(date_frame, textvariable=due_hour, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(date_frame, text=":").pack(side=tk.LEFT)
        ttk.Entry(date_frame, textvariable=due_minute, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(date_frame, text="(YYYY-MM-DD HH:MM)").pack(side=tk.LEFT, padx=(10, 0))
        
        # Priority and recurrence frame
        options_frame = ttk.Frame(dialog)
        options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(options_frame, text="Priority:").pack(side=tk.LEFT)
        priority_var = tk.StringVar(value="Medium")
        priority_combo = ttk.Combobox(options_frame, textvariable=priority_var,
                                     values=["Low", "Medium", "High"], state="readonly", width=10)
        priority_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(options_frame, text="Recurrence:").pack(side=tk.LEFT)
        recurrence_var = tk.StringVar()
        recurrence_combo = ttk.Combobox(options_frame, textvariable=recurrence_var,
                                       values=["", "Daily", "Weekly", "Monthly"], state="readonly", width=10)
        recurrence_combo.pack(side=tk.LEFT, padx=5)
        
        # Fill form if editing
        if task_data:
            title_entry.insert(0, task_data['title'])
            if task_data['description']:
                desc_text.insert(1.0, task_data['description'])
            
            if task_data['due_date']:
                try:
                    due_dt = datetime.fromisoformat(task_data['due_date'])
                    due_year.set(str(due_dt.year))
                    due_month.set(f"{due_dt.month:02d}")
                    due_day.set(f"{due_dt.day:02d}")
                    due_hour.set(f"{due_dt.hour:02d}")
                    due_minute.set(f"{due_dt.minute:02d}")
                except:
                    pass
            
            priority_var.set(task_data['priority'])
            if task_data['recurrence']:
                recurrence_var.set(task_data['recurrence'])
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_task():
            title = title_entry.get().strip()
            description = desc_text.get(1.0, tk.END).strip()
            priority = priority_var.get()
            recurrence = recurrence_var.get() if recurrence_var.get() else None
            
            if not title:
                messagebox.showerror("Error", "Please enter a task title")
                return
            
            # Parse due date
            due_date = None
            if due_year.get() and due_month.get() and due_day.get():
                try:
                    year = int(due_year.get())
                    month = int(due_month.get())
                    day = int(due_day.get())
                    hour = int(due_hour.get()) if due_hour.get() else 23
                    minute = int(due_minute.get()) if due_minute.get() else 59
                    
                    due_date = datetime(year, month, day, hour, minute).isoformat()
                except ValueError:
                    messagebox.showerror("Error", "Invalid due date format")
                    return
            
            try:
                if mode == "add":
                    self.db.add_task(title, description, due_date, priority, recurrence)
                    messagebox.showinfo("Success", "Task added successfully!")
                else:
                    self.db.update_task(task_id, title=title, description=description,
                                      due_date=due_date, priority=priority, recurrence=recurrence)
                    messagebox.showinfo("Success", "Task updated successfully!")
                
                self.load_tasks()
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save task: {e}")
        
        ttk.Button(button_frame, text="Save", command=save_task).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
        
        title_entry.focus()
    
    def complete_task(self):
        """Mark selected task as completed"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task to complete")
            return
        
        task_id = self.task_tree.item(selection[0])['tags'][0]
        task_title = self.task_tree.item(selection[0])['text']
        
        if messagebox.askyesno("Confirm", f"Mark task '{task_title}' as completed?"):
            try:
                self.db.complete_task(task_id)
                self.load_tasks()
                messagebox.showinfo("Success", "Task marked as completed!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to complete task: {e}")
    
    def delete_task(self):
        """Delete selected task"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task to delete")
            return
        
        task_id = self.task_tree.item(selection[0])['tags'][0]
        task_title = self.task_tree.item(selection[0])['text']
        
        if messagebox.askyesno("Confirm", f"Delete task '{task_title}'?"):
            try:
                self.db.delete_task(task_id)
                self.load_tasks()
                messagebox.showinfo("Success", "Task deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete task: {e}")
    
    def send_reminders(self):
        """Send task reminders to Discord"""
        webhook_url = self.db.get_setting('discord_webhook_url')
        if not webhook_url:
            messagebox.showerror("Error", "No Discord webhook URL configured in Settings")
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
                    self.frame.after(0, lambda: messagebox.showinfo("Info", "No tasks due for reminders"))
                    return
                
                # Send task reminders in batches
                batches_sent = self.send_task_batches(webhook_url, due_tasks, today, "Task Reminder Bot", "⏰ **Task Reminders**")
                
                self.frame.after(0, lambda: messagebox.showinfo("Success", f"Sent reminders for {len(due_tasks)} tasks in {batches_sent} message(s)!"))
                
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Error", f"Failed to send reminders: {e}"))
        
        threading.Thread(target=send_in_thread, daemon=True).start()
    
    def send_task_batches(self, webhook_url, due_tasks, today, username="Task Reminder Bot", header="⏰ **Task Reminders**"):
        """Send task reminders in batches to respect Discord's character limit"""
        import time
        
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
            messagebox.showerror("Error", "No Discord webhook URL configured in Settings")
            return
        
        auto_reminders = self.db.get_setting('auto_task_reminders', 'true').lower() == 'true'
        if not auto_reminders:
            messagebox.showwarning("Warning", "Auto-reminders are disabled in Settings > Discord tab")
            return
        
        def test_in_thread():
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
                    self.frame.after(0, lambda: messagebox.showinfo("Info", "No tasks due for reminders"))
                    return
                
                # Send task reminders in batches with pings (same as auto system)
                header = "⏰ **Test Auto-Reminder System**"
                batches_sent = self.send_task_batches_with_ping(webhook_url, due_tasks, today, "Task Reminder Test", header)
                
                webhook_type = "task webhook" if task_webhook_url else "news webhook (fallback)"
                self.frame.after(0, lambda: messagebox.showinfo("Success", 
                    f"Auto-reminder test successful!\n"
                    f"Sent reminders for {len(due_tasks)} tasks in {batches_sent} message(s)\n"
                    f"Using: {webhook_type}\n\n"
                    f"This is how automatic daily reminders at 9 AM will work."))
                
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Error", f"Auto-reminder test failed: {e}"))
        
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    def send_task_batches_with_ping(self, webhook_url, due_tasks, today, username="Task Reminder Bot", header="⏰ **Task Reminders**"):
        """Send task reminders in batches with Discord pings"""
        import time
        
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