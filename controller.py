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
    return ''.join([str(s.read()) for i in range(s.inWaiting())])


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
            int(((c/255)**(power*m))*255) for c, m in zip(color, mods)
        ])
    elif mode == "trig":
        return tuple([int(
            ((math.cos((c/255)*math.pi + math.pi) + 1)/2)**power*255
        ) for c, m in zip(color, mods)])


def main(*, testing=False, delay=0.02, port="COM6"):
    DEBUG = False

    available_ports = SerialDetector.serial_ports()
    if testing:
        chosen_port = port
    else:
        chosen_port = user_pick_list(available_ports)

    myport = serial.Serial(port=chosen_port, baudrate=115200)
    myalarm = Alarm(0.1)
    packed = ''
    while True:
        try:
            if myalarm.alarm():
                im = ImageGrab.grab()
                im.thumbnail((1, 1))
                c = im.getpixel((0, 0))
                packed = pack_rgb(
                    *rescale_c(c, power=2, mode="poly", balance=False))
                if DEBUG:
                    print(c, packed)
                myport.write((str(packed) + "\n").encode(encoding='UTF-8'))
                myalarm.reset()
                feedback = read_available(myport)
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
            print("Possible system sleep detected. Waiting...")
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
    timeit.timeit(stmt="main(testing=True)", number=10)
