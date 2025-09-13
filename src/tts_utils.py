# Basic PiperTTS integration for text-to-speech

import os
import sys
import wave
from piper import PiperVoice


def speak(text, model_path="piper_models/en_US-danny-low.onnx", output_wav="output.wav"):
    """
    Uses PiperTTS Python API to synthesize speech from text and play it.
    """
    voice = PiperVoice.load(model_path)
    with wave.open(output_wav, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)
    # Play the wav file (MacOS: afplay, Raspberry Pi: aplay)
    if sys.platform == "darwin":
        os.system(f"afplay {output_wav}")
    else:
        os.system(f"aplay {output_wav}")

if __name__ == "__main__":
    speak("Hello from PiperTTS!")
