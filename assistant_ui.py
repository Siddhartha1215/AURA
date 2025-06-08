import tkinter as tk
from tkinter import ttk, messagebox
from db import save_schedule_to_mongo, get_schedule_from_mongo
import pymongo
from datetime import datetime
import threading
import sys
import os
import json
import importlib.util

# Try to import main functions with error handling
main_functions_available = False
try:
    # Check if main.py exists before importing
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'main.py')):
        # Import main module selectively to avoid issues with pywhatkit
        spec = importlib.util.spec_from_file_location("main", 
                                                     os.path.join(os.path.dirname(__file__), 'main.py'))
        main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main)
        
        # Now reference the functions we need
        speak = main.speak
        command = main.command
        cal_day = main.cal_day
        social_media = main.social_media
        openApp = main.openApp
        closeApp = main.closeApp
        system_settings = main.system_settings
        wiki_search = main.wiki_search
        
        main_functions_available = True
    else:
        print("Warning: main.py not found")
except Exception as e:
    print(f"Error importing from main.py: {e}")

class AssistantUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AURA Assistant")
        self.root.geometry("800x600")
        
        # Path for local storage as MongoDB fallback
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.schedule_file = os.path.join(self.data_dir, "schedules.json")
        
        # Initialize storage mechanism with fallbacks
        self.db_connected = False
        self.client = None
        self.db = None
        self.schedule_collection = None
        
        try:
            # Try MongoDB connection with short timeout
            self.client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
            # Quick connection test 
            self.client.server_info()
            self.db = self.client["assistant_db"]
            self.schedule_collection = self.db["schedules"]
            self.db_connected = True
            print("Successfully connected to MongoDB")
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            print("Using local file storage instead")
            # Don't show error message here - we'll use local storage
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.schedule_tab = ttk.Frame(self.notebook)
        self.commands_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.schedule_tab, text="Schedule")
        self.notebook.add(self.commands_tab, text="Commands")
        self.notebook.add(self.settings_tab, text="Settings")
        
        # Initialize tabs
        self.init_schedule_tab()
        self.init_commands_tab()
        self.init_settings_tab()
    
    def get_local_schedules(self):
        """Read schedule data from local file"""
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading schedule file: {e}")
        return {}
    
    def save_local_schedules(self, schedules):
        """Save schedule data to local file"""
        try:
            with open(self.schedule_file, 'w') as f:
                json.dump(schedules, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving schedule file: {e}")
            return False
            
    def init_schedule_tab(self):
        # Days frame
        days_frame = ttk.Frame(self.schedule_tab)
        days_frame.pack(fill='x', pady=10)

        self.selected_day = tk.StringVar(value="monday")
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        for day in days:
            ttk.Radiobutton(days_frame, text=day.capitalize(), variable=self.selected_day, value=day).pack(side='left', padx=5)

        # Schedule entries frame
        self.schedule_frame = ttk.LabelFrame(self.schedule_tab, text="Day Schedule")
        self.schedule_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Time slots
        time_slots_frame = ttk.Frame(self.schedule_frame)
        time_slots_frame.pack(fill='x', pady=5)
        
        ttk.Label(time_slots_frame, text="Time Slot").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(time_slots_frame, text="Activity").grid(row=0, column=1, padx=5, pady=5)
        
        self.time_slots = [
            "9:00-9:50", "10:00-10:50", "11:00-11:50", "12:00-12:50",
            "1:00-2:00", "2:00-3:50"
        ]
        
        self.schedule_entries = {}
        
        for i, time_slot in enumerate(self.time_slots):
            ttk.Label(time_slots_frame, text=time_slot).grid(row=i+1, column=0, padx=5, pady=5)
            entry = ttk.Entry(time_slots_frame, width=50)
            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky='w')
            self.schedule_entries[time_slot] = entry
        
        # Buttons
        buttons_frame = ttk.Frame(self.schedule_tab)
        buttons_frame.pack(fill='x', pady=10)
        
        ttk.Button(buttons_frame, text="Save Schedule", command=self.save_schedule).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Clear Fields", command=self.clear_schedule_fields).pack(side='left', padx=5)
        
        # Try MongoDB connection button
        # ttk.Button(buttons_frame, text="Try MongoDB Connection", 
        #          command=self.try_mongodb_connection).pack(side='right', padx=5)
        
        # Load initial schedule
        self.load_schedule()
    
    def try_mongodb_connection(self):
        """Attempt to connect to MongoDB"""
        if self.db_connected:
            messagebox.showinfo("Database", "Already connected to MongoDB")
            return
            
        try:
            # Try MongoDB connection with short timeout
            self.client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
            # Quick connection test 
            self.client.server_info()
            self.db = self.client["assistant_db"]
            self.schedule_collection = self.db["schedules"]
            self.db_connected = True
            self.db_status.set("Connected to MongoDB")
            
            # Transfer local data to MongoDB
            local_schedules = self.get_local_schedules()
            if local_schedules:
                for day, schedule in local_schedules.items():
                    self.schedule_collection.update_one(
                        {"day": day},
                        {"$set": schedule},
                        upsert=True
                    )
                
            messagebox.showinfo("Database", "Successfully connected to MongoDB")
            self.load_schedule() # Reload from MongoDB
            
        except Exception as e:
            self.db_connected = False
            messagebox.showerror("Database Error", f"Could not connect to MongoDB: {e}")
    
    def init_commands_tab(self):
        # Voice command test area
        test_frame = ttk.LabelFrame(self.commands_tab, text="Test Voice Commands")
        test_frame.pack(fill='x', padx=10, pady=10)
        
        # Status label for voice commands
        self.voice_status = tk.StringVar(value="Voice Commands: " + 
                                       ("Available" if main_functions_available else "Unavailable"))
        status_label = ttk.Label(test_frame, textvariable=self.voice_status, 
                              foreground="green" if main_functions_available else "red")
        status_label.pack(padx=10, pady=5)
        
        # Add buttons frame
        buttons_frame = ttk.Frame(test_frame)
        buttons_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Start Listening", 
                 command=self.start_voice_command,
                 state="normal" if main_functions_available else "disabled").pack(side='left', padx=5)
        
        # Add text input as fallback
        ttk.Label(test_frame, text="Or type your command:").pack(anchor='w', padx=10, pady=5)
        
        text_input_frame = ttk.Frame(test_frame)
        text_input_frame.pack(fill='x', padx=10, pady=5)
        
        self.command_input = ttk.Entry(text_input_frame, width=50)
        self.command_input.pack(side='left', padx=5, fill='x', expand=True)
        self.command_input.bind('<Return>', lambda e: self.process_text_command())
        
        ttk.Button(text_input_frame, text="Submit", 
                 command=self.process_text_command).pack(side='right', padx=5)
        
        # Recent commands list
        history_frame = ttk.LabelFrame(self.commands_tab, text="Command History")
        history_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.command_history = tk.Listbox(history_frame, height=15)
        self.command_history.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Add some dummy history
        for cmd in ["open calculator", "what's the weather", "schedule for today"]:
            self.command_history.insert(tk.END, cmd)
    
    def init_settings_tab(self):
        # Voice settings
        voice_frame = ttk.LabelFrame(self.settings_tab, text="Voice Settings")
        voice_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(voice_frame, text="Voice Type:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.voice_type = tk.StringVar(value="Default Female")
        voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_type, 
                                 values=["Default Female", "Default Male"])
        voice_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(voice_frame, text="Speech Rate:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.speech_rate = tk.IntVar(value=50)
        rate_scale = ttk.Scale(voice_frame, from_=0, to=100, orient='horizontal', variable=self.speech_rate)
        rate_scale.grid(row=1, column=1, padx=5, pady=5, sticky='we')
        
        # Application settings
        app_frame = ttk.LabelFrame(self.settings_tab, text="Application Settings")
        app_frame.pack(fill='x', padx=10, pady=10)
        
        self.start_with_windows = tk.BooleanVar(value=False)
        ttk.Checkbutton(app_frame, text="Start with Windows", 
                      variable=self.start_with_windows).pack(anchor='w', padx=5, pady=2)
        
        self.minimize_to_tray = tk.BooleanVar(value=False)
        ttk.Checkbutton(app_frame, text="Minimize to tray", 
                      variable=self.minimize_to_tray).pack(anchor='w', padx=5, pady=2)
        
        self.enable_voice = tk.BooleanVar(value=True)
        ttk.Checkbutton(app_frame, text="Enable voice activation", 
                      variable=self.enable_voice).pack(anchor='w', padx=5, pady=2)
    
    def test_mongo_connection(self):
        """Test MongoDB connection with the URL from settings"""
        url = self.mongo_url.get()
        try:
            # Try connection with URL from settings
            client = pymongo.MongoClient(url, serverSelectionTimeoutMS=2000)
            client.server_info()  # Will raise exception if connection fails
            
            # Update connection if successful
            self.client = client
            self.db = self.client["assistant_db"]
            self.schedule_collection = self.db["schedules"]
            self.db_connected = True
            self.db_status.set("Connected to MongoDB")
            
            messagebox.showinfo("Connection Test", "Successfully connected to MongoDB!")
        except Exception as e:
            messagebox.showerror("Connection Test", f"Failed to connect: {e}")
    
    def export_data(self):
        """Export all schedule data to a JSON file"""
        export_file = os.path.join(self.data_dir, f"schedule_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        try:
            if self.db_connected:
                # Export from MongoDB
                schedules = list(self.schedule_collection.find({}, {'_id': 0}))
                export_data = {item['day']: item for item in schedules}
            else:
                # Export from local storage
                export_data = self.get_local_schedules()
                
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
                
            messagebox.showinfo("Export", f"Data exported successfully to {export_file}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {e}")
        
    def load_schedule(self):
        day = self.selected_day.get()
        try:
            schedule = get_schedule_from_mongo(day)
            if schedule:
                for slot, entry in self.schedule_entries.items():
                    entry.delete(0, tk.END)
                    entry.insert(0, schedule.get(slot, ""))
            else:
                for entry in self.schedule_entries.values():
                    entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load schedule: {e}")
    
    def save_schedule(self):
        day = self.selected_day.get()
        schedule = {slot: entry.get() for slot, entry in self.schedule_entries.items()}
        try:
            save_schedule_to_mongo(day, schedule)
            messagebox.showinfo("Success", f"Schedule for {day.capitalize()} saved to database.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save schedule: {e}")

    def clear_schedule_fields(self):
        for entry in self.schedule_entries.values():
            entry.delete(0, tk.END)
    
    def start_voice_command(self):
        if not main_functions_available:
            messagebox.showerror("Error", "Voice command functions not available")
            return
        
        # Use a thread to prevent UI freezing during voice recognition
        def voice_command_thread():
            # Update UI to show listening status
            self.root.title("AURA Assistant (Listening...)")
            speak("I'm listening")
            
            # Get the command using the imported function
            query = command().lower()
            
            # Add command to history
            if query != "none":
                self.command_history.insert(0, query)  # Add to top of list
                # Process the command
                self.process_command(query)
            else:
                speak("Sorry, I didn't catch that")
            
            # Reset UI
            self.root.title("AURA Assistant")
        
        # Start the voice command in a separate thread
        threading.Thread(target=voice_command_thread).start()
    
    def process_command(self, query):
        """Process voice commands and update UI accordingly"""
        response = "Command received: " + query

        try:
            # Handle social media commands
            if ('facebook' in query) or ('discord' in query) or ('whatsapp' in query) or ('instagram' in query):
                social_media(query)
                response = f"Opening {query}"

            # Handle schedule requests
            elif "schedule" in query:
                day = cal_day().lower()
                # Show schedule in UI
                self.notebook.select(self.schedule_tab)
                self.selected_day.set(day)
                self.load_schedule()
                response = f"Showing schedule for {day}"

            # Handle app commands
            elif "open" in query and any(app in query for app in ["calculator", "notepad", "paint", "vs code", "vlc", "powerpoint", "word", "excel", "chrome"]):
                openApp(query)
                response = f"Opening {query.replace('open ', '')}"

            # Handle close app commands
            elif "close" in query and any(app in query for app in ["calculator", "notepad", "paint", "vs code", "vlc", "powerpoint", "word", "excel", "chrome"]):
                closeApp(query)
                response = f"Closing {query.replace('close ', '')}"

            # Handle system settings
            elif any(setting in query for setting in ["brightness", "wifi", "bluetooth", "night mode", "display", "sound"]):
                system_settings(query)
                response = f"Adjusting {query} settings"

            # Handle Wikipedia searches
            elif "wikipedia" in query:
                # This will be handled by wiki_search function which already speaks the response
                wiki_search(query)
                response = "Searched Wikipedia for " + query.replace("wikipedia", "").strip()

        except Exception as e:
            response = f"Error processing command: {e}"
            print(f"Command processing error: {e}")

        # Log the response
        print(response)
        speak(response)
        # messagebox.showinfo("Command Response", response)  # <-- Remove or comment out this line

    def process_text_command(self):
        """Process commands entered via text input"""
        query = self.command_input.get().strip().lower()
        if query:
            self.command_history.insert(0, query)  # Add to top of list
            self.command_input.delete(0, tk.END)  # Clear input field
            self.process_command(query)

if __name__ == "__main__":
    root = tk.Tk()
    app = AssistantUI(root)
    root.mainloop()
