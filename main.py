import datetime
import os
import smtplib
import sys
import time
import webbrowser
import pyautogui
import pyjokes
import pyttsx3 #!pip install pyttsx3
import speech_recognition as sr
import json
import pickle
import warnings
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
from sklearn.preprocessing import LabelEncoder
import screen_brightness_control as sbc
import random
import numpy as np
import psutil 
import subprocess
import pywhatkit as kit
import wikipedia
import groq
from dotenv import load_dotenv  # Add this import at the top

warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

# from elevenlabs import generate, play
# from elevenlabs import set_api_key
# from api_key import api_key_data
# set_api_key(api_key_data)

# def engine_talk(query):
#     audio = generate(
#         text=query, 
#         voice='Grace',
#         model="eleven_monolingual_v1"
#     )
#     play(audio)

with open("intents.json") as file:
    data = json.load(file)

model = load_model("chat_model.h5")

with open("stokenizer.pkl", "rb") as f:
    tokenizer = pickle.load(f)

with open("label_encoder.pkl", "rb") as encoder_file:
    label_encoder = pickle.load(encoder_file)

load_dotenv()  # Load environment variables from .env

def initialize_engine():
    # engine = pyttsx3.init('espeak')
    engine = pyttsx3.init("sapi5")
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-50)
    volume = engine.getProperty('volume')
    engine.setProperty('volume', volume+0.25)
    return engine

def speak(text):
    engine = initialize_engine()
    engine.say(text)
    engine.runAndWait()

def command():
    r = sr.Recognizer()
    query = "none"
    
    try:
        with sr.Microphone() as source:
            print("Listening...")
            # Adjust for ambient noise and set timeout
            r.adjust_for_ambient_noise(source, duration=0.5)
            r.pause_threshold = 1
            r.energy_threshold = 300  # Lower threshold for better detection
            
            # Listen for audio with a timeout
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
                print("Recognizing...")
            except sr.WaitTimeoutError:
                print("No audio detected within timeout period")
                speak("I didn't hear anything. Please try again.")
                return "none"
                
            # Try multiple recognition engines with error handling
            try:
                # Try Google's speech recognition first (requires internet)
                query = r.recognize_google(audio)
                print(f"User said: {query}")
            except sr.RequestError:
                # If Google fails, try Sphinx (offline, less accurate)
                try:
                    # This requires 'pip install pocketsphinx'
                    query = r.recognize_sphinx(audio)
                    print(f"User said (using Sphinx): {query}")
                except:
                    print("Sorry, speech recognition services unavailable")
                    speak("Sorry, I couldn't understand that")
                    return "none"
            except sr.UnknownValueError:
                print("Sorry, I did not understand what you said")
                speak("I didn't catch that. Please try again.")
                return "none"
                
    except Exception as e:
        print(f"Error accessing microphone: {e}")
        speak("I'm having trouble with your microphone. Please check your settings.")
        return "none"
        
    return query.lower()

def cal_day():
    day = datetime.datetime.today().weekday() + 1
    day_dict={
        1:"Monday",
        2:"Tuesday",
        3:"Wednesday",
        4:"Thursday",
        5:"Friday",
        6:"Saturday",
        7:"Sunday"
    }
    if day in day_dict.keys():
        day_of_week = day_dict[day]
        print(day_of_week)
    return day_of_week

def wishMe():
    hour = int(datetime.datetime.now().hour)
    t = time.strftime("%I:%M:%p")
    day = cal_day()

    if(hour>=0) and (hour<=12) and ('AM' in t):
        speak(f"Good morning Sir, it's {day} and the time is {t}")
    elif(hour>=12)  and (hour<=16) and ('PM' in t):
        speak(f"Good afternoon Sir, it's {day} and the time is {t}")
    else:
        speak(f"Good evening Sir, it's {day} and the time is {t}")

def social_media(command):
    if 'facebook' in command:
        speak("opening your facebook")
        webbrowser.open("https://www.facebook.com/")
    elif 'whatsapp' in command:
        # speak("opening your whatsapp")
        # speak("To whom should I send the message?")
        # print("Reciptent No: ")
        # number = input()
        # speak("Tell me the message please")
        # print("Message to send")
        # message = input()
        # kit.sendwhatmsg_instantly(number, message, 10)
        try:
            speak("Opening WhatsApp")
            subprocess.run([
                'powershell.exe',
                'start',
                'shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App'
            ])
            speak("WhatsApp opened successfully")                    
        except Exception as e:
            speak("Error opening WhatsApp. Opening WhatsApp Web instead.")
            print(f"Error: {e}")
            webbrowser.open("https://web.whatsapp.com/")
        
    elif 'discord' in command:
        speak("opening your discord server")
        webbrowser.open("https://discord.com/")
    elif 'instagram' in command:
        speak("opening your instagram")
        webbrowser.open("https://www.instagram.com/")
    else:
        speak("No result found")
        
