"""
Headless chat that automatically boots up with voice enabled and always starts a new chat.
No user prompts - just starts talking immediately.
"""

from ollama_client import OllamaClient
from session_storage import SessionStorage
from gemma_prompts import MICRO_SYSTEM
from voice_utils import SpeechRecognizer
from tts_utils import speak
import random
import os
import json
import threading
import time
import platform
from datetime import datetime

try:  # Optional dependency (psutil) for performance monitoring
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional
    psutil = None

def log_messages(original_messages, prepared_messages, actual_payload, response, log_file="headless_message_log.json"):
    """Log the original messages, prepared messages, actual payload sent to Ollama and the response received"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "original_messages": original_messages,
        "prepared_messages_sent": prepared_messages,
        "actual_ollama_payload": actual_payload,
        "response_received": response
    }
    
    # Read existing log or create new list
    try:
        with open(log_file, 'r') as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = []
    
    # Append new entry
    log_data.append(log_entry)
    
    # Write back to file
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)

def _is_raspberry_pi() -> bool:
    try:
        if platform.system() != "Linux":
            return False
        # Broad markers: raspberry pi often has 'raspberrypi' in uname or BCM in cpuinfo
        with open('/proc/cpuinfo', 'r', encoding='utf-8', errors='ignore') as f:
            cpuinfo = f.read().lower()
        return 'raspberry pi' in cpuinfo or 'raspberrypi' in cpuinfo or 'bcm' in cpuinfo
    except Exception:
        return False


def _start_perf_monitor(interval: int = 30):
    if psutil is None:
        print("[perf] psutil not installed; performance monitoring disabled.")
        return None

    def _loop():
        while True:
            try:
                proc = psutil.Process()
                cpu = proc.cpu_percent(interval=None)  # uses last interval snapshot
                mem = proc.memory_info().rss / (1024 * 1024)
                sys_cpu = psutil.cpu_percent(interval=None)
                print(f"[perf] proc_cpu={cpu:.1f}% sys_cpu={sys_cpu:.1f}% rss={mem:.1f}MB")
                time.sleep(interval)
            except Exception:
                time.sleep(interval)
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t


def main():
    print("🎤 Starting Headless Voice Chat (Pi-optimized)...")
    if _is_raspberry_pi():
        print("🐧 Detected Raspberry Pi environment. Applying lightweight settings.")
    print("Voice mode enabled automatically. Say 'exit' or 'quit' to end the conversation.")

    # Fixed configuration - no user input required
    system_message = MICRO_SYSTEM
    temperature = float(os.getenv("SKRAVLE_TEMPERATURE", 0.3))

    # Initialize components
    client = OllamaClient()

    # Always start with a fresh session - remove any existing session file
    session_file = os.getenv("SKRAVLE_SESSION_FILE", 'headless_session.json')
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
            print("🔄 Cleared previous session - starting fresh!")
        except Exception as e:
            print(f"[warn] Could not remove old session file: {e}")

    session = SessionStorage(path=session_file)

    # Optional performance monitor
    if os.getenv("SKRAVLE_PERF_MONITOR") == "1":
        _start_perf_monitor(interval=int(os.getenv("SKRAVLE_PERF_INTERVAL", 30)))

    # Initialize voice components
    try:
        recognizer = SpeechRecognizer()
        print("✅ Voice recognition initialized")
    except Exception as e:
        print(f"❌ Error initializing voice recognition: {e}")
        print("Please ensure Vosk model is available in 'model' directory")
        return
    
    # Start with a random greeting that fits the undercover alien explorer character
    greeting_options = [
        "Hello fellow human! I'm Mikkey and I too enjoy... human activities! What's your name?",
        "Greetings! I'm Mikkey, definitely a normal person like yourself! What should I call you?", 
        "Hi there! I'm Mikkey and I'm very excited to be at this human gathering! What's your name?",
        "Hello! I'm Mikkey and I love being human just like you! What do you call yourself?",
        "Good day human friend! I'm Mikkey and I'm practicing my human conversation skills. What shall we discuss?",
        "Salutations! I'm Mikkey, a completely ordinary human who definitely didn't arrive here in a spacecraft! What's happening?"
    ]
    
    greeting_prompt = random.choice(greeting_options)
    greeting_message = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": greeting_prompt}
    ]

    # Send greeting and get AI response
    print("\n🤖 AI is thinking...")
    prepared_greeting = client._prepare_messages_for_gemma(greeting_message)
    greeting_chunks = []
    
    try:
        for chunk in client.prompt_stream(greeting_message, temperature=temperature):
            greeting_chunks.append(chunk)
        greeting = "".join(greeting_chunks)
        print(f"🤖 AI: {greeting}")
        session.add_message("ai", greeting)
        
        # Log the greeting exchange
        log_messages(greeting_message, prepared_greeting, client.last_payload, greeting)
        
        # Speak the greeting
        print("🔊 Speaking...")
        speak(greeting)
        
    except Exception as e:
        print(f"❌ Error getting AI response: {e}")
        return

    # Main conversation loop
    print("\n🎤 Ready for voice input! Speak now...")
    
    while True:
        try:
            # Get voice input with timeouts (env configurable)
            user_input = recognizer.listen(
                "🎤 Listening...",
                timeout=float(os.getenv("SKRAVLE_LISTEN_TIMEOUT", 12)),
                silence_timeout=float(os.getenv("SKRAVLE_SILENCE_TIMEOUT", 2.5))
            )
            
            if not user_input or not user_input.strip():
                print("🔇 No speech detected, trying again...")
                continue
                
            if user_input.strip().lower() in ["exit", "quit", "goodbye", "bye"]:
                print("👋 Goodbye!")
                try:
                    speak("Goodbye! It was nice talking with you, fellow human!")
                except Exception as e:
                    print(f"[TTS Error] {e}")
                break
                
            print(f"👤 You: {user_input}")
            session.add_message("user", user_input)

            # Build messages array for Ollama - ALWAYS include system message
            history = session.get_history()
            messages = [{"role": "system", "content": system_message}]
            
            for msg in history:
                if msg["role"] == "user":
                    messages.append({"role": "user", "content": msg["text"]})
                elif msg["role"] == "ai":
                    messages.append({"role": "assistant", "content": msg["text"]})

            # Get AI response
            print("🤖 AI is thinking...")
            prepared_messages = client._prepare_messages_for_gemma(messages)
            response_chunks = []
            
            for chunk in client.prompt_stream(messages, temperature=temperature):
                response_chunks.append(chunk)
                
            response = "".join(response_chunks)
            print(f"🤖 AI: {response}")
            session.add_message("ai", response)
            
            # Log the exchange
            log_messages(messages, prepared_messages, client.last_payload, response)

            # Speak the AI response
            print("🔊 Speaking...")
            try:
                speak(response)
            except Exception as e:
                print(f"[TTS Error] {e}")
            
            print("\n🎤 Ready for your next message...")

        except KeyboardInterrupt:
            print("\n\n⏹️  Chat interrupted by user")
            try:
                speak("Chat session ended. Goodbye!")
            except Exception:
                pass
            break
        except Exception as e:
            print(f"❌ Error in conversation: {e}")
            print("🔄 Continuing chat...")
            continue

if __name__ == "__main__":
    main()