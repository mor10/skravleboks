import requests
import os
import json

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

class OllamaClient:
    def __init__(self, host=OLLAMA_HOST, model=MODEL):
        self.host = host.rstrip("/")
        self.model = model

    def prompt(self, prompt_text):
        url = f"{self.host}/api/generate"
        payload = {"model": self.model, "prompt": prompt_text}
        try:
            response = requests.post(url, json=payload, timeout=60, stream=True)
            response.raise_for_status()
            result = ""
            for line in response.iter_lines():
                if line:
                    try:
                        # Decode bytes to string before loading JSON
                        data = json.loads(line.decode("utf-8"))
                        result += data.get("response", "")
                    except Exception:
                        continue
            return result
        except Exception as e:
            return f"Error: {e}"

if __name__ == "__main__":
    client = OllamaClient()
    result = client.prompt("Hello, Ollama! What can you do?")
    print("Response from Ollama:")
    print(result)