def play_music(query):
    if "spotify" in query:
        speak("Opening Spotify...")
        webbrowser.open("https://www.spotify.com")
    elif "youtube" in query:
        speak("Opening YouTube...")
        webbrowser.open("https://www.youtube.com")
        
def schedule():
    day = cal_day().lower()
    speak("Boss today's schedule is ")
    week={
    "monday": "Boss, from 9:00 to 9:50 you have Algorithms class, from 10:00 to 11:50 you have System Design class, from 12:00 to 2:00 you have a break, and today you have Programming Lab from 2:00 onwards.",
    "tuesday": "Boss, from 9:00 to 9:50 you have Web Development class, from 10:00 to 10:50 you have a break, from 11:00 to 12:50 you have Database Systems class, from 1:00 to 2:00 you have a break, and today you have Open Source Projects lab from 2:00 onwards.",
    "wednesday": "Boss, today you have a full day of classes. From 9:00 to 10:50 you have Machine Learning class, from 11:00 to 11:50 you have Operating Systems class, from 12:00 to 12:50 you have Ethics in Technology class, from 1:00 to 2:00 you have a break, and today you have Software Engineering workshop from 2:00 onwards.",
    "thursday": "Boss, today you have a full day of classes. From 9:00 to 10:50 you have Computer Networks class, from 11:00 to 12:50 you have Cloud Computing class, from 1:00 to 2:00 you have a break, and today you have Cybersecurity lab from 2:00 onwards.",
    "friday": "Boss, today you have a full day of classes. From 9:00 to 9:50 you have Artificial Intelligence class, from 10:00 to 10:50 you have Advanced Programming class, from 11:00 to 12:50 you have UI/UX Design class, from 1:00 to 2:00 you have a break, and today you have Capstone Project work from 2:00 onwards.",
    "saturday": "Boss, today you have a more relaxed day. From 9:00 to 11:50 you have team meetings for your Capstone Project, from 12:00 to 12:50 you have Innovation and Entrepreneurship class, from 1:00 to 2:00 you have a break, and today you have extra time to work on personal development and coding practice from 2:00 onwards.",
    "sunday": "Boss, today is a holiday, but keep an eye on upcoming deadlines and use this time to catch up on any reading or project work."
    }
    if day in week.keys():
        speak(week[day])

def openApp(command):
    if "calculator" in command:
        speak("opening calculator")
        os.startfile('C:\\Windows\\System32\\calc.exe')
    elif "notepad" in command:
        speak("opening notepad")
        os.startfile('C:\\Windows\\System32\\notepad.exe')
    elif "paint" in command:
        speak("opening paint")
        os.startfile('C:\\Windows\\System32\\mspaint.exe')
    elif "vs code" in command or "visual studio code" in command:
        speak("opening visual studio code")
        try:
            os.startfile(os.path.join(os.environ['LOCALAPPDATA'], 'Programs', 'Microsoft VS Code', 'Code.exe'))
        except FileNotFoundError:
            speak("Sorry, I couldn't find Visual Studio Code on your system")
    elif "vlc" in command or "media player" in command:
        speak("opening vlc media player")
        try:
            os.startfile('C:\\Program Files\\VideoLAN\\VLC\\vlc.exe')
        except FileNotFoundError:
            speak("Sorry, I couldn't find VLC on your system")
    elif "powerpoint" in command or "presentation" in command:
        speak("opening microsoft powerpoint")
        try:
            os.startfile('C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE')
        except FileNotFoundError:
            speak("Sorry, I couldn't find PowerPoint on your system")
    elif "word" in command or "document" in command:
        speak("opening microsoft word")
        try:
            os.startfile('C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE')
        except FileNotFoundError:
            speak("Sorry, I couldn't find Word on your system")
    elif "excel" in command or "spreadsheet" in command:
        speak("opening microsoft excel")
        try:
            os.startfile('C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE')
        except FileNotFoundError:
            speak("Sorry, I couldn't find Excel on your system")
    elif "chrome" in command:
        speak("opening google chrome")
        try:
            os.startfile('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe')
        except FileNotFoundError:
            speak("Sorry, I couldn't find Chrome on your system")

