#!/usr/bin/env python3
import tkinter as tk
import tkinter.ttk as ttk
import threading
import controller
from collections import namedtuple
import queue
import SerialDetector
import serial
import time
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
                    time.sleep(1/rate)
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
        self.status_text = tk.StringVar()
        self.status_label = ttk.Label(
            self, textvariable=self.status_text, width=80)
        self.btn_start = ttk.Button(
            self, text="start", command=self.start_callback)
        self.btn_stop = ttk.Button(
            self, text="stop", command=self.stop_callback)
        self.serial_list = tk.Listbox(self,)
        self.console_area = tk.Text(self)

        self.btn_start.pack()
        self.btn_stop.pack()
        self.status_label.pack()
        self.serial_list.pack()
        self.console_area.pack()

    def update(self):
        # self.status_text.set("test{}".format(self.count))
        try:
            while not self.inbox.empty():
                self.status_text.set(self.inbox.get(False).data)
        except queue.Empty:
            pass
        # clear serial list

        self.after(500, self.update)
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
        except IndexError:
            self.status_text.set("Please select a port")
        except serial.serialutil.SerialException as e:
            self.status_text.set("Serial error: {}".format(e))

    def refresh_port_list(self):
        for _ in range(self.serial_list.size()):
            self.serial_list.delete(0)
        serials = SerialDetector.serial_ports()

        for index, item in enumerate(serials):
            self.serial_list.insert(index, item)
        
    def stop_callback(self):
        self.outbox.put(Message(descriptor="pause", text=None, data=None))

            
        self.paused = True
        self.status_text.set("Stopped")
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
    root.geometry("300x500")
    app.mainloop()

if __name__ == '__main__':
    main()
