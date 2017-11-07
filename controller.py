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
import math


class Alarm():

    """A simple class that implements a timer."""

    def __init__(self, duration):
        self.dur = duration
        self.reset()

    def alarm(self):
        return bool(time.time() - self.start >= self.dur)

    def reset(self):
        self.start = time.time()

    def set(self, t):
        self.dur = t


class Controller():
    """Handles the serial connection and translating RGB tuples into packed numeric output."""

    def __init__(self,
                 port="COM15",
                 baudrate=115200,):
        self.port = port
        self.baudrate = baudrate
        self.open()

    def terminate(self):
        self.serial.close()

    def write_frame(self, colors):
        """Take a list of RGB tuples and write them out to the 'duino via serial."""
        attempts_remaining = 30
        while attempts_remaining > 0:
            try:
                out_tokens = []
                out_tokens.append("-2")
                for c in colors:
                    out_tokens.append(str(pack_rgb(c)))
                # out_tokens.append('\n')
                out_str = " ".join(out_tokens) + '\n'
                # print("write:", out_str)
                self.serial.write(
                    (out_str).encode(encoding="UTF-8"))
                self.serial.flush()
                # chars = []
                # while self.serial.in_waiting > 0:
                #     chars.append(self.serial.read().decode())
                # s = ''.join(chars).strip()
                # if len(s) > 0:
                #     print(s)
                #     pass

                return
            except serial.serialutil.SerialException as e:
                attempts_remaining -= 1
                # close the connection ASAP so the device can connect to the
                # same serial port
                self.close()
                time.sleep(1)
                try:
                    self.open()
                except serial.serialutil.SerialException:
                    # continue to close the connection to the port every time
                    # it fails.
                    self.close()
                    pass
                if attempts_remaining == 0:
                    raise RuntimeError(
                        "The controller attempted to recover from a disconnect but failed.\n{}".format(e))

    def close(self):
        self.terminate()

    def open(self):
        self.serial = serial.Serial(
            port=self.port, baudrate=self.baudrate, write_timeout=0.5)


class ScreenToRGB():
    """Handles capturing the screen and processing slices to send to 
    Arduino through a Controller."""

    def __init__(self, *,
                 port="COM15",
                 baudrate=115200,
                 n_slices=10,
                 slice_mapping=None,
                 color_scale_type="poly",
                 color_pow=1,
                 color_eccen=1,
                 balance_color=True,
                 color_mods=(1, 1, 1)):
        self.port = port
        self.baudrate = baudrate
        self.connection = Controller(port=self.port, baudrate=self.baudrate)

        self.n_slices = n_slices
        self.slice_mapping = slice_mapping
        self.color_scale_type = color_scale_type
        self.color_pow = color_pow
        self.color_eccen = color_eccen
        self.balance_color = balance_color
        self.color_mods = color_mods
        self.im = None
        self.slices = []
        self.colors = []

    def step(self):
        self.im = shoot()

        # Split the screen into N vertical strips.
        # Assign the average color of each strip to
        # its respective LED.
        self.colors = extract_colors(self.im,
                                     self.n_slices,
                                     power=self.color_pow,
                                     mode=self.color_scale_type,
                                     balance=self.balance_color,
                                     mods=self.color_mods)
        self.slices = []
        if self.slice_mapping:
            for m in self.slice_mapping:
                self.slices.append(self.colors[m])
        else:
            self.slices = self.colors[::-1] + self.colors
        self.connection.write_frame(self.slices)
        return self.slices[:]

    def terminate(self):
        self.connection.close()

    def __repr__(self):
        return "ScreenToRGB(port=\"{}\", baudrate={}, n_slices={}, color_scale_type=\"{}\", color_pow={}, color_eccen={}, balance_color={}, color_mods={})".format(self.port,
                                                                                                                                                                   self.baudrate,
                                                                                                                                                                   self.n_slices,
                                                                                                                                                                   self.color_scale_type,
                                                                                                                                                                   self.color_pow,
                                                                                                                                                                   self.color_eccen,
                                                                                                                                                                   self.balance_color,
                                                                                                                                                                   self.color_mods)


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


