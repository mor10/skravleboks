import requests
import os
import json

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

class OllamaClient:
    def __init__(self, host=OLLAMA_HOST, model=MODEL):
        self.host = host.rstrip("/")
        self.model = model

    def prompt_stream(self, messages, temperature=0.7):
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": 100,
                "top_k": 200,
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=60, stream=True)
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk
                    except Exception:
                        continue
        except Exception as e:
            yield f"Error: {e}"

if __name__ == "__main__":
    client = OllamaClient()
    result = client.prompt("Hello, Ollama! What can you do?")
    print("Response from Ollama:")
    print(result)
