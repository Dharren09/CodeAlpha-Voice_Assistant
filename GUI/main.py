import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
import os

class VoiceAssistantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Jey - Voice Assistant")

        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=40, height=10)
        self.text_area.pack(padx=10, pady=10)

        self.start_button = tk.Button(self.root, text="Start Assistant", command=self.start_assistant)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="Stop Assistant", command=self.stop_assistant)
        self.stop_button.pack(pady=10)

        self.sound_icon_label = tk.Label(self.root, text="🔊", font=("Arial", 20))  # Sound icon
        self.sound_icon_label.pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.voice_assistant_thread = None

    def start_assistant(self):
        self.text_area.delete("1.0", tk.END)
        self.voice_assistant_thread = Thread(target=self.run_voice_assistant)
        self.voice_assistant_thread.start()
        self.animate_sound_icon()

    def run_voice_assistant(self):
        os.system("python voice-assistant/Voice-Assistant/voice.py")  # Replace with the path to your actual script

    def stop_assistant(self):
        os.system("pkill -f 'voice-assistant/Voice-Assistant/voice.py'")  # Replace with the path to your actual script
        self.text_area.insert(tk.END, "Voice Assistant Stopped\n")

    def on_close(self):
        if self.voice_assistant_thread and self.voice_assistant_thread.is_alive():
            self.stop_assistant()
        self.root.destroy()

    def animate_sound_icon(self):
         self.stop_animation = False  # Flag to stop the animation

         def toggle_sound_icon():
             if not self.stop_animation:
                 current_text = self.sound_icon_label.cget("text")
                 new_text = "🔊" if current_text == "🔈" else "🔈"
                 self.sound_icon_label.config(text=new_text)
                 self.root.after(500, toggle_sound_icon)  # Change icon every 500 milliseconds

         toggle_sound_icon()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = VoiceAssistantGUI()
    gui.run()
