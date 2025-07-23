from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
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
        
        query = f"Przeszukaj internet i odpowiedz na pytanie: {result['text']}. Odpowiedz krótko."
        search_result = websearch_agent.search(query)

        return {"answer": search_result.get("answer", "No answer available")}
    
    except Exception as e:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

import time
processing_lock = False

@app.post("/stream/")
async def stream_audio(request: Request) -> Dict[str, Any]:
    global processing_lock
    
    if processing_lock:
        print("[DEBUG] BUSY - Another request is being processed")
        raise HTTPException(status_code=429, detail="Server busy processing another request")
    
    processing_lock = True
    print(f"[DEBUG] Request started at {time.time()}")
    
    try:
        body = await request.body()
        print(f"[DEBUG] Received body size: {len(body)} bytes")
        print(f"[DEBUG] Content-Type: {request.headers.get('content-type', 'None')}")
        print(f"[DEBUG] Content-Length header: {request.headers.get('content-length', 'None')}")
        print(f"[DEBUG] All headers: {dict(request.headers)}")
        
        if not body:
            print("[DEBUG] Body is empty!")
            raise HTTPException(status_code=400, detail="No audio data received")
        
        # Debug: sprawdź pierwsze bajty
        if len(body) > 0:
            first_bytes = body[:20] if len(body) >= 20 else body
            print(f"[DEBUG] First {len(first_bytes)} bytes: {first_bytes}")
            print(f"[DEBUG] First bytes as hex: {first_bytes.hex()}")
        
        # Zapisz plik debug
        debug_file_path = f"/tmp/debug_audio_{len(body)}_bytes.wav"
        with open(debug_file_path, "wb") as debug_file:
            debug_file.write(body)
        print(f"[DEBUG] Saved received data to: {debug_file_path}")
        
        # Konwertuj sample rate jeśli potrzebne
        try:
            import subprocess
            converted_path = f"/tmp/converted_{len(body)}_bytes.wav"
            subprocess.run([
                "ffmpeg", "-i", debug_file_path, "-ar", "16000", 
                converted_path, "-y", "-loglevel", "quiet"
            ], check=True)
            print(f"[DEBUG] Converted to 16kHz: {converted_path}")
            
            # Sprawdź poziom audio
            volume_check = subprocess.run([
                "ffmpeg", "-i", converted_path, "-af", "volumedetect", 
                "-f", "null", "-", "-loglevel", "info"
            ], capture_output=True, text=True)
            print(f"[DEBUG] Audio analysis: {volume_check.stderr}")
            
            print(f"[DEBUG] Testing Whisper transcription...")
            result = model.transcribe(converted_path)
            print(f"[DEBUG] Transcription result: '{result['text']}'")
            print(f"[DEBUG] Full result keys: {list(result.keys())}")
            
            # Nie usuwaj plików dla debugowania
            # os.unlink(converted_path)
            
            if not result['text'].strip():
                return {"debug": f"Received {len(body)} bytes, transcription EMPTY - check audio level"}
            else:
                return {"debug": f"Received {len(body)} bytes, transcribed: '{result['text']}'"}
        except Exception as whisper_error:
            print(f"[DEBUG] Whisper/conversion error: {str(whisper_error)}")
            return {"debug": f"Received {len(body)} bytes, processing failed: {str(whisper_error)}"}
        
    except Exception as e:
        print(f"[DEBUG] Exception occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stream transcription failed: {str(e)}")
    finally:
        processing_lock = False
        print(f"[DEBUG] Request finished at {time.time()}")
        
        # Zakomentowany oryginalny kod:
        # with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        #     temp_file.write(body)
        #     temp_file_path = temp_file.name
        # 
        # result = model.transcribe(temp_file_path)
        # 
        # os.unlink(temp_file_path)
        # 
        # response = {
        #     "text": result["text"],
        #     "language": result["language"],
        #     "segments": result["segments"]
        # }
        # 
        # query = f"Przeszukaj internet i odpowiedz na pytanie: {result['text']}. Odpowiedz krótko."
        # search_result = websearch_agent.search(query)
        #
        # return {"answer": search_result.get("answer", "No answer available")}

@app.get("/")
async def root():
    return {"message": "Frank Brain API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)