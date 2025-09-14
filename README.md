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

### 2. Install Vosk Model (Speech Recognition)

#### On MacOS:

```sh
curl -LO https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 model
```

#### On Raspberry Pi:

```sh
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 model
```

### 3. Test Hello World

```sh
python src/hello.py
# Output should be: Hello, skravleboks!
```

### 4. Test Voice Input

```sh
python src/voice_utils.py
# Speak into your microphone and see the recognized text.
```

---

## Spec

- Model environment: Ollama
- Model: llama3.2
- Speech recognition: Vosk
- Text-to-speech: PiperTTS

Develop on MacOS

Deploy on Raspberry Pi 5 8GB
