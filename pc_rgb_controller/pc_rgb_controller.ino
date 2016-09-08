// NeoPixel Ring simple sketch (c) 2013 Shae Erisson
// released under the GPLv3 license to match the rest of the AdaFruit NeoPixel library

#include <Adafruit_NeoPixel.h>
#include <avr/power.h>

// Which pin on the Arduino is connected to the NeoPixels?
// On a Trinket or Gemma we suggest changing this to 1
#define PIN            6

// How many NeoPixels are attached to the Arduino?
#define NUMPIXELS      20


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
  long n;
  uint32_t color;
  uint32_t colorLeft;
  uint32_t colorRight;
  //   For a set of NeoPixels the first NeoPixel is 0, second is 1, all the way up to the count of pixels minus one.
  switch (modeState) {
    case 0:
      n = Serial.parseInt();
      //      Serial.print("N:");
      Serial.println(n);
      //change input mode based on n
      if (n >= 0) {
        //n>=0 treats n as a packed RGB color
        modeState = 0;
        color = n;
        //and simply writes it to all LEDs
        setColor(pixels, color);
        pixels.show();
      }
      else {
        //n < 0 is a special command, triggering different input modes
        if (n == -1) {
          modeState = 1;

        }
        else if (n == -2) {
          modeState = 2;

        }
      }
      break;
    case 1:
      //2color mode, a left color and right color
      
      colorLeft = Serial.parseInt();
      colorRight = Serial.parseInt();


      //strip is separated into 2 strips of 10,
      //LEDs 5-9 and 10-14 are on the left
      //LEDs 0-4 and 15-19 are on the right

      setColor(pixels, colorLeft, 10, 10 + 5);
      setColor(pixels, colorLeft, 5, 5 + 5);

      setColor(pixels, colorRight, 0, 0 + 5);
      setColor(pixels, colorRight, 15, 15 + 5);
      pixels.show();
      modeState = 0;
      break;
    case 2:
    //pixel mode. 
    //At the moment, the strip of 20 LEDs is folded on itself on my monitor stand.
    //This means that there is  really only one physical row.
      for (int i = 0; i < 10; i++) {
        color =  Serial.parseInt();
        pixels.setPixelColor(i, color);
        pixels.setPixelColor(pixels.numPixels() - i - 1, color);
      }
      pixels.show();
      modeState = 0;
      break;
  }
  //  Serial.print("MODE:");
  Serial.println(modeState);
}

void setColor( Adafruit_NeoPixel &strip, uint32_t color, int a = 0, int b = -1) {
  if (b == -1) {
    b = strip.numPixels();
  }
  for (uint8_t i = a; i < b; i ++) {
    //    Serial.print("Setting pixel ");
    //    Serial.print(i);
    //    Serial.print(" to ");
    //    Serial.print(color);
    //    Serial.print("\n");
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


