import controller
import random
import SerialDetector
import time
import colorsys
from gui import load_or_create
def randcolor():
    return rgb_float_to_int(colorsys.hsv_to_rgb(random.random(),1,1))

def remap(colors):
    return colors[::-1] + colors


def rgb_float_to_int(rgb):
    return tuple(map(lambda c: int(c * 255), rgb))
NUMPIXELS = 20


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
            N = 30
            for n in range(N):
                T = 0.8
                c = randcolor()
                for i in range(NUMPIXELS):
                    cs = [(0,0,0)]*NUMPIXELS
                    cs[i] = c
                    connection.write_frame(cs)
                    time.sleep(T/NUMPIXELS)


            n = 500
            T = 30
            delta_t = T / n
            for i in range(n):
                cs.pop(0)
                cs.append(tuple(map(lambda t: int(t * 255),
                                    colorsys.hsv_to_rgb(i / n, 1, 1))))
                connection.write_frame(cs)
                time.sleep(delta_t)

            N = 7
            width = 1
            for nn in range(N, 0, -1):
                numsteps = 100
                T = 5
                width = nn / N
                for i in range(numsteps):
                    cs = list(map(lambda x: rgb_float_to_int(colorsys.hsv_to_rgb(
                        (x) / (NUMPIXELS * width) + i / numsteps, 1, 1)), range(NUMPIXELS)))
                    connection.write_frame(cs)
                    # cs.append(cs.pop(0))
                    time.sleep(T / numsteps)
        except KeyboardInterrupt:
            connection.terminate()
            quit()
if __name__ == '__main__':
    main()
