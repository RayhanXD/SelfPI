import openai

openai.api_key = "sk-test"

def transcribe(path: str) -> str:
    with open(path, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    return transcript["text"]
