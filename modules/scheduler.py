"""
Scheduler module for background tasks
Handles periodic news fetching and recurring task management
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
import requests

class SchedulerManager:
    def __init__(self, db):
        self.db = db
        self.running = False
        self.scheduler_thread = None
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Schedule jobs
        self.setup_jobs()
    
    def setup_jobs(self):
        """Set up scheduled jobs"""
        # News fetching every hour
        schedule.every().hour.do(self.fetch_news_job)
        
        # Auto-send news every hour (5 minutes after fetching)
        schedule.every().hour.at(":05").do(self.auto_send_news_job)
        
        # Check for recurring tasks daily at midnight
        schedule.every().day.at("00:00").do(self.process_recurring_tasks)
        
        # Send task reminders daily at 9 AM
        schedule.every().day.at("09:00").do(self.send_task_reminders)
        
        self.logger.info("Scheduled jobs set up successfully")
    
    def start(self):
        """Start the scheduler"""
        self.running = True
        self.logger.info("Scheduler started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        self.logger.info("Scheduler stopped")
    
    def fetch_news_job(self):
        """Scheduled job to fetch news from all feeds"""
        try:
            self.logger.info("Starting scheduled news fetch")
            
            # Create a temporary news tab instance for fetching with AI summarization
            class TempNewsTab:
                def __init__(self, db):
                    self.db = db
                
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
                
                def fetch_all_news(self):
                    """Fetch news from all active feeds"""
                    import feedparser
                    
                    feeds = self.db.get_feeds()
                    
                    news_count = 0
                    for feed in feeds:
                        try:
                            # Parse RSS feed
                            parsed_feed = feedparser.parse(feed['url'])
                            
                            for entry in parsed_feed.entries[:5]:  # Limit to 5 most recent per feed
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
                            self.logger.error(f"Failed to fetch from feed {feed['name']}: {e}")
                    
                    self.logger.info(f"Fetched {news_count} new news items")
                    return news_count
            
            # Fetch news
            temp_tab = TempNewsTab(self.db)
            news_count = temp_tab.fetch_all_news()
            
        except Exception as e:
            self.logger.error(f"News fetch job failed: {e}")
    
    def auto_send_news_job(self):
        """Automatically send unsent news to Discord"""
        try:
            webhook_url = self.db.get_setting('discord_webhook_url')
            auto_send = self.db.get_setting('auto_send_news', 'true').lower() == 'true'
            
            if not webhook_url or not auto_send:
                return
            
            # Get unsent news items
            unsent_news = self.db.get_unsent_news_items(10)
            
            if not unsent_news:
                self.logger.info("No unsent news items to send")
                return
            
            self.logger.info(f"Auto-sending {len(unsent_news)} unsent news items to Discord")
            
            # Send news in batches with pings
            header = f"📰 **Hourly News Update** ({len(unsent_news)} new items)"
            batches_sent = self.send_news_batches_with_ping(webhook_url, unsent_news, "News Bot (Auto)", header)
            
            # Mark items as sent
            news_ids = [item['id'] for item in unsent_news]
            self.db.mark_news_items_as_sent(news_ids)
            
            self.logger.info(f"Auto-sent news to Discord successfully in {batches_sent} message(s)")
            
        except Exception as e:
            self.logger.error(f"Auto-send news job failed: {e}")
    
    def send_news_batches_with_ping(self, webhook_url, news_items, username="News Bot", header="📰 **News Update**"):
        """Send news items in batches with Discord pings"""
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
    
    def send_news_batches(self, webhook_url, news_items, username="News Bot", header="📰 **News Update**"):
        """Send news items in batches to respect Discord's character limit"""
        import time
        
        batches = []
        current_batch = f"{header}\n\n"
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
                current_batch = f"{header} (Part {batch_count + 1})\n\n{item_text}"
            else:
                current_batch += item_text
        
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
    
    def send_task_batches(self, webhook_url, due_tasks, today, username="Task Reminder Bot", header="⏰ **Task Reminders**"):
        """Send task reminders in batches to respect Discord's character limit"""
        import time
        
        batches = []
        current_batch = f"{header}\n\n"
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
                current_batch = f"{header} (Part {batch_count + 1})\n\n{task_text}"
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
    
    def process_recurring_tasks(self):
        """Process recurring tasks and create new instances"""
        try:
            self.logger.info("Processing recurring tasks")
            
            # Get all recurring tasks
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT * FROM tasks 
                WHERE recurrence IS NOT NULL AND recurrence != ''
                AND status = 'Completed'
            ''')
            recurring_tasks = cursor.fetchall()
            
            today = datetime.now().date()
            new_tasks = 0
            
            for task in recurring_tasks:
                try:
                    # Check if we need to create a new instance
                    completed_date = None
                    if task['completed_at']:
                        completed_date = datetime.fromisoformat(task['completed_at']).date()
                    
                    should_create = False
                    new_due_date = None
                    
                    if task['recurrence'] == 'Daily':
                        if completed_date and completed_date < today:
                            should_create = True
                            new_due_date = today
                    
                    elif task['recurrence'] == 'Weekly':
                        if completed_date and (today - completed_date).days >= 7:
                            should_create = True
                            new_due_date = today + timedelta(days=7)
                    
                    elif task['recurrence'] == 'Monthly':
                        if completed_date and (today - completed_date).days >= 30:
                            should_create = True
                            new_due_date = today + timedelta(days=30)
                    
                    if should_create:
                        # Create new task instance
                        due_datetime = None
                        if new_due_date and task['due_date']:
                            # Preserve the time from original due date
                            original_due = datetime.fromisoformat(task['due_date'])
                            due_datetime = datetime.combine(new_due_date, original_due.time()).isoformat()
                        
                        self.db.add_task(
                            title=task['title'],
                            description=task['description'],
                            due_date=due_datetime,
                            priority=task['priority'],
                            recurrence=task['recurrence']
                        )
                        new_tasks += 1
                        
                        self.logger.info(f"Created new recurring task: {task['title']}")
                
                except Exception as e:
                    self.logger.error(f"Failed to process recurring task {task['title']}: {e}")
            
            if new_tasks > 0:
                self.logger.info(f"Created {new_tasks} new recurring task instances")
            
        except Exception as e:
            self.logger.error(f"Recurring tasks processing failed: {e}")
    
    def send_task_reminders(self):
        """Send task reminders to Discord automatically"""
        try:
            # Use separate task webhook or fall back to news webhook
            task_webhook_url = self.db.get_setting('discord_task_webhook_url')
            news_webhook_url = self.db.get_setting('discord_webhook_url')
            webhook_url = task_webhook_url or news_webhook_url
            
            auto_reminders = self.db.get_setting('auto_task_reminders', 'true').lower() == 'true'
            
            if not webhook_url or not auto_reminders:
                self.logger.info("Task reminders disabled or no webhook configured")
                return
            
            self.logger.info("Sending automatic task reminders")
            
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
                self.logger.info("No tasks due for reminders")
                return
            
            # Send task reminders in batches with pings
            header = "⏰ **Daily Task Reminders**"
            batches_sent = self.send_task_batches_with_ping(webhook_url, due_tasks, today, "Task Reminder Bot (Auto)", header)
            
            self.logger.info(f"Auto-sent reminders for {len(due_tasks)} tasks in {batches_sent} message(s)")
            
        except Exception as e:
            self.logger.error(f"Failed to send task reminders: {e}")
    
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
    
    def run_job_now(self, job_name):
        """Manually run a specific job"""
        try:
            if job_name == "fetch_news":
                self.fetch_news_job()
            elif job_name == "recurring_tasks":
                self.process_recurring_tasks()
            elif job_name == "task_reminders":
                self.send_task_reminders()
            elif job_name == "auto_send_news":
                self.auto_send_news_job()
            else:
                self.logger.error(f"Unknown job: {job_name}")
        except Exception as e:
            self.logger.error(f"Failed to run job {job_name}: {e}")
    
    def test_task_reminders(self):
        """Test task reminders (same as automatic but with different header)"""
        try:
            # Use separate task webhook or fall back to news webhook
            task_webhook_url = self.db.get_setting('discord_task_webhook_url')
            news_webhook_url = self.db.get_setting('discord_webhook_url')
            webhook_url = task_webhook_url or news_webhook_url
            
            if not webhook_url:
                raise Exception("No webhook URL configured")
            
            self.logger.info("Testing task reminders")
            
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
                self.logger.info("No tasks due for reminders")
                return 0
            
            # Send task reminders in batches with pings
            header = "⏰ **Task Reminder Test**"
            batches_sent = self.send_task_batches_with_ping(webhook_url, due_tasks, today, "Task Reminder Test", header)
            
            self.logger.info(f"Test sent reminders for {len(due_tasks)} tasks in {batches_sent} message(s)")
            return len(due_tasks)
            
        except Exception as e:
            self.logger.error(f"Failed to test task reminders: {e}")
            raise