# Basic PiperTTS integration for text-to-speech


import os
import sys
import wave
import re
from piper import PiperVoice


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
    """
    Uses PiperTTS Python API to synthesize speech from text and play it.
    Strips Markdown formatting and removes emojis/symbols before synthesis.
    """
    clean_text = strip_markdown(text)
    clean_text = strip_emojis_and_symbols(clean_text)
    voice = PiperVoice.load(model_path)
    with wave.open(output_wav, "wb") as wav_file:
        voice.synthesize_wav(clean_text, wav_file)
    # Play the wav file (MacOS: afplay, Raspberry Pi: aplay)
    if sys.platform == "darwin":
        os.system(f"afplay {output_wav}")
    else:
        os.system(f"aplay {output_wav}")

if __name__ == "__main__":
    speak("Hello from PiperTTS!")
