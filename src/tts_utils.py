# Basic PiperTTS integration for text-to-speech


import os
import sys
import wave
import re
from piper import PiperVoice

# Optional caching for Piper voice to avoid reloading model each utterance on Pi.
# Disable caching by setting SKRAVLE_TTS_NOCACHE=1
_VOICE_CACHE = {}


def strip_markdown(text):
    # Remove Markdown formatting (bold, italics, code, links, etc.)
    text = re.sub(r'(`{1,3})(.*?)\1', r'\2', text)  # inline/backtick code
    text = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)  # bold/italic
    text = re.sub(r'_([^_]+)_', r'\1', text)  # underscore italic
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', text)  # links
    text = re.sub(r'\[(.*?)\]', r'\1', text)  # brackets
    text = re.sub(r'#+\s*(.*)', r'\1', text)  # headers
    text = re.sub(r'>\s*(.*)', r'\1', text)  # blockquotes
    text = re.sub(r'-\s*(.*)', r'\1', text)  # lists
    text = re.sub(r'!\[(.*?)\]\((.*?)\)', r'\1', text)  # images
    text = re.sub(r'\n{2,}', '\n', text)  # collapse multiple newlines
    return text.strip()

def strip_emojis_and_symbols(text):
    # Remove emojis and most non-text symbols (Unicode ranges)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002700-\U000027BF"  # Dingbats
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U00002600-\U000026FF"  # Misc symbols
        "\U00002B50"              # Star
        "\U000024C2-\U0001F251"  # Enclosed characters
        "]+",
        flags=re.UNICODE)
    # Remove other non-alphanumeric symbols except basic punctuation
    text = emoji_pattern.sub(r'', text)
    text = re.sub(r'[^\w\s.,!?\'\"-]', '', text)
    return text

def speak(text, model_path="piper_models/en_GB-semaine-medium.onnx", output_wav="output.wav"):
    """Synthesize speech (optionally cached voice) and play it.

    Environment:
      SKRAVLE_DISABLE_TTS   -> if set to '1', skip speaking (useful for headless tests)
      SKRAVLE_TTS_NOCACHE   -> if set to '1', do not cache model in memory
    """
    if os.getenv("SKRAVLE_DISABLE_TTS") == "1":
        return

    clean_text = strip_markdown(text)
    clean_text = strip_emojis_and_symbols(clean_text)

    use_cache = os.getenv("SKRAVLE_TTS_NOCACHE") != "1"
    voice = None
    if use_cache:
        voice = _VOICE_CACHE.get(model_path)
    if voice is None:
        voice = PiperVoice.load(model_path)
        if use_cache:
            _VOICE_CACHE[model_path] = voice

    with wave.open(output_wav, "wb") as wav_file:
        voice.synthesize_wav(clean_text, wav_file)
    # Play the wav file (MacOS: afplay, Raspberry Pi: aplay)
    play_cmd = "afplay" if sys.platform == "darwin" else "aplay"
    # Use non-blocking background play if available
    os.system(f"{play_cmd} {output_wav} >/dev/null 2>&1 &")

if __name__ == "__main__":
    speak("Hello from PiperTTS!")
