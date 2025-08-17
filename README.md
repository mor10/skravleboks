# skravleboks

A local AI voice assistant.

## Project Setup

### 1. Initialize Python Project

```sh
# On MacOS or Raspberry Pi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Test Hello World

```sh
python src/hello.py
# Output should be: Hello, skravleboks!
```

---

## Spec
- Model environment: Ollama
- Model: llama3.2
- Speech recognition: Vosk
- Text-to-speech: PiperTTS

Develop on MacOS

Deploy on Raspberry Pi 5 8GB