def closeApp(command):
    if "calculator" in command:
        speak("closing calculator")
        os.system("taskkill /f /im calc.exe")
    elif "notepad" in command:
        speak("closing notepad")
        os.system('taskkill /f /im notepad.exe')
    elif "paint" in command:
        speak("closing paint")
        os.system('taskkill /f /im mspaint.exe')
    elif "vs code" in command or "visual studio code" in command:
        speak("closing visual studio code")
        os.system('taskkill /f /im Code.exe')
    elif "vlc" in command or "media player" in command:
        speak("closing vlc media player")
        os.system('taskkill /f /im vlc.exe')
    elif "powerpoint" in command or "presentation" in command:
        speak("closing microsoft powerpoint")
        os.system('taskkill /f /im POWERPNT.EXE')
    elif "word" in command or "document" in command:
        speak("closing microsoft word")
        os.system('taskkill /f /im WINWORD.EXE')
    elif "excel" in command or "spreadsheet" in command:
        speak("closing microsoft excel")
        os.system('taskkill /f /im EXCEL.EXE')
    elif "chrome" in command:
        speak("closing google chrome")
        os.system('taskkill /f /im chrome.exe')

def browsing(query):
    if 'google' in query:
        speak("Boss, what should i search on google..")
        s = command().lower()
        webbrowser.open(f"{s}")
    elif 'edge' in query:
        speak("opening your microsoft edge")
        try:
            # Try common Edge installation paths
            os.startfile("C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe")
        except FileNotFoundError:
            try:
                os.startfile("C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe")
            except FileNotFoundError:
                # Fallback to web if exe not found
                webbrowser.open("https://www.microsoft.com/edge")

def mail_sent(to, content):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login('your-email@example.com', 'your-app-password')  # Use app password
    server.sendmail('your-email@example.com', to, content)
    server.close()
    
def condition():
    usage = str(psutil.cpu_percent())
    speak(f"CPU is at {usage} percentage")
    battery = psutil.sensors_battery()
    percentage = battery.percent
    speak(f"Boss our system have {percentage} percentage battery")

    if percentage>=80:
        speak("Boss we could have enough charging to continue our recording")
    elif percentage>=40 and percentage<=75:
        speak("Boss we should connect our system to charging point to charge our battery")
    else:
        speak("Boss we have very low power, please connect to charging otherwise recording should be off...")

def tell_joke():
    joke = pyjokes.get_joke()
    speak(joke)

def wiki_search(query):
    speak('Give me sometime I am looking into Wikipedia')
    query = query.replace("wikipedia", "").strip()
    try:
        summary = wikipedia.summary(query, sentences=5)
        speak("This is what I found!")
        print(summary.prettyfy())
        speak(summary.prettyfy())
    except wikipedia.exceptions.DisambiguationError as e:
        speak(f"Your query is ambiguous. Here are some options: {e.options[:5]}")
    except wikipedia.exceptions.HTTPTimeoutError:
        speak("The request timed out. Please try again.")
    except wikipedia.exceptions.RedirectError:
        speak("The page has been redirected. Please try again.")
    except Exception as e:
        speak(f"An error occurred: {e}")

def system_settings(command):
    if "brightness" in command:
        if "increase" in command or "up" in command:
            speak("Increasing brightness")
            # Requires installing screen_brightness_control package
            try:
                current = sbc.get_brightness()[0]
                new_brightness = min(current + 10, 100)
                sbc.set_brightness(new_brightness)
                speak(f"Brightness set to {new_brightness} percent")
            except ImportError:
                speak("Sorry, I need the screen_brightness_control package to adjust brightness")
                speak("Please install it with: pip install screen_brightness_control")
        elif "decrease" in command or "down" in command:
            speak("Decreasing brightness")
            try:
                current = sbc.get_brightness()[0]
                new_brightness = max(current - 10, 0)
                sbc.set_brightness(new_brightness)
                speak(f"Brightness set to {new_brightness} percent")
            except ImportError:
                speak("Sorry, I need the screen_brightness_control package to adjust brightness")
    
    elif "wifi" in command:
        if "on" in command or "enable" in command:
            speak("Turning WiFi on")
            os.system("netsh interface set interface \"Wi-Fi\" enabled")
        elif "off" in command or "disable" in command:
            speak("Turning WiFi off")
            os.system("netsh interface set interface \"Wi-Fi\" disabled")
    
    elif "bluetooth" in command:
        if "on" in command or "enable" in command:
            speak("Turning Bluetooth on")
            os.system("start ms-settings:bluetooth")
            speak("I've opened Bluetooth settings for you")
        elif "off" in command or "disable" in command:
            speak("Turning Bluetooth off")
            os.system("start ms-settings:bluetooth")
            speak("I've opened Bluetooth settings for you")
    
    elif "night mode" in command or "night light" in command:
        speak("Opening night light settings")
        os.system("start ms-settings:nightlight")
    
    elif "airplane mode" in command:
        speak("Opening airplane mode settings")
        os.system("start ms-settings:network-airplanemode")
    
    elif "power" in command:
        speak("Opening power settings")
        os.system("start ms-settings:batterysaver")
    
    elif "display" in command:
        speak("Opening display settings")
        os.system("start ms-settings:display")
    
    elif "sound" in command or "audio" in command:
        speak("Opening sound settings")
        os.system("start ms-settings:sound")
    
    elif "theme" in command or "personalization" in command:
        speak("Opening personalization settings")
        os.system("start ms-settings:personalization")
    
    elif "update" in command:
        speak("Opening Windows Update")
        os.system("start ms-settings:windowsupdate")
    
    elif "control panel" in command:
        speak("Opening control panel")
        os.system("control panel")
    
    elif "settings" in command:
        speak("Opening Windows settings")
        os.system("start ms-settings:")
    
    else:
        speak("I'm not sure which setting you want to access")
    
