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

def speak(text, model_path="piper_models/en_GB-semaine-medium.onnx", output_wav="output.wav"):
    """
    Uses PiperTTS Python API to synthesize speech from text and play it.
    Strips Markdown formatting before synthesis.
    """
    clean_text = strip_markdown(text)
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
