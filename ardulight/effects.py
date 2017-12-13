import ardulight.cdc_rgb_controller as controller
import ardulight.color_utils as color_utils
import random
import math
from gui import load_or_create
try:
    NUMPIXELS = len(load_or_create("config/mapping.txt", None).split(" "))
    print("NUMPIXELS=", NUMPIXELS)
except TypeError:
    raise RuntimeError("Run the GUI to generate config files!")


def lightning(connection, color=color_utils.Colors.white, max_duration=3):
        # count iterations
    i = 0
    # brightness
    b = 100
    last = -1
    thresh = 0.5
    step_size = 5
    time_step = 0.02
    while b > 0 and i < max_duration / time_step:
        n = random.random()

        if last == -1:
            thresh = 0.7
        elif last == 1:
            thresh = 0.4

        if n > thresh:
            b = min(100, b + step_size)
            last = 1
        else:
            last = -1
            b = max(b - step_size, 0)

        connection.write_frame([color_utils.scale_brightness(
            color, b / 100)] * NUMPIXELS)
        connection.sleep_alive(time_step)
        i += 1

        # print(i, b)
    connection.fade_to([color_utils.Colors.black] * NUMPIXELS, duration=0.1)


def present_mtg_colors(connection, colors='wubrg'):
    chosen = colors.lower()
    if len(set('wubrg') | set(chosen)) > 5:
        raise ValueError("Only wubrg allowed.")
    xlat = {
        'w': color_utils.Colors.mtg_white,
        'u': color_utils.Colors.mtg_blue,
        'b': color_utils.Colors.mtg_black,
        'r': color_utils.Colors.mtg_red,
        'g': color_utils.Colors.mtg_green,
    }
    num_repeat = math.ceil(NUMPIXELS / len(chosen))
    frame = [xlat[c] for c in (chosen * num_repeat)[:NUMPIXELS]]
    # connection.write_frame(frame)
    for c in chosen:
        lightning(connection, xlat[c], max_duration=(5 / 2) / len(chosen))


def main():
    connection = controller.interactive_choose_serial_device()
    # present_mtg_colors(connection, 'bg')
    while True:
        lightning(connection, color=color_utils.randcolor())
    print("done")


if __name__ == '__main__':
    main()
