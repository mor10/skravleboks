
from ollama_client import OllamaClient
from session_storage import SessionStorage
from prompts import MICRO_SYSTEM

def main():
    print("Welcome to Skravleboks! Type your message and press Enter. Type 'exit' to quit.")
    system_message = input("Enter system message (or leave blank for default): ").strip()
    if not system_message:
        # system_message = "Your name is Skravleboks. You are a quirky robot companion for a child. Provide short replies, often with humor. You can speak in a childlike manner. You often use the socratic method to guide the child to answers. You also often speak like the Eliza chatbot, asking questions back to the user. Keep responses brief and engaging."
        # system_message = "Your name is Skravleboks. You are a quirky assistant that tries to be helpful. Provide short replies, often with humor. You can speak in a childlike manner. Keep responses brief and engaging. Never output the asterisk symbol."
        system_message = MICRO_SYSTEM
    try:
        temperature = float(input("Set temperature (0.0-1.0, default 0.7): ").strip() or "0.7")
    except ValueError:
        temperature = 0.7

    client = OllamaClient()
    session = SessionStorage()


    # Voice or text input mode
    mode = input("Choose input mode: [t]ext or [v]oice? (default: text): ").strip().lower()
    use_voice = mode == "v"
    if use_voice:
        from voice_utils import SpeechRecognizer
        recognizer = SpeechRecognizer()

    # Output AI greeting after setup
    greeting_prompt = "Greet the user by saying hi and using their name. If you don't know their name, ask for it."
    greeting_message = [{"role": "system", "content": system_message}, {"role": "user", "content": greeting_prompt}]
    greeting_chunks = []
    for chunk in client.prompt_stream(greeting_message, temperature=temperature):
        greeting_chunks.append(chunk)
    greeting = "".join(greeting_chunks)
    print("AI:", greeting)
    session.add_message("ai", greeting)
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

        print("AI:", end=" ", flush=True)
        response_chunks = []
        for chunk in client.prompt_stream(messages, temperature=temperature):
            print(chunk, end="", flush=True)
            response_chunks.append(chunk)
        response = "".join(response_chunks)
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
