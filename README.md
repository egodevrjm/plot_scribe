# PlotScribe
I had this idea, based on the fact Luma AI has published an API for Dream Machine — create a tool that can take a simple text prompt and generate a multi-shot video. Basically a rapid prototyper for AI video content.

I sat down to work out a rough workflow this morning before work. Created some core code structure on my lunchbreak and now I have a roughly functional application that does most of what I want.

Each stage will also have a manual entry option including the story generation for users who want to just use it to plot out their own ideas and rapid prototype with the AI image and video before filming themselves.

1. User enters a title and the number of 'shots' the project should have.
2. It sends that to the Groq API running Meta's Llama 3.1 8b model
3. Groq generates a short story based on the title 
4. Groq splits the short story up logically into however many 'shots' the user defined and creates a description, image prompt and motion prompt for each shot
5. User can generate an image using the fal ai Flux API for each shot individually or all shots as a whole, with descriptive prompts for consistency.
6. User can then send the image and motion prompt to the Luma AI Dream Machine API to generate a video for each shot.
7. User can export shots individually 

## TO DO
8. Export of clips stitched together.
9. Improved UI for re-ordering shots, sending it back to Groq API to re-write based on position.
10. Integration of an AI music API such as Suno 
11. Integration of ElevenLabs for voice over and SFX 
12. Could even integrate Hedra API for lip-sync 

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up your API keys as environment variables or create a `.env` file in the project root with the following content:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   FAL_KEY=your_fal_api_key_here
   LUMAAI_API_KEY=your_lumaai_api_key_here
   ```
   Replace `your_*_api_key_here` with your actual API keys.

4. Run the application:
   ```
   python plotscribe.py
   ```
### Platforms

1. Video: Luma AI Dream Machine API
2. Image: FAL AI Flux API (I've used Schnell in code but upgrade to Pro for better output)
3. Text: Groq API (I've used Llama 3.1 70B but any model should work)


![PlotScribe Screenshot](/ps_ss.png)
