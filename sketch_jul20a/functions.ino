void initializeDisplay() {
  Serial.println("Trying manual ST7735S init...");
  
  // Hardware reset
  pinMode(TFT_RST, OUTPUT);
  digitalWrite(TFT_RST, LOW);
  delay(100);
  digitalWrite(TFT_RST, HIGH);
  delay(100);
  
  // Użyj podstawowej inicjalizacji
  tft.initR(INITR_BLACKTAB);  // Ten wariant dla 128x160
  
  tft.setRotation(0);  // Spróbuj 0, 1, 2, 3
  
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(10, 10);
  tft.println("HELLO");
  
  Serial.println("Manual init done");
}


void updateDisplay(String message) {
  // Clear only the top 64px area for text messages
  tft.fillRect(0, 0, 128, 64, ST77XX_BLACK);
  
  // Set text properties
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(1);
  tft.setCursor(2, 2);
  
  // Word wrap the message if it's too long
  int maxCharsPerLine = (tft.width() - 4) / 6; // Approximate chars per line
  
  if (message.length() <= maxCharsPerLine) {
    tft.println(message);
  } else {
    // Split message into multiple lines
    int startPos = 0;
    int line = 0;
    
    while (startPos < message.length() && line < 6) { // Max 6 lines for top 64px
      int endPos = startPos + maxCharsPerLine;
      
      if (endPos < message.length()) {
        // Find last space to avoid breaking words
        int lastSpace = message.lastIndexOf(' ', endPos);
        if (lastSpace > startPos) {
          endPos = lastSpace;
        }
      } else {
        endPos = message.length();
      }
      
      String lineText = message.substring(startPos, endPos);
      tft.setCursor(2, 2 + (line * 10));
      tft.println(lineText);
      
      startPos = endPos + 1; // Skip the space
      line++;
    }
  }
  
  Serial.println("Display updated with: " + message);
}

void updateDisplaySafe(String message) {
  // Safe wrapper for updateDisplay with error handling
  Serial.println("Updating display: " + message);
  
  try {
    updateDisplay(message);
  } catch (...) {
    Serial.println("Display update failed - continuing without display");
  }
}

String parseAnswerFromResponse(String response) {
  Serial.println("=== PARSING DEBUG ===");
  
  // Try to parse "answer" field first
  Serial.println("Looking for 'answer' field...");
  int answerStart = response.indexOf("\"answer\":\"");
  Serial.println("Answer start position: " + String(answerStart));
  
  if (answerStart != -1) {
    answerStart += 10; // Length of "\"answer\":\""
    int answerEnd = response.indexOf("\"", answerStart);
    Serial.println("Answer end position: " + String(answerEnd));
    
    if (answerEnd > answerStart) {
      String answer = response.substring(answerStart, answerEnd);
      Serial.println("Found answer: '" + answer + "'");
      return answer;
    }
  }
  
  // Fallback to "text" field
  Serial.println("Looking for 'text' field...");
  int textStart = response.indexOf("\"text\":\"");
  Serial.println("Text start position: " + String(textStart));
  
  if (textStart != -1) {
    textStart += 8; // Length of "\"text\":\""
    int textEnd = response.indexOf("\"", textStart);
    Serial.println("Text end position: " + String(textEnd));
    
    if (textEnd > textStart) {
      String text = response.substring(textStart, textEnd);
      Serial.println("Found text: '" + text + "'");
      return text;
    }
  }
  
  Serial.println("No answer or text field found!");
  return ""; // No answer found
}

// Emotion display functions - Method 1: Using drawRGBBitmap for 16-bit color
void displayEmotion(const uint16_t* bitmap) {
  // Clear bottom area first (y=64, height=64)
  tft.fillRect(0, 64, 128, 64, ST77XX_BLACK);
  
  // Display 64x64 bitmap in bottom area, centered horizontally
  // Using drawRGBBitmap for 16-bit RGB565 color bitmaps - Method 1 (confirmed working)
  tft.drawRGBBitmap(32, 64, bitmap, 64, 64);
}

void animateEmotion(const uint16_t* frame1, const uint16_t* frame2, int duration) {
  unsigned long startTime = millis();
  bool showFrame1 = true;
  
  while (millis() - startTime < duration) {
    if (showFrame1) {
      displayEmotion(frame1);
    } else {
      displayEmotion(frame2);
    }
    showFrame1 = !showFrame1;
    delay(500); // Switch frame every 500ms
  }
}

