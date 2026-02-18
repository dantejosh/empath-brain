#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>
#include <math.h>

// ---------------- CONFIG ----------------
const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASS = "YOUR_PASS";
const char* EMOTION_URL = "https://your-service.onrender.com/emotion";

#define LED_PIN 5
#define LED_COUNT 60

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

const unsigned long POLL_INTERVAL = 300000; // 5 min

unsigned long lastPoll = 0;
unsigned long startTime = 0;

// ---------------- EMOTION STATE ----------------
float currentHue = 40;
float targetHue = 40;

float baseBrightness = 0.3;
float targetBrightness = 0.3;

float breathPeriod = 6.0;
float targetBreath = 6.0;

int currentIndex = 43;

// micro-drift phase timers
float hueDriftPhase = 0;
float brightDriftPhase = 0;
float breathDriftPhase = 0;


// ------------------------------------------------
// WiFi
// ------------------------------------------------
void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}


// ------------------------------------------------
// Fetch emotion index
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
  return currentIndex;
}


// ------------------------------------------------
// Map index to emotional targets
// ------------------------------------------------
void mapEmotion(int index) {

  if (index < 30) {
    targetHue = 300;
    targetBrightness = 0.15;
    targetBreath = 2.0;
  }
  else if (index < 45) {
    targetHue = 30;
    targetBrightness = 0.25;
    targetBreath = 4.0;
  }
  else if (index < 60) {
    targetHue = 45;
    targetBrightness = 0.35;
    targetBreath = 6.0;
  }
  else if (index < 80) {
    targetHue = 190;
    targetBrightness = 0.5;
    targetBreath = 9.0;
  }
  else {
    targetHue = 140;
    targetBrightness = 0.7;
    targetBreath = 12.0;
  }
}


// ------------------------------------------------
// Helpers
// ------------------------------------------------
float lerp(float a, float b, float t) {
  return a + (b - a) * t;
}


// HSV to RGB
uint32_t hsvToRgb(float h, float s, float v) {

  float c = v * s;
  float x = c * (1 - fabs(fmod(h / 60.0, 2) - 1));
  float m = v - c;

  float r, g, b;

  if (h < 60)       { r = c; g = x; b = 0; }
  else if (h < 120) { r = x; g = c; b = 0; }
  else if (h < 180) { r = 0; g = c; b = x; }
  else if (h < 240) { r = 0; g = x; b = c; }
  else if (h < 300) { r = x; g = 0; b = c; }
  else              { r = c; g = 0; b = x; }

  return strip.Color((r + m) * 255, (g + m) * 255, (b + m) * 255);
}


// ------------------------------------------------
// Breathing curve with elastic drift
// ------------------------------------------------
float breathingBrightness() {
  float t = (millis() - startTime) / 1000.0;

  float elasticBreath = breathPeriod + 0.4 * sin(breathDriftPhase);

  float phase = sin((2 * PI * t) / elasticBreath) * 0.5 + 0.5;

  return baseBrightness * (0.65 + 0.35 * phase);
}


// ------------------------------------------------
// Continuous render with micro-drift
// ------------------------------------------------
void renderFrame() {

  // advance drift phases slowly
  hueDriftPhase += 0.002;
  brightDriftPhase += 0.0015;
  breathDriftPhase += 0.001;

  // smooth toward emotional targets
  currentHue = lerp(currentHue, targetHue, 0.01);
  baseBrightness = lerp(baseBrightness, targetBrightness, 0.01);
  breathPeriod = lerp(breathPeriod, targetBreath, 0.01);

  // bounded micro-drift
  float driftedHue = currentHue + 3.0 * sin(hueDriftPhase);
  float driftedBright = breathingBrightness() + 0.02 * sin(brightDriftPhase);

  driftedBright = constrain(driftedBright, 0.0, 1.0);

  uint32_t color = hsvToRgb(driftedHue, 1.0, driftedBright);

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
// Loop
// ------------------------------------------------
void loop() {

  if (millis() - lastPoll > POLL_INTERVAL) {
    currentIndex = fetchEmotion();
    mapEmotion(currentIndex);
    lastPoll = millis();
  }

  renderFrame();
  delay(16); // ~60 FPS
}
