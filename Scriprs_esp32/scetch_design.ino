#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <math.h>

// Proven wiring from the working display test.
#define TFT_SCK  14
#define TFT_MOSI 13  // Display SDA
#define TFT_DC    2  // Display AO
#define TFT_RST  27
#define TFT_CS   15

Adafruit_ST7735 tft(TFT_CS, TFT_DC, TFT_RST);

// Rotation 1 gives a 160 x 128 display. Only this small eye area is updated.
constexpr int16_t EYE_X = 30;
constexpr int16_t EYE_Y = 36;
constexpr int16_t EYE_W = 100;
constexpr int16_t EYE_H = 56;
constexpr int16_t CX = EYE_W / 2;
constexpr int16_t CY = EYE_H / 2;
constexpr int16_t IRIS_R = 16;

constexpr uint16_t BLACK = ST77XX_BLACK;
constexpr uint16_t CYAN = 0x07FF;
constexpr uint16_t WHITE = 0xDFFF;

GFXcanvas16 eye(EYE_W, EYE_H);
uint32_t lastFrame = 0;

void drawEye(int16_t gazeX, int16_t gazeY) {
  eye.fillScreen(BLACK); // Clear the RAM buffer, not the visible display.

  int16_t ix = CX + gazeX;
  int16_t iy = CY + gazeY;

  // One luminous pupil, without an eye outline or other graphics.
  eye.fillCircle(ix, iy, IRIS_R, CYAN);
  eye.fillCircle(ix, iy, 8, BLACK);
  eye.fillCircle(ix - 6, iy - 6, 3, WHITE);

  tft.drawRGBBitmap(EYE_X, EYE_Y, eye.getBuffer(), EYE_W, EYE_H);
}

void setup() {
  Serial.begin(115200);
  SPI.begin(TFT_SCK, -1, TFT_MOSI, TFT_CS);
  tft.initR(INITR_BLACKTAB);
  tft.setRotation(1);
  tft.fillScreen(BLACK);
  drawEye(0, 0);
  Serial.println("Pupil ready");
}

void loop() {
  uint32_t now = millis();
  if (now - lastFrame < 50) return; // Up to 20 complete frames per second.
  lastFrame = now;

  // Slowly look left/right, then slightly up/down.
  float t = now * 0.001f;
  int16_t gazeX = (int16_t)(sinf(t * 0.8f) * 13.0f);
  int16_t gazeY = (int16_t)(sinf(t * 0.43f + 1.0f) * 4.0f);
  drawEye(gazeX, gazeY);
}