// Global variable to track last displayed frame to prevent unnecessary redraws
static const uint16_t* lastDisplayedFrame = nullptr;

void updateEmotion() {
  if (!emotionAnimating) return;
  
  unsigned long currentTime = millis();
  unsigned long elapsed = currentTime - emotionStartTime;
  const uint16_t* frameToShow = nullptr;
  
  switch (currentEmotion) {
    case EMOTION_ANGRY:
      // Animate between angry1 and angry2 every 1000ms until switch is toggled
      if ((elapsed / 1000) % 2 == 0) {
        frameToShow = bitmap_angry1;
      } else {
        frameToShow = bitmap_angry2;
      }
      break;
      
    case EMOTION_THINKING:
      // Continuous thinking animation while waiting for API response
      if ((elapsed / 1000) % 2 == 0) {
        frameToShow = bitmap_thinking1;
      } else {
        frameToShow = bitmap_thinking2;
      }
      break;
      
    case EMOTION_TALKING:
      // Continuous animation while recording
      if ((elapsed / 1000) % 2 == 0) {
        frameToShow = bitmap_talking;
      } else {
        frameToShow = bitmap_happy1; // Alternate with happy for talking effect
      }
      break;
      
    case EMOTION_HAPPY:
      // Animate between happy1 and happy2 for 3 seconds then return to angry
      if (elapsed >= 3000) {
        Serial.println("Happy emotion finished - returning to angry state");
        setEmotion(EMOTION_ANGRY);
        return;
      } else {
        if ((elapsed / 1000) % 2 == 0) {
          frameToShow = bitmap_happy1;
        } else {
          frameToShow = bitmap_happy2;
        }
      }
      break;
      
    case EMOTION_FAILED:
      // Show failed emotion for 3 seconds then return to angry
      if (elapsed >= 3000) {
        Serial.println("Failed emotion finished - returning to angry state");
        setEmotion(EMOTION_ANGRY);
        return;
      } else {
        frameToShow = bitmap_failed;
      }
      break;
  }
  
  // Only redraw if frame changed
  if (frameToShow != lastDisplayedFrame) {
    displayEmotion(frameToShow);
    lastDisplayedFrame = frameToShow;
  }
}

void setEmotion(EmotionState emotion) {
  currentEmotion = emotion;
  emotionAnimating = true;
  emotionStartTime = millis();
  lastDisplayedFrame = nullptr; // Reset to force redraw of new emotion
  Serial.println("Emotion set to: " + String(emotion));
  
  // Clear display when returning to angry state (ready for next action)
  if (emotion == EMOTION_ANGRY) {
    tft.fillRect(0, 0, 128, 64, ST77XX_BLACK); // Clear top area
    Serial.println("Display cleared - ready for next action");
  }
}

EmotionState analyzeAPIResponse(String response, int httpCode) {
  // First check HTTP status code
  if (httpCode != 200) {
    Serial.println("API Error - HTTP code: " + String(httpCode));
    return EMOTION_FAILED;
  }
  
  // Parse the response content
  String answer = parseAnswerFromResponse(response);
  
  if (answer.length() == 0) {
    Serial.println("No answer found in response");
    return EMOTION_FAILED;
  }
  
  // Convert to lowercase for analysis
  String lowerAnswer = answer;
  lowerAnswer.toLowerCase();
  
  // Check for negative/error keywords
  if (lowerAnswer.indexOf("error") != -1 || 
      lowerAnswer.indexOf("sorry") != -1 ||
      lowerAnswer.indexOf("can't") != -1 ||
      lowerAnswer.indexOf("cannot") != -1 ||
      lowerAnswer.indexOf("unable") != -1 ||
      lowerAnswer.indexOf("failed") != -1 ||
      lowerAnswer.indexOf("problem") != -1) {
    Serial.println("Negative response detected: " + answer);
    return EMOTION_FAILED;
  }
  
  // Check for positive keywords
  if (lowerAnswer.indexOf("yes") != -1 || 
      lowerAnswer.indexOf("ok") != -1 ||
      lowerAnswer.indexOf("good") != -1 ||
      lowerAnswer.indexOf("great") != -1 ||
      lowerAnswer.indexOf("success") != -1 ||
      lowerAnswer.indexOf("done") != -1 ||
      lowerAnswer.indexOf("completed") != -1) {
    Serial.println("Positive response detected: " + answer);
    return EMOTION_HAPPY;
  }
  
  // Default to happy for normal responses
  Serial.println("Normal response detected: " + answer);
  return EMOTION_HAPPY;
}