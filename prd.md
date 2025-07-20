# Product Requirements Document (PRD)

**Project:** Frank – Goose AI Assistant  
**Version:** MVP 1.1  
**Author:** [Your Name]  
**Date:** 2025-07-20

## 1. Product Goal

Create a physical, personal AI assistant in the form of a walkie-talkie-like device, with voice recognition functionality and a display showing the assistant's state – a friendly goose character. The assistant responds to the user's voice, transmits data to a server, processes queries using AI agents, and plays back voice and text responses on screen.

## 2. Technologies Used

### Microcontroller:
- ESP32 or Raspberry Pi Zero 2 W / Nano (to be decided)
- OLED/LCD screen – displaying character emotions (pixel art)
- Microphone – e.g., I2S MEMS (audio recording)
- Physical button – activates recording

### Backend / Server:
- Python
- LangChain + LangGraph
- ASR (Whisper / other) – Polish speech recognition
- TTS (e.g., Coqui TTS, Piper, Google TTS) – Polish speech synthesis
- Local database on server (e.g., SQLite / JSON)
- HTTP API – communication with device

## 3. MVP Features

### 3.1. Device (ESP32 / RPi)
- **Button hold:** records audio
- **Button release:** sends recording via HTTP POST to server
- **Display current goose state** (static graphics):
  - Idle
  - Thinking
  - Talking
  - Happy
  - Sad / Failed

### 3.2. Server
- Receives recording
- ASR converts recording to text (language: Polish)
- LangChain selects appropriate agent (e.g., browser / dietitian)
- Agent executes task:
  - **Browser agent:** searches for answers on the internet
  - **Dietitian agent:** analyzes food and saves data to database
- Response feedback:
  - Generates text response
  - Generates audio via TTS
  - Returns data via HTTP to microcontroller

### 3.3. Response Playback
- Device plays sound (if it has DAC/codec)
- Alternatively displays text on screen (like GameBoy game dialogs)

## 4. AI Agents

### 4.1. Browser Agent
- Serves to answer general questions (e.g., "How many calories does a banana have?")
- Uses Browser Tool or LLM tools to extract knowledge from the internet

### 4.2. Dietitian Agent
- Recognizes what the user ate (e.g., "I ate 100g of bread")
- Calculates calories
- Saves data (product, quantity, calories, date) to local database

## 5. Functional Requirements

| ID | Function Description | Priority |
|---|---|---|
| F1 | Button activates audio recording | High |
| F2 | Audio transmitted via HTTP POST to server | High |
| F3 | ASR converts audio to text (Polish) | High |
| F4 | AI agent analyzes query | High |
| F5 | Response generated (text + TTS) | High |
| F6 | Response transmitted back to microcontroller | High |
| F7 | Audio playback (if possible) or text display | Medium |
| F8 | Display goose state/emotions as pixel-art | Medium |
| F9 | Save meal data to database | High |

## 6. Non-Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| N1 | Server runs locally (user owns their own) | High |
| N2 | Communication via HTTP | High |
| N3 | ASR and TTS support Polish language | High |
| N4 | Device operates with minimal power consumption | Medium |
| N5 | All audio processes handled by server | High |

## 7. MVP Scope

### ✅ Included:
- Audio communication ESP32/RPi → HTTP → Server
- Support for two agents (browser, dietitian)
- TTS and text responses
- Goose emotions as simple graphics (sprites)
- Local backend with database

### ❌ Not Included:
- Goose personalization
- Synchronization with external apps (e.g., Fitatu)
- Web panel
- Multi-user support

## 8. Architecture Schema (Descriptive)

```
[Microcontroller (ESP32 / RPi)]
   |                     ↑
   |--- Audio recording → | 
   |                     |
   |  ← TTS audio / text / goose state
   |
[Python Server]
   - ASR (Whisper)
   - LangChain + LangGraph
   - Agents (Browser, Dietitian)
   - TTS (Piper / Coqui / Google)
   - Local database
```

## 9. Next Steps

1. **Microcontroller selection** – ESP32 (cheaper, harder) vs RPi Zero 2 W (easier, more expensive)
2. **Collect goose graphics** (pixel-art style sprites)
3. **Backend prototype** – Flask / FastAPI server in Python + LangChain
4. **Audio recording and playback module**
5. **HTTP API integration with microcontroller**