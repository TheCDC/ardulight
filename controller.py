import PIL
from PIL import Image
from PIL import ImageGrab
import serial
import SerialDetector
import time
import timeit
import sys
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
    """Interactively ask the user to choose an itme from a list by number."""
    if len(l) == 1:
        # if there is only one item then choose that one
        return l[0]
    else:
        print("Choose:")
        print('\n'.join(["{}:{}".format(index, item)
                         for index, item in enumerate(l)]))
        return l[int(input(">>>"))]


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


def scale_trig(c, power, eccen):
    return int(
        ((math.cos((c / 255) * math.pi + math.pi) + 1) /
         2)**(power * eccen) * 255
    )


def scale_poly(c, power, eccen):
    return int(((c / 255)**(power * eccen)) * 255)


def rescale_c(color, power=2, mode="poly", balance=True):
    """Change the shape of the curve of a color
    Higher powers will put more distance between dark and light.
    This is recommended.
    Smaller fractional powers bring them closer."""
    if balance:
        # adjust color response curve of each color channel
        mods = (0.7, 0.8, 1)
    else:
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
    if testing:
        chosen_port = port
    else:
        chosen_port = user_pick_list(available_ports)

    return serial.Serial(port=chosen_port, baudrate=115200)


def shoot():
    return ImageGrab.grab()


def extract_colors(im, n=10):
    colors = []
    width, height = im.size
    for i in range(n):
        tempimg = im.crop((i * width // n, 0, (i + 1) * width // n, height))
        tempimg.thumbnail((1, 1))
        c = tempimg.getpixel((0, 0))
        c = pack_rgb(
            *rescale_c(c, power=2, mode="trig", balance=True))
        colors.append(c)
    return colors


def main(*, testing=False, delay=0.02, port="COM6"):
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
    rate = 20
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
                colors = extract_colors(im, N)[::-1]
                # send a single string telling the 'duino to switch modes,
                # and also the colors for each LED
                myport.write((
                    "-2\n" + '\n'.join([
                        str(i) for i in colors
                    ])
                ).encode(encoding="UTF-8"))
                feedback = read_available(myport)
                tf = time.time()
                print(
                    "Loop time:{:.3f}\tRate:{:.2f}".format(
                        tf - ti, 1 / (tf - ti)
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
            quit()

        if DEBUG:
            pass
        else:
            pass

        if testing:
            return 0

if __name__ == '__main__':
    main(testing=False)
