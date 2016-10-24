import controller
import random
import SerialDetector
import time
import colorsys
def remap(colors):
    return colors[::-1] + colors

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
    cs = [(0,0,0,) for i in range(NUMPIXELS)]
    n = 100
    T = 10
    delta_t = T/n
    while True:
        try:
            for i in range(n):
                cs.pop(0)
                cs.append(tuple(map(lambda t: int(t*255),colorsys.hsv_to_rgb(i/n,1,1))))
                connection.write_frame(cs)
                time.sleep(delta_t)
        except KeyboardInterrupt:
            connection.terminate()
            quit()
if __name__ == '__main__':
    main()
