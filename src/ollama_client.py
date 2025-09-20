import requests
import os
import json


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")

class OllamaClient:
    def __init__(self, host=OLLAMA_HOST, model=MODEL):
        self.host = host.rstrip("/")
        self.model = model

    def _is_gemma_model(self):
        """Check if the current model is a Gemma model that doesn't support system messages"""
        return "gemma" in self.model.lower()

    def _prepare_messages_for_gemma(self, messages):
        """Prepare messages for Gemma models by converting system messages to user messages"""
        if not self._is_gemma_model():
            return messages
        
        prepared_messages = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                # Convert system message to user message - Ollama will format it correctly
                prepared_messages.append({
                    "role": "user",
                    "content": content
                })
            elif role == "user":
                prepared_messages.append({
                    "role": "user",
                    "content": content
                })
            elif role in ["assistant", "ai"]:
                prepared_messages.append({
                    "role": "assistant",
                    "content": content
                })
        
        return prepared_messages

    def prompt_stream(self, messages, temperature=0.7):
        # Prepare messages for Gemma models if needed
        prepared_messages = self._prepare_messages_for_gemma(messages)
        
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": prepared_messages,
            "options": {
                "temperature": temperature,
                "num_predict": 150,
                "top_k": 40,
                "top_p": 0.9,
            }
        }
        
        # Store the payload for logging purposes
        self.last_payload = payload
        
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