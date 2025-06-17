# app/chat_handler.py
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def get_llm_response(prompt: str) -> str:
    print(f"Sending prompt: {prompt}")
    payload = {
        "model": "llama3.2:latest",
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        print("Response:", response.text)
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"[Error talking to LLM: {e}]"
