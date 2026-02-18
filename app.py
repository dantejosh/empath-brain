#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>
#include <time.h>
#include <math.h>

// WIFI
const char* WIFI_SSID = "67";
const char* WIFI_PASS = "Quandt85!!!~";
const char* EMOTION_URL = "https://empath-brain.onrender.com/emotion";

// LED
#define LED_PIN 13
#define LED_COUNT 44
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

// TIMING
const unsigned long POLL_INTERVAL = 300000;
unsigned long lastPoll = 0;
unsigned long startTime = 0;

// EMOTION
int liveIndex = 43;
float memoryIndex = 43.0;

float currentHue = 32, targetHue = 32;
float baseBrightness = 0.26, targetBrightness = 0.26;
float breathPeriod = 7.0, targetBreath = 7.0;

float hueDrift = 0;

// WIFI
void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(300);
}

// TIME
void initTime() {
  configTzTime("EST5EDT,M3.2.0,M11.1.0", "pool.ntp.org");
  struct tm t;
  while (!getLocalTime(&t)) delay(300);
}

int getHour() {
  struct tm t;
  if (!getLocalTime(&t)) return 12;
  return t.tm_hour;
}

// FETCH
int fetchEmotion() {
  if (WiFi.status() != WL_CONNECTED) return liveIndex;

  HTTPClient http;
  http.begin(EMOTION_URL);
  http.setTimeout(3000);

  int code = http.GET();

  if (code == 200) {
    DynamicJsonDocument doc(256);
    deserializeJson(doc, http.getString());
    http.end();
    return doc["index"];
  }

  http.end();
  return liveIndex;
}

// MEMORY
void updateMemory() {
  float rate = 0.002;
  memoryIndex += (liveIndex - memoryIndex) * rate;
}

// MAP EMOTION  (neutral band corrected)
void mapEmotion(float idx) {

  if (idx < 30) { targetHue = 320; targetBrightness = 0.16; targetBreath = 5.0; }
  else if (idx < 45) { targetHue = 25; targetBrightness = 0.22; targetBreath = 6.0; }

  // ---- FIXED NEUTRAL BAND ----
  else if (idx < 60) { targetHue = 32; targetBrightness = 0.26; targetBreath = 7.0; }

  else if (idx < 80) { targetHue = 185; targetBrightness = 0.36; targetBreath = 9.0; }
  else { targetHue = 155; targetBrightness = 0.46; targetBreath = 11.0; }
}

// DAY MOD
float dayBrightnessMultiplier() {
  int h = getHour();
  if (h < 6) return 0.5;
  if (h < 10) return 0.75;
  if (h < 18) return 1.0;
  if (h < 22) return 0.8;
  return 0.6;
}

// SMOOTH
float smoothStep(float a, float b, float t) {
  return a + (b - a) * t;
}

// HSV → RGB  (raised saturation for visibility)
uint32_t hsvToRgb(float h, float v) {

  float s = 0.72;   // ← key perceptual fix

  float c = v * s;
  float x = c * (1 - fabs(fmod(h / 60.0, 2) - 1));
  float m = v - c;

  float r, g, b;

  if (h < 60) { r = c; g = x; b = 0; }
  else if (h < 120) { r = x; g = c; b = 0; }
  else if (h < 180) { r = 0; g = c; b = x; }
  else if (h < 240) { r = 0; g = x; b = c; }
  else if (h < 300) { r = x; g = 0; b = c; }
  else { r = c; g = 0; b = x; }

  return strip.Color((r + m) * 255, (g + m) * 255, (b + m) * 255);
}

// BREATH
float breathingBrightness() {
  float t = (millis() - startTime) / 1000.0;

  float breath = sin((2 * PI * t) / breathPeriod) * 0.5 + 0.5;
  float swell  = sin((2 * PI * t) / 40.0) * 0.5 + 0.5;

  float visible = 0.35 + 0.65 * breath;

  return baseBrightness * dayBrightnessMultiplier() * visible * (0.8 + 0.2 * swell);
}

// RENDER
void renderFrame() {

  hueDrift += 0.0008;

  currentHue = smoothStep(currentHue, targetHue, 0.01);
  baseBrightness = smoothStep(baseBrightness, targetBrightness, 0.01);
  breathPeriod = smoothStep(breathPeriod, targetBreath, 0.01);

  float hue = currentHue + 2.0 * sin(hueDrift);
  float bright = constrain(breathingBrightness(), 0.0, 1.0);

  uint32_t color = hsvToRgb(hue, bright);

  for (int i = 0; i < LED_COUNT; i++) strip.setPixelColor(i, color);
  strip.show();
}

// SETUP
void setup() {
  strip.begin();
  strip.show();
  connectWiFi();
  initTime();
  startTime = millis();
}

// LOOP
void loop() {

  if (millis() - lastPoll > POLL_INTERVAL) {
    liveIndex = fetchEmotion();
    lastPoll = millis();
  }

  updateMemory();
  mapEmotion(memoryIndex);

  renderFrame();
  delay(16);
}
