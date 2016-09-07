from ctypes import windll
from controller import unpack_rgb
import controller
import timeit
import time
dc = windll.user32.GetDC(0)


def getpixel(x, y):
    return windll.gdi32.GetPixel(dc, x, y)


def sample_screen(divisor, width, height):
    cs = []
    for x in range(0, width, width // divisor):
        for y in range(0, height, height // divisor):
            cs.append(getpixel(x, y))
    c = sum(cs) // len(cs)
    return unpack_rgb(c)


def main():
    # print(unpack_rgb(getpixel(0, 0)))
    # divisor = 10
    # WIDTH = 1920
    # HEIGHT = 1080
    # for i in range(2):
           #  c = sample_screen(10,WIDTH,HEIGHT)
    # print(c)
    # print(timeit.timeit("ImageGrab.grab()",setup="from PIL import ImageGrab",number=500))
    # print(timeit.timeit("controller.main(testing=True,port='COM6')",setup="import controller",number=10))
    myport = controller.choose_serial()
    # for i in range(10):
    #     c1 = controller.pack_rgb(255, 0,0)
    #     c1s = str(c1)
    #     c2 = controller.pack_rgb(0, 255,0)
    #     c2s = str(c2)
    #     myport.write("-1\n{}\n{}\n".format(c1s,c2s).encode(encoding='UTF-8'))
    #     time.sleep(0.1)
    #     print(controller.read_available(myport))
    # for i in range(5):
    #     myport.write((str(controller.pack_rgb(255,255,255)) + "\n").encode(encoding='UTF-8'))
    #     time.sleep(0.1)
    #     print(controller.read_available(myport))
    cmd = "-2\n" + \
        '\n'.join(str(controller.pack_rgb(255 // i, 255 // i, 255 // i))
                  for i in range(1, 11))
    for i in range(10):
        myport.write(cmd.encode(encoding='UTF-8'))
        time.sleep(0.2)
if __name__ == '__main__':
    main()
