import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import main
import queue
import json
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import random

class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AURA Voice Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg='#2C3E50')
        
        # Initialize LLM client
        self.llm = main.init_chat_model("meta-llama/llama-4-scout-17b-16e-instruct", model_provider="groq")
    
        # Message queue for thread-safe GUI updates
        self.msg_queue = queue.Queue()
        
        self.create_widgets()
        self.update_gui()
        
    def create_widgets(self):
        # Title
        title_label = tk.Label(
            self.root, 
            text="AURA Voice Assistant",
            font=("Helvetica", 24, "bold"),
            bg='#2C3E50',
            fg='white'
        )
        title_label.pack(pady=20)

        # Output Display
        self.output_area = scrolledtext.ScrolledText(
            self.root,
            width=70,
            height=20,
            font=("Helvetica", 10),
            bg='#34495E',
            fg='white'
        )
        self.output_area.pack(pady=10, padx=20)

        # Status Label
        self.status_label = tk.Label(
            self.root,
            text="Status: Ready",
            font=("Helvetica", 12),
            bg='#2C3E50',
            fg='white'
        )
        self.status_label.pack(pady=10)

        # Control Buttons Frame
        button_frame = tk.Frame(self.root, bg='#2C3E50')
        button_frame.pack(pady=20)

        # Start Button
        self.start_button = ttk.Button(
            button_frame,
            text="Start Listening",
            command=self.start_assistant
        )
        self.start_button.pack(side=tk.LEFT, padx=10)

        # Stop Button
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self.stop_assistant,
            state='disabled'
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # Running flag
        self.running = False

    def update_gui(self):
        """Update GUI with messages from the queue"""
        try:
            while True:
                message = self.msg_queue.get_nowait()
                self.output_area.insert(tk.END, message + "\n")
                self.output_area.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.update_gui)

    def start_assistant(self):
        self.running = True
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.status_label.configure(text="Status: Listening...")
        
        # Start assistant in a separate thread
        self.assistant_thread = threading.Thread(target=self.run_assistant)
        self.assistant_thread.daemon = True
        self.assistant_thread.start()

    def stop_assistant(self):
        self.running = False
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.status_label.configure(text="Status: Stopped")

    def run_assistant(self):
        """Handle assistant responses and actions"""
        # main.wishMe()
        
        while self.running:
            query = main.command().lower()
            if query != "none":
                # Display user's query
                self.msg_queue.put(f"You: {query}")
                
                # Process the query and get response
                response = self.process_query(query)
                
                # Display assistant's response
                self.msg_queue.put(f"AURA: {response}")
                
    def process_query(self, query):
        """Process user query and return appropriate response"""
        try:
            # Social media commands
            if ('facebook' in query) or ('discord' in query) or ('whatsapp' in query) or ('instagram' in query):
                main.social_media(query)
                return f"Opening {query}"
                
            # Schedule related
            elif ("university time table" in query) or ("schedule" in query):
                main.schedule()
                return "Here's your schedule"
                
            # Volume controls
            elif ("volume up" in query) or ("increase volume" in query) or ("increase the volume" in query):
                main.pyautogui.press("volumeup")
                return "Volume increased"
                
            elif ("volume down" in query) or ("decrease volume" in query) or ("decrease volume" in query):
                main.pyautogui.press("volumedown")
                return "Volume decreased"
                
            elif ("volume mute" in query) or ("mute the sound" in query):
                main.pyautogui.press("volumemute")
                return "Volume muted"
                
            # App operations
            elif any(x in query for x in ["open calculator", "open notepad", "open paint", 
                    "open vs code", "open vlc", "open powerpoint", "open word", 
                    "open excel", "open chrome"]):
                main.openApp(query)
                return f"Opening {query.replace('open', '').strip()}"
                
            elif any(x in query for x in ["close calculator", "close notepad", "close paint", 
                    "close vs code", "close vlc", "close powerpoint", "close word", 
                    "close excel", "close chrome"]):
                main.closeApp(query)
                return f"Closing {query.replace('close', '').strip()}"
                
            # Browser operations
            elif ("open google" in query) or ("open edge" in query):
                main.browsing(query)
                return "Opening browser"
                
            # System condition
            elif ("system condition" in query) or ("condition of the system" in query):
                main.condition()
                return "Checking system condition"
                
            # Wikipedia
            elif 'wikipedia' in query:
                result = main.wiki_search(query)
                return result
                
            # Settings
            elif any(word in query for word in ["settings", "airplane mode", "aeroplane mode", 
                    "bluetooth", "wifi", "display", "sound", "theme", "update"]):
                main.system_settings(query)
                return "Adjusting system settings"
                
            # General queries
            elif any(word in query for word in ["what", "who", "how", "hi", "thanks", "hello"]):
                response = main.query_llm(query, main.llm)
                return response
                
            # Exit command
            elif "exit" in query:
                self.stop_assistant()
                return "Goodbye! Have a great day!"
                
            else:
                # Use your existing ML model for other intents
                texts_p = []
                prediction_input = [query]
                prediction_input = main.tokenizer.texts_to_sequences(prediction_input)
                prediction_input = pad_sequences(prediction_input, maxlen=20, padding='post')
                prediction = main.model.predict(prediction_input)
                predicted_label = main.label_encoder.inverse_transform([np.argmax(prediction)])
                
                for intent in main.data['intents']:
                    if intent['tag'] == predicted_label[0]:
                        response = random.choice(intent['responses'])
                        main.speak(response)
                        return response
                
                return "I'm not sure how to help with that"
                
        except Exception as e:
            print(f"Error processing query: {e}")
            return f"I encountered an error: {str(e)}"

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceAssistantGUI(root)
    root.mainloop()