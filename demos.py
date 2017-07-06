import controller
import random
import SerialDetector
import time
import colorsys
from gui import load_or_create


def randcolor():
    return rgb_float_to_int(colorsys.hsv_to_rgb(random.random(), 1, 1))


def remap(colors):
    return colors[::-1] + colors


def rgb_float_to_int(rgb):
    return tuple(map(lambda c: int(c * 255), rgb))

try:
    NUMPIXELS = len(load_or_create("config/mapping.txt", None).split(" "))
    print("NUMPIXELS=", NUMPIXELS)
except TypeError:
    raise RuntimeError("Run the GUI to generate config files!")


def main():

    connection = controller.Controller(
        port=controller.user_pick_list(SerialDetector.serial_ports()),
        baudrate=115200)
    r = (255, 0, 0)
    g = (0, 255, 0)
    b = (0, 0, 255)
    # for i in range(100):
    #  for c in [r, g, b]:
    #      connection.write_frame([c]*NUMPIXELS)
    #      time.sleep(0.01)
    cs = [(0, 0, 0,) for i in range(NUMPIXELS)]
    while True:
        try:
            # moving hump of color
            N = 45
            for n in range(N):
                T = 1
                c = randcolor()
                res = 5
                for i in range(NUMPIXELS * res):
                    cs = []
                    for j in range(NUMPIXELS):
                        cs.append(
                            tuple(map(lambda x: int(x / (1 + abs(i / res - j))**2), c)))
                    # cs = [(0, 0, 0)] * NUMPIXELS
                    # cs[i] = c
                    connection.write_frame(cs)
                    dt = T / (NUMPIXELS * res)
                    time.sleep(dt)
            # slice of the color wheel
            N = 10
            width = 1
            for nn in range(N * 4, 0, -2):
                numsteps = 100
                T = 1
                width = nn / N
                for i in range(numsteps):
                    cs = list(map(lambda x: rgb_float_to_int(colorsys.hsv_to_rgb(
                        (x) / (NUMPIXELS * width) + i / numsteps, 1, 1)), range(NUMPIXELS)))
                    connection.write_frame(cs)
                    # cs.append(cs.pop(0))
                    time.sleep(T / numsteps)
            # single color that goes around the wheel
            n = 500
            T = 60
            delta_t = T / n
            for i in range(n):
                cs.pop(0)
                cs.append(tuple(map(lambda t: int(t * 255),
                                    colorsys.hsv_to_rgb(i / n, 1, 1))))
                connection.write_frame(cs)
                time.sleep(delta_t)

        except KeyboardInterrupt:
            connection.terminate()
            quit()
if __name__ == '__main__':
    main()