def pack_rgb(r, g=None, b=None):
    """Take RGB values and 'pack' them into a 24-bit number."""
    if isinstance(r, tuple):
        b = r[2]
        g = r[1]
        r = r[0]
    elif isinstance(r, int):
        pass
    else:
        raise ValueError(
            "Colors must be three ints or a single tuple, not {}".format(type(r)))
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


def reshape_color(color, power=2, mode="poly", balance=True, mods=(0.7, 0.8, 1)):
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


def rescale_rgb(c):
    return list(map(reshape_color, c))


def choose_serial(testing=False, port=""):
    """Let the user choose a serial port on which their board
    is connected.
    If the program is in testing mode, instead choose a supplied port."""
    available_ports = SerialDetector.serial_ports()
    try:
        if testing:
            chosen_port = port
        else:
            chosen_port = user_pick_list(available_ports)
    except ValueError:
        raise RuntimeError(
            "No serial devices found. May require admin privileges.")

    return serial.Serial(port=chosen_port, baudrate=115200)


def shoot():
    """Return PIL Image of the screen."""
    if PLATFORM == "linux":
        return ImageGrab.grab(backend=None)
    else:
        return ImageGrab.grab()


def extract_colors(im,
                   n=10,
                   power=2,
                   *,
                   mode="poly",
                   balance=True,
                   mods=(1, 1, 1)):
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
        colors.append(reshape_color(c, power=power,
                                    mode=mode, balance=balance, mods=mods))
    return colors


def main(*, testing=False, port="COM6", target_rate=20):
    """The basic gist is this:
    Set up the serial connection with the Arduino.
    There might be multiple serial ports connected.
    If so, the user should be asked to pick one.
    After a port is selected, perform a loop
        In this loop, capture the screen as an image,
        slice that image into vertical slices
        write the average colors of those slices to
        the arduino over the serial connection.
    """
    DEBUG = False
    # myport = choose_serial(testing, port=port)
    rate = target_rate
    myalarm = Alarm(1 / rate)
    # stuff for tracking performance
    ti = time.time()
    tf = ti
    N = 10
    error = 1
    my_controller = ScreenToRGB(
        port=user_pick_list(SerialDetector.serial_ports()),
        n_slices=10,
        slice_mapping=list(
            map(int, "9 8 7 6 5 4 3 2 1 0 0 1 2 3 4 5 6 7 8 9".split(' '))),
        color_pow=2,
        color_mods=(1, 1, 1,)
    )
    while True:
        try:
            if myalarm.alarm():
                ti = time.time()
                myalarm.reset()
                my_controller.step()

                # im = shoot()
                # # # Split the screen into N vertical strips.
                # # Assign the average color of each strip to
                # # its respective LED.
                # colors = extract_colors(im, N)
                # colors = colors[::-1] + colors
                # # send a single string telling the 'duino to switch modes,
                # # and also the colors for each LED
                # print(myport.write((
                #                     "-2\n" + '\n'.join(map(str,colors))
                #                 ).encode(encoding="UTF-8")))
                # # Throw away all the incoming serial data.
                # read_available(myport)

                tf = time.time()
                # Some debug data.
                loop_time = tf - ti
                loop_rate = 1 / (tf - ti)
                error = (loop_rate - rate) / rate
                if (error < -0.1):
                    rate -= 1
                elif error > 0.1:
                    rate += 1
                print(
                    "LoopT:{:.3f}\t1/T:{:.2f}\tError:{:.2f}\tCurRate:{}".format(
                        loop_time, loop_rate, error, rate
                    )
                )
        except serial.serialutil.SerialException as e:
            print("Serial error. Attempting to reconnect.")
            myport.close()
            try:
                # reconnect after serial disconnect
                myport.open()
                print("Reconnected on {}!".format(myport.port))
            except serial.serialutil.SerialException as e:
                pass
                # print(repr(e))
            time.sleep(3)

        except OSError as e:
            # wait out a system sleep
            print("{}\nPossible system sleep detected. Waiting...".format(e))
            time.sleep(7)
        except KeyboardInterrupt:
            # quit cleanly
            print("Have a nice day!")
            # im.save("debug/out.png")
            quit()

        if DEBUG:
            pass
        else:
            pass

        if testing:
            return 0

if __name__ == '__main__':
    main(testing=False)
