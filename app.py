#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

// ---------------- CONFIG ----------------
const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASS = "YOUR_PASS";
const char* EMOTION_URL = "https://your-service.onrender.com/emotion";

#define LED_PIN 5
#define LED_COUNT 60

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

// polling interval (ms)
const unsigned long POLL_INTERVAL = 300000; // 5 minutes

// animation timing
unsigned long lastPoll = 0;
unsigned long startTime = 0;

// ---------------- EMOTION STATE ----------------
float currentHue = 40;
float targetHue = 40;

float baseBrightness = 0.3;
float targetBrightness = 0.3;

float breathPeriod = 6.0; // seconds

int currentIndex = 43;


// ------------------------------------------------
// Wi-Fi
// ------------------------------------------------
void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}


// ------------------------------------------------
// Fetch emotion index from server
// ------------------------------------------------
int fetchEmotion() {
  if (WiFi.status() != WL_CONNECTED) return currentIndex;

  HTTPClient http;
  http.begin(EMOTION_URL);

  int code = http.GET();

  if (code == 200) {
    DynamicJsonDocument doc(256);
    deserializeJson(doc, http.getString());
    http.end();
    return doc["index"];
  }

  http.end();
  return currentIndex; // fallback
}


// ------------------------------------------------
// Map index → emotional parameters
// ------------------------------------------------
void mapEmotion(int index) {

  if (index < 30) {                // Distress
    targetHue = 300;               // violet/red
    targetBrightness = 0.15;
    breathPeriod = 2.0;
  }
  else if (index < 45) {           // Tension
    targetHue = 30;                // amber
    targetBrightness = 0.25;
    breathPeriod = 4.0;
  }
  else if (index < 60) {           // Neutral calm
    targetHue = 45;                // warm gold
    targetBrightness = 0.35;
    breathPeriod = 6.0;
  }
  else if (index < 80) {           // Optimism
    targetHue = 190;               // sky blue
    targetBrightness = 0.5;
    breathPeriod = 9.0;
  }
  else {                           // Collective joy
    targetHue = 140;               // soft green
    targetBrightness = 0.7;
    breathPeriod = 12.0;
  }
}


// ------------------------------------------------
// Smooth interpolation helper
// ------------------------------------------------
float lerp(float a, float b, float t) {
  return a + (b - a) * t;
}


// ------------------------------------------------
// HSV → RGB (0-360, 0-1, 0-1)
// ------------------------------------------------
uint32_t hsvToRgb(float h, float s, float v) {

  float c = v * s;
  float x = c * (1 - abs(fmod(h / 60.0, 2) - 1));
  float m = v - c;

  float r, g, b;

  if (h < 60)       { r = c; g = x; b = 0; }
  else if (h < 120) { r = x; g = c; b = 0; }
  else if (h < 180) { r = 0; g = c; b = x; }
  else if (h < 240) { r = 0; g = x; b = c; }
  else if (h < 300) { r = x; g = 0; b = c; }
  else              { r = c; g = 0; b = x; }

  return strip.Color(
    (r + m) * 255,
    (g + m) * 255,
    (b + m) * 255
  );
}


// ------------------------------------------------
// Breathing brightness curve
// ------------------------------------------------
float breathingBrightness() {
  float t = (millis() - startTime) / 1000.0;
  float phase = sin((2 * PI * t) / breathPeriod) * 0.5 + 0.5;
  return baseBrightness * (0.6 + 0.4 * phase);
}


// ------------------------------------------------
// Update LEDs continuously
// ------------------------------------------------
void renderFrame() {

  // smooth transitions toward targets
  currentHue = lerp(currentHue, targetHue, 0.01);
  baseBrightness = lerp(baseBrightness, targetBrightness, 0.01);

  float brightness = breathingBrightness();

  uint32_t color = hsvToRgb(currentHue, 1.0, brightness);

  for (int i = 0; i < LED_COUNT; i++) {
    strip.setPixelColor(i, color);
  }

  strip.show();
}


// ------------------------------------------------
// Setup
// ------------------------------------------------
void setup() {
  strip.begin();
  strip.show();

  connectWiFi();

  startTime = millis();
}


// ------------------------------------------------
// Main loop
// ------------------------------------------------
void loop() {

  // periodic emotion fetch
  if (millis() - lastPoll > POLL_INTERVAL) {
    currentIndex = fetchEmotion();
    mapEmotion(currentIndex);
    lastPoll = millis();
  }

  // continuous animation
  renderFrame();

  delay(16); // ~60 FPS
}
