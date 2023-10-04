from fastapi import FastAPI, Request, File
import whisper
from fastapi.responses import RedirectResponse
import torch

app = FastAPI()

@app.get("/", response_class=RedirectResponse)
def read_root():
    """
    Redirects the root URL ("/") to the documentation page ("/docs").
    """
    return "/docs"

# Global Language - Can be changed via form data or language detection
language = "English"

# Loading the model globally to speed up the process
# Models depend on accuracy
torch.cuda.is_available()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

modal = whisper.load_model("small", device=DEVICE)

@app.post("/uploadfile/")
async def add_audio(request: Request, file: bytes = File()):
    """
    Transcribes audio files and returns the transcribed text.

    Args:
        request (Request): The HTTP request object.
        file (bytes): The audio file to be transcribed.

    Returns:
        dict: A dictionary containing the transcribed text and status code.
            - "data": Transcribed text or an error message.
            - "status": HTTP status code (201 for success, 400 for an error).
    """
    # Save the uploaded audio file as 'audio.mp3'
    with open('audio.mp3', 'wb') as f:
        f.write(file)

    # Load the global model
    model = modal

    try:
        # Transcribe the audio
        result = model.transcribe("audio.mp3", language=language, fp16=False)
        context = {
            "data": result['text'],
            "status": 201
        }
    except:
        context = {
            "data": "Please record again",
            "status": 400
        }

    return context

# Another way to perform these operations is via a pipeline (Python feature) if graphics are available in the system
