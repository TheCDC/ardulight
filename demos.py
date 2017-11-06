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


def ani_wheel(n, t, connection, num_pixels=NUMPIXELS):
    # single color that goes around the wheel
    print(locals())
    cs = default_pixels()
    for nn in range(n * 4, 0, -2):
        numsteps = 100

        width = nn / n
        for i in range(numsteps):
            cs = list(map(lambda x: rgb_float_to_int(colorsys.hsv_to_rgb(
                (x) / (num_pixels * width) + i / numsteps, 1, 1)), range(num_pixels)))
            connection.write_frame(cs)
            # cs.append(cs.pop(0))
            time.sleep(t / numsteps)


def ani_wheel_slice(n, t, connection):
    # slice of the color wheel
    print(locals())
    cs = default_pixels()
    delta_t = t / n
    for i in range(n):
        cs.pop(0)
        cs.append(tuple(map(lambda tup: int(tup * 255),
                            colorsys.hsv_to_rgb(i / n, 1, 1))))
        connection.write_frame(cs)
        time.sleep(delta_t)


def ani_sinwave(n, t, resolution, connection, power=2, num_pixels=NUMPIXELS,):
    # moving hump of color
    """n: number of cycles to perform.
    t: total duration of each cycle
    resolution: sub pixel resolution. Decrease if animation is slower than intended.
    connection: serial connection object
    power: exponent for decay rate of brightness of pixels as distance from hump increases
    """
    print(locals())
    for nn in range(n):
        # nn is number of iterations of the animation
        c = randcolor()
        num = random.random()
        movement_eccentricity = random.choice(
            [num / 2 + 0.5, num + 1])
        num_steps = num_pixels * resolution
        # print(movement_eccentricity)
        for i in range(num_steps):
            # i is the current step/frame of the animation
            cs = []
            # hump_fraction is progress of the hump along the strip as a
            # fraction
            hump_fraction = i / num_steps
            # hump_fraction is progress of the hump along the strip as a pixel
            # index
            hump_location = ((hump_fraction) **
                             movement_eccentricity) * num_pixels
            for j in range(num_pixels):
                # this distance between this pixel and the center of the hump
                # 1 is added to avoid division by zero
                this_pixel_distance = abs(hump_location - j) + 1
                brightness_divisor = (this_pixel_distance)**(power)
                cs.append(
                    tuple(map(lambda x: int(x / brightness_divisor), c)))
            # cs = [(0, 0, 0)] * num_pixels
            # cs[i] = c
            connection.write_frame(cs)
            dt = t / (num_pixels * resolution)
            time.sleep(dt)


def main():
    try:
        port = controller.user_pick_list(
            SerialDetector.serial_ports())
    except ValueError:
        raise RuntimeError(
            "No devices were found! If you are on *nix you may need to run as root.")
    connection = controller.Controller(
        port=port,
        baudrate=115200)
    # for i in range(100):
    #  for c in [r, g, b]:
    #      connection.write_frame([c]*NUMPIXELS)
    #      time.sleep(0.01)
    while True:
        try:
            ani_sinwave(n=50, t=3, resolution=2,
                        power=1.5, connection=connection)
            ani_wheel_slice(n=500, t=10, connection=connection)
            ani_wheel(n=10, t=5, connection=connection)

        except KeyboardInterrupt:
            connection.terminate()
            quit()


if __name__ == '__main__':
    main()
