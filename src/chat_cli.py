from ollama_client import OllamaClient
from session_storage import SessionStorage
from gemma_prompts import MICRO_SYSTEM
import random
import os
import json
from datetime import datetime

def log_messages(original_messages, prepared_messages, actual_payload, response, log_file="message_log.json"):
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

def main():
    print("Welcome to Skravleboks! Type your message and press Enter. Type 'exit' to quit.")
    system_message = input("Enter system message (or leave blank for default): ").strip()
    if not system_message:
        system_message = MICRO_SYSTEM
    try:
        temperature = float(input("Set temperature (0.0-1.0, default 0.3): ").strip() or "0.3")
    except ValueError:
        temperature = 0.3

    client = OllamaClient()
    session = SessionStorage()

    # Voice or text input mode
    mode = input("Choose input mode: [t]ext or [v]oice? (default: text): ").strip().lower()
    use_voice = mode == "v"
    if use_voice:
        from voice_utils import SpeechRecognizer
        recognizer = SpeechRecognizer()

    # Check if session.json exists and ask about continuation
    session_exists = os.path.exists('session.json')
    
    if session_exists:
        continue_session = input("Previous conversation found. Continue? [y/n] (default: n): ").strip().lower()
        if continue_session != "y":
            # Clear the session for a fresh start
            if os.path.exists('session.json'):
                os.remove('session.json')
            session = SessionStorage()  # Create fresh session
            session_exists = False
    
    if session_exists:
        # Load the full conversation history into the context for seamless continuation
        history = session.get_history()
        
        # Build the continuation message with system + full history + continuation prompt
        greeting_message = [{"role": "system", "content": system_message}]
        
        # Add all the previous conversation history
        for msg in history:
            if msg["role"] == "user":
                greeting_message.append({"role": "user", "content": msg["text"]})
            elif msg["role"] == "ai":
                greeting_message.append({"role": "assistant", "content": msg["text"]})
        
        # Add the continuation prompt as the latest user message
        greeting_message.append({"role": "user", "content": "Hello again! What should we talk about now?"})
    else:
        # New conversation - start with greetings that fit the undercover alien explorer
        greeting_options = [
            "Hello fellow human! I'm Mikkey and I too enjoy... human activities! What's your name?",
            "Greetings! I'm Mikkey, definitely a normal person like yourself! What should I call you?", 
            "Hi there! I'm Mikkey and I'm very excited to be at this human gathering! What's your name?",
            "Hello! I'm Mikkey and I love being human just like you! What do you call yourself?",
        ]
        greeting_prompt = random.choice(greeting_options)
        greeting_message = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": greeting_prompt}
        ]

    # Send greeting
    prepared_greeting = client._prepare_messages_for_gemma(greeting_message)
    greeting_chunks = []
    for chunk in client.prompt_stream(greeting_message, temperature=temperature):
        greeting_chunks.append(chunk)
    greeting = "".join(greeting_chunks)
    print("AI:", greeting)
    session.add_message("ai", greeting)
    
    # Log the greeting exchange with actual payload
    log_messages(greeting_message, prepared_greeting, client.last_payload, greeting)
    
    if use_voice:
        try:
            from tts_utils import speak
            speak(greeting)
        except Exception as e:
            print(f"[TTS Error] {e}")

    while True:
        if use_voice:
            user_input = recognizer.listen()
        else:
            user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            print("Goodbye!")
            break
        session.add_message("user", user_input)

        # Build messages array for Ollama - ALWAYS include system message
        history = session.get_history()  # Get ALL history, don't truncate
        messages = [{"role": "system", "content": system_message}]  # Always include system message
        
        for msg in history:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["text"]})
            elif msg["role"] == "ai":
                messages.append({"role": "assistant", "content": msg["text"]})

        print("AI:", end=" ", flush=True)
        prepared_messages = client._prepare_messages_for_gemma(messages)
        response_chunks = []
        for chunk in client.prompt_stream(messages, temperature=temperature):
            print(chunk, end="", flush=True)
            response_chunks.append(chunk)
        response = "".join(response_chunks)
        print()
        session.add_message("ai", response)
        
        # Log the exchange with actual payload
        log_messages(messages, prepared_messages, client.last_payload, response)

        # Speak the AI response using PiperTTS
        if use_voice:
            try:
                from tts_utils import speak
                speak(response)
            except Exception as e:
                print(f"[TTS Error] {e}")

if __name__ == "__main__":
    main()