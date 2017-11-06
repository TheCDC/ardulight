// NeoPixel Ring simple sketch (c) 2013 Shae Erisson
// released under the GPLv3 license to match the rest of the AdaFruit NeoPixel library

#include <Adafruit_NeoPixel.h>
#include <avr/power.h>

// Which pin on the Arduino is connected to the NeoPixels?
// On a Trinket or Gemma we suggest changing this to 1
#define PIN            6

// How many NeoPixels are attached to the Arduino?
#define NUMPIXELS      30


void setColor( Adafruit_NeoPixel &strip, uint32_t color, int a = 0, int b = -1);

// When we setup the NeoPixel library, we tell it how many pixels, and which pin to use to send signals.
// Note that for older NeoPixel strips you might need to change the third parameter--see the strandtest
// example for more information on possible values.
Adafruit_NeoPixel pixels = Adafruit_NeoPixel(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

int delayval = 500; // delay for half a second

unsigned int modeState = 0;

void setup() {
  // This is for Trinket 5V 16MHz, you can remove these three lines if you are not using a Trinket
#if defined (__AVR_ATtiny85__)
  if (F_CPU == 16000000) clock_prescale_set(clock_div_1);
#endif
  // End of trinket special code

  pixels.begin(); // This initializes the NeoPixel library.
  Serial.begin(115200);
  //  set timeout in millis
  Serial.setTimeout(100) ;
  int d = 200;
  setColor(pixels, pixels.Color(255, 0, 0));
  pixels.show();
  delay(d);
  blank(pixels);
  setColor(pixels, pixels.Color(0, 255, 0));
  pixels.show();
  delay(d);

  setColor(pixels, pixels.Color(0, 0, 255));
  pixels.show();
  delay(d);
  blank(pixels);
  pixels.show();
}

void loop() {
  long n;
  uint32_t color;
  uint32_t colorLeft;
  uint32_t colorRight;
  boolean flag = false;
  //   For a set of NeoPixels the first NeoPixel is 0, second is 1, all the way up to the count of pixels minus one.
  switch (modeState) {
    case 0:
      n = Serial.parseInt();
      //      Serial.print("N:");
      //      Serial.println(n);
      //change input mode based on n

      //n < 0 is a special command, triggering different input modes
      modeState = controlCodeToModeState(n);
      //      Serial.print("NEXTMODE=");
      //      Serial.println(modeState);
      break;

    case 2:
//      Serial.println("Exec mode 2");
      //pixel mode.
      //At the moment, the strip of LEDs is folded on itself on my monitor stand.
      //This means that there is  really only one physical row.
      flag = false;
      for (int i = 0; i < pixels.numPixels(); i++) {
        color =  Serial.parseInt();
//        Serial.print("Setting pixel ");
//        Serial.print(i);
//        Serial.print(" to ");
//        Serial.print(color);
//        Serial.print("\n");
        if (color < 0) {
          Serial.println("ERROR");
          modeState = -color;
          flag = true;
          break;
        }
        if (flag) {
          break;
        }
        pixels.setPixelColor(i, color);
      }
      pixels.show();
      modeState = 0;
      break;
    default:
      modeState = 0;
      break;
  }
  //  Serial.print("MODE=");
  //  Serial.println(modeState);
}

void setColor( Adafruit_NeoPixel &strip, uint32_t color, int a = 0, int b = -1) {
  if (b == -1) {
    b = strip.numPixels();
  }
  for (uint8_t i = a; i < b; i ++) {
    pixels.setPixelColor(i, color);

  }

}
void blank(Adafruit_NeoPixel &strip) {
  //  set all pixels to black
  for (int i = 0; i < strip.numPixels(); i ++) {
    strip.setPixelColor(i, 0);
  }
}
void serialFlush() {
  //get rid of all remaining serial input
  while (Serial.available() > 0) {
    char t = Serial.read();
  }
}

int controlCodeToModeState(int code) {
  if (code == -1) {
    return 1;
  }
  else if (code == -2) {
    return 2;
  }
  else {
    return 0;
  }
}


