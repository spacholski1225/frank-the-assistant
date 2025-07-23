#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <SPI.h>
#include <WiFi.h>
#include <driver/i2s.h>

#define TFT_CS     5
#define TFT_RST    4
#define TFT_DC     2

// INMP441 microphone pins
#define I2S_WS   25
#define I2S_SD   32
#define I2S_SCK  26
#define BTN_PIN  22

Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);

// Konfiguracja WiFi
const char* ssid = "###";        // Zmień na swoją sieć WiFi
const char* password = "###";          // Zmień na swoje hasło

// Logowanie
#define LOG_LEVEL_DEBUG 0
#define LOG_LEVEL_INFO  1
#define LOG_LEVEL_WARN  2
#define LOG_LEVEL_ERROR 3

#define CURRENT_LOG_LEVEL LOG_LEVEL_DEBUG

#define LOG_DEBUG(msg) if(CURRENT_LOG_LEVEL <= LOG_LEVEL_DEBUG) { Serial.print("[DEBUG] "); Serial.println(msg); }
#define LOG_INFO(msg)  if(CURRENT_LOG_LEVEL <= LOG_LEVEL_INFO)  { Serial.print("[INFO]  "); Serial.println(msg); }
#define LOG_WARN(msg)  if(CURRENT_LOG_LEVEL <= LOG_LEVEL_WARN)  { Serial.print("[WARN]  "); Serial.println(msg); }
#define LOG_ERROR(msg) if(CURRENT_LOG_LEVEL <= LOG_LEVEL_ERROR) { Serial.print("[ERROR] "); Serial.println(msg); }

void setupI2SMic() {
  const i2s_config_t i2s_config = {
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = i2s_comm_format_t(I2S_COMM_FORMAT_I2S),
    .intr_alloc_flags = 0,
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false
  };

  const i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
  LOG_INFO("I2S microphone initialized");
}

void setup() {
  Serial.begin(115200);
  delay(2000); // Daj czas na uruchomienie Serial Monitor
  
  Serial.println("\n=== ESP32 WiFi Display ===");
  Serial.println("[INIT] Starting system initialization...");
  
  // Inicjalizacja ekranu ST7735
  Serial.println("[INIT] Initializing ST7735 display...");
  tft.initR(INITR_BLACKTAB);
  Serial.println("[INIT] ST7735 display initialized successfully");
  
  // Inicjalizacja przycisku mikrofonu
  pinMode(BTN_PIN, INPUT);
  LOG_INFO("Button initialized on GPIO22");
  
  // Inicjalizacja mikrofonu I2S
  setupI2SMic();

  tft.fillScreen(ST77XX_BLACK);
  tft.setCursor(0, 0);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.println("Starting...");
  
  // Sprawdź dostępną pamięć na starcie
  Serial.print("[MEMORY] Initial free heap: ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");
  
  // Łączenie z WiFi z retry (5 prób)
  Serial.print("[WIFI] Connecting to WiFi network: ");
  Serial.println(ssid);
  
  tft.fillScreen(ST77XX_BLACK);
  tft.setCursor(0, 0);
  tft.setTextColor(ST77XX_YELLOW);
  tft.setTextSize(1);
  tft.println("Connecting to WiFi...");
  
  bool wifiConnected = false;
  int maxRetries = 5;
  
  for (int retry = 1; retry <= maxRetries && !wifiConnected; retry++) {
    Serial.print("[WIFI] Connection attempt ");
    Serial.print(retry);
    Serial.print("/");
    Serial.println(maxRetries);
    
    tft.print("Attempt ");
    tft.print(retry);
    tft.print("/");
    tft.println(maxRetries);
    
    WiFi.begin(ssid, password);
    
    int wifiAttempts = 0;
    while (WiFi.status() != WL_CONNECTED && wifiAttempts < 30) {
      delay(500);
      yield(); // Feed the watchdog
      Serial.print(".");
      wifiAttempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
      wifiConnected = true;
      Serial.println();
      Serial.println("[WIFI] WiFi connected successfully!");
      Serial.print("[WIFI] IP Address: ");
      Serial.println(WiFi.localIP());
      Serial.print("[WIFI] Signal strength: ");
      Serial.print(WiFi.RSSI());
      Serial.println(" dBm");
      
      tft.fillScreen(ST77XX_BLACK);
      tft.setCursor(0, 0);
      tft.setTextColor(ST77XX_GREEN);
      tft.setTextSize(1);
      tft.println("WiFi Connected!");
      tft.print("IP: ");
      tft.println(WiFi.localIP());
      tft.print("Signal: ");
      tft.print(WiFi.RSSI());
      tft.println(" dBm");
      
    } else {
      Serial.println();
      Serial.print("[WARN] Connection attempt ");
      Serial.print(retry);
      Serial.println(" failed");
      
      if (retry < maxRetries) {
        Serial.println("[WIFI] Disconnecting and waiting 2 seconds before retry...");
        WiFi.disconnect();
        delay(2000);
        yield(); // Feed the watchdog
      }
    }
  }
  
  if (!wifiConnected) {
    Serial.println("[ERROR] Failed to connect to WiFi after 5 attempts!");
    tft.fillScreen(ST77XX_BLACK);
    tft.setCursor(0, 0);
    tft.setTextColor(ST77XX_RED);
    tft.setTextSize(1);
    tft.println("WiFi Failed!");
    tft.println("Check settings");
    for (;;); // Zatrzymaj program
  }
  
  Serial.println("[INIT] System initialization completed");
  Serial.println("=================================\n");
}

