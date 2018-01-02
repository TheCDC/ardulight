"""A script to show off animations that can be performed by ardulight."""
import colorsys
import enum
import random
import time
import ardulight.cdc_rgb_controller as controller

COLORS = {
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (255, 0, 0),
    'white': (255, 255, 255),
    'black': (0, 0, 0),
}


def randcolor():
    """Return a random RGB color.
    Uses HSV to ensure the color is 'bright'."""
    return rgb_float_to_int(colorsys.hsv_to_rgb(random.random(), 1, 1))


def rgb_float_to_int(rgb):
    """Convert an RGB tuple of the form
    ([0,1],[0,1],[0,1]) to ([0,255],[0,255],[0,255])"""
    return tuple(map(lambda channel: int(channel * 255), rgb))


def scale_brightness(rgb, factor):
    """Multiply each value in an RGB tuple by a factor."""
    return tuple(int(channel * factor) for channel in rgb)


NUMPIXELS = int(input("Num. of pixels\n>>>"))


def default_pixels(num_pixels=NUMPIXELS):
    """Return a blank animation frame suitable for the LED
    strip currently in use."""
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
    """Animation showing a slice of the color wheel."""
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
    """n:
        number of cycles to perform.
    t:
        total duration of each cycle
    resolution:
         sub pixel resolution.
         Decrease if animation has bad performance.
         Increase if animation is choppy.
    connection:
        serial connection object
    power:
        Exponent describing shape of hump.
    """
    print(locals())

    def generate_frame(pos):
        cs = []
        for j in range(num_pixels):
            # this distance between this pixel and the center of the hump
            # 1 is added to avoid division by zero
            this_pixel_distance = abs(pos - j) + 1
            brightness_divisor = (this_pixel_distance)**(power)
            cs.append(
                tuple(map(lambda x: int(x / brightness_divisor), c)))
        return cs
    for _ in range(n):
        # nn is number of iterations of the animation
        c = randcolor()
        num = random.random()
        movement_eccentricity = random.choice(
            [num / 3 + 0.25, num * 2 + 1])
        num_steps = num_pixels * resolution
        # print(movement_eccentricity)
        connection.fade_to(generate_frame(0), t / 8)
        for i in range(num_steps):
            # i is the current step/frame of the animation
            # hump_fraction is progress of the hump along the strip as a
            # fraction
            hump_fraction = i / num_steps
            # hump_fraction is progress of the hump along the strip as a pixel
            # index
            hump_location = ((hump_fraction) **
                             movement_eccentricity) * num_pixels

            cs = generate_frame(hump_location)
            connection.write_frame(cs)
            dt = (t * 3 / 4) / (num_pixels * resolution)
            connection.sleep_alive(dt)
        connection.fade_to([COLORS['black']] * NUMPIXELS, t / 8)


def christmas_hump(n, t, connection, resolution=2, exponent=1, reverse=False):
    num_steps = NUMPIXELS * resolution

    for _ in range(n):
        colors = [COLORS[random.choice(['red', 'green'])]
                  for _ in range(NUMPIXELS)]
        for step in range(num_steps):
            hump_position = NUMPIXELS * step / num_steps
            if reverse:
                hump_position = NUMPIXELS - hump_position - 1
            brightness_mask = [(abs(hump_position - index) + 1)**(-exponent)
                               for index in range(NUMPIXELS)]
            out_frame = [scale_brightness(pixel, factor)
                         for pixel, factor in zip(colors, brightness_mask)]
            connection.write_frame(out_frame)
            # print(brightness_mask)
            connection.sleep_alive(t / num_steps)


def generic_demos(connection):
    ani_sinwave(n=50, t=6, resolution=3,
                power=1.5, connection=connection)
    ani_wheel(n=10, t=5, connection=connection)
    ani_wheel_slice(n=500, t=10, connection=connection)
    for _ in range(10):
        c = randcolor()
        connection.fade_to(frame=[c for i in range(
            NUMPIXELS)], duration=2, num_steps=50)


def quick_demos(connection):
    ani_wheel_slice(n=200, t=3, connection=connection)
    ani_sinwave(n=1, t=6, resolution=3,
                power=1.5, connection=connection)
    ani_wheel(n=2, t=3, connection=connection)
    for _ in range(3):
        c = randcolor()
        connection.fade_to(frame=[c for i in range(
            NUMPIXELS)], duration=2, num_steps=50)


class Modes(enum.Enum):
    generic = 0
    christmas = 1
    quick = 2


def main():
    connection = controller.interactive_choose_serial_device()
    chosen_mode = controller.user_pick_list(list(Modes))
    try:
        if chosen_mode == Modes.generic:

            while True:
                generic_demos(connection)
        elif chosen_mode == Modes.quick:
            while True:
                quick_demos(connection)
        elif chosen_mode == Modes.christmas:
            fps = 30
            delay = 2
            while True:
                for _ in range(10):
                    christmas_hump(n=1, t=5, connection=connection,
                                   resolution=30, exponent=2)
                    christmas_hump(n=1, t=5, connection=connection,
                                   resolution=30, exponent=2, reverse=True)
                # continue
                for _ in range(10):
                    frame = [randcolor() for i in range(NUMPIXELS)]
                    onecolor = [randcolor()] * NUMPIXELS
                    ns = int(fps * delay)
                    connection.fade_to(frame=frame,
                                       duration=delay,
                                       num_steps=ns, )
                    connection.sleep_alive(delay)
                    connection.fade_to(frame=onecolor,
                                       duration=delay / 2,
                                       num_steps=ns)
                    connection.sleep_alive(delay * 4)
    except KeyboardInterrupt:
        connection.terminate()
        quit()


if __name__ == '__main__':
    main()
