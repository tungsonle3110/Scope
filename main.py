import amprio_canopen
import online_mode
import trigger_mode
import measurement
import end_of_line
import can.interfaces.pcan.pcan
import canopen.sdo.exceptions
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk


class MainWindow:
    def __init__(self):
        try:  # offline
            self.co = amprio_canopen.ScopeCanOpen("DriveUnit.eds")
        except can.interfaces.pcan.pcan.PcanError as e:
            self.co = None
            messagebox.showerror(title="Error", message=f"can.interfaces.pcan.pcan.PcanError:\n{e}\n"
                                                        "Please check error again and restart the application tool")
        except FileNotFoundError as e:
            self.co = None
            messagebox.showerror(title="Error", message=f"FileNotFoundError:\n{e}\n"
                                                        "Please check file again or setup device driver")

        self.root = Tk()
        self.root.title("Amprio Scope 2.0")
        self.root.iconbitmap('amprio_ngz_1.ico')
        self.root.geometry("+0+0")

        self.work_frame = Frame(self.root)
        self.work_frame.pack(fill=BOTH, expand=1)

        self.notebook = ttk.Notebook(self.work_frame)
        self.notebook.pack(fill=BOTH, expand=1)

        self.online_mode = online_mode.OnlineMode(self.notebook, self.co)
        self.trigger_mode = trigger_mode.TriggerMode(self.notebook, self.co)
        self.measurement = measurement.Measurement(self.notebook, self.co)
        self.end_of_line = end_of_line.EndOfLine(self.notebook)

    def update(self):
        try:
            if self.notebook.index(self.notebook.select()) == 2:
                self.measurement.update()
            self.trigger_mode.update()
        except canopen.sdo.exceptions.SdoCommunicationError as e:  # No SDO
            print(f"canopen.sdo.exceptions.SdoCommunicationError: {e}")
        except canopen.sdo.exceptions.SdoAbortedError as e:  # Bootloader
            print(f"canopen.sdo.exceptions.SdoAbortedError: {e}")
        except AttributeError:
            print("offline")
        self.root.after(500, self.update)

    def mainloop(self):
        self.root.after(500, self.update)
        self.root.mainloop()


if __name__ == '__main__':
    window = MainWindow()
    window.mainloop()
