import tkinter as tk
from tkinter import scrolledtext, Entry, Button, END
import speech_recognition as sr
import pyttsx3
from ollama import Client
import threading

class ChatbotUI:
    def __init__(self, master):
        self.master = master
        master.title("Voice Chatbot UI (Mistral Model)") # Updated title

        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.ollama_client = Client()

        # --- Speech Rate Adjustment ---
        default_rate = self.engine.getProperty('rate')
        new_rate = int(default_rate * 1.2)
        self.engine.setProperty('rate', new_rate)
        print(f"Speech rate adjusted from {default_rate} to {new_rate}")

        # Chat History Display
        self.chat_display = scrolledtext.ScrolledText(master, wrap=tk.WORD, state=tk.DISABLED, height=20)
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # User Input Entry
        self.user_input_entry = Entry(master)
        self.user_input_entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        self.user_input_entry.bind("<Return>", self.send_message_event) # Bind Enter key

        # Send Button
        self.send_button = Button(master, text="Send", command=self.send_message)
        self.send_button.pack(pady=(0, 10))

        # Voice Input Button
        self.voice_button = Button(master, text="Voice Input", command=self.start_voice_input)
        self.voice_button.pack(pady=(0, 10))

        self.add_bot_message("Voice Chatbot Started! (Using Mistral Model)") # Updated start message
        self.speak_response("Voice Chatbot Started! Using Mistral Model")

    def add_message(self, sender, message):
        """Adds a message to the chat display."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(END, f"{sender}: {message}\n", sender)
        self.chat_display.tag_config("user", foreground="blue")
        self.chat_display.tag_config("bot", foreground="green")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(END)

    def add_user_message(self, message):
        self.add_message("You", message)

    def add_bot_message(self, message):
        self.add_message("Chatbot", message)

    def speak_response(self, text):
        """Speaks the chatbot's response."""
        self.engine.say(text)
        self.engine.runAndWait()

    def generate_response(self, user_input):
        """Generates chatbot response using Ollama with Mistral model.""" # Model name updated in comment
        try:
            response = self.ollama_client.chat(
                model='mistral',  # Model is now set to 'mistral'
                messages=[{'role': 'user', 'content': user_input}]
            )
            return response['message']['content']
        except Exception as e:
            print(f"Error from Ollama: {e}")
            return "Sorry, I had trouble responding."

    def send_message(self):
        """Handles sending a text message from the input field."""
        user_input = self.user_input_entry.get()
        if user_input:
            self.add_user_message(user_input)
            self.user_input_entry.delete(0, END)

            bot_response_text = self.generate_response(user_input)
            self.add_bot_message(bot_response_text)
            self.speak_response(bot_response_text)

    def send_message_event(self, event):
        """Handles sending message when Enter key is pressed."""
        self.send_message()

    def recognize_speech(self):
        """Listens for speech and returns text with UI feedback.""" # Comment updated
        with sr.Microphone() as source:
            print("Listening for voice input...")
            self.add_bot_message("Listening for voice input...") # UI feedback: message in chat
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
        try:
            self.add_bot_message("Recognizing...") # UI feedback: message in chat
            print(f"Recognizing voice input...") # Console debug
            text = self.recognizer.recognize_google(audio)
            print(f"Voice input recognized: {text}")
            self.add_user_message(text)
            return text.lower()
        except sr.UnknownValueError:
            print("Could not understand audio")
            self.add_bot_message("Could not understand audio") # UI feedback
            return ""
        except sr.RequestError as e:
            print(f"Speech recognition error; {e}")
            self.add_bot_message("Speech recognition error") # UI feedback
            return ""

    def process_voice_input(self):
        """Processes voice input and generates response (in thread)."""
        user_voice_input = self.recognize_speech()
        if user_voice_input:
            bot_response_text = self.generate_response(user_voice_input)
            self.add_bot_message(bot_response_text)
            self.speak_response(bot_response_text)

    def start_voice_input(self):
        """Starts voice input in a separate thread."""
        threading.Thread(target=self.process_voice_input, daemon=True).start()


def main():
    root = tk.Tk()
    chatbot_ui = ChatbotUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()