def init_chat_model(model_name="llama3-70b-8192", model_provider="groq"):
    """Initialize the Groq LLM client."""
    try:
        import os
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            speak("GROQ_API_KEY not found in environment variables.")
            print("GROQ_API_KEY not found in environment variables.")
            return None
        groq_client = groq.Client(api_key=api_key)
        return groq_client
    except Exception as e:
        speak(f"Error initializing LLM: {e}")
        print(f"Error initializing LLM: {e}")
        return None

def query_llm(prompt, llm_client):
    """Send a query to the LLM and get the response."""
    try:
        if llm_client is None:
            speak("LLM client not initialized. Please check your API key.")
            return "I'm having trouble connecting to my knowledge base."
        
        # Call the Groq API with the prompt
        response = llm_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are AURA, a helpful AI assistant. Provide concise, accurate answers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        
        # Extract and return the response text
        return response.choices[0].message.content
    except Exception as e:
        speak(f"Error querying LLM: {e}")
        print(f"Error querying LLM: {e}")
        return "I encountered an error while processing your request."

if __name__ == "__main__":
    # Initialize the LLM client
    llm = init_chat_model("llama3-70b-8192", model_provider="groq")
    # speak("Hello, I'm AURA")
    wishMe()
    # engine_talk("Allow me to introduce myself I am Aura, the virtual artificial intelligence and I'm here to assist you with a variety of tasks as best I can, 24 hours a day seven days a week.")
    while True:
        query = command().lower()
        # query  = input("Enter your command-> ")
        if ('facebook' in query) or ('discord' in query) or ('whatsapp' in query) or ('instagram' in query):
            social_media(query)
        elif ("university time table" in query) or ("schedule" in query):
            schedule()
        elif ("volume up" in query) or ("increase volume" in query):
            pyautogui.press("volumeup")
            speak("Volume increased")
        elif ("volume down" in query) or ("decrease volume" in query):
            pyautogui.press("volumedown")
            speak("Volume decrease")
        elif ("volume mute" in query) or ("mute the sound" in query):
            pyautogui.press("volumemute")
            speak("Volume muted")
        elif ("open calculator" in query) or ("open notepad" in query) or ("open paint" in query) or ("open vs code" in query) or ("open vlc" in query) or ("open powerpoint" in query) or ("open word" in query) or ("open excel" in query) or ("open chrome" in query):
            openApp(query)
        elif ("close calculator" in query) or ("close notepad" in query) or ("close paint" in query) or ("close vs code" in query) or ("close vlc" in query) or ("close powerpoint" in query) or ("close word" in query) or ("close excel" in query) or ("close chrome" in query):
            closeApp(query)
        elif ("what" in query) or ("who" in query) or ("how" in query) or ("hi" in query) or ("thanks" in query) or ("hello" in query):
            # Try the existing model first for specific intents
            padded_sequences = pad_sequences(tokenizer.texts_to_sequences([query]), maxlen=20, truncating='post')
            result = model.predict(padded_sequences)
            tag = label_encoder.inverse_transform([np.argmax(result)])
            confidence = result[0][np.argmax(result)]
            
            # If high confidence (>0.8), use existing model response
            if confidence > 0.8:
                for i in data['intents']:
                    if i['tag'] == tag:
                        speak(np.random.choice(i['responses']))
            # Otherwise, use LLaMA model for more complex queries
            else:
                print("Using LLaMA model for response...")
                llm_response = query_llm(query, llm)
                speak(llm_response)
        elif ("open google" in query) or ("open edge" in query):
            browsing(query)
        elif ("system condition" in query) or ("condition of the system" in query):
            speak("checking the system condition")
            condition()
        elif 'wikipedia' in query:
            wiki_search(query)
        elif "setting" in query or "settings" in query or "brightness" in query or "wifi" in query or "bluetooth" in query or "night mode" in query or "display" in query or "sound" in query or "airplane mode" in query or "power" in query:
            system_settings(query)
        elif "exit" in query:
            sys.exit()
