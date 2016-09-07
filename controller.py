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
    if len(l) == 1:
        # if there is only one serial device then choose that one
        return l[0]
    else:
        print("Choose:")
        print('\n'.join(["{}:{}".format(index, item)
                         for index, item in enumerate(l)]))
        return l[int(input(">>>"))]


def pack_rgb(r, g, b):
    return r << 16 | g << 8 | b


def unpack_rgb(n):
    r = n >> 16
    g = (n >> 8) % (1 << 8)
    b = n % (1 << 8)
    return (r, g, b)


def read_available(s):
    return str(''.join([s.read().decode() for i in range(s.inWaiting())]))


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
            int(((c / 255)**(power * m)) * 255) for c, m in zip(color, mods)
        ])
    elif mode == "trig":
        return tuple([int(
            ((math.cos((c / 255) * math.pi + math.pi) + 1) / 2)**power * 255
        ) for c, m in zip(color, mods)])


def choose_serial(testing=False, port=""):
    available_ports = SerialDetector.serial_ports()
    if testing:
        chosen_port = port
    else:
        chosen_port = user_pick_list(available_ports)

    return serial.Serial(port=chosen_port, baudrate=115200)


def main(*, testing=False, delay=0.02, port="COM6"):
    DEBUG = False
    myport = choose_serial(testing, port=port)
    rate = 20
    myalarm = Alarm(1 / rate)
    packed = ''
    ti = time.time()
    tf = time.time()
    N = 10
    while True:
        try:
            if myalarm.alarm():
                myalarm.reset()
                im = ImageGrab.grab()
                width, height = im.size
                colors = []
                for i in range(N):
                    tempimg = im.crop((i * width // N, 0, (i+1) * width // N  , height))
                    tempimg.thumbnail((1, 1))
                    c = tempimg.getpixel((0, 0))
                    c = pack_rgb(
                        *rescale_c(c, power=2, mode="trig", balance=True))
                    colors.append(c)
                colors = colors[::-1]
                myport.write(("-2\n" + '\n'.join([str(i) for i in colors])).encode(encoding="UTF-8"))
                feedback = read_available(myport)
                tf = time.time()
                print(
                    "Loop time:{:.3f}\tRate:{:.2f}\tColor:{}".format(
                        tf - ti, 1 / (tf - ti),0
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
    # timeit.timeit(stmt="main(testing=True)", number=10)
