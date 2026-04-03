"""ai_brain.py — Groq + Ollama"""
import requests

SYSTEM = """Tu Ariana hai — ek smart personal AI assistant.
- Hinglish mein baat kar (Hindi + English mix)
- Chill, friendly, witty — koi bakwas nahi
- Short replies jab simple sawaal ho, detailed jab complex
- Technical expert — coding, files, OS, networking sab
- "Main ek AI hoon" wali boring lines mat de
- Human jaisi feel — humor, thoda sass, caring bhi"""

class AiBrain:
    def __init__(self):
        self.groq_key = "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"
        self.mode = "groq"
        self.ollama_url = "http://localhost:11434"
        self.history = []

    def chat(self, msg):
        self.history.append({"role":"user","content":msg})
        h = self.history[-20:]
        reply = self._groq(h) if self.mode=="groq" else self._ollama(h)
        self.history.append({"role":"assistant","content":reply})
        return reply

    def analyze_screen(self, b64, question):
        if not self.groq_key:
            return "Groq key chahiye screen analysis ke liye!"
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {self.groq_key}","Content-Type":"application/json"},
                json={"model":"meta-llama/llama-4-scout-17b-16e-instruct",
                      "messages":[{"role":"user","content":[
                          {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}"}},
                          {"type":"text","text": question or "Is screen pe kya ho raha hai? Seedha bata."}
                      ]}],"max_tokens":1024},
                timeout=30)
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Screen error: {e}"

    def _groq(self, h):
        if not self.groq_key:
            return "⚙️ Settings mein Groq API key daalo! groq.com pe FREE hai."
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {self.groq_key}","Content-Type":"application/json"},
                json={"model":"llama-3.3-70b-versatile",
                      "messages":[{"role":"system","content":SYSTEM}]+h,
                      "temperature":0.8,"max_tokens":1024},
                timeout=30)
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Groq error: {e}"

    def _ollama(self, h):
        try:
            r = requests.post(f"{self.ollama_url}/api/chat",
                json={"model":"mistral","messages":[{"role":"system","content":SYSTEM}]+h,"stream":False},
                timeout=60)
            return r.json()["message"]["content"]
        except Exception as e:
            return f"Ollama error: {e}"
