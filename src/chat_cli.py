
from ollama_client import OllamaClient
from session_storage import SessionStorage
from prompts import SMALL_SYSTEM
import os
import sys
import time

# Tuning knobs (env overridable) for low-power devices like Raspberry Pi
FLUSH_INTERVAL = float(os.getenv("SKRAVLE_FLUSH_INTERVAL", "0.05"))  # seconds between stdout flushes while streaming
MAX_BUFFER_BEFORE_FLUSH = int(os.getenv("SKRAVLE_BUFFER_CHARS", "120"))


def stream_collect_print(chunks_iter):
    """Print streaming chunks efficiently and return the full concatenated text.

    Flushes stdout at a controlled cadence to reduce overhead on low-power devices.
    """
    last_flush = time.time()
    buffer = []
    total = 0
    collected = []
    for chunk in chunks_iter:
        if chunk.startswith("[Ollama error]"):
            # Flush anything pending first
            if buffer:
                sys.stdout.write("".join(buffer))
                sys.stdout.flush()
                buffer.clear()
            print(chunk)
            collected.append(chunk)
            break
        buffer.append(chunk)
        collected.append(chunk)
        total += len(chunk)
        now = time.time()
        if (now - last_flush) >= FLUSH_INTERVAL or total >= MAX_BUFFER_BEFORE_FLUSH:
            sys.stdout.write("".join(buffer))
            sys.stdout.flush()
            buffer.clear()
            total = 0
            last_flush = now
    if buffer:
        sys.stdout.write("".join(buffer))
        sys.stdout.flush()
    return "".join(collected)

def main():
    print("Welcome to Skravleboks! Type your message and press Enter. Type 'exit' to quit.")
    system_message = input("Enter system message (or leave blank for default): ").strip()
    if not system_message:
        # system_message = "Your name is Skravleboks. You are a quirky robot companion for a child. Provide short replies, often with humor. You can speak in a childlike manner. You often use the socratic method to guide the child to answers. You also often speak like the Eliza chatbot, asking questions back to the user. Keep responses brief and engaging."
        # system_message = "Your name is Skravleboks. You are a quirky assistant that tries to be helpful. Provide short replies, often with humor. You can speak in a childlike manner. Keep responses brief and engaging. Never output the asterisk symbol."
        system_message = SMALL_SYSTEM
    def _to_float(raw, default):
        try:
            return float(raw)
        except Exception:
            return default
    def _to_int(raw, default):
        try:
            return int(raw)
        except Exception:
            return default

    try:
        temperature = _to_float(input("Set temperature (0.0-1.0, default 0.7): ").strip() or os.getenv("OLLAMA_TEMPERATURE", "0.7"), 0.7)
    except Exception:
        temperature = 0.7
    num_predict = _to_int(input("Max tokens to predict (default 100): ").strip() or os.getenv("OLLAMA_NUM_PREDICT", "100"), 100)
    top_k = _to_int(input("top_k (default 200): ").strip() or os.getenv("OLLAMA_TOP_K", "200"), 200)
    top_p = _to_float(input("top_p (default 0.9): ").strip() or os.getenv("OLLAMA_TOP_P", "0.9"), 0.9)

    client = OllamaClient()
    session = SessionStorage()


    # Voice or text input mode
    mode = input("Choose input mode: [t]ext or [v]oice? (default: text): ").strip().lower()
    use_voice = mode == "v"
    if use_voice:
        from voice_utils import SpeechRecognizer
        recognizer = SpeechRecognizer()

    # Output AI greeting after setup
    greeting_prompt = "Greet the user by saying hi and using their name. If you don't know their name, ask for it. Keep it brief."
    greeting_message = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": greeting_prompt},
    ]
    print("AI:", end=" ")
    greeting = stream_collect_print(
        client.prompt_stream(
            greeting_message,
            temperature=temperature,
            num_predict=num_predict,
            top_k=top_k,
            top_p=top_p,
        )
    )
    print()
    session.add_message("ai", greeting)


    while True:
        if use_voice:
            user_input = recognizer.listen()
        else:
            user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            print("Goodbye!")
            break
        session.add_message("user", user_input)

        # Build messages array for Ollama
        history = session.get_history()[-10:]
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        for msg in history:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["text"]})
            elif msg["role"] == "ai":
                messages.append({"role": "assistant", "content": msg["text"]})
            # Do not append user_input again; it's already in history

        print("AI:", end=" ")
        response = stream_collect_print(
            client.prompt_stream(
                messages,
                temperature=temperature,
                num_predict=num_predict,
                top_k=top_k,
                top_p=top_p,
            )
        )
        print()
        session.add_message("ai", response)

        # Speak the AI response using PiperTTS
        try:
            from tts_utils import speak
            speak(response)
        except Exception as e:
            print(f"[TTS Error] {e}")

if __name__ == "__main__":
    main()
