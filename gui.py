#!/usr/bin/env python3
import tkinter as tk
import tkinter.ttk as ttk
import sys
import multiprocessing
import controller
from collections import namedtuple
import queue
import SerialDetector
import serial
import time
import textwrap

# class Message():
#     def __init__(self,descriptor=None,text=None,data=None):
#         self.descriptor = descriptor
#         self.text = text
#         self.data = data
Message = namedtuple("Message", ["descriptor", "text", "data"])


def ScreenWorker(inqueue=None, outqueue=None):
    target_rate = 16
    rate = target_rate
    myalarm = controller.Alarm(1 / target_rate)
    paused = True
    ScreenReader = None
    while True:
        while not inqueue.empty():
            m = inqueue.get()
            print("Worker received:", m)
            if m.descriptor == "pause":
                paused = True
                # print("pausing")
                try:
                    ScreenReader.terminate()
                except AttributeError:
                    pass
            if m.descriptor == "play":
                paused = False
            if m.descriptor == "new_worker":
                if ScreenReader:
                    ScreenReader.terminate()
                time.sleep(0.1)
                ScreenReader = controller.ScreenToRGB(*m.data[0], **m.data[1])
            if m.descriptor == "terminate":
                return
        if not ScreenReader is None:
            if not paused:
                if myalarm.alarm():
                    myalarm.reset()
                    # print("stepping")
                    ti = time.time()
                    try:
                        ScreenReader.step()
                        tf = time.time()
                        loop_time = tf - ti
                        loop_rate = 1 / (tf - ti)
                        error = (loop_rate - rate) / rate
                        # if error > 0.1:
                        #     rate += 1
                        # elif error < -0.1:
                        #     rate -= 1
                        outqueue.put(
                            Message(
                                "status",
                                "Frame processed",
                                "LoopT:{:.3f}, 1/T:{:.2f}, Error:{:.2f}, CurRate:{}".format(
                                    loop_time, loop_rate, error, rate
                                )
                            ),
                            False
                        )
                        time.sleep(1 / rate)
                    except IndexError:
                        outqueue.put(Message("error", "INVALID MAPPING!", ""))
        else:
            pass


