"""
News Summary Tab
Handles RSS feed management, news fetching, and summarization
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime
import feedparser
import requests
import google.generativeai as genai
from urllib.parse import urlparse
import logging

class NewsTab:
    def __init__(self, parent, db, scheduler):
        self.parent = parent
        self.db = db
        self.scheduler = scheduler
        
        self.frame = ttk.Frame(parent)
        self.create_widgets()
        self.load_news()
    
    def create_widgets(self):
        """Create the news tab widgets"""
        # Main container with paned window
        paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Feed management
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        # Feed management section
        feed_frame = ttk.LabelFrame(left_frame, text="RSS Feeds", padding=10)
        feed_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Feed list
        self.feed_tree = ttk.Treeview(feed_frame, columns=("url",), show="tree headings", height=8)
        self.feed_tree.heading("#0", text="Name")
        self.feed_tree.heading("url", text="URL")
        self.feed_tree.column("#0", width=150)
        self.feed_tree.column("url", width=300)
        
        feed_scroll = ttk.Scrollbar(feed_frame, orient=tk.VERTICAL, command=self.feed_tree.yview)
        self.feed_tree.configure(yscrollcommand=feed_scroll.set)
        
        self.feed_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        feed_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Feed controls
        feed_controls = ttk.Frame(left_frame)
        feed_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(feed_controls, text="Add Feed", command=self.add_feed_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(feed_controls, text="Remove Feed", command=self.remove_feed).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(feed_controls, text="Fetch Now", command=self.fetch_news_manual).pack(side=tk.LEFT, padx=(0, 5))
        
        # News controls
        news_controls = ttk.Frame(left_frame)
        news_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(news_controls, text="Send to Discord", command=self.send_to_discord).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(news_controls, text="Refresh View", command=self.load_news).pack(side=tk.LEFT, padx=(0, 5))
        
        # Right panel - News display
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        
        # News list
        news_frame = ttk.LabelFrame(right_frame, text="Recent News", padding=10)
        news_frame.pack(fill=tk.BOTH, expand=True)
        
        # News treeview
        self.news_tree = ttk.Treeview(news_frame, columns=("source", "published"), show="tree headings")
        self.news_tree.heading("#0", text="Title")
        self.news_tree.heading("source", text="Source")
        self.news_tree.heading("published", text="Published")
        self.news_tree.column("#0", width=400)
        self.news_tree.column("source", width=150)
        self.news_tree.column("published", width=150)
        
        news_scroll = ttk.Scrollbar(news_frame, orient=tk.VERTICAL, command=self.news_tree.yview)
        self.news_tree.configure(yscrollcommand=news_scroll.set)
        
        self.news_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        news_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to show details
        self.news_tree.bind("<Double-1>", self.show_news_details)
        
        # Load feeds
        self.load_feeds()
    
    def load_feeds(self):
        """Load RSS feeds into the tree"""
        # Clear existing items
        for item in self.feed_tree.get_children():
            self.feed_tree.delete(item)
        
        # Load feeds from database
        feeds = self.db.get_feeds()
        for feed in feeds:
            self.feed_tree.insert("", tk.END, text=feed['name'], values=(feed['url'],), tags=(feed['id'],))
    
    def load_news(self):
        """Load news items into the tree"""
        # Clear existing items
        for item in self.news_tree.get_children():
            self.news_tree.delete(item)
        
        # Load news from database
        news_items = self.db.get_news_items(50)
        for item in news_items:
            published = item['published'] or item['created_at']
            if published:
                try:
                    pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    pub_str = pub_date.strftime("%Y-%m-%d %H:%M")
                except:
                    pub_str = published[:16] if published else "Unknown"
            else:
                pub_str = "Unknown"
            
            self.news_tree.insert("", tk.END, 
                                text=item['title'][:80] + ("..." if len(item['title']) > 80 else ""),
                                values=(item['feed_name'], pub_str),
                                tags=(item['id'],))
    
    def add_feed_dialog(self):
        """Show dialog to add new RSS feed"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add RSS Feed")
        dialog.geometry("400x150")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Form fields
        ttk.Label(dialog, text="Feed Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=50)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Feed URL:").pack(pady=5)
        url_entry = ttk.Entry(dialog, width=50)
        url_entry.pack(pady=5)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def add_feed():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            
            if not name or not url:
                messagebox.showerror("Error", "Please enter both name and URL")
                return
            
            try:
                # Validate URL by trying to parse the feed
                feed = feedparser.parse(url)
                if feed.bozo and not feed.entries:
                    messagebox.showerror("Error", "Invalid RSS feed URL")
                    return
                
                # Add to database
                self.db.add_feed(name, url)
                self.load_feeds()
                dialog.destroy()
                messagebox.showinfo("Success", "Feed added successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add feed: {e}")
        
        ttk.Button(button_frame, text="Add", command=add_feed).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        name_entry.focus()
    
    def remove_feed(self):
        """Remove selected RSS feed"""
        selection = self.feed_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a feed to remove")
            return
        
        item = self.feed_tree.item(selection[0])
        feed_name = item['text']
        feed_id = item['tags'][0]
        
        if messagebox.askyesno("Confirm", f"Remove feed '{feed_name}' and all its news items?"):
            try:
                self.db.delete_feed(feed_id)
                self.load_feeds()
                self.load_news()
                messagebox.showinfo("Success", "Feed removed successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove feed: {e}")
    
    def fetch_news_manual(self):
        """Manually fetch news from all feeds"""
        def fetch_in_thread():
            try:
                self.fetch_all_news()
                self.frame.after(0, lambda: messagebox.showinfo("Success", "News fetched successfully!"))
                self.frame.after(0, self.load_news)
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch news: {e}"))
        
        threading.Thread(target=fetch_in_thread, daemon=True).start()
    
    def fetch_all_news(self):
        """Fetch news from all active feeds"""
        feeds = self.db.get_feeds()
        
        for feed in feeds:
            try:
                # Parse RSS feed
                parsed_feed = feedparser.parse(feed['url'])
                
                for entry in parsed_feed.entries[:10]:  # Limit to 10 most recent
                    # Check if item already exists
                    title = entry.get('title', 'No title')
                    link = entry.get('link', '')
                    
                    if self.db.news_item_exists(feed['id'], title, link):
                        continue
                    
                    # Get description
                    description = entry.get('description', '') or entry.get('summary', '')
                    
                    # Generate AI summary if description is long enough and API is configured
                    summary = self.generate_summary(title, description)
                    
                    # Get published date
                    published = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6]).isoformat()
                    elif hasattr(entry, 'published'):
                        published = entry.published
                    
                    # Add to database
                    self.db.add_news_item(feed['id'], title, link, description, summary, published)
                
            except Exception as e:
                logging.error(f"Failed to fetch from feed {feed['name']}: {e}")
    
    def send_to_discord(self):
        """Send recent news summaries to Discord webhook in batches"""
        webhook_url = self.db.get_setting('discord_webhook_url')
        if not webhook_url:
            messagebox.showerror("Error", "No Discord webhook URL configured in Settings")
            return
        
        def send_in_thread():
            try:
                # Get recent news items
                news_items = self.db.get_news_items(10)  # Get more items for batching
                
                if not news_items:
                    self.frame.after(0, lambda: messagebox.showinfo("Info", "No news items to send"))
                    return
                
                # Send news in batches to respect Discord's 2000 character limit
                batches_sent = self.send_news_batches(webhook_url, news_items, "News Bot")
                
                self.frame.after(0, lambda: messagebox.showinfo("Success", f"News sent to Discord in {batches_sent} message(s)!"))
                
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Error", f"Failed to send to Discord: {e}"))
        
        threading.Thread(target=send_in_thread, daemon=True).start()
    
    def send_news_batches(self, webhook_url, news_items, username="News Bot", header="📰 **Latest News Summary**"):
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
                if len(summary) > 300:
                    summary = summary[:297] + "..."
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
    
    def show_news_details(self, event):
        """Show detailed view of selected news item"""
        selection = self.news_tree.selection()
        if not selection:
            return
        
        item_id = self.news_tree.item(selection[0])['tags'][0]
        
        # Get full news item from database
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT n.*, f.name as feed_name 
            FROM news_items n 
            JOIN feeds f ON n.feed_id = f.id 
            WHERE n.id = ?
        ''', (item_id,))
        news_item = cursor.fetchone()
        
        if not news_item:
            return
        
        # Create details window
        details_window = tk.Toplevel(self.frame)
        details_window.title("News Details")
        details_window.geometry("800x600")
        
        # Title
        title_label = ttk.Label(details_window, text=news_item['title'], font=("Arial", 12, "bold"))
        title_label.pack(pady=10, padx=10, anchor=tk.W)
        
        # Source and date
        info_frame = ttk.Frame(details_window)
        info_frame.pack(fill=tk.X, padx=10)
        
        ttk.Label(info_frame, text=f"Source: {news_item['feed_name']}").pack(anchor=tk.W)
        if news_item['published']:
            ttk.Label(info_frame, text=f"Published: {news_item['published']}").pack(anchor=tk.W)
        
        # Link
        if news_item['link']:
            link_frame = ttk.Frame(details_window)
            link_frame.pack(fill=tk.X, padx=10, pady=5)
            ttk.Label(link_frame, text="Link:").pack(anchor=tk.W)
            link_text = tk.Text(link_frame, height=2, wrap=tk.WORD)
            link_text.insert(tk.END, news_item['link'])
            link_text.config(state=tk.DISABLED)
            link_text.pack(fill=tk.X)
        
        # Summary
        if news_item['summary']:
            ttk.Label(details_window, text="Summary:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))
            summary_text = scrolledtext.ScrolledText(details_window, height=8, wrap=tk.WORD)
            summary_text.insert(tk.END, news_item['summary'])
            summary_text.config(state=tk.DISABLED)
            summary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Original description
        if news_item['description'] and news_item['description'] != news_item['summary']:
            ttk.Label(details_window, text="Original Description:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))
            desc_text = scrolledtext.ScrolledText(details_window, height=8, wrap=tk.WORD)
            desc_text.insert(tk.END, news_item['description'])
            desc_text.config(state=tk.DISABLED)
            desc_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Close button
        ttk.Button(details_window, text="Close", command=details_window.destroy).pack(pady=10)
    
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