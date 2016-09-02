#Introduction
You know Philips Ambilight? This is my attempt at that.

#Platforms
The Python half of this project should work on Linux/Mac/Windows.

#Materials
WS28* RGB LED strip attached to some sort of Arduino that has a serial connection to your PC.

#Requirements
Python libraries:
```
pyserial
pillow
```

#Usage
Upload the arduino program found in `pc_rgb_controller` to your arduino.
Run the appropriate launch script for your OS: `run.sh` for *nix and `run.bat` for Windows.
If you have multiple serial devices connected the command line interface asks you to choose one.
Make sure to choose the serial port connected to your Arduino.

#Under the hood

##PC
The Python `pillow` library is used to grab a screenshot of the desktop, resize it to a 1x1 thumbnail, and read the RGB values of that pixel.
That RGB value is packed/serialized into an integer which is sent to the Arduino via `pyserial`.

##Arduino
The `loop()` checks for a integer sent over serial connection, unpacks/deserializes the RGB values from it and writes that color to the whole strip.

#Future
Eventually I will add some sort of command structure so that more complex animations can be triggered and controlled by the PC.