from ctypes import windll
from controller import unpack_rgb
import controller
import timeit

dc = windll.user32.GetDC(0)
def getpixel(x, y):
    return windll.gdi32.GetPixel(dc, x, y)

def sample_screen(divisor,width, height):
    cs = []
    for x in range(0, width, width // divisor):
        for y in range(0, height, height // divisor):
            cs.append(getpixel(x,y))
    c = sum(cs)//len(cs)
    return unpack_rgb(c)
	

def main():
    # print(unpack_rgb(getpixel(0, 0)))
    # divisor = 10
    # WIDTH = 1920
    # HEIGHT = 1080
    # for i in range(2):
	   #  c = sample_screen(10,WIDTH,HEIGHT)
    # print(c)
    print(timeit.timeit("ImageGrab.grab()",setup="from PIL import ImageGrab",number=500))
    print(timeit.timeit("controller.main(testing=True,port='COM6')",setup="import controller",number=10))
if __name__ == '__main__':
    main()