class ScreenToRGBApp(ttk.Frame):

    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        # fixed window size
        master.resizable(width=False, height=False)
        # specify parent widget
        self.root = master
        self.outbox = multiprocessing.Queue()
        self.inbox = multiprocessing.Queue()
        self.n_slices = tk.StringVar()
        self.user_slice_map = tk.StringVar()
        self.user_color_mods = tk.StringVar()
        self.user_color_mods.set("1 1 1")
        self.user_color_pow = tk.StringVar()
        self.myscreener = None

        self.worker = multiprocessing.Process(
            target=ScreenWorker, args=(self.outbox, self.inbox))
        self.worker.start()
        self.create_widgets()
        self.pack()
        self.paused = True
        self.stop_callback()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(1, self.update)

        # load configs and create files if necessary
        l = list(range(10))
        self.slice_map = l[::-1] + l
        self.user_slice_map.set(load_or_create(
            "config/mapping.txt", ' '.join(map(str, self.slice_map))))
        self.user_color_mods.set(load_or_create(
            "config/color_curves.txt", "1 1 1"))
        self.n_slices.set(load_or_create("config/screen_slices.txt", "10"))
        self.user_color_pow.set(load_or_create("config/color_exponent.txt","2"))

    def create_widgets(self):
        self.frame_top = ttk.Frame()
        self.frame_bot = ttk.Frame()
        self.config_frame = ttk.Frame()
        self.config_frame_right = ttk.Frame(self.config_frame)
        self.config_frame_left = ttk.Frame(self.config_frame)
        self.status1 = tk.StringVar()
        self.status2 = tk.StringVar()

        self.status_label1 = ttk.Label(
            self.frame_bot, textvariable=self.status1, width=80)
        self.status_label2 = ttk.Label(
            self.frame_bot, textvariable=self.status2, width=80)
        self.btn_start = ttk.Button(
            self.frame_top, text="start", command=self.start_callback)
        self.btn_stop = ttk.Button(
            self.frame_top, text="stop", command=self.stop_callback)
        self.btn_restart = ttk.Button(
            self.frame_top, text="restart", command=self.restart_callback)

        self.serial_list = tk.Listbox(self.config_frame_left)
        self.slices_entry = ttk.Entry(
            self.config_frame_right, textvariable=self.n_slices)
        self.slice_map_entry = ttk.Entry(
            self.config_frame_right, textvariable=self.user_slice_map)
        self.color_pow_entry = ttk.Entry(
            self.config_frame_right, textvariable=self.user_color_pow)
        self.color_mod_entry = ttk.Entry(
            self.config_frame_right, textvariable=self.user_color_mods)

        self.console_area = tk.Text(self)
        self.frame_top.pack(expand=0)
        self.frame_bot.pack()

        self.config_frame.pack(fill="both")
        self.config_frame_left.pack(side="left")
        ttk.Label(self.config_frame_left,
                  text="Port selection").pack(side="top")
        self.config_frame_right.pack(side="right", expand=1, fill="both")
        ttk.Label(self.config_frame_right,
                  text="num. screen slices").pack(side="top")
        self.serial_list.pack(side="bottom")
        self.slices_entry.pack(side="top", fill="both")
        ttk.Label(self.config_frame_right,
                  text="slice mapping").pack(side="top")
        self.slice_map_entry.pack(side="top", fill="both")
        ttk.Label(self.config_frame_right, text="Color curve exponent").pack()
        self.color_pow_entry.pack()
        ttk.Label(self.config_frame_right,
                  text="RGB color curves").pack(side="top")
        self.color_mod_entry.pack()

        self.btn_start.pack(side="left")
        self.btn_stop.pack(side="left")
        # self.btn_restart.pack(side="left")
        self.status_label1.pack()
        self.status_label2.pack(side="top")
        self.console_area.pack(fill="both")

    def update(self):
        # self.status1.set("test{}".format(self.count))
        try:
            while not self.inbox.empty():
                m = self.inbox.get(False)
                # "1.0" means line 1 col 0
                self.console_area.insert("1.0", ' '.join(
                    [m.descriptor, m.text, m.data]) + "\n")
                self.status2.set(m.data)
                # print("GUI received:",m)
        except queue.Empty:
            pass
        # clear serial list

        self.after(1000, self.update)
        # print(self.con)

    def start_callback(self):
        try:
            selected_port = self.serial_list.get(
                self.serial_list.curselection()[0])
            # construct a new RGB controller to give to the worker
            new_controller = controller.ScreenToRGB(port=selected_port)
            kwargs = {
                "port": selected_port,
                "n_slices": int(self.n_slices.get()),
                "slice_mapping": list(map(int, self.user_slice_map.get().split())),
                "color_mods": tuple(map(float, self.user_color_mods.get().split(' '))),
                "color_pow": float(self.user_color_pow.get())
            }
            self.outbox.put(Message(descriptor="new_worker",
                                    data=(tuple(), kwargs), text="message to new worker with args"))
            self.outbox.put(Message("play", None, None))
            self.worker = multiprocessing.Process(
                target=ScreenWorker, args=(self.outbox, self.inbox))
            self.worker.start()

            self.paused = False
            self.status1.set(
                '\n'.join(textwrap.wrap(repr(new_controller), 70)))
        except IndexError:
            self.status1.set("Please select a port")
        except serial.serialutil.SerialException as e:
            self.status1.set("Serial error: {}".format(e))

    def refresh_port_list(self):
        for _ in range(self.serial_list.size()):
            self.serial_list.delete(0)
        serials = SerialDetector.serial_ports()

        for index, item in enumerate(serials):
            self.serial_list.insert(index, item)

    def stop_callback(self):
        self.outbox.put(Message(descriptor="pause", text=None, data=None))
        self.status2.set("")
        self.paused = True
        self.status1.set("Stopped")
        self.worker.terminate()

        self.refresh_port_list()

    def restart_callback(self):
        self.stop_callback()
        time.sleep(1)
        self.start_callback()

    def on_closing(self):
        self.outbox.put(Message(descriptor="terminate", text=None, data=None))
        self.root.destroy()


def load_or_create(fname, default=""):
    try:
        with open(fname) as f:
            return f.read()
    except FileNotFoundError:
        with open(fname, 'w') as f:
            f.write(default)
        return default


def main():
    root = tk.Tk()
    root.style = ttk.Style()
    root.style.theme_use("clam")
    app = ScreenToRGBApp(master=root, )
    root.geometry("400x500")
    app.mainloop()

if __name__ == '__main__':
    main()