void loop() {
  static bool recording = false;
  
  bool buttonPressed = (digitalRead(BTN_PIN) == LOW);
  
  // Prosty stan - nagrywaj tylko gdy przycisk jest wciśnięty
  if (buttonPressed && !recording) {
    recording = true;
    LOG_INFO("🎙️ Recording started");
  } else if (!buttonPressed && recording) {
    recording = false;
    LOG_INFO("🎙️ Recording stopped");
  }
  
  // Wyświetl status WiFi i mikrofonu
  tft.fillScreen(ST77XX_BLACK);
  tft.setCursor(0, 0);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(1);
  tft.println("ESP32 Status:");
  
  if (WiFi.status() == WL_CONNECTED) {
    tft.setTextColor(ST77XX_GREEN);
    tft.println("WiFi: Connected");
    tft.print("IP: ");
    tft.println(WiFi.localIP());
    tft.print("RSSI: ");
    tft.print(WiFi.RSSI());
    tft.println(" dBm");
  } else {
    tft.setTextColor(ST77XX_RED);
    tft.println("WiFi: Disconnected");
  }
  
  // Status mikrofonu
  if (recording) {
    tft.setTextColor(ST77XX_RED);
    tft.println("🎙️ RECORDING...");
    
    // Odczytaj próbki audio
    int16_t samples[1024];
    size_t bytesRead;
    i2s_read(I2S_NUM_0, (char*)samples, sizeof(samples), &bytesRead, portMAX_DELAY);
    
    // Wyświetl kilka próbek na konsoli
    Serial.print("[MIC] Samples: ");
    for (int i = 0; i < 5; i++) {
      Serial.print(samples[i]);
      Serial.print(" ");
    }
    Serial.println();
    
    // Wyświetl poziom sygnału
    int maxLevel = 0;
    for (int i = 0; i < 1024; i++) {
      int level = abs(samples[i]);
      if (level > maxLevel) maxLevel = level;
    }
    tft.print("Level: ");
    tft.println(maxLevel);
    
  } else {
    tft.setTextColor(ST77XX_WHITE);
    tft.println("Mic: Ready");
    tft.println("Hold button to record");
  }
  
  tft.setTextColor(ST77XX_CYAN);
  tft.print("Free heap: ");
  tft.print(ESP.getFreeHeap());
  tft.println(" bytes");
  
  tft.setTextColor(ST77XX_YELLOW);
  tft.print("Uptime: ");
  tft.print(millis() / 1000);
  tft.println(" sec");
  
  Serial.print("[STATUS] Free heap: ");
  Serial.print(ESP.getFreeHeap());
  Serial.print(" bytes, WiFi: ");
  Serial.print(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
  Serial.print(", Button PIN22: ");
  Serial.print(digitalRead(BTN_PIN));
  Serial.print(" (");
  Serial.print(digitalRead(BTN_PIN) == LOW ? "PRESSED" : "RELEASED");
  Serial.print(")");
  Serial.print(", Recording: ");
  Serial.print(recording ? "YES" : "NO");
  Serial.print(", Uptime: ");
  Serial.print(millis() / 1000);
  Serial.println(" sec");
  
  delay(recording ? 50 : 1000); // Szybsze odświeżanie podczas nagrywania
}