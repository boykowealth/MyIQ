# app/voice_trigger.py
import speech_recognition as sr
import threading
from chat_handler import get_llm_response

TRIGGER_WORD = "myiq"

def listen_loop():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
    while True:
        with mic as source:
            audio = recognizer.listen(source)
        try:
            phrase = recognizer.recognize_whisper(audio)
            if TRIGGER_WORD.lower() in phrase.lower():
                print("✅ Trigger word detected.")
                with mic as source:
                    print("🎤 Listening for command...")
                    audio = recognizer.listen(source)
                    command = recognizer.recognize_whisper(audio)
                    print(f">> You said: {command}")
                    response = get_llm_response(command)
                    print(f"<< MyIQ: {response}")
        except Exception as e:
            print(f"[Voice error: {e}]")

def start_voice_listener():
    thread = threading.Thread(target=listen_loop, daemon=True)
    thread.start()
