// NeoPixel Ring simple sketch (c) 2013 Shae Erisson
// released under the GPLv3 license to match the rest of the AdaFruit NeoPixel library

#include <Adafruit_NeoPixel.h>
#include <avr/power.h>

// Which pin on the Arduino is connected to the NeoPixels?
// On a Trinket or Gemma we suggest changing this to 1
#define PIN            6

// How many NeoPixels are attached to the Arduino?
#define NUMPIXELS      20

// When we setup the NeoPixel library, we tell it how many pixels, and which pin to use to send signals.
// Note that for older NeoPixel strips you might need to change the third parameter--see the strandtest
// example for more information on possible values.
Adafruit_NeoPixel pixels = Adafruit_NeoPixel(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

int delayval = 500; // delay for half a second

void setup() {
  // This is for Trinket 5V 16MHz, you can remove these three lines if you are not using a Trinket
#if defined (__AVR_ATtiny85__)
  if (F_CPU == 16000000) clock_prescale_set(clock_div_1);
#endif
  // End of trinket special code

  pixels.begin(); // This initializes the NeoPixel library.
  Serial.begin(115200);
  //  set timeout in millis
  Serial.setTimeout(200) ;
  int d = 500;
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

  //   For a set of NeoPixels the first NeoPixel is 0, second is 1, all the way up to the count of pixels minus one.

  uint32_t color = Serial.parseInt();
//  Serial.println(color);
  setColor(pixels, color);
  serialFlush();
  pixels.show();


  //    for(int i=0;i<NUMPIXELS;i++){
  //
  //      // pixels.Color takes RGB values, from 0,0,0 up to 255,255,255
  //      pixels.setPixelColor(i, pixels.Color(0,150,0)); // Moderately bright green color.
  //
  //      pixels.show(); // This sends the updated pixel color to the hardware.
  //
  //      delay(delayval); // Delay for a period of time (in milliseconds).
  //
  //    }
}

void setColor( Adafruit_NeoPixel &strip, uint32_t color) {
  for (uint8_t i = 0; i < pixels.numPixels(); i ++) {
    //    Serial.print("Setting pixel ");
    //    Serial.print(i);
    //    Serial.print(" to ");
    //    Serial.print(color);
    //    Serial.print("\n");
    pixels.setPixelColor(i, color);

  }

}
void blank(Adafruit_NeoPixel &strip) {
  for (int i = 0; i < strip.numPixels(); i ++) {
    strip.setPixelColor(i, 0);
  }
}

void serialFlush() {

  while (Serial.available() > 0) {
    char t = Serial.read();
  }
}


