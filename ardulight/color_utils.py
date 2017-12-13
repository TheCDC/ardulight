import random
import colorsys


class Colors:
    red = (255, 0, 0)
    green = (0, 255, 0)
    blue = (0, 0, 255)
    white = (255, 255, 255)
    black = (0, 0, 0)
    mtg_black = (182, 0, 255)
    mtg_green = (148, 255, 0)
    mtg_white = (255, 255, 75)
    mtg_red = (255, 32, 0)
    mtg_blue = (0, 165, 255)


def randcolor():
    return rgb_float_to_int(colorsys.hsv_to_rgb(random.random(), 1, 1))


def rgb_float_to_int(rgb):
    return tuple(map(lambda channel: int(channel * 255), rgb))


def scale_brightness(rgb, factor):
    return tuple(int(channel * factor) for channel in rgb)


def mix_colors(c1, c2):
    """Average two pixels"""
    return ((a + b) / 2 for a, b in zip(c1, c2))
