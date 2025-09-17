# skravleboks

A local AI voice assistant.

## Project Setup

### 1. Initialize Python Project

```sh
# On MacOS or Raspberry Pi
python3 -m venv .venv
source .venv/bin/activate
uv sync
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

### 5. Install voices for PiperTTS

Voice samples: https://rhasspy.github.io/piper-samples/

You need two files: `.onnx` and `.onnx.json`

Place them in the `./piper_models/` folder

#### On MacOS:

```sh
cd piper_models
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/semaine/medium/en_GB-semaine-medium.onnx
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/semaine/medium/en_GB-semaine-medium.onnx.json
```

#### On Raspberry Pi:

```sh
cd piper_models
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/semaine/medium/en_GB-semaine-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/semaine/medium/en_GB-semaine-medium.onnx.json
```

---

## Spec

- Model environment: Ollama
- Model: llama3.2
- Speech recognition: Vosk
- Text-to-speech: PiperTTS

Develop on MacOS

Deploy on Raspberry Pi 5 8GB

---

## Ollama Client & Performance Tuning

The chat CLI (`python src/chat_cli.py`) now uses the official `ollama` Python library for streaming responses. You can tune generation and streaming performance via environment variables (helpful on Raspberry Pi):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `smollm2:1.7b` | Model to load (must be pulled with `ollama pull <model>`). |
| `OLLAMA_TEMPERATURE` | `0.7` | Default temperature if not provided at runtime. |
| `OLLAMA_NUM_PREDICT` | `100` | Max new tokens to generate. Lower for faster latency. |
| `OLLAMA_TOP_K` | `200` | Sampling top-k. Reduce to slightly speed up on low power. |
| `OLLAMA_TOP_P` | `0.9` | Nucleus sampling probability mass. |
| `SKRAVLE_FLUSH_INTERVAL` | `0.05` | Seconds between stdout flush during streaming. Increase to reduce overhead. |
| `SKRAVLE_BUFFER_CHARS` | `120` | Flush when this many characters buffered (whichever first with interval). |

Example (faster first token latency, slightly shorter replies):

```sh
export OLLAMA_NUM_PREDICT=60
export OLLAMA_TOP_K=100
export SKRAVLE_FLUSH_INTERVAL=0.08
python src/chat_cli.py
```

If you encounter very slow streaming, verify the Ollama server is running locally and that the model is already loaded (first request can be slower due to initial load / compilation).

