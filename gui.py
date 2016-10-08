#!/usr/bin/env python3
import tkinter as tk
import tkinter.ttk as ttk
import sys
import threading
if sys.platform in ["win32"]:
    import multiprocess as multiprocessing
else:
    import multiprocessing
import controller
from collections import namedtuple
import queue
import SerialDetector
import serial
import time
import textwrap

Message = namedtuple("Message", ["descriptor", "text",  "data"])


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
                del ScreenReader
                ScreenReader = m.data
            if m.descriptor == "terminate":
                return
        if not ScreenReader is None:
            if not paused:
                if myalarm.alarm():
                    # print("stepping")
                    ti = time.time()
                    myalarm.reset()
                    ScreenReader.step()
                    tf = time.time()
                    loop_time = tf - ti
                    loop_rate = 1 / (tf - ti)
                    error = (loop_rate - rate) / rate
                    outqueue.put(
                        Message(
                            "status",
                            "Frame processed",
                            "LoopT:{:.3f}, 1/T:{:.2f}, Error:{:.2f}, CurRate:{}".format(
                                loop_time, loop_rate, error, rate
                            )
                        )
                    )
                    time.sleep(1 / rate)
        else:
            time.sleep(0.2)


class ScreenToRGBApp(ttk.Frame):

    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        # fixed window size
        master.resizable(width=False, height=False)
        # specify parent widget
        self.root = master
        self.create_widgets()
        self.outbox = queue.Queue()
        self.inbox = queue.Queue()
        self.myscreener = None
        self.worker = threading.Thread(
            target=ScreenWorker, args=(self.outbox, self.inbox))
        self.pack()
        self.after(1, self.update)
        self.paused = True
        self.stop_callback()
        self.worker.start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.frame_a = ttk.Frame()
        self.frame_b = ttk.Frame()
        self.status1 = tk.StringVar()
        self.status2 = tk.StringVar()

        self.status_label1 = ttk.Label(
            self.frame_b, textvariable=self.status1, width=80)
        self.status_label2 = ttk.Label(
            self.frame_b, textvariable=self.status2, width=80)
        self.btn_start = ttk.Button(
            self.frame_a, text="start", command=self.start_callback)
        self.btn_stop = ttk.Button(
            self.frame_a, text="stop", command=self.stop_callback)

        self.serial_list = tk.Listbox(self,)
        self.console_area = tk.Text(self)
        self.frame_a.pack()
        self.frame_b.pack()
        self.btn_start.pack(side="left")
        self.btn_stop.pack(side="left")
        self.status_label1.pack()
        self.status_label2.pack(side="top")
        self.serial_list.pack()
        self.console_area.pack(fill="both")

    def update(self):
        # self.status1.set("test{}".format(self.count))
        try:
            while not self.inbox.empty():
                m = self.inbox.get(False)
                # "1.0" means line 1 col 0
                self.console_area.insert("1.0",m.data + "\n")
                self.status2.set(m.data)
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
            self.outbox.put(Message(descriptor="new_worker",
                                    data=new_controller, text="new worker"))
            self.outbox.put(Message("play", None, None))
            self.paused = False
            self.status1.set('\n'.join(textwrap.wrap(repr(new_controller), 70)))
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
        time.sleep(0.2)
        self.refresh_port_list()

    def on_closing(self):
        self.outbox.put(Message(descriptor="terminate", text=None, data=None))
        self.root.destroy()


def main():
    root = tk.Tk()
    root.style = ttk.Style()
    root.style.theme_use("clam")
    app = ScreenToRGBApp(master=root, )
    root.geometry("400x500")
    app.mainloop()

if __name__ == '__main__':
    main()
