# plotscribe_app.py

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox, simpledialog
import threading
import queue
import os
import json
import requests
import logging
import asyncio
import time
import tempfile

# API clients
import fal_client  # FAL API client
from groq import Groq  # Groq API client
from lumaai import AsyncLumaAI  # Luma Labs API client

from PIL import Image, ImageTk
import io

# Import your data models and UI components
from models import Shot, Project
from ui_components import ShotWidget

# Initialize logging for debugging
logging.basicConfig(level=logging.DEBUG)


# Main GUI Application
class PlotScribeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PlotScribe")
        style = ttk.Style()
        style.theme_use('clam')
        self.project = None
        self.queue = queue.Queue()
        self.init_ui()

        # Initialize API Handlers
        self.groq_api = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.fal_api_key = os.environ.get("FAL_KEY")
        if not self.fal_api_key:
            logging.error("FAL API key not found in environment variables")
            messagebox.showerror("Configuration Error", "FAL API key not found. Please set the FAL_KEY environment variable.")
        self.luma_api = AsyncLumaAI(auth_token=os.environ.get("LUMAAI_API_KEY"))

        # Start the queue processor
        self.after(100, self.process_queue)

    def init_ui(self):
        self.geometry("1024x768")  # Set window size
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Project Title and Shot Number Input
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, padx=5, pady=5)

        self.title_label = ttk.Label(title_frame, text="Project Title:")
        self.title_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.title_input = ttk.Entry(title_frame)
        self.title_input.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        self.shot_label = ttk.Label(title_frame, text="Number of Shots:")
        self.shot_label.grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.shot_input = ttk.Entry(title_frame)
        self.shot_input.grid(row=0, column=3, padx=5, pady=5, sticky='ew')

        self.generate_project_btn = ttk.Button(title_frame, text="Generate Project", command=self.generate_story_and_shots)
        self.generate_project_btn.grid(row=0, column=4, padx=5, pady=5)

        # Configure column weights
        title_frame.columnconfigure(1, weight=1)
        title_frame.columnconfigure(3, weight=1)

        # Status Frame for Progress Indicator
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        self.status_label = ttk.Label(self.status_frame, text="")
        self.status_label.pack(side=tk.LEFT)
        self.progress_bar = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        # Initially hide the status frame
        self.status_frame.pack_forget()

        # Content Frame
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Shot List Area with Scrollbar
        shot_frame = ttk.Frame(content_frame)
        shot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.shot_canvas = tk.Canvas(shot_frame)
        self.shot_scrollbar = ttk.Scrollbar(shot_frame, orient="vertical", command=self.shot_canvas.yview)
        self.shot_canvas.configure(yscrollcommand=self.shot_scrollbar.set)
        self.shot_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.shot_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.shot_container = ttk.Frame(self.shot_canvas)
        self.shot_container.bind("<Configure>", self.on_frame_configure)
        self.shot_canvas.create_window((0, 0), window=self.shot_container, anchor="nw")

        # Action Buttons on the right
        action_frame = ttk.Frame(content_frame)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        self.save_project_btn = ttk.Button(action_frame, text="Save Project", command=self.save_project)
        self.save_project_btn.pack(fill=tk.X, pady=5)

        self.export_images_btn = ttk.Button(action_frame, text="Export All Images", command=self.export_all_images)
        self.export_images_btn.pack(fill=tk.X, pady=5)

        self.export_videos_btn = ttk.Button(action_frame, text="Export All Videos", command=self.export_all_videos)
        self.export_videos_btn.pack(fill=tk.X, pady=5)

        self.stitch_export_btn = ttk.Button(action_frame, text="Stitch and Export Videos", command=self.stitch_and_export_videos)
        self.stitch_export_btn.pack(fill=tk.X, pady=5)

        self.add_shot_btn = ttk.Button(action_frame, text="Add Shot", command=self.add_new_shot)
        self.add_shot_btn.pack(fill=tk.X, pady=5)

        self.reorder_shots_btn = ttk.Button(action_frame, text="Reorder Shots", command=self.reorder_shots)
        self.reorder_shots_btn.pack(fill=tk.X, pady=5)

    def on_frame_configure(self, event):
        self.shot_canvas.configure(scrollregion=self.shot_canvas.bbox("all"))

    def process_queue(self):
        try:
            while True:
                func, args = self.queue.get_nowait()
                func(*args)
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def generate_story_and_shots(self):
        title = self.title_input.get()
        try:
            num_shots = int(self.shot_input.get())
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter a valid number of shots.")
            return

        if not title or num_shots <= 0:
            messagebox.showwarning("Input Error", "Please enter a valid title and number of shots.")
            return

        logging.debug(f"Generating project '{title}' with {num_shots} shots")
        self.project = Project(title)

        # Clear the current shot layout
        for widget in self.shot_container.winfo_children():
            widget.destroy()

        # Show the status frame and start progress bar
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        self.status_label.config(text="Generating project...")
        self.progress_bar.start()

        # Generate the story and shots in a separate thread
        threading.Thread(target=self.generate_story, args=(title, num_shots)).start()

    def generate_story(self, title, num_shots):
        try:
            # Step 2: Generate a short story based on the title
            story_response = self.groq_api.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a creative writer tasked with creating a short story."},
                    {"role": "user", "content": f"Write a short story based on the title '{title}'. The story should be suitable for splitting into {num_shots} distinct scenes or shots."}
                ],
                model="llama-3.1-70b-versatile"
            )
            story = story_response.choices[0].message.content
            logging.debug(f"Generated story: {story}")

            # Step 3: Split the story into logical shots
            split_response = self.groq_api.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a screenplay writer tasked with dividing a story into distinct shots."},
                    {"role": "user", "content": f"Split the following story into exactly {num_shots} logical shots or scenes. Number each shot and provide a brief description of what happens in that shot:\n\n{story}"}
                ],
                model="llama-3.1-70b-versatile"
            )
            shot_descriptions = split_response.choices[0].message.content
            logging.debug(f"Split shots: {shot_descriptions}")

            # Step 4: Generate detailed shot information
            shots = []
            shot_list = shot_descriptions.strip().split('\n')
            for i in range(1, num_shots + 1):
                description = next((s for s in shot_list if s.startswith(f"{i}.")), f"Shot {i}: No description provided")
                shot = self.generate_single_shot(i, num_shots, description)
                shots.append(shot)

            self.queue.put((self.populate_shots, (shots,)))
        except Exception as e:
            logging.error(f"Error generating story and shots: {str(e)}")
            self.queue.put((self.handle_api_error, (e,)))

    def generate_single_shot(self, shot_number, total_shots, description):
        try:
            shot_response = self.groq_api.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a film director providing details for a shot."},
                    {"role": "user", "content": f"""
Based on the following shot description, provide:
1. A concise one-sentence description of the shot.
2. An image prompt for generating a visual representation of the shot (two sentences).
3. A motion prompt describing a brief camera movement or effect for the shot (one action).

Shot description: {description}

Format your response as follows:
1. **Shot Description**: [Your one-sentence description]
2. **Image Prompt**: [Your two-sentence image prompt]
3. **Motion Prompt**: [Your one-action motion prompt]
"""}
                ],
                model="llama-3.1-70b-versatile"
            )
            shot_content = shot_response.choices[0].message.content
            shot_desc, image_prompt, motion_prompt = self.parse_shot_content(shot_content)

            logging.debug(f"Generated shot {shot_number}:")
            logging.debug(f"Description: {shot_desc}")
            logging.debug(f"Image Prompt: {image_prompt}")
            logging.debug(f"Motion Prompt: {motion_prompt}")

            return Shot(number=shot_number, description=shot_desc, image_prompt=image_prompt, motion_prompt=motion_prompt)
        except Exception as e:
            logging.error(f"Error generating shot {shot_number}: {str(e)}")
            return Shot(number=shot_number, description=f"Error generating shot {shot_number}", image_prompt="", motion_prompt="")

    def parse_shot_content(self, content):
        parts = content.strip().split('\n')
        description = ""
        image_prompt = ""
        motion_prompt = ""
        for part in parts:
            if part.startswith("1. **Shot Description**:"):
                description = part.replace("1. **Shot Description**:", "").strip()
            elif part.startswith("2. **Image Prompt**:"):
                image_prompt = part.replace("2. **Image Prompt**:", "").strip()
            elif part.startswith("3. **Motion Prompt**:"):
                motion_prompt = part.replace("3. **Motion Prompt**:", "").strip()
        return description, image_prompt, motion_prompt

    def populate_shots(self, shots):
        logging.debug(f"Populating {len(shots)} shots.")
        self.project.shots = shots

        # Clear existing widgets from the shot_container
        for widget in self.shot_container.winfo_children():
            widget.destroy()

        for shot in shots:
            shot_widget = ShotWidget(self.shot_container, shot, self)
            shot_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Stop the progress bar and hide the status frame
        self.progress_bar.stop()
        self.status_label.config(text="Project generated successfully.")
        # Optionally, hide the status frame after a short delay
        self.after(3000, self.status_frame.pack_forget)

    def handle_api_error(self, error):
        logging.error(f"API error occurred: {error}")
        error_message = str(error)
        detailed_message = f"An error occurred: {error_message}\n\nPlease check the application logs for more details."
        messagebox.showerror("API Error", detailed_message)

        # Stop the progress bar and update status label
        self.progress_bar.stop()
        self.status_label.config(text="An error occurred.")
        # Optionally, hide the status frame after a short delay
        self.after(3000, self.status_frame.pack_forget)

    def generate_image_for_shot(self, shot, shot_widget):
        def worker():
            try:
                logging.debug(f"Sending request to FAL API for shot {shot.number} with prompt: {shot.image_prompt}")
                handler = fal_client.submit(
                    "fal-ai/flux/schnell",
                    arguments={
                        "prompt": shot.image_prompt,
                        "image_size": "landscape_16_9"
                    },
                )
                logging.debug(f"Request submitted to FAL API. Request ID: {handler.request_id}")

                result = handler.get()
                logging.debug(f"Received response from FAL API: {json.dumps(result, indent=2)}")

                if 'images' in result and len(result['images']) > 0:
                    image_url = result['images'][0]['url']
                    logging.debug(f"Image generated for shot {shot.number}: {image_url}")
                    self.queue.put((shot_widget.update_image, (image_url,)))
                else:
                    logging.error(f"No image URL found in FAL API response: {result}")
                    raise ValueError("No image URL in API response")
            except Exception as e:
                logging.error(f"Error in FAL API call for shot {shot.number}: {str(e)}")
                self.queue.put((shot_widget.show_error, (str(e), "image")))

        threading.Thread(target=worker).start()

    def generate_video_for_shot(self, shot, shot_widget):
        def worker():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.async_generate_video(shot, shot_widget))
                loop.close()
            except Exception as e:
                logging.error(f"Error generating video for shot {shot.number}: {str(e)}")
                self.queue.put((shot_widget.show_error, (str(e), "video")))

        threading.Thread(target=worker).start()

    async def async_generate_video(self, shot, shot_widget):
        try:
            generation = await self.luma_api.generations.create(
                prompt=shot.motion_prompt,
                keyframes={
                    "frame0": {
                        "type": "image",
                        "url": shot.image_url
                    }
                }
            )
            logging.debug(f"Initial Luma API response for shot {shot.number}: {json.dumps(generation, indent=2, default=str)}")

            # Poll for completion
            max_attempts = 30  # Adjust as needed
            for attempt in range(max_attempts):
                generation = await self.luma_api.generations.get(id=generation.id)
                logging.debug(f"Poll attempt {attempt + 1} for shot {shot.number}: {json.dumps(generation, indent=2, default=str)}")

                if hasattr(generation, 'state') and generation.state == 'completed':
                    if hasattr(generation, 'assets') and hasattr(generation.assets, 'video'):
                        video_url = generation.assets.video
                        logging.info(f"Video generated for shot {shot.number}: {video_url}")
                        self.queue.put((shot_widget.update_video, (video_url,)))
                        return
                    else:
                        raise ValueError(f"Completed generation for shot {shot.number} missing video URL")
                elif hasattr(generation, 'state') and generation.state == 'failed':
                    raise ValueError(f"Generation for shot {shot.number} failed")

                await asyncio.sleep(10)  # Wait 10 seconds before polling again

            raise TimeoutError(f"Video generation for shot {shot.number} timed out")

        except Exception as e:
            logging.error(f"Error in Luma API call for shot {shot.number}: {str(e)}")
            self.queue.put((shot_widget.show_error, (str(e), "video")))

    def save_project(self):
        if not self.project:
            messagebox.showwarning("No Project", "There is no project to save.")
            return

        file_name = filedialog.asksaveasfilename(title="Save Project", initialfile=f"{self.project.title}.json", defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not file_name:
            return  # User cancelled the dialog

        try:
            project_data = {
                "title": self.project.title,
                "shots": [
                    {
                        "number": shot.number,
                        "description": shot.description,
                        "image_prompt": shot.image_prompt,
                        "motion_prompt": shot.motion_prompt,
                        "image_url": shot.image_url,
                        "video_url": shot.video_url
                    }
                    for shot in self.project.shots
                ]
            }

            with open(file_name, 'w') as f:
                json.dump(project_data, f, indent=2)

            messagebox.showinfo("Save Complete", f"Project has been saved to {file_name}")
        except Exception as e:
            logging.error(f"Failed to save project: {str(e)}")
            messagebox.showerror("Save Error", f"Failed to save project: {str(e)}")

    def export_all_images(self):
        if not self.project or not self.project.shots:
            messagebox.showwarning("No Images", "There are no images to export.")
            return

        directory = filedialog.askdirectory(title="Select Directory to Save Images")
        if not directory:
            return  # User cancelled the dialog

        for shot in self.project.shots:
            if shot.image_url:
                file_name = os.path.join(directory, f"{self.project.title}_shot_{shot.number}.jpg")
                try:
                    response = requests.get(shot.image_url)
                    response.raise_for_status()
                    with open(file_name, 'wb') as file:
                        file.write(response.content)
                    logging.debug(f"Exported image for shot {shot.number} to {file_name}")
                except Exception as e:
                    logging.error(f"Failed to export image for shot {shot.number}: {str(e)}")

        messagebox.showinfo("Export Complete", f"All available images have been exported to {directory}")

    def export_all_videos(self):
        if not self.project or not self.project.shots:
            messagebox.showwarning("No Videos", "There are no videos to export.")
            return

        directory = filedialog.askdirectory(title="Select Directory to Save Videos")
        if not directory:
            return  # User cancelled the dialog

        for shot in self.project.shots:
            if shot.video_url:
                file_name = os.path.join(directory, f"{self.project.title}_shot_{shot.number}.mp4")
                try:
                    response = requests.get(shot.video_url, stream=True)
                    response.raise_for_status()
                    with open(file_name, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            file.write(chunk)
                    logging.debug(f"Exported video for shot {shot.number} to {file_name}")
                except Exception as e:
                    logging.error(f"Failed to export video for shot {shot.number}: {str(e)}")

        messagebox.showinfo("Export Complete", f"All available videos have been exported to {directory}")

    def stitch_and_export_videos(self):
        if not self.project or not self.project.shots:
            messagebox.showwarning("No Videos", "There are no videos to stitch and export.")
            return

        # Check if all shots have videos
        missing_videos = [shot.number for shot in self.project.shots if not shot.video_url]
        if missing_videos:
            messagebox.showwarning("Missing Videos", f"The following shots are missing videos: {', '.join(map(str, missing_videos))}")
            return

        output_file = filedialog.asksaveasfilename(title="Save Stitched Video", initialfile=f"{self.project.title}_stitched.mp4", defaultextension=".mp4", filetypes=[("MP4 Files", "*.mp4")])
        if not output_file:
            return  # User cancelled the dialog

        try:
            # Import MoviePy only when needed
            from moviepy.editor import VideoFileClip, concatenate_videoclips

            # Download all videos to temporary files
            temp_files = []
            for shot in self.project.shots:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                response = requests.get(shot.video_url, stream=True)
                response.raise_for_status()
                with open(temp_file.name, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                temp_files.append(temp_file.name)

            # Stitch videos
            clips = [VideoFileClip(file) for file in temp_files]
            final_clip = concatenate_videoclips(clips)
            final_clip.write_videofile(output_file)

            # Clean up temporary files
            for file in temp_files:
                os.remove(file)

            messagebox.showinfo("Export Complete", f"Stitched video has been exported to {output_file}")
        except Exception as e:
            logging.error(f"Failed to stitch and export videos: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to stitch and export videos: {str(e)}")

    def add_new_shot(self):
        if not self.project:
            messagebox.showwarning("No Project", "Please generate a project first.")
            return
        new_shot_number = len(self.project.shots) + 1
        new_shot = Shot(number=new_shot_number)
        self.project.shots.append(new_shot)
        shot_widget = ShotWidget(self.shot_container, new_shot, self)
        shot_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def regenerate_shot(self, shot, shot_widget):
        threading.Thread(target=self.thread_regenerate_shot, args=(shot, shot_widget)).start()

    def thread_regenerate_shot(self, shot, shot_widget):
        try:
            updated_shot = self.generate_single_shot(shot.number, len(self.project.shots), shot.description)
            self.queue.put((self.update_shot_widget, (shot, updated_shot, shot_widget)))
        except Exception as e:
            logging.error(f"Error regenerating shot: {str(e)}")
            self.queue.put((shot_widget.show_error, (str(e), "regenerate")))

    def update_shot_widget(self, old_shot, updated_shot, shot_widget):
        shot_widget.update_shot_content(updated_shot.description, updated_shot.image_prompt, updated_shot.motion_prompt)
        shot_widget.generate_shot_btn.config(state=tk.NORMAL)
        shot_widget.regenerate_progress.stop()
        shot_widget.regenerate_progress.pack_forget()

    def remove_shot(self, shot):
        # Remove the shot from the project
        self.project.shots = [s for s in self.project.shots if s.number != shot.number]

        # Renumber remaining shots
        for i, s in enumerate(self.project.shots, 1):
            s.number = i

        # Refresh the shot layout
        for widget in self.shot_container.winfo_children():
            widget.destroy()
        self.populate_shots(self.project.shots)

    def reorder_shots(self):
        if not self.project or not self.project.shots:
            messagebox.showwarning("No Shots", "There are no shots to reorder.")
            return

        current_order = [str(shot.number) for shot in self.project.shots]
        new_order = simpledialog.askstring("Reorder Shots", "Enter the new order of shots (comma-separated numbers):", initialvalue=",".join(current_order))

        if new_order:
            try:
                new_order_list = [int(x.strip()) for x in new_order.split(',')]
                if set(new_order_list) != set(range(1, len(self.project.shots) + 1)):
                    raise ValueError("Invalid shot numbers")

                # Reorder shots
                self.project.shots = [next(shot for shot in self.project.shots if shot.number == num) for num in new_order_list]

                # Renumber shots
                for i, shot in enumerate(self.project.shots, 1):
                    shot.number = i

                # Refresh the shot layout
                for widget in self.shot_container.winfo_children():
                    widget.destroy()
                self.populate_shots(self.project.shots)
            except (ValueError, StopIteration):
                messagebox.showwarning("Invalid Input", "Please enter valid shot numbers.")


if __name__ == "__main__":
    app = PlotScribeApp()
    app.mainloop()
