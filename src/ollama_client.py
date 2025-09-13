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
            "temperature": temperature
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

    def prompt(self, messages, temperature=0.7, stream=False):
        """Convenience method that sends a prompt and returns the full response.

        - `messages` may be a plain string (treated as a user message) or a list of
          message dicts expected by the Ollama API.
        - If `stream=True` this will return a generator delegating to `prompt_stream`.
        - Otherwise it returns the assembled response string (or an error message).
        """
        # Accept a plain string prompt for convenience
        if isinstance(messages, str):
            msgs = [{"role": "user", "content": messages}]
        else:
            msgs = messages

        if stream:
            # Return the generator from prompt_stream so callers can iterate
            return self.prompt_stream(msgs, temperature)

        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": msgs,
            "temperature": temperature,
        }
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            # Try to parse JSON and extract the content
            try:
                data = response.json()
                # Ollama can return different shapes; try common locations
                content = None
                if isinstance(data, dict):
                    content = data.get("message", {}).get("content")
                    if content is None:
                        choices = data.get("choices")
                        if choices and isinstance(choices, list):
                            content = choices[0].get("message", {}).get("content")
                if content is None:
                    # Fallback: return the full JSON as a string
                    return json.dumps(data)
                return content
            except ValueError:
                # Not JSON — return raw text
                return response.text
        except Exception as e:
            return f"Error: {e}"

if __name__ == "__main__":
    client = OllamaClient()
    result = client.prompt("Hello, Ollama! What can you do?")
    print("Response from Ollama:")
    print(result)
