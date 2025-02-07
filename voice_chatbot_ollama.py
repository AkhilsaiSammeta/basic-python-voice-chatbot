import speech_recognition as sr
import pyttsx3
from ollama import Client  # Changed import to Client

# Initialize speech recognition, text-to-speech, and Ollama client
recognizer = sr.Recognizer()
engine = pyttsx3.init()
ollama_client = Client()  # Changed to use Client class

def recognize_speech():
    """Listens for speech and converts it to text."""
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        print("Recognizing...")
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text.lower()
    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return ""

def generate_response(user_input):
    """Generates response using Ollama Llama 3."""
    try:
        response = ollama_client.chat(
            # model='llama3:3b',
            model='llama3.2:latest',  # <-- UPDATED MODEL NAME
            messages=[{'role': 'user', 'content': user_input}]
        )
        return response['message']['content']
    except Exception as e:
        print(f"Error from Ollama: {e}")
        return "Sorry, I had trouble responding."

def speak_response(text):
    """Speaks the given text."""
    engine.say(text)
    engine.runAndWait()

def main():
    """Main function to run the chatbot."""
    print("Voice Chatbot Started with Ollama Llama 3!")
    speak_response("Voice Chatbot Started with Llama 3!")
    while True:
        user_input = recognize_speech()
        if user_input:
            response_text = generate_response(user_input)
            print(f"Chatbot: {response_text}")
            speak_response(response_text)
            if "bye" in user_input or "exit" in user_input or "goodbye" in user_input:
                break

if __name__ == "__main__":
    main()