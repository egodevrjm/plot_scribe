# PlotScribe

PlotScribe is a tool designed for rapid prototyping of AI-generated videos, transforming simple text prompts into multi-shot videos. Leveraging APIs like Luma AI's Dream Machine, FAL AI's Flux API, and Groq, PlotScribe automates the process of generating a story, splitting it into individual shots, creating images for each shot, and stitching them into a video.

## Concept

The inspiration for PlotScribe came from the release of the Luma AI Dream Machine API. The goal was to build a rapid prototyping tool for AI video content, enabling users to generate and visualize ideas quickly.

PlotScribe allows users to automate or manually input each stage of the video creation process. For users who prefer manual control, the tool can also be used to plot their own ideas and prototype the visuals before actual filming.

## Features

1. **Title and Shot Definition**: Input a project title and specify the desired number of shots.
2. **Story Generation**: Sends the title to the Groq API (using Meta's Llama 3.1 70B model) to generate a short story based on the title.
3. **Shot Creation**: The story is split into the specified number of shots, each with a description, image prompt, and motion prompt.
4. **Image Generation**: Generate images for individual shots using the FAL AI Flux API, with prompts designed for consistency across shots.
5. **Video Generation**: Use the Luma AI Dream Machine API to generate a video for each shot based on the image and motion prompt.
6. **Export and Stitching**: Export images and videos individually or stitch all videos together into a single video file.
7. **Shot Management**: Add, remove, and reorder shots within the project.

## Updates

- **User Interface Overhaul**: Transitioned to Tkinter for the GUI, providing a more streamlined and user-friendly interface.
- **Progress Indicators**: Added progress bars and status messages to inform users of ongoing API calls and processes.
- **Improved Layout**: Action buttons are now arranged vertically on the right side, making the shot display area wider and more prominent.
- **Error Handling**: Enhanced error messages and handling for a better user experience.
- **Dependencies Updated**: Requirements have been updated to reflect the current libraries used.

## To-Do

- **Video Playback**: Integrate video playback within the application using a suitable library.
- **AI Music Integration**: Integrate a music API such as Suno for background scores.
- **Voice and SFX**: Integrate ElevenLabs for voiceover and sound effects.
- **Lip-sync**: Consider integrating Hedra API for lip-sync functionality in videos.

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/egodevrjm/plot_scribe.git
   
2. ***Install required packages***:
   ```bash
   pip install -r requirements.txt
   
3. ***Set up API keys***: You can either set them as environment variables or create a .env file in the project root with the following content:
   ```bash
   GROQ_API_KEY=your_groq_api_key_here
   FAL_KEY=your_fal_api_key_here
   LUMAAI_API_KEY=your_lumaai_api_key_here
   ```
   Replace your_*_api_key_here with your actual API keys.
   
5. ***Run the application***:
   python plotscribe_app.py

### ffmpeg

PlotScribe uses moviepy to stitch together the generated videos. To use moviepy you need [ffmpeg] (https://www.ffmpeg.org/) on your system. 

***For macOS (using Homebrew)***:
```bash
   brew install ffmpeg
```

***For Linux (Ubuntu/Debian)***:
```bash
   sudo apt-get update
   sudo apt-get install ffmpeg
```

***For Windows***:
Download the FFmpeg builds from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
Extract the downloaded file
Add the bin folder to your system PATH

***_After installing ffmpeg, make sure to restart your Python environment or IDE for the changes to take effect._***

### Platforms

1. Video: [Luma AI Dream Machine API](https://lumalabs.ai/dream-machine/api)
2. Image: [FAL AI Flux API](https://fal.ai) (I've used Schnell in code but upgrade to Pro for better output)
3. Text: [Groq API](https://console.groq.com/docs/models) (I've used Llama 3.1 70B but any model should work)


