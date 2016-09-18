#!/usr/bin/env python3

import PIL
from PIL import Image
import sys
PLATFORM = sys.platform
if PLATFORM == "win32":
    from PIL import ImageGrab
else:
    import pyscreenshot as ImageGrab
# import pyscreenshot as ImageGrab
import serial
import SerialDetector
import time
import timeit
import math


class Alarm(object):

    """A simple class that implements a timer."""

    def __init__(self, duration):
        self.dur = duration
        self.reset()

    def alarm(self):
        if time.time() - self.start >= self.dur:
            return True
        else:
            return False

    def reset(self):
        self.start = time.time()


def user_pick_list(l):
    """Interactively ask the user to choose an item from a list by number."""
    if len(l) == 0:
        raise ValueError("Can't choose from list of length 0.")
    elif len(l) == 1:
        # if there is only one item then choose that one
        return l[0]
    else:
        response = '-10'
        choice = int(response)
        while choice < 0:
            print("Choose:")
            print('\n'.join(["{}:{}".format(index, item)
                             for index, item in enumerate(l)]))
            response = input(">>>")
            try:
                choice = int(response)
            except ValueError:
                print("ERROR! Try again.")
                continue
        return l[int(response)]


def pack_rgb(r, g, b):
    """Take RGB values and 'pack' them into a 24-bit number."""
    return r << 16 | g << 8 | b


def unpack_rgb(n):
    """Take a 24-bit integer and 'unpack' it into RGB values."""
    r = n >> 16
    g = (n >> 8) % (1 << 8)
    b = n % (1 << 8)
    return (r, g, b)


def read_available(s):
    return str(''.join([s.read().decode() for i in range(s.inWaiting())]))


def scale_trig(c, power=1, eccen=1):
    """Reshape a color curve into a trig function."""
    return int(
        ((math.cos((c / 255) * math.pi + math.pi) + 1) /
         2)**(power * eccen) * 255
    )


def scale_poly(c, power=1, eccen=1):
    """Reshape a color curve into a different order/eccentricity
    polynomial."""
    return int(((c / 255)**(power * eccen)) * 255)


def rescale_c(color, power=2, mode="poly", balance=True, mods=(0.7, 0.8, 1)):
    """Change the shape of the curve of a color
    Higher powers will put more distance between dark and light.
    This is recommended.
    Smaller fractional powers bring them closer."""
    if balance:
        # adjust color response curve of each color channel
        pass
    else:
        # disable custom color response if not desired
        mods = (1, 1, 1)

    if mode == "poly":
        return tuple([
            scale_poly(c, power, eccen) for c, eccen in zip(color, mods)
        ])
    elif mode == "trig":
        return tuple([
            scale_trig(c, power, eccen)
            for c, eccen in zip(color, mods)
        ])


def choose_serial(testing=False, port=""):
    """Let the user choose a serial port on which their board
    is connected. If the propgram is ins testing mode, instead 
    choose a supplied port."""
    available_ports = SerialDetector.serial_ports()
    try:
        if testing:
            chosen_port = port
        else:
            chosen_port = user_pick_list(available_ports)
    except ValueError:
        raise RuntimeError("No serial devices found. May require admin privileges.")

    return serial.Serial(port=chosen_port, baudrate=115200)


def shoot():
    """Return PIL Image of the screen."""
    if PLATFORM == "linux":
        return ImageGrab.grab(backend=None)
    else:
        return ImageGrab.grab()


def extract_colors(im, n=10, mode="poly"):
    """Get the average colors of vertical strips of the screen as a list."""
    colors = []
    width, height = im.size
    for i in range(n):
        # First get the whole strip.
        tempimg = im.crop((i * width // n, 0, (i + 1) * width // n, height))
        # Uses whatever resizing algorithm Pillow uses to shrink
        # the image it to one pixel.
        # Theoretically that should give us a 1x1 image that is the
        # average color.
        tempimg.thumbnail((1, 1))
        # Given that the image is 1x1, get the color of that one pixel.
        c = tempimg.getpixel((0, 0))
        # Run it through the
        c = pack_rgb(
            *rescale_c(c, power=2, mode=mode, balance=True))
        colors.append(c)
    return colors


<<<<<<< HEAD
def main(*, testing=False, delay=0.02, port="COM6", target_rate=20):
=======
def main(*, testing=False, delay=0.02, port="COM6",target_rate=16):
>>>>>>> 983173309b4ef39a3643573a6899bac236b46c51
    """The basic gist is this:
    Set up the serial connection with the Arduino.
    There might be multiple serial ports connected so 
    the user should be asked to pick one.

    After a port is selected, perform a loop
        In this loop, capture the screen as an image,
        slice that image into vertical slices
        write the average colors of those slices to
        the arduino over the serial connection.
    """
    DEBUG = False
    myport = choose_serial(testing, port=port)
    rate = target_rate
    myalarm = Alarm(1 / rate)
    packed = ''
    # stuff for tracking performance
    ti = time.time()
    tf = ti
    N = 10
    while True:
        try:
            if myalarm.alarm():
                myalarm.reset()
                im = shoot()

                # Split the screen into N vertical strips.
                # Assign the average color of each strip to
                # its respective LED.
                colors = extract_colors(im, N)
                colors = colors[::-1] + colors
                # send a single string telling the 'duino to switch modes,
                # and also the colors for each LED
                myport.write((
                    "-2\n" + '\n'.join([
                        str(i) for i in colors
                    ])
                ).encode(encoding="UTF-8"))
                # Throw away all the incoming serial data.
                feedback = read_available(myport)
                tf = time.time()
                # Some debug data.
                loop_time = tf - ti
                loop_rate = 1 / (tf - ti)
<<<<<<< HEAD
                error = (loop_rate - rate) / rate
                print(
                    "Loop time:{:.3f}\tRate:{:.2f}\tError:{:.2f}".format(
                        loop_time, loop_rate, error
=======
                error = (loop_rate - rate)/rate
                print(
                    "Loop time:{:.3f}\tRate:{:.2f}\tError:{:.2f}".format(
                        loop_time, loop_rate,error
>>>>>>> 983173309b4ef39a3643573a6899bac236b46c51
                    )
                )
                ti = time.time()
        except serial.serialutil.SerialException as e:
            print("Serial error. Attempting to reconnect.".format(repr(e)))
            myport.close()
            try:
                # reconnect after serial disconnect
                myport = serial.Serial(port=chosen_port, baudrate=115200)
                print("Reconnected on {}!".format(chosen_port))
            except:
                pass
            time.sleep(3)

        except OSError as e:
            # wait out a system sleep
            print("{}\nPossible system sleep detected. Waiting...".format(e))
            time.sleep(7)
        except KeyboardInterrupt:
            # quit cleanly
            print("Have a nice day!")
            im.save("debug/out.png")
            quit()

        if DEBUG:
            pass
        else:
            pass

        if testing:
            return 0

if __name__ == '__main__':
    main(testing=False)
