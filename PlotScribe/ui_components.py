# ui_components.py

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import threading
import requests
import logging
from PIL import Image, ImageTk
import io

from models import Shot  # Import the Shot class from models.py

# Custom Widget for Each Shot
class ShotWidget(ttk.Frame):
    def __init__(self, master, shot, parent_app):
        super().__init__(master)
        self.shot = shot
        self.parent_app = parent_app
        self.photo = None  # Keep a reference to the photo
        self.init_ui()

    def init_ui(self):
        # Configure grid weights
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Header Frame
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=5)

        # Shot Number
        self.shot_number_label = ttk.Label(header_frame, text=f"Shot {self.shot.number}:", font=('Arial', 12, 'bold'))
        self.shot_number_label.pack(side=tk.LEFT)

        # Generate/Regenerate Shot Button
        btn_text = "Generate Shot" if not self.shot.description else "Regenerate Shot"
        self.generate_shot_btn = ttk.Button(header_frame, text=btn_text, command=self.request_shot_generation)
        self.generate_shot_btn.pack(side=tk.LEFT, padx=5)

        # Progress bar for shot regeneration
        self.regenerate_progress = ttk.Progressbar(header_frame, mode='indeterminate')
        self.regenerate_progress.pack(side=tk.LEFT, padx=5)
        self.regenerate_progress.pack_forget()

        # Remove Shot Button
        self.remove_btn = ttk.Button(header_frame, text="Remove Shot", command=self.request_shot_removal)
        self.remove_btn.pack(side=tk.LEFT, padx=5)

        # Toggle Details Button
        self.details_visible = tk.BooleanVar(value=True)
        self.toggle_details_btn = ttk.Button(header_frame, text='Hide Details', command=self.toggle_details)
        self.toggle_details_btn.pack(side=tk.LEFT, padx=5)

        # Details Frame
        self.details_frame = ttk.Frame(self)
        self.details_frame.grid(row=1, column=0, columnspan=2, sticky='nsew')
        self.rowconfigure(1, weight=1)  # Allow details frame to expand

        # Notebook for Description and Prompts
        self.notebook = ttk.Notebook(self.details_frame)
        self.notebook.pack(fill='both', expand=True)

        # Description Tab
        description_frame = ttk.Frame(self.notebook)
        self.notebook.add(description_frame, text='Description')

        self.description_text = tk.Text(description_frame, height=4, wrap='word')
        self.description_text.insert('1.0', self.shot.description)
        self.description_text.config(state='disabled')
        self.description_text.pack(fill='both', expand=True)

        # Image Prompt Tab
        image_prompt_frame = ttk.Frame(self.notebook)
        self.notebook.add(image_prompt_frame, text='Image Prompt')

        self.image_prompt_text = tk.Text(image_prompt_frame, height=4, wrap='word')
        self.image_prompt_text.insert('1.0', self.shot.image_prompt)
        self.image_prompt_text.config(state='disabled')
        self.image_prompt_text.pack(fill='both', expand=True)

        # Motion Prompt Tab
        motion_prompt_frame = ttk.Frame(self.notebook)
        self.notebook.add(motion_prompt_frame, text='Motion Prompt')

        self.motion_prompt_text = tk.Text(motion_prompt_frame, height=4, wrap='word')
        self.motion_prompt_text.insert('1.0', self.shot.motion_prompt)
        self.motion_prompt_text.config(state='disabled')
        self.motion_prompt_text.pack(fill='both', expand=True)

        # Media Frame
        media_frame = ttk.Frame(self)
        media_frame.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=5)
        self.rowconfigure(2, weight=1)  # Allow media frame to expand

        # Image Section
        image_frame = ttk.Frame(media_frame)
        image_frame.grid(row=0, column=0, sticky='nsew', padx=5)
        media_frame.columnconfigure(0, weight=1)
        media_frame.rowconfigure(0, weight=1)

        self.image_label = ttk.Label(image_frame)
        self.image_label.pack()

        self.image_status = ttk.Label(image_frame, text="")
        self.image_status.pack()

        self.image_progress = ttk.Progressbar(image_frame, mode='indeterminate')

        # Image Buttons
        image_button_frame = ttk.Frame(media_frame)
        image_button_frame.grid(row=1, column=0, sticky='ew', padx=5)

        self.generate_image_btn = ttk.Button(image_button_frame, text="Generate Image", command=self.request_image_generation)
        self.generate_image_btn.pack(pady=2)

        # Video Section
        video_frame = ttk.Frame(media_frame)
        video_frame.grid(row=0, column=1, sticky='nsew', padx=5)
        media_frame.columnconfigure(1, weight=1)

        # Removed the video_label that displays the URL
        # self.video_label = ttk.Label(video_frame)
        # self.video_label.pack()

        self.video_status = ttk.Label(video_frame, text="")
        self.video_status.pack()

        self.video_progress = ttk.Progressbar(video_frame, mode='indeterminate')

        # Video Buttons
        video_button_frame = ttk.Frame(media_frame)
        video_button_frame.grid(row=1, column=1, sticky='ew', padx=5)

        self.generate_video_btn = ttk.Button(video_button_frame, text="Generate Video", command=self.request_video_generation)
        self.generate_video_btn.config(state=tk.DISABLED)
        self.generate_video_btn.pack(pady=2)

        # Removed the play button since video playback isn't supported
        # self.play_btn = ttk.Button(video_button_frame, text="Play", command=self.play_pause_video)
        # self.play_btn.config(state=tk.DISABLED)
        # self.play_btn.pack(pady=2)

        self.download_btn = ttk.Button(video_button_frame, text="Download Video", command=self.download_video)
        self.download_btn.config(state=tk.DISABLED)
        self.download_btn.pack(pady=2)

    def toggle_details(self):
        if self.details_visible.get():
            self.details_frame.grid_remove()
            self.details_visible.set(False)
            self.toggle_details_btn.config(text='Show Details')
        else:
            self.details_frame.grid()
            self.details_visible.set(True)
            self.toggle_details_btn.config(text='Hide Details')

    def request_shot_generation(self):
        self.regenerate_progress.pack(side=tk.LEFT, padx=5)
        self.regenerate_progress.start()
        self.generate_shot_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.parent_app.regenerate_shot, args=(self.shot, self)).start()

    def request_image_generation(self):
        self.image_progress.pack()
        self.image_progress.start()
        self.image_status.config(text="Generating image...")
        self.generate_image_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.parent_app.generate_image_for_shot, args=(self.shot, self)).start()

    def request_video_generation(self):
        self.video_progress.pack()
        self.video_progress.start()
        self.video_status.config(text="Generating video...")
        self.generate_video_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.parent_app.generate_video_for_shot, args=(self.shot, self)).start()

    def request_shot_removal(self):
        self.parent_app.remove_shot(self.shot)

    def update_shot_content(self, description, image_prompt, motion_prompt):
        self.shot.description = description
        self.shot.image_prompt = image_prompt
        self.shot.motion_prompt = motion_prompt
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(tk.END, description)
        self.description_text.config(state=tk.DISABLED)
        self.image_prompt_text.config(state=tk.NORMAL)
        self.image_prompt_text.delete(1.0, tk.END)
        self.image_prompt_text.insert(tk.END, image_prompt)
        self.image_prompt_text.config(state=tk.DISABLED)
        self.motion_prompt_text.config(state=tk.NORMAL)
        self.motion_prompt_text.delete(1.0, tk.END)
        self.motion_prompt_text.insert(tk.END, motion_prompt)
        self.motion_prompt_text.config(state=tk.DISABLED)
        self.generate_shot_btn.config(text="Regenerate Shot")

    def update_image(self, image_url):
        self.shot.image_url = image_url
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((400, 250), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.photo)
            self.image_label.image = self.photo  # Keep a reference
        except requests.RequestException as e:
            logging.error(f"Failed to load image: {e}")
            self.image_label.config(text="Failed to load image")

        self.image_progress.stop()
        self.image_progress.pack_forget()
        self.image_status.config(text="Image generated successfully!")
        self.generate_image_btn.config(state=tk.NORMAL)
        self.generate_video_btn.config(state=tk.NORMAL)

    def update_video(self, video_url):
        logging.info(f"Updating video for shot {self.shot.number}")
        self.video_progress.stop()
        self.video_progress.pack_forget()
        self.video_status.config(text="Video generated successfully!")
        self.generate_video_btn.config(state=tk.NORMAL)
        self.shot.video_url = video_url
        # Removed updating the video_label with the URL
        # self.video_label.config(text=f"Video generated: {video_url}")
        # Enable the download button
        self.download_btn.config(state=tk.NORMAL)
        logging.info(f"Video update complete for shot {self.shot.number}")

    def show_error(self, error_message, error_type=None):
        if error_type == "regenerate":
            self.regenerate_progress.stop()
            self.regenerate_progress.pack_forget()
            self.generate_shot_btn.config(state=tk.NORMAL)
            messagebox.showerror("Error", f"Error regenerating shot {self.shot.number}: {error_message}")
        elif error_type == "video":
            self.video_progress.stop()
            self.video_progress.pack_forget()
            self.video_status.config(text=f"Error: {error_message}")
            self.generate_video_btn.config(state=tk.NORMAL)
        elif error_type == "image":
            self.image_progress.stop()
            self.image_progress.pack_forget()
            self.image_status.config(text=f"Error: {error_message}")
            self.generate_image_btn.config(state=tk.NORMAL)
        else:
            # General error
            messagebox.showerror("Error", error_message)

    # Removed the play_pause_video method since playback isn't supported
    # def play_pause_video(self):
    #     messagebox.showinfo("Video Playback", "Video playback is not implemented in this Tkinter version.")

    def download_video(self):
        if not self.shot.video_url:
            messagebox.showwarning("Download Error", "No video available to download.")
            return
        file_name = filedialog.asksaveasfilename(
            title="Save Video",
            initialfile=f"shot_{self.shot.number}.mp4",
            defaultextension=".mp4",
            filetypes=[("MP4 Files", "*.mp4")],
        )
        if file_name:
            try:
                response = requests.get(self.shot.video_url, stream=True)
                response.raise_for_status()
                with open(file_name, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                messagebox.showinfo("Download Complete", f"Video saved as {file_name}")
            except Exception as e:
                messagebox.showerror("Download Error", f"Failed to download video: {str(e)}")
