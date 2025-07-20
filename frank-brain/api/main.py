from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
import openai
import whisper
import tempfile
import os
import io
from typing import Dict, Any, Optional
import sys
sys.path.append('/home/spacholski/Sources/frank-the-assistant/frank-brain')
from agents.websearch.agent import WebSearchAgent

app = FastAPI(title="Frank Brain API", version="1.0.0")

model = whisper.load_model("base")
websearch_agent = WebSearchAgent()

@app.post("/transcribe/")
async def transcribe_audio(
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        contents = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(contents)
            temp_file_path = temp_file.name
        
        result = model.transcribe(temp_file_path)
        
        os.unlink(temp_file_path)
        
        response = {
            "text": result["text"],
            "language": result["language"],
            "segments": result["segments"]
        }
        
        query = f"Przeszukaj internet i odpowiedz na pytanie: {result['text']}"
        search_result = websearch_agent.search(query)
        response["search_results"] = search_result
        
        return response
    
    except Exception as e:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Frank Brain API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)