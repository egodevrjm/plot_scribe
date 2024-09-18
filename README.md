# PlotScribe
I had this idea, based on the fact Luma AI has published an API for Dream Machine — create a tool that can take a simple text prompt and generate a multi-shot video. Basically a rapid prototyper for AI video content.

I sat down to work out a rough workflow this morning before work. Created some core code structure on my lunchbreak and now I have a roughly functional application that does most of what I want.

Each stage will also have a manual entry option including the story generation for users who want to just use it to plot out their own ideas and rapid prototype with the AI image and video before filming themselves.

1. User enters a title and the number of 'shots' the project should have.
2. It sends that to the Groq API running Meta's Llama 3.1 8b model
3. Groq generates a short story based on the title 
4. Groq splits the short story up logically into however many 'shots' the user defined and creates a description, image prompt and motion prompt for each shot
5. User can generate an image using the fal ai Flux API for each shot individually or all shots as a whole, with descriptive prompts for consistency.
.... below here is functionality I'm still working on ....
6. User can then send the image and motion prompt to the Luma AI Dream Machine API to generate a video for each shot.
7. User can export shots individually or stitched together.

Ideas for expansion:
Integration of an AI music API such as Suno and ElevenLabs for voice over and SFX. Could even integrate Hedra API for lip-sync.

Will be making it open source and available on GitHub once steps 1-7 are functional. So far its been about 18 hours from concept to step 5.

![PlotScribe screenshot]([ps_ss.png]))
