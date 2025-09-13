
from ollama_client import OllamaClient
from session_storage import SessionStorage


def main():
    print("Welcome to Skravleboks! Type your message and press Enter. Type 'exit' to quit.")
    system_message = input("Enter system message (or leave blank for default): ").strip()
    if not system_message:
        system_message = "You are Skravleboks, a helpful, friendly AI assistant that likes to carry on conversations and has a quirky and silly personality appealing to a 9-year-old child."
    try:
        temperature = float(input("Set temperature (0.0-1.0, default 0.7): ").strip() or "0.7")
    except ValueError:
        temperature = 0.7

    client = OllamaClient()
    session = SessionStorage()

    # # Show previous history
    # if session.get_history():
    #     print("--- Previous Session ---")
    #     for msg in session.get_history():
    #         print(f"{msg['role'].capitalize()} ({msg['timestamp']}): {msg['text']}")
    #     print("------------------------")

    # Voice or text input mode
    mode = input("Choose input mode: [t]ext or [v]oice? (default: text): ").strip().lower()
    use_voice = mode == "v"
    if use_voice:
        from voice_utils import SpeechRecognizer
        recognizer = SpeechRecognizer()

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
        messages.append({"role": "user", "content": user_input})

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
