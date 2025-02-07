import tkinter as tk
from tkinter import scrolledtext, Entry, Button, END, WORD, RIGHT, Y, BOTH, X, TOP, BOTTOM, LEFT, Text, Menu, Scale, HORIZONTAL, Frame, Label, filedialog, colorchooser
import speech_recognition as sr
import pyttsx3
from ollama import Client
import threading
import pyperclip  # For clipboard functionality

class ChatbotUI:
    def __init__(self, master):
        self.master = master
        master.title("ChatGPT-like Voice Chatbot (Mistral)")
        master.geometry("600x750") # Increased window height to accommodate more UI elements

        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.ollama_client = Client()
        self.voice_muted = False # Initialize voice mute state

        # --- Speech Rate Adjustment ---
        default_rate = self.engine.getProperty('rate')
        new_rate = int(default_rate * 1.2)
        self.engine.setProperty('rate', new_rate)
        print(f"Speech rate adjusted from {default_rate} to {new_rate}")

        # --- Theme Colors ---
        self.themes = {
            "Light Mode": {"bg": "white", "fg": "black", "button_bg": "#f0f0f0", "button_fg": "black", "input_bg": "white", "input_fg": "black"},
            "Dark Mode": {"bg": "#333333", "fg": "white", "button_bg": "#555555", "button_fg": "white", "input_bg": "#444444", "input_fg": "white"}
        }
        self.current_theme = "Light Mode" # Default theme
        self.set_theme(self.current_theme) # Apply initial theme

        # --- Font ---
        self.default_font = ("Arial", 10)
        self.chat_font = tk.font.Font(family=self.default_font[0], size=self.default_font[1]) # Create font object

        # --- Menu Bar ---
        menubar = Menu(master)
        master.config(menu=menubar)

        # File Menu
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Chat History", command=self.save_chat_history)
        file_menu.add_command(label="Load Chat History", command=self.load_chat_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=master.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Theme Menu
        theme_menu = Menu(menubar, tearoff=0)
        theme_menu.add_command(label="Light Mode", command=lambda: self.set_theme("Light Mode"))
        theme_menu.add_command(label="Dark Mode", command=lambda: self.set_theme("Dark Mode"))
        menubar.add_cascade(label="Theme", menu=theme_menu)

        # Color Menu
        color_menu = Menu(menubar, tearoff=0)
        color_menu.add_command(label="User Message Color", command=self.choose_user_color)
        color_menu.add_command(label="Chatbot Message Color", command=self.choose_bot_color)
        menubar.add_cascade(label="Colors", menu=color_menu)

        # Voice Menu
        self.voice_menu = Menu(menubar, tearoff=0) # Create voice menu (populated later)
        menubar.add_cascade(label="Voice", menu=self.voice_menu)
        self.populate_voice_menu() # Populate voice menu with available voices

        # Chat History Display
        self.chat_display = Text(master, wrap=WORD, state=tk.DISABLED, height=25, padx=10, pady=10, font=self.chat_font, bg=self.themes[self.current_theme]["bg"], fg=self.themes[self.current_theme]["fg"], insertbackground=self.themes[self.current_theme]["fg"])
        self.chat_display.pack(pady=10, padx=10, fill=BOTH, expand=True)

        # Font Control Frame
        font_frame = Frame(master, bg=self.themes[self.current_theme]["bg"]) # Frame for font controls, themed
        font_frame.pack(pady=(0, 5))
        increase_font_button = Button(font_frame, text="+ Font", command=lambda: self.change_font_size(2), font=self.default_font, bg=self.themes[self.current_theme]["button_bg"], fg=self.themes[self.current_theme]["button_fg"], activebackground=self.themes[self.current_theme]["button_bg"], activeforeground=self.themes[self.current_theme]["button_fg"])
        increase_font_button.pack(side=LEFT, padx=5)
        decrease_font_button = Button(font_frame, text="- Font", command=lambda: self.change_font_size(-2), font=self.default_font, bg=self.themes[self.current_theme]["button_bg"], fg=self.themes[self.current_theme]["button_fg"], activebackground=self.themes[self.current_theme]["button_bg"], activeforeground=self.themes[self.current_theme]["button_fg"])
        decrease_font_button.pack(side=LEFT, padx=5)

        # Speech Rate Control Frame
        rate_frame = Frame(master, bg=self.themes[self.current_theme]["bg"]) # Frame for rate control, themed
        rate_frame.pack(pady=(0, 5))
        rate_label = Label(rate_frame, text="Speech Rate:", font=self.default_font, bg=self.themes[self.current_theme]["bg"], fg=self.themes[self.current_theme]["fg"])
        rate_label.pack(side=LEFT, padx=5)
        self.rate_slider = Scale(rate_frame, from_=50, to=300, orient=HORIZONTAL, command=self.set_speech_rate, length=200, bg=self.themes[self.current_theme]["bg"], fg=self.themes[self.current_theme]["fg"], highlightbackground=self.themes[self.current_theme]["bg"]) # Themed slider
        self.rate_slider.set(new_rate)
        self.rate_slider.pack(side=LEFT)

        # Input Frame
        input_frame = Frame(master, bg=self.themes[self.current_theme]["bg"]) # Input frame themed
        input_frame.pack(padx=10, pady=(0, 10), fill=X)

        # User Input Entry
        self.user_input_entry = Entry(input_frame, font=self.default_font, bg=self.themes[self.current_theme]["input_bg"], fg=self.themes[self.current_theme]["input_fg"], insertbackground=self.themes[self.current_theme]["input_fg"]) # Themed input
        self.user_input_entry.pack(side=LEFT, padx=(0, 5), fill=X, expand=True)
        self.user_input_entry.bind("<Return>", self.send_message_event)

        # Send Button
        self.send_button = Button(input_frame, text="Send", command=self.send_message, font=self.default_font, bg=self.themes[self.current_theme]["button_bg"], fg=self.themes[self.current_theme]["button_fg"], activebackground=self.themes[self.current_theme]["button_bg"], activeforeground=self.themes[self.current_theme]["button_fg"]) # Themed button
        self.send_button.pack(side=LEFT)

        # Voice Input Button
        self.voice_button = Button(master, text="Voice Input", command=self.start_voice_input, font=self.default_font, bg=self.themes[self.current_theme]["button_bg"], fg=self.themes[self.current_theme]["button_fg"], activebackground=self.themes[self.current_theme]["button_bg"], activeforeground=self.themes[self.current_theme]["button_fg"]) # Themed button
        self.voice_button.pack(pady=(0, 10))

        # Clear Chat Button
        self.clear_button = Button(master, text="Clear Chat", command=self.clear_chat_history, font=self.default_font, bg=self.themes[self.current_theme]["button_bg"], fg=self.themes[self.current_theme]["button_fg"], activebackground=self.themes[self.current_theme]["button_bg"], activeforeground=self.themes[self.current_theme]["button_fg"]) # Themed button
        self.clear_button.pack(pady=(0, 10))

        # Mute Voice Button
        self.mute_button = Button(master, text="Mute Voice", command=self.toggle_mute_voice, font=self.default_font, bg=self.themes[self.current_theme]["button_bg"], fg=self.themes[self.current_theme]["button_fg"], activebackground=self.themes[self.current_theme]["button_bg"], activeforeground=self.themes[self.current_theme]["button_fg"]) # Themed button
        self.mute_button.pack(pady=(0, 10))


        self.add_bot_message("Voice Chatbot Started! (Mistral Model)")
        self.speak_response("Voice Chatbot Started! Using Mistral Model")
        self.add_bot_message("How can I help you today?")

    def set_theme(self, theme_name):
        """Sets the color theme for the UI."""
        self.current_theme = theme_name
        theme_colors = self.themes[theme_name]
        bg_color, fg_color, button_bg, button_fg, input_bg, input_fg = theme_colors.values()

        self.master.config(bg=bg_color)
        self.chat_display.config(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self.user_input_entry.config(bg=input_bg, fg=input_fg, insertbackground=input_fg)
        self.send_button.config(bg=button_bg, fg=button_fg, activebackground=button_bg, activeforeground=button_fg)
        self.voice_button.config(bg=button_bg, fg=button_fg, activebackground=button_bg, activeforeground=button_fg)
        self.clear_button.config(bg=button_bg, fg=button_fg, activebackground=button_bg, activeforeground=button_fg)
        self.mute_button.config(bg=button_bg, fg=button_fg, activebackground=button_bg, activeforeground=button_fg)
        font_frame_bg = bg_color # Frame background same as main background
        rate_frame_bg = bg_color
        input_frame_bg = bg_color
        font_frame.config(bg=font_frame_bg)
        rate_frame.config(bg=rate_frame_bg)
        input_frame.config(bg=input_frame_bg)
        rate_label.config(bg=rate_frame_bg, fg=fg_color) # Themed label
        self.rate_slider.config(bg=rate_frame_bg, fg=fg_color, highlightbackground=rate_frame_bg) # Themed slider


    def change_font_size(self, size_change):
        """Changes the font size of chat and input text."""
        current_font = self.chat_font.actual() # Get actual font properties as dict
        font_size = current_font['size'] + size_change
        if font_size > 6: # Basic minimum size limit
            self.chat_font.config(size=font_size) # Update font object directly
            self.chat_display.config(font=self.chat_font)
            self.user_input_entry.config(font=self.chat_font)

    def set_speech_rate(self, value):
        """Sets the speech rate based on slider value."""
        try:
            new_rate = int(float(value))
            self.engine.setProperty('rate', new_rate)
            print(f"Speech rate set to: {new_rate}")
        except ValueError:
            print("Invalid speech rate value")

    def populate_voice_menu(self):
        """Populates the Voice menu with available voices."""
        voices = self.engine.getProperty('voices')
        self.voice_menu.delete(0, END) # Clear existing menu items
        for voice in voices:
            self.voice_menu.add_command(label=voice.name, command=lambda v=voice.id: self.set_voice(v))

    def set_voice(self, voice_id):
        """Sets the text-to-speech voice."""
        self.engine.setProperty('voice', voice_id)
        print(f"Voice set to: {voice_id}")

    def toggle_mute_voice(self):
        """Toggles voice output on/off."""
        self.voice_muted = not self.voice_muted
        if self.voice_muted:
            self.mute_button.config(text="Unmute Voice")
            print("Voice output muted")
        else:
            self.mute_button.config(text="Mute Voice")
            print("Voice output unmuted")

    def clear_chat_history(self):
        """Clears the chat display."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, END)
        self.chat_display.config(state=tk.DISABLED)
        self.add_bot_message("Chat history cleared.")
        self.speak_response("Chat history cleared.")

    def save_chat_history(self):
        """Saves chat history to a text file."""
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filepath:
            try:
                chat_log = self.chat_display.get(1.0, END)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(chat_log)
                self.add_bot_message(f"Chat history saved to: {filepath}")
                self.speak_response("Chat history saved.")
            except Exception as e:
                self.add_bot_message(f"Error saving chat history: {e}")
                self.speak_response("Error saving chat history.")

    def load_chat_history(self):
        """Loads chat history from a text file."""
        filepath = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filepath:
            try:
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.delete(1.0, END)
                with open(filepath, "r", encoding="utf-8") as f:
                    loaded_chat_log = f.read()
                    for line in loaded_chat_log.splitlines():
                        if line.startswith("Chatbot:"):
                            self.add_bot_message(line[len("Chatbot:"):].strip())
                        elif line.startswith("You:"):
                            self.add_user_message(line[len("You:"):].strip())
                        else:
                            self.add_bot_message(line.strip())
                self.chat_display.config(state=tk.DISABLED)
                self.add_bot_message(f"Chat history loaded from: {filepath}")
                self.speak_response("Chat history loaded.")
            except Exception as e:
                self.add_bot_message(f"Error loading chat history: {e}")
                self.speak_response("Error loading chat history.")

    def add_message(self, sender, message, is_bot_message=False):
        """Adds a message to the chat display with formatting and Copy button."""
        self.chat_display.config(state=tk.NORMAL)
        if is_bot_message:
            self.chat_display.insert(END, f"Chatbot: ", "bot_label")
        else:
            self.chat_display.insert(END, f"You: ", "user_label")

        message_start_index = self.chat_display.index(END)

        self.chat_display.insert(END, f"{message}\n")

        message_end_index = self.chat_display.index(END)

        if is_bot_message:
            self.chat_display.tag_config("bot_label", foreground="green", font=("Arial", 10, "bold"))
            self.chat_display.tag_add("bot_message", message_start_index, message_end_index)
            self.chat_display.tag_config("bot_message", foreground="green")
            copy_button = Button(self.chat_display, text="Copy", font=("Arial", 8),
                                 command=lambda msg=message: self.copy_to_clipboard(msg), bg=self.themes[self.current_theme]["button_bg"], fg=self.themes[self.current_theme]["button_fg"], activebackground=self.themes[self.current_theme]["button_bg"], activeforeground=self.themes[self.current_theme]["button_fg"]) # Themed button
            self.chat_display.window_create(END, window=copy_button)
            self.chat_display.insert(END, "\n")

        else:
            self.chat_display.tag_config("user_label", foreground="blue", font=("Arial", 10, "bold"))
            self.chat_display.tag_config("user_message", foreground="blue")
            self.chat_display.tag_add("user_message", message_start_index, message_end_index)

        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(END)

    def add_user_message(self, message):
        self.add_message("You", message, is_bot_message=False)

    def add_bot_message(self, message):
        self.add_message("Chatbot", message, is_bot_message=True)

    def speak_response(self, text):
        """Speaks the chatbot's response if not muted."""
        if not self.voice_muted:
            self.engine.say(text)
            self.engine.runAndWait()

    def generate_response(self, user_input):
        """Generates chatbot response using Ollama with Mistral model."""
        try:
            response = self.ollama_client.chat(
                model='mistral',
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
        """Listens for speech and returns text with UI feedback."""
        with sr.Microphone() as source:
            print("Listening for voice input...")
            self.add_bot_message("Listening for voice input...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
        try:
            self.add_bot_message("Recognizing...")
            print(f"Recognizing voice input...")
            text = self.recognizer.recognize_google(audio)
            print(f"Voice input recognized: {text}")
            self.add_user_message(text)
            return text.lower()
        except sr.UnknownValueError:
            print("Could not understand audio")
            self.add_bot_message("Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Speech recognition error; {e}")
            self.add_bot_message("Speech recognition error")
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

    def copy_to_clipboard(self, text_to_copy):
        """Copies text to the clipboard."""
        pyperclip.copy(text_to_copy)
        print("Chatbot response copied to clipboard!")  # Optional feedback

def main():
    root = tk.Tk()
    chatbot_ui = ChatbotUI(root)
    tk.font.nametofont("TkDefaultFont").configure(family="Arial", size=10) # Set default font for Tkinter
    root.mainloop()

if __name__ == "__main__":
    main()