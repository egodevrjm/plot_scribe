# models.py

# Data Models

class Shot:
    def __init__(self, number, description="", image_prompt="", motion_prompt="", image_url="", video_url=""):
        self.number = number
        self.description = description
        self.image_prompt = image_prompt
        self.motion_prompt = motion_prompt
        self.image_url = image_url
        self.video_url = video_url


class Project:
    def __init__(self, title, shots=None):
        self.title = title
        self.shots = shots if shots else []
