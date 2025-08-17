import sys
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# Change this to your Vosk model path
VOSK_MODEL_PATH = "model"

class SpeechRecognizer:
    def __init__(self, model_path=VOSK_MODEL_PATH, samplerate=16000, device=4):
        self.model = Model(model_path)
        self.samplerate = samplerate
        self.device = device
        self.q = queue.Queue()
        self.rec = KaldiRecognizer(self.model, self.samplerate)

    def _callback(self, indata, frames, time, status):
        self.q.put(bytes(indata))

    def listen(self, prompt="Speak now..."):
        print(prompt)
        with sd.RawInputStream(device=self.device, samplerate=self.samplerate, blocksize=8000, dtype='int16', channels=1, callback=self._callback):
            result = ""
            while True:
                data = self.q.get()
                if self.rec.AcceptWaveform(data):
                    res = self.rec.Result()
                    import json
                    text = json.loads(res).get("text", "")
                    if text:
                        print(f"You said: {text}")
                        return text
                else:
                    partial = self.rec.PartialResult()
                    # Optionally print partial results

if __name__ == "__main__":
    recognizer = SpeechRecognizer()
    recognizer.listen()
