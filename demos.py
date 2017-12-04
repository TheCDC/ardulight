import ardulight.cdc_rgb_controller as controller
import random
from ardulight import serial_utils
import time
import colorsys
from gui import load_or_create
import enum

COLORS = {
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (255, 0, 0),
    'white': (255, 255, 255),
}


def randcolor():
    return rgb_float_to_int(colorsys.hsv_to_rgb(random.random(), 1, 1))


def rgb_float_to_int(rgb):
    return tuple(map(lambda channel: int(channel * 255), rgb))


def scale_brightness(rgb, factor):
    return tuple(int(channel * factor) for channel in rgb)


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
    start = n * 4
    stop = 4
    for nn in range(start, stop, -2):
        # print(nn)
        numsteps = 100

        width = nn / n
        for j in range(start // nn):
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
            [num / 4 + 0.25, num * 2 + 1])
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


def christmas_hump(n, t, connection, resolution=2, exponent=1):
    num_steps = NUMPIXELS * resolution
    for iteration in range(n):
        colors = [COLORS[random.choice(['red', 'green'])]
                  for _ in range(NUMPIXELS)]
        for step in range(num_steps):
            hump_position = NUMPIXELS * step / num_steps
            brightness_mask = [(abs(hump_position - index) + 1)**(-exponent)
                               for index in range(NUMPIXELS)]
            out_frame = [scale_brightness(pixel, factor)
                         for pixel, factor in zip(colors, brightness_mask)]
            connection.write_frame(out_frame)
            # print(brightness_mask)
            sleep_alive(connection, t / num_steps)


def generic_demos(connection):
    ani_wheel(n=10, t=5, connection=connection)
    ani_sinwave(n=50, t=3, resolution=2,
                power=1.5, connection=connection)
    ani_wheel_slice(n=500, t=10, connection=connection)
    for _ in range(10):
        c = randcolor()
        connection.fade_to(frame=[c for i in range(
            NUMPIXELS)], duration=2, num_steps=50)


class Modes(enum.Enum):
    generic = 0
    christmas = 1


def sleep_alive(connection, duration):
    """Sleep while preserving the last frame.
    The hardware defaults to a blank fram on timeout
    This prevents that.

    The name is a play on sleep/keep alive."""
    frame = connection.last_frame
    step_duration = controller.TIMEOUT / 4
    num_steps = duration / step_duration
    # handle case that the requested sleep time is
    # actually fine
    if duration < controller.TIMEOUT:
        time.sleep(duration)
    else:
        for _ in range(int(num_steps)):
            connection.write_frame(frame)
            time.sleep(step_duration)


def main():
    try:
        port = controller.user_pick_list(
            serial_utils.serial_ports())
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
    chosen_mode = controller.user_pick_list(list(Modes))
    if chosen_mode == Modes.generic:

        while True:
            try:
                generic_demos(connection)
            except KeyboardInterrupt:
                connection.terminate()
                quit()
    elif chosen_mode == Modes.christmas:
        christmas_colors = [(255, 0, 0), (0, 255, 0), (255, 255, 255)]
        fps = 30
        delay = 1
        while True:
            # christmas_hump(n=5, t=5, connection=connection,
            #                resolution=30, exponent=1)
            # continue
            frame = [randcolor() for i in range(NUMPIXELS)]
            onecolor = [randcolor()] * NUMPIXELS
            ns = int(fps * delay)
            connection.fade_to(frame=frame,
                               duration=delay / 2,
                               num_steps=ns, )
            sleep_alive(connection, delay / 2)
            connection.fade_to(frame=onecolor,
                               duration=delay / 2,
                               num_steps=ns)
            sleep_alive(connection, delay * 2)
            # time.sleep(delay / 4)


if __name__ == '__main__':
    main()
