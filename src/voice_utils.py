"""Voice / speech recognition utilities optimized for Raspberry Pi.

Enhancements over the original version:
 - Automatic device detection with environment overrides
 - Configurable sample rate & block size via env vars
 - Timeout + silence detection to avoid hanging
 - Graceful handling of missing audio devices/models
 - Lower per-loop CPU usage on constrained hardware (Pi 5)

Environment Variables:
  SKRAVLE_AUDIO_DEVICE   -> explicit device index (int)
  SKRAVLE_AUDIO_RATE     -> sample rate (default 16000)
  SKRAVLE_AUDIO_BLOCK    -> block size in frames (default 8000)
  SKRAVLE_LISTEN_TIMEOUT -> max seconds for a single listen (default 12)
  SKRAVLE_SILENCE_TIMEOUT-> seconds of no new partial text before return (default 2.5)
  SKRAVLE_PRINT_PARTIALS -> if set ("1") prints partial recognition results
"""

import os
import sys
import time
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

VOSK_MODEL_PATH = os.getenv("SKRAVLE_VOSK_MODEL", "model")

def _parse_int(env_name: str, default: int) -> int:
    try:
        return int(os.getenv(env_name, default))
    except (TypeError, ValueError):
        return default


class SpeechRecognizer:
    def __init__(self,
                 model_path: str = VOSK_MODEL_PATH,
                 samplerate: int = None,
                 device: int | None = None,
                 blocksize: int | None = None):
        self.samplerate = samplerate or _parse_int("SKRAVLE_AUDIO_RATE", 16000)
        self.blocksize = blocksize or _parse_int("SKRAVLE_AUDIO_BLOCK", 8000)
        # Device override via env var
        env_dev = os.getenv("SKRAVLE_AUDIO_DEVICE")
        if env_dev is not None:
            try:
                device = int(env_dev)
            except ValueError:
                print(f"[voice] Invalid SKRAVLE_AUDIO_DEVICE '{env_dev}', falling back to auto.")
                device = None
        self.device = device if device is not None else self._auto_detect_device()

        # Lazy failure messaging
        try:
            self.model = Model(model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load Vosk model at '{model_path}': {e}")

        self.q: "queue.Queue[bytes]" = queue.Queue()
        self.rec = KaldiRecognizer(self.model, self.samplerate)
        self.print_partials = os.getenv("SKRAVLE_PRINT_PARTIALS") == "1"

    def _auto_detect_device(self):
        """Try to pick a reasonable default input device.
        Preference order: default device -> first device with input channels.
        """
        try:
            default = sd.default.device
            if default and default[0] is not None:
                return default[0]
        except Exception:
            pass
        try:
            devices = sd.query_devices()
            for idx, info in enumerate(devices):
                if info.get('max_input_channels', 0) > 0:
                    return idx
        except Exception as e:
            print(f"[voice] Could not enumerate devices: {e}")
        return None  # Let sounddevice pick

    def _callback(self, indata, frames, time_info, status):  # noqa: D401
        if status:
            # Status (over/under-runs) are common on small hardware; just log once in a while
            print(f"[voice] Stream status: {status}")
        self.q.put(bytes(indata))

    def listen(self,
               prompt: str = "Speak now...",
               timeout: float | None = None,
               silence_timeout: float | None = None) -> str:
        """Listen for speech and return transcribed text.

        timeout: absolute cap on seconds spent waiting (returns best partial)
        silence_timeout: seconds of *no improvement* in partial hypothesis after at least one token
        """
        if timeout is None:
            timeout = float(os.getenv("SKRAVLE_LISTEN_TIMEOUT", 12))
        if silence_timeout is None:
            silence_timeout = float(os.getenv("SKRAVLE_SILENCE_TIMEOUT", 2.5))

        print(prompt)
        start_time = time.time()
        last_partial_time = start_time
        last_partial_text = ""
        final_text = ""

        stream_kwargs = dict(
            device=self.device,
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            dtype='int16',
            channels=1,
            callback=self._callback
        )

        try:
            with sd.RawInputStream(**stream_kwargs):
                while True:
                    # Time checks
                    now = time.time()
                    if timeout and (now - start_time) >= timeout:
                        if final_text:
                            print(f"[voice] Timeout reached, returning: {final_text}")
                            return final_text
                        if last_partial_text:
                            print(f"[voice] Timeout (partial) returning: {last_partial_text}")
                            return last_partial_text
                        return ""

                    try:
                        data = self.q.get(timeout=0.25)
                    except queue.Empty:
                        # Silence check (no new audio processed) also counts toward silence
                        if last_partial_text and (now - last_partial_time) >= silence_timeout:
                            print(f"[voice] Silence reached, returning: {last_partial_text}")
                            return last_partial_text
                        continue

                    if self.rec.AcceptWaveform(data):
                        res = self.rec.Result()
                        text = json.loads(res).get("text", "").strip()
                        if text:
                            final_text = text
                            print(f"You said: {final_text}")
                            return final_text
                    else:
                        partial_json = self.rec.PartialResult()
                        try:
                            partial_text = json.loads(partial_json).get("partial", "").strip()
                        except Exception:
                            partial_text = ""
                        if partial_text and partial_text != last_partial_text:
                            last_partial_text = partial_text
                            last_partial_time = now
                            if self.print_partials:
                                print(f"(partial) {partial_text}")
                        elif last_partial_text and (now - last_partial_time) >= silence_timeout:
                            # Consider done
                            print(f"[voice] Silence reached, returning: {last_partial_text}")
                            return last_partial_text
        except KeyboardInterrupt:
            return final_text or last_partial_text
        except Exception as e:
            print(f"[voice] Error during listen: {e}")
            return final_text or last_partial_text


if __name__ == "__main__":
    recognizer = SpeechRecognizer()
    print(recognizer.listen())
