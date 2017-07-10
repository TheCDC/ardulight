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


def default_pixels(num_pixels=NUMPIXELS):
    return [(0, 0, 0,) for i in range(num_pixels)]


def ani_wheel(n, connection, num_pixels=NUMPIXELS):
    # single color that goes around the wheel
    cs = default_pixels()
    for nn in range(n * 4, 0, -2):
        numsteps = 100
        T = 5
        width = nn / n
        for i in range(numsteps):
            cs = list(map(lambda x: rgb_float_to_int(colorsys.hsv_to_rgb(
                (x) / (num_pixels * width) + i / numsteps, 1, 1)), range(num_pixels)))
            connection.write_frame(cs)
            # cs.append(cs.pop(0))
            time.sleep(T / numsteps)


def ani_wheel_slice(n, t, connection):
    # slice of the color wheel
    cs = default_pixels()
    delta_t = t / n
    for i in range(n):
        cs.pop(0)
        cs.append(tuple(map(lambda tup: int(tup * 255),
                            colorsys.hsv_to_rgb(i / n, 1, 1))))
        connection.write_frame(cs)
        time.sleep(delta_t)


def ani_sinwave(n, t, resolution, connection, num_pixels=NUMPIXELS):
    # moving hump of color

    for n in range(n):
        c = randcolor()
        for i in range(num_pixels * resolution):
            cs = []
            for j in range(num_pixels):
                cs.append(
                    tuple(map(lambda x: int(x / (1 + abs(i / resolution - j))**(2)), c)))
            # cs = [(0, 0, 0)] * num_pixels
            # cs[i] = c
            connection.write_frame(cs)
            dt = t / (num_pixels * resolution)
            time.sleep(dt)


def main():

    connection = controller.Controller(
        port=controller.user_pick_list(SerialDetector.serial_ports()),
        baudrate=115200)
    # for i in range(100):
    #  for c in [r, g, b]:
    #      connection.write_frame([c]*NUMPIXELS)
    #      time.sleep(0.01)
    while True:
        try:
            ani_wheel(n=10,  connection=connection)
            ani_sinwave(n=45, t=2, resolution=10, connection=connection)
            ani_wheel_slice(n=500, t=60, connection=connection)

        except KeyboardInterrupt:
            connection.terminate()
            quit()


if __name__ == '__main__':
    main()
