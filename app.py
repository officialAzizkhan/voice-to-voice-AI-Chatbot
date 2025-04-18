import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import pygame
import requests
import os
import dotenv
import tempfile
import time

# Load API Key
dotenv.load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("ERROR: GROQ_API_KEY not found!")
    st.stop()

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": "You are a helpful voice to voice AI assistant."}
    ]

# Function: Speech to Text
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=5)  # Timeout to prevent infinite listening
    
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None

# Function: Get AI Response with Memory
def get_groq_response(user_text):
    # Append user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_text})
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama3-70b-8192",
        "messages": st.session_state.chat_history  # Send full chat history
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        ai_response = response.json()["choices"][0]["message"]["content"]
        # Append AI response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        return ai_response
    return None

# Function: Text-to-Speech
def text_to_speech(text):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_filename = temp_audio.name

    tts = gTTS(text, lang="en")
    tts.save(temp_filename)
    
    pygame.mixer.music.load(temp_filename)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        if not st.session_state.active:
            pygame.mixer.music.stop()
            break
        time.sleep(0.1)
    
    pygame.mixer.quit()
    time.sleep(0.1)
    os.remove(temp_filename)
    pygame.init()
    pygame.mixer.init()

# Streamlit UI
st.title("Voice-to-Voice AI Assistant")

# Initialize session states if not set
if "active" not in st.session_state:
    st.session_state.active = False

# Start button
if not st.session_state.active:
    if st.button("Start Conversation"):
        st.session_state.active = True
        st.rerun()

# Stop button
if st.session_state.active:
    if st.button("Stop Conversation"):
        st.session_state.active = False
        pygame.mixer.music.stop()
        st.rerun()

# Continuous loop until user stops
while st.session_state.active:
    user_text = speech_to_text()
    
    if user_text:  # Only process if input is recognized
        ai_response = get_groq_response(user_text)
        
        if ai_response and st.session_state.active:
            text_to_speech(ai_response)




