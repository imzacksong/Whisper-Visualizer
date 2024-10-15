import os
import whisper
import librosa
import numpy as np
import pygame
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk

import ttkbootstrap as ttk  

import imageio
from imageio_ffmpeg import get_ffmpeg_exe  

# Global variables
audio_file = None
segments = []
playback_running = False
waveform_color = (0, 255, 0)  # Default waveform color
subtitle_color = "#00FF00"  # Default subtitle color in hex
rainbow_effect = False  # Track if rainbow effect is enabled
max_words = 10  # Max words per subtitle chunk

FONT_OPTIONS = [
    "Arial", "Helvetica", "Courier", "Times New Roman", "Verdana",
    "Georgia", "Calibri", "Tahoma", "Comic Sans MS", "Papyrus"
]

WAVEFORM_STYLES = ["Line", "Bar", "Filled"]

class WaveformApp(ttk.Window):  
    def __init__(self):
        super().__init__(themename="superhero")  
        self.title("Waveform Visualizer with Subtitles")
        self.configure(bg="#1e1e1e")  

        self.init_variables()
        self.create_widgets()
        pygame.init()
        self.screen = pygame.Surface((900, 400))

        # Update the window size based on the content
        self.update_idletasks()
        self.minsize(self.winfo_width(), self.winfo_height())
        self.geometry(f"{self.winfo_width()}x{self.winfo_height()}")

    def init_variables(self):
        self.rainbow_var = tk.IntVar()
        self.max_words_var = tk.IntVar(value=10)
        self.font_var = tk.StringVar(value="Arial")
        self.waveform_style_var = tk.StringVar(value="Line")
        self.amplitude_scale_var = tk.DoubleVar(value=1.0)
        self.playback_position_var = tk.DoubleVar(value=0.0)
        self.playback_paused = False
        self.export_format_var = tk.StringVar(value="mp4")
        self.export_quality_var = tk.StringVar(value="High")

    def create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title and Upload Section
        title_label = ttk.Label(main_frame, text="Upload or Drag-and-Drop Audio", font=("Arial", 18, "bold"))
        title_label.pack(pady=10)

        upload_btn = ttk.Button(main_frame, text="Select Audio", command=self.open_audio, width=20)
        upload_btn.pack(pady=5)

        # Canvas for visualization
        self.canvas = tk.Canvas(main_frame, width=900, height=400, highlightthickness=0, bg="black")
        self.canvas.pack(pady=10)
        self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW)
        self.canvas.tag_lower(self.canvas_image)

        # Controls Frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(pady=5)

        self.preview_btn = ttk.Button(controls_frame, text="Start Preview", command=self.start_preview, state=tk.DISABLED, width=12)
        self.preview_btn.grid(row=0, column=0, padx=5, pady=5)

        self.pause_btn = ttk.Button(controls_frame, text="Pause", command=self.pause_preview, state=tk.DISABLED, width=12)
        self.pause_btn.grid(row=0, column=1, padx=5, pady=5)

        self.resume_btn = ttk.Button(controls_frame, text="Resume", command=self.resume_preview, state=tk.DISABLED, width=12)
        self.resume_btn.grid(row=0, column=2, padx=5, pady=5)

        self.stop_btn = ttk.Button(controls_frame, text="Stop", command=self.stop_preview, state=tk.DISABLED, width=12)
        self.stop_btn.grid(row=0, column=3, padx=5, pady=5)

        # Playback Slider
        self.playback_slider = ttk.Scale(main_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.playback_position_var, command=self.seek_audio, length=800)
        self.playback_slider.pack(pady=10)

        # Settings Frame
        settings_frame = ttk.Frame(main_frame)
        settings_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Use grid to layout the settings
        settings_frame.columnconfigure(0, weight=1, uniform="group1")
        settings_frame.columnconfigure(1, weight=1, uniform="group1")
        settings_frame.columnconfigure(2, weight=1, uniform="group1")

        # Waveform Settings
        waveform_frame = ttk.Labelframe(settings_frame, text="Waveform Settings", padding=10)
        waveform_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        waveform_color_btn = ttk.Button(waveform_frame, text="Select Waveform Color", command=self.choose_waveform_color)
        waveform_color_btn.pack(pady=5, fill=tk.X)

        rainbow_check = ttk.Checkbutton(waveform_frame, text="Enable Rainbow Effect", variable=self.rainbow_var, command=self.toggle_rainbow)
        rainbow_check.pack(pady=5, anchor="w")

        waveform_style_label = ttk.Label(waveform_frame, text="Waveform Style:")
        waveform_style_label.pack(pady=5, anchor="w")

        waveform_style_menu = ttk.Combobox(waveform_frame, textvariable=self.waveform_style_var, values=WAVEFORM_STYLES, state="readonly")
        waveform_style_menu.pack(pady=5, fill=tk.X)

        amplitude_scale_label = ttk.Label(waveform_frame, text="Amplitude Scaling:")
        amplitude_scale_label.pack(pady=5, anchor="w")

        amplitude_scale_slider = ttk.Scale(waveform_frame, from_=0.1, to=5.0, variable=self.amplitude_scale_var, orient=tk.HORIZONTAL)
        amplitude_scale_slider.pack(pady=5, fill=tk.X)

        # Subtitle Settings
        subtitle_frame = ttk.Labelframe(settings_frame, text="Subtitle Settings", padding=10)
        subtitle_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        subtitle_color_btn = ttk.Button(subtitle_frame, text="Select Subtitle Color", command=self.choose_subtitle_color)
        subtitle_color_btn.pack(pady=5, fill=tk.X)

        font_label = ttk.Label(subtitle_frame, text="Select Subtitle Font:")
        font_label.pack(pady=5, anchor="w")

        font_dropdown = ttk.Combobox(subtitle_frame, textvariable=self.font_var, values=FONT_OPTIONS, state="readonly")
        font_dropdown.pack(pady=5, fill=tk.X)

        max_words_label = ttk.Label(subtitle_frame, text="Max Words per Subtitle:")
        max_words_label.pack(pady=5, anchor="w")

        max_words_spinbox = ttk.Spinbox(subtitle_frame, from_=1, to=20, textvariable=self.max_words_var)
        max_words_spinbox.pack(pady=5, fill=tk.X)

        # Export Settings
        export_frame = ttk.Labelframe(settings_frame, text="Export Settings", padding=10)
        export_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        export_format_label = ttk.Label(export_frame, text="Export Format:")
        export_format_label.pack(pady=5, anchor="w")

        export_format_menu = ttk.Combobox(export_frame, textvariable=self.export_format_var, values=["mp4", "avi", "mkv"], state="readonly")
        export_format_menu.pack(pady=5, fill=tk.X)

        export_quality_label = ttk.Label(export_frame, text="Export Quality:")
        export_quality_label.pack(pady=5, anchor="w")

        export_quality_menu = ttk.Combobox(export_frame, textvariable=self.export_quality_var, values=["Low", "Medium", "High"], state="readonly")
        export_quality_menu.pack(pady=5, fill=tk.X)

        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode="determinate", length=400)
        self.progress.pack(pady=10)

        # Export Button
        export_btn = ttk.Button(main_frame, text="Select Output Location & Export", command=self.export_video, width=30)
        export_btn.pack(pady=10)

    def toggle_rainbow(self):
        global rainbow_effect
        rainbow_effect = bool(self.rainbow_var.get())

    def open_audio(self):
        global audio_file
        audio_file = filedialog.askopenfilename(title="Select Audio File", filetypes=[("Audio Files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac")])
        if audio_file:
            self.preview_btn.config(state=tk.NORMAL)
            messagebox.showinfo("File Uploaded", "Audio file uploaded successfully!")

    def start_preview(self):
        global playback_running, max_words
        max_words = self.max_words_var.get()
        if audio_file:
            playback_running = True
            self.progress.start()
            self.preview_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.NORMAL)
            self.playback_paused = False

            # Start transcription in a separate thread
            threading.Thread(target=self.transcribe_and_preview).start()
        else:
            messagebox.showerror("Error", "Please select an audio file first.")

    def pause_preview(self):
        if not self.playback_paused:
            pygame.mixer.music.pause()
            self.playback_paused = True
            self.pause_btn.config(state=tk.DISABLED)
            self.resume_btn.config(state=tk.NORMAL)

    def resume_preview(self):
        if self.playback_paused:
            pygame.mixer.music.unpause()
            self.playback_paused = False
            self.pause_btn.config(state=tk.NORMAL)
            self.resume_btn.config(state=tk.DISABLED)

    def stop_preview(self):
        global playback_running
        playback_running = False
        pygame.mixer.music.stop()
        self.canvas.delete("subtitle")
        self.preview_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
        self.playback_slider.set(0)

    def transcribe_and_preview(self):
        global segments
        try:
            self.progress.config(mode="indeterminate")
            self.progress.start()

            # Load the whisper model once to prevent lag
            if not hasattr(self, 'whisper_model'):
                self.whisper_model = whisper.load_model("base")
            result = self.whisper_model.transcribe(audio_file, word_timestamps=True)

            segments = []

            # Process each segment and split into chunks with accurate timing
            for segment in result['segments']:
                words = segment['words']
                num_words = len(words)
                i = 0
                while i < num_words:
                    chunk_words = words[i:i + max_words]
                    chunk_text = ' '.join([w['word'] for w in chunk_words])
                    chunk_start = chunk_words[0]['start']
                    chunk_end = chunk_words[-1]['end']
                    segments.append({
                        'start': chunk_start,
                        'end': chunk_end,
                        'text': chunk_text
                    })
                    i += max_words

            self.progress.stop()
            self.progress.config(mode="determinate")
            self.after(0, self.play_audio_with_waveform)
        except Exception as e:
            self.progress.stop()
            messagebox.showerror("Error", f"An error occurred during transcription: {e}")

    def play_audio_with_waveform(self):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            pygame.mixer.music.set_endevent(pygame.USEREVENT)
            self.playback_duration = librosa.get_duration(filename=audio_file)

            # Preload and process audio data once
            if not hasattr(self, 'amplitudes'):
                y, sr = librosa.load(audio_file, sr=None)
                self.duration = librosa.get_duration(y=y, sr=sr)
                self.amplitudes = np.abs(y)
                self.samples_len = len(self.amplitudes)

            self.run_waveform_visualization()
            self.update_subtitles()
            self.update_playback_slider()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during playback: {e}")

    def seek_audio(self, value):
        if playback_running:
            position = float(value)
            new_time = (position / 100.0) * self.playback_duration
            pygame.mixer.music.play(start=new_time)
            self.playback_paused = False
            self.pause_btn.config(state=tk.NORMAL)
            self.resume_btn.config(state=tk.DISABLED)

    def update_playback_slider(self):
        if playback_running and pygame.mixer.music.get_busy():
            current_time = pygame.mixer.music.get_pos() / 1000.0
            position = (current_time / self.playback_duration) * 100.0
            self.playback_position_var.set(position)
            self.after(100, self.update_playback_slider)  
        else:
            self.playback_position_var.set(0)

    def run_waveform_visualization(self):
        if playback_running and pygame.mixer.music.get_busy():
            self.screen.fill((0, 0, 0))  
            current_time = pygame.mixer.music.get_pos() / 1000
            current_sample = int((current_time / self.duration) * self.samples_len)
            amplitude_scale = self.amplitude_scale_var.get()
            waveform_style = self.waveform_style_var.get()
            num_samples = 200  

            for i in range(current_sample, min(current_sample + num_samples, self.samples_len)):
                amp = self.amplitudes[i] * amplitude_scale
                bar_height = int(amp * 200)
                x_pos = int((i - current_sample) * (900 / num_samples))
                color = self.get_waveform_color(i)
                if waveform_style == "Line":
                    pygame.draw.line(self.screen, color, (x_pos, 200 - bar_height // 2), (x_pos, 200 + bar_height // 2), 2)
                elif waveform_style == "Bar":
                    pygame.draw.rect(self.screen, color, (x_pos, 200 - bar_height // 2, 3, bar_height))
                elif waveform_style == "Filled":
                    pygame.draw.polygon(self.screen, color, [(x_pos, 200), (x_pos, 200 - bar_height // 2), (x_pos + 3, 200 - bar_height // 2), (x_pos + 3, 200)])

            pygame_image = pygame.surfarray.array3d(self.screen)
            pygame_image = np.transpose(pygame_image, (1, 0, 2))
            img = Image.fromarray(pygame_image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.canvas.image = imgtk  # Keep a reference
            self.canvas.itemconfig(self.canvas_image, image=imgtk)
            self.after(33, self.run_waveform_visualization)
        else:
            self.progress.stop()

    def get_waveform_color(self, index):
        if rainbow_effect:
            colors = [
                (255, 0, 0),     # Red
                (255, 127, 0),   # Orange
                (255, 255, 0),   # Yellow
                (0, 255, 0),     # Green
                (0, 0, 255),     # Blue
                (75, 0, 130),    # Indigo
                (148, 0, 211)    # Violet
            ]
            return colors[index % len(colors)]
        return waveform_color

    def update_subtitles(self):
        current_time = pygame.mixer.music.get_pos() / 1000
        subtitle = ""
        for segment in segments:
            if segment['start'] <= current_time <= segment['end']:
                subtitle = segment['text']
                break

        if getattr(self, "current_subtitle", None) != subtitle:
            self.current_subtitle = subtitle
            self.canvas.delete("subtitle")
            selected_font = (self.font_var.get(), 18)
            self.canvas.create_text(450, 375, text=subtitle, fill=subtitle_color, font=selected_font, anchor="center", width=800, tags="subtitle")
        if playback_running and pygame.mixer.music.get_busy():
            self.after(200, self.update_subtitles)  

    def choose_waveform_color(self):
        global waveform_color
        color = colorchooser.askcolor()[0]
        if color:
            waveform_color = tuple(map(int, color))

    def choose_subtitle_color(self):
        global subtitle_color
        color = colorchooser.askcolor()[1]
        if color:
            subtitle_color = color

    def export_video(self):
        output_format = self.export_format_var.get().lower()
        quality = self.export_quality_var.get()
        output_path = filedialog.asksaveasfilename(defaultextension=f".{output_format}", filetypes=[(f"{output_format.upper()} files", f"*.{output_format}")])
        if output_path:
            try:
                from tqdm import tqdm  

                self.progress.config(mode="indeterminate")
                self.progress.start()

                # Prepare variables
                if not hasattr(self, 'amplitudes'):
                    y, sr = librosa.load(audio_file, sr=None)
                    duration = librosa.get_duration(y=y, sr=sr)
                    amplitudes = np.abs(y)
                    samples_len = len(amplitudes)
                    self.amplitudes = amplitudes
                    self.samples_len = samples_len
                    self.duration = duration

                else:
                    amplitudes = self.amplitudes
                    samples_len = self.samples_len
                    duration = self.duration

                # Prepare font for subtitles
                font_name = self.font_var.get()
                font_size = 18
                font = pygame.font.SysFont(font_name, font_size)

                # Convert subtitle color to RGB tuple
                subtitle_color_rgb = pygame.Color(subtitle_color)

                # Calculate total frames
                fps = 30
                total_frames = int(duration * fps)

                # Quality settings
                if quality == "High":
                    codec_quality = 10  
                elif quality == "Medium":
                    codec_quality = 20
                else:
                    codec_quality = 30

                # Use imageio to write video
                writer = imageio.get_writer(output_path, fps=fps, codec='libx264', quality=codec_quality, ffmpeg_log_level='error')

                # Load audio data for writing into video
                audio_data, audio_sr = librosa.load(audio_file, sr=None)

                # Resample audio to 44100 Hz for compatibility
                if audio_sr != 44100:
                    audio_data = librosa.resample(audio_data, orig_sr=audio_sr, target_sr=44100)
                    audio_sr = 44100

                # Prepare audio for writing
                audio_data = (audio_data * 32767).astype(np.int16)  # Convert to 16-bit PCM

                # Create a temporary file for the audio
                import tempfile
                import soundfile as sf

                temp_audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                sf.write(temp_audio_file.name, audio_data, audio_sr, subtype='PCM_16')

                # Render frames and write to video
                for frame_num in tqdm(range(total_frames), desc="Exporting video"):
                    t = frame_num / fps

                    # Create a new surface
                    screen = pygame.Surface((900, 400))

                    # Fill background
                    screen.fill((0, 0, 0))

                    # Compute current sample
                    current_sample = int((t / duration) * samples_len)
                    amplitude_scale = self.amplitude_scale_var.get()
                    waveform_style = self.waveform_style_var.get()
                    num_samples = 200  

                    for i in range(current_sample, min(current_sample + num_samples, samples_len)):
                        amp = amplitudes[i] * amplitude_scale
                        bar_height = int(amp * 200)
                        x_pos = int((i - current_sample) * (900 / num_samples))
                        color = self.get_waveform_color(i)
                        if waveform_style == "Line":
                            pygame.draw.line(screen, color, (x_pos, 200 - bar_height // 2), (x_pos, 200 + bar_height // 2), 2)
                        elif waveform_style == "Bar":
                            pygame.draw.rect(screen, color, (x_pos, 200 - bar_height // 2, 3, bar_height))
                        elif waveform_style == "Filled":
                            pygame.draw.polygon(screen, color, [(x_pos, 200), (x_pos, 200 - bar_height // 2), (x_pos + 3, 200 - bar_height // 2), (x_pos + 3, 200)])

                    # Render subtitle
                    subtitle = ""
                    for segment in segments:
                        if segment['start'] <= t <= segment['end']:
                            subtitle = segment['text']
                            break
                    if subtitle:
                        text_surface = font.render(subtitle, True, subtitle_color_rgb)
                        text_rect = text_surface.get_rect(center=(450, 375))
                        screen.blit(text_surface, text_rect)

                    # Convert frame to numpy array
                    frame_image = pygame.surfarray.array3d(screen)
                    frame_image = np.transpose(frame_image, (1, 0, 2))

                    writer.append_data(frame_image)

                writer.close()

                # Merge audio and video using imageio_ffmpeg
                final_output = output_path
                temp_video_file = output_path + '_video_only.mp4'
                os.rename(output_path, temp_video_file)

                ffmpeg_exe = get_ffmpeg_exe()

                # Command to merge audio and video
                merge_cmd = [
                    ffmpeg_exe,
                    '-y',
                    '-i', temp_video_file,
                    '-i', temp_audio_file.name,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-strict', 'experimental',
                    '-b:a', '192k',
                    final_output
                ]

                subprocess.run(merge_cmd, check=True)

                # Cleanup temporary files
                os.remove(temp_video_file)
                os.remove(temp_audio_file.name)

                self.progress.stop()

                messagebox.showinfo("Export", f"Exported video to {final_output}!")
            except Exception as e:
                self.progress.stop()
                messagebox.showerror("Error", f"An error occurred during export: {e}")

if __name__ == "__main__":
    app = WaveformApp()
    app.mainloop()
