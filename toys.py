import colorsys
import enum
import random
import time
import ardulight.cdc_rgb_controller as controller
import pyautogui

NUMPIXELS = int(input("Num. pixels\n>>>"))


def scale_brightness(rgb, factor):
    """Multiply each value in an RGB tuple by a factor."""
    return tuple(int(channel * factor) for channel in rgb)


def rgb_float_to_int(rgb):
    """Convert an RGB tuple of the form
    ([0,1],[0,1],[0,1]) to ([0,255],[0,255],[0,255])"""
    return tuple(map(lambda channel: int(channel * 255), rgb))


def scale_brightness(rgb, factor):
    """Multiply each value in an RGB tuple by a factor."""
    return tuple(int(channel * factor) for channel in rgb)


def randcolor(value=1):
    """Return a random RGB color.
    Uses HSV to ensure the color is 'bright'."""
    return rgb_float_to_int(colorsys.hsv_to_rgb(random.random(), 1, value))


class Modes(enum.Enum):
    mouse = 0
    mouse_flat_color = 1
    solid_white = 2


def main():
    connection = controller.interactive_choose_serial_device()
    chosen_mode = controller.user_pick_list(list(Modes))
    try:
        if chosen_mode == Modes.mouse:
            last_move_time = time.time()
            movement_threshold = 10
            time_threshold_short = 30
            time_threshold_long = 60*10
            last_pos = pyautogui.position()
            while True:
                cur_time = time.time()
                w, h = pyautogui.size()
                pos = pyautogui.position()
                x, y = pos

                # idle detection
                diffs = [abs(a - b) for a, b in zip(last_pos, pos)]
                if max(diffs) >= movement_threshold:
                    last_move_time = time.time()
                    last_pos = pos
                idle_time = cur_time - last_move_time
                if idle_time <= time_threshold_short:

                    index = NUMPIXELS * x / w
                    color = [i * 255 for i in colorsys.hsv_to_rgb(y / h, 1, 1)]
                    # print(x, y, w, h, color)
                    frame = []
                    for i in range(NUMPIXELS):
                        factor = 1 / (1 + abs(index - i)**2)
                        # print(i, factor)
                        frame.append(scale_brightness(color, factor))
                    connection.fade_to(
                        frame=frame[::-1], duration=1 / 5, num_steps=10)
                elif idle_time > time_threshold_short and idle_time <= time_threshold_long:
                    frame = [randcolor(value=1 / 8) for i in range(NUMPIXELS)]
                    connection.fade_to(frame=frame, duration=1, num_steps=10)

                else:
                    time.sleep(0.1)
                # connection.write_frame(frame)
        elif chosen_mode == Modes.mouse_flat_color:
            last_move_time = time.time()
            movement_threshold = 10
            time_threshold = 30
            last_pos = pyautogui.position()
            while True:
                cur_time = time.time()
                w, h = pyautogui.size()
                pos = pyautogui.position()
                x, y = pos

                # idle detection
                diffs = [abs(a - b) for a, b in zip(last_pos, pos)]

                color = [i * 255 for i in colorsys.hsv_to_rgb(y / h, 1, 1)]
                # print(x, y, w, h, color)
                frame = [color for i in range(NUMPIXELS)]
                connection.fade_to(
                    frame=frame[::-1], duration=1 / 5, num_steps=10)
                # connection.write_frame(frame)
        elif chosen_mode == Modes.solid_white:
            while True:
                frame = [(255, 255, 255) for i in range(NUMPIXELS)]
                connection.fade_to(
                    frame=frame[::-1], duration=1 / 5, num_steps=10)

    except KeyboardInterrupt:
        quit()


if __name__ == '__main__':
    main()
