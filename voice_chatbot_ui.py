import tkinter as tk
from tkinter import scrolledtext, Entry, Button, END
import speech_recognition as sr
import pyttsx3
from ollama import Client
import threading  # For non-blocking speech recognition

class ChatbotUI:
    def __init__(self, master):
        self.master = master
        master.title("Voice Chatbot UI")

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

        self.add_bot_message("Voice Chatbot Started!")
        self.speak_response("Voice Chatbot Started!")

    def add_message(self, sender, message):
        """Adds a message to the chat display."""
        self.chat_display.config(state=tk.NORMAL) # Enable editing to append
        self.chat_display.insert(END, f"{sender}: {message}\n", sender) # Add with tag
        self.chat_display.tag_config("user", foreground="blue") # Example user message color
        self.chat_display.tag_config("bot", foreground="green") # Example bot message color
        self.chat_display.config(state=tk.DISABLED) # Disable editing again
        self.chat_display.see(END) # Scroll to the end

    def add_user_message(self, message):
        self.add_message("You", message)

    def add_bot_message(self, message):
        self.add_message("Chatbot", message)

    def speak_response(self, text):
        """Speaks the chatbot's response."""
        self.engine.say(text)
        self.engine.runAndWait()

    def generate_response(self, user_input):
        """Generates chatbot response using Ollama."""
        try:
            response = self.ollama_client.chat(
                model='llama3.2:latest',  # Or use 'mistral:latest', 'gemma:7b', etc.
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
            self.user_input_entry.delete(0, END) # Clear input field

            bot_response_text = self.generate_response(user_input)
            self.add_bot_message(bot_response_text)
            self.speak_response(bot_response_text)

    def send_message_event(self, event):
        """Handles sending message when Enter key is pressed in input field."""
        self.send_message() # Call the same send_message function

    def recognize_speech(self):
        """Listens for speech and returns text."""
        with sr.Microphone() as source:
            print("Listening for voice input...") # For console debugging
            self.add_bot_message("Listening for voice input...") # In UI
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
        try:
            text = self.recognizer.recognize_google(audio)
            print(f"Voice input recognized: {text}") # Console debug
            self.add_user_message(text) # Add voice input to UI
            return text.lower()
        except sr.UnknownValueError:
            print("Could not understand audio") # Console debug
            self.add_bot_message("Could not understand audio") # UI feedback
            return ""
        except sr.RequestError as e:
            print(f"Speech recognition error; {e}") # Console debug
            self.add_bot_message("Speech recognition error") # UI feedback
            return ""

    def process_voice_input(self):
        """Processes voice input and generates response (run in thread)."""
        user_voice_input = self.recognize_speech()
        if user_voice_input:
            bot_response_text = self.generate_response(user_voice_input)
            self.add_bot_message(bot_response_text)
            self.speak_response(bot_response_text)

    def start_voice_input(self):
        """Starts voice input in a separate thread to prevent UI blocking."""
        threading.Thread(target=self.process_voice_input, daemon=True).start()


def main():
    root = tk.Tk()
    chatbot_ui = ChatbotUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()