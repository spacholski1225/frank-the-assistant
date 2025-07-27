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
import wave
import struct
import datetime
processing_lock = False

# Chunked streaming storage
chunk_sessions = {}  # session_id -> {chunks: {chunk_id: data}, total_chunks: int, received_chunks: int}

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
        
        # Zapisz surowe audio jako plik debug
        debug_file_path = f"/tmp/debug_audio_{len(body)}_bytes.raw"
        with open(debug_file_path, "wb") as debug_file:
            debug_file.write(body)
        print(f"[DEBUG] Saved received raw data to: {debug_file_path}")
        
        # Konwertuj raw audio na WAV do łatwego odtwarzania
        wav_file_path = f"/tmp/audio_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        try:
            # Konwertuj raw 16-bit audio na WAV
            with wave.open(wav_file_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # mono
                wav_file.setsampwidth(2)  # 16-bit = 2 bytes
                wav_file.setframerate(16000)  # 16kHz
                wav_file.writeframes(body)
            print(f"[DEBUG] Saved as WAV file: {wav_file_path}")
        except Exception as wav_error:
            print(f"[DEBUG] WAV conversion failed: {str(wav_error)}")
        
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
                return {
                    "debug": f"Received {len(body)} bytes, transcription EMPTY - check audio level",
                    "wav_file": wav_file_path,
                    "raw_file": debug_file_path
                }
            else:
                return {
                    "debug": f"Received {len(body)} bytes, transcribed: '{result['text']}'",
                    "transcription": result['text'],
                    "wav_file": wav_file_path,
                    "raw_file": debug_file_path
                }
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

@app.post("/chunk")
async def receive_chunk(request: Request) -> Dict[str, Any]:
    session_id = request.headers.get("X-Session-ID")
    chunk_id = int(request.headers.get("X-Chunk-ID"))
    total_chunks = int(request.headers.get("X-Total-Chunks"))
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")
    
    body = await request.body()
    print(f"[CHUNK] Session {session_id}: Received chunk {chunk_id}/{total_chunks-1} ({len(body)} bytes)")
    
    # Initialize session if new
    if session_id not in chunk_sessions:
        chunk_sessions[session_id] = {
            "chunks": {},
            "total_chunks": total_chunks,
            "received_chunks": 0
        }
    
    # Store chunk
    chunk_sessions[session_id]["chunks"][chunk_id] = body
    chunk_sessions[session_id]["received_chunks"] += 1
    
    return {"status": "chunk_received", "chunk_id": chunk_id}

@app.post("/complete")
async def complete_session(request: Request) -> Dict[str, Any]:
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id or session_id not in chunk_sessions:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    session = chunk_sessions[session_id]
    print(f"[COMPLETE] Session {session_id}: {session['received_chunks']}/{session['total_chunks']} chunks received")
    
    # Check if all chunks received
    if session["received_chunks"] != session["total_chunks"]:
        return {"error": f"Missing chunks: {session['received_chunks']}/{session['total_chunks']}"}
    
    # Combine chunks in order
    audio_data = b""
    for chunk_id in range(session["total_chunks"]):
        if chunk_id in session["chunks"]:
            audio_data += session["chunks"][chunk_id]
        else:
            return {"error": f"Missing chunk {chunk_id}"}
    
    print(f"[COMPLETE] Combined audio: {len(audio_data)} bytes")
    
    # Save combined audio files for testing
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    debug_file_path = f"/tmp/mic_test_{timestamp}_{session_id}.raw"  
    wav_file_path = f"/tmp/mic_test_{timestamp}_{session_id}.wav"
    
    # Save raw audio
    with open(debug_file_path, "wb") as debug_file:
        debug_file.write(audio_data)
    print(f"[SAVED] Raw audio: {debug_file_path}")
    
    # Convert to WAV for easy playback testing
    try:
        with wave.open(wav_file_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 16-bit = 2 bytes
            wav_file.setframerate(16000)  # 16kHz
            wav_file.writeframes(audio_data)
        print(f"[SAVED] WAV audio: {wav_file_path}")
        
        # Clean up session
        del chunk_sessions[session_id]
        
        return {
            "status": "success",
            "message": f"Audio saved for testing - {len(audio_data)} bytes",
            "files": {
                "raw": debug_file_path,
                "wav": wav_file_path
            },
            "info": {
                "chunks_received": session["total_chunks"],
                "total_bytes": len(audio_data),
                "duration_estimate": f"{len(audio_data) / (16000 * 2):.1f} seconds"
            }
        }
            
    except Exception as e:
        print(f"[ERROR] File save failed: {str(e)}")
        # Clean up session
        if session_id in chunk_sessions:
            del chunk_sessions[session_id]
        return {"error": f"File save failed: {str(e)}"}

@app.get("/sessions")
async def get_sessions():
    return {"active_sessions": list(chunk_sessions.keys())}

@app.get("/")
async def root():
    return {"message": "Frank Brain API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)