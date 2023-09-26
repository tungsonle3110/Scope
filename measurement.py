import color
import time
import os
import canopen.sdo.exceptions
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from ttkwidgets.autocomplete import AutocompleteCombobox
try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk


class Measurement:
    def __init__(self, notebook, co):
        self.co = co
        self.measurement = Frame(notebook)
        self.measurement.pack(fill=BOTH, expand=1)
        notebook.add(self.measurement, text="Measurement")
        self.side_frame = Frame(self.measurement, width=150)
        self.side_frame.pack(side=LEFT, fill=BOTH, expand=0)
        self.main_frame = Frame(self.measurement)
        self.main_frame.pack(side=LEFT, fill=BOTH, expand=1)

        self.data_type = None
        self.data_type_dict = {0x0001: "BOOLEAN", 0x0002: "INTEGER8", 0x0003: "INTEGER16", 0x0010: "INTEGER24",
                               0x0004: "INTEGER32", 0x0012: "INTEGER40", 0x0013: "INTEGER48", 0x0014: "INTEGER56",
                               0x0015: "INTEGER64", 0x0005: "UNSIGNED8", 0x0006: "UNSIGNED16", 0x0016: "UNSIGNED24",
                               0x0007: "UNSIGNED32", 0x0018: "UNSIGNED40", 0x0019: "UNSIGNED48", 0x001A: "UNSIGNED56",
                               0x001B: "UNSIGNED64", 0x0008: "REAL32", 0x0011: "REAL64", 0x000A: "OCTET_STRING",
                               0x000B: "UNICODE_STRING", 0x0009: "VISIBLE_STRING", 0x000C: "TIME_OF_DAY",
                               0x000D: "TIME_DIFFERENCE", 0x000F: "DOMAIN"}

        try:  # offline
            self.scope_objects = self.co.get_eds_content()
            self.scope_objects_name = list(self.scope_objects.keys())
            self.scope_objects_parameter = list(self.scope_objects.values())
        except AttributeError:
            self.scope_objects = None
            self.scope_objects_name = None
            self.scope_objects_parameter = None

        # Control
        self.control = StringVar()
        self.control_frame = LabelFrame(self.side_frame, text="Control")
        self.control_frame.pack(fill=X, expand=0)
        self.run = Radiobutton(self.control_frame, text="⏩", variable=self.control, value="run", indicator=0,
                               width=1, command=self.start)
        self.run.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.pause = Radiobutton(self.control_frame, text="⏸", variable=self.control, value="pause", indicator=0,
                                 width=1, command=self.stop)
        self.pause.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.open_file_button = Button(self.control_frame, text="🗁", width=1, command=self.open_file)
        self.open_file_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.save_file_button = Button(self.control_frame, text="🖫", width=1, command=self.save_file)
        self.save_file_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        # Show
        self.show_value = StringVar()
        self.show_value.set("total")
        self.txt_file = ""
        self.show_frame = LabelFrame(self.side_frame, text="Show")
        self.show_frame.pack(fill=X, expand=0)
        self.show_type_frame = Frame(self.show_frame)
        self.show_type_frame.pack(fill=X, expand=0)
        self.total = Radiobutton(self.show_type_frame, text="Total", variable=self.show_value, value="total", width=1,
                                 indicator=0, command=lambda: self.show(self.show_value.get()))
        self.total.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.part = Radiobutton(self.show_type_frame, text="Data(.txt)", variable=self.show_value, value="part",
                                width=1, indicator=0, command=lambda: self.show(self.show_value.get()))
        self.part.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        # Parameter
        self.parameter_frame = LabelFrame(self.side_frame, text="Parameter")
        self.parameter_frame.pack(fill=BOTH, expand=0, padx=2, pady=2)
        self.value_combobox = AutocompleteCombobox(self.parameter_frame, width=25)
        self.value_combobox.pack(fill=X, expand=0, padx=2, pady=2)
        try:  # offline
            self.value_combobox["completevalues"] = self.scope_objects_name
        except TypeError:
            pass
        self.set_entry = Entry(self.parameter_frame)
        self.set_entry.pack(fill=X, expand=0, padx=2, pady=2)
        self.set_entry.bind('<Return>',
                            lambda event: self.set_value(float(self.set_entry.get()), self.value_combobox.get()))
        self.set_button = Button(self.parameter_frame, text="Set",
                                 command=lambda: self.set_value(float(self.set_entry.get()), self.value_combobox.get()))
        self.set_button.pack(fill=X, expand=0, padx=2, pady=2)

        # Motor Control
        self.motor_control_frame = LabelFrame(self.side_frame, text="Motor Control")
        self.motor_control_frame.pack(fill=X, expand=0)
        self.app_start_value = StringVar()
        self.app_start_frame = LabelFrame(self.motor_control_frame, text="App Start")
        self.app_start_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.app_start_on = Radiobutton(self.app_start_frame, text="ON", variable=self.app_start_value, value="on",
                                        width=1, indicator=0, command=self.app_start)
        self.app_start_on.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.app_start_off = Radiobutton(self.app_start_frame, text="OFF", variable=self.app_start_value, value="off",
                                         width=1, indicator=0, command=self.app_start)
        self.app_start_off.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        self.mode_value = StringVar()
        self.mode_frame = LabelFrame(self.motor_control_frame, text="Mode")
        self.mode_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.torque = Radiobutton(self.mode_frame, text="Torque", variable=self.mode_value, value="torque",
                                  width=1, indicator=0, command=self.mode)
        self.torque.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.current = Radiobutton(self.mode_frame, text="Current", variable=self.mode_value, value="current",
                                   width=1, indicator=0, command=self.mode)
        self.current.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.voltage = Radiobutton(self.mode_frame, text="Voltage", variable=self.mode_value, value="voltage",
                                   width=1, indicator=0, command=self.mode)
        self.voltage.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        self.trq_ref_frame = Frame(self.motor_control_frame)
        self.trq_ref_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.trq_ref_button = Button(self.trq_ref_frame, text="trq ref", width=1, command=self.set_trq_ref)
        self.trq_ref_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.trq_ref_entry = Entry(self.trq_ref_frame, width=1)
        self.trq_ref_entry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.trq_ref_entry.bind('<Return>', lambda event: self.set_trq_ref())

        self.q_ref_frame = Frame(self.motor_control_frame)
        self.q_ref_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.q_ref_button = Button(self.q_ref_frame, text="q ref", width=1, command=self.set_q_ref)
        self.q_ref_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.q_ref_entry = Entry(self.q_ref_frame, width=1)
        self.q_ref_entry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.q_ref_entry.bind('<Return>', lambda event: self.set_q_ref())

        self.d_ref_frame = Frame(self.motor_control_frame)
        self.d_ref_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.d_ref_button = Button(self.d_ref_frame, text="d ref", width=1, command=self.set_d_ref)
        self.d_ref_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.d_ref_entry = Entry(self.d_ref_frame, width=1)
        self.d_ref_entry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.d_ref_entry.bind('<Return>', lambda event: self.set_d_ref())

        self.degree_frame = Frame(self.motor_control_frame)
        self.degree_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.degree_button = Button(self.degree_frame, text="Degree", width=1, command=self.set_degree)
        self.degree_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.degree_entry = Entry(self.degree_frame, width=1)
        self.degree_entry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.degree_entry.bind('<Return>', lambda event: self.set_degree())

        self.trq_ref_button["state"] = DISABLED
        self.trq_ref_entry["state"] = DISABLED
        self.q_ref_button["state"] = DISABLED
        self.q_ref_entry["state"] = DISABLED
        self.d_ref_button["state"] = DISABLED
        self.d_ref_entry["state"] = DISABLED

        # Calibration
        self.calibration_frame = LabelFrame(self.side_frame, text="Calibration")
        self.calibration_frame.pack(fill=X, expand=0)
        self.command_frame = Frame(self.calibration_frame)
        self.command_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.command_button = Button(self.command_frame, text="Command", width=1, command=self.set_command)
        self.command_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.command_entry = Entry(self.command_frame, width=1)
        self.command_entry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.command_entry.bind('<Return>', lambda event: self.set_command())
        self.load_frame = Frame(self.calibration_frame)
        self.load_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.load_button = Button(self.load_frame, text="Load", width=1, command=self.set_load)
        self.load_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.load_entry = Entry(self.load_frame, width=1)
        self.load_entry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.load_entry.bind('<Return>', lambda event: self.set_load())

        # Tree
        self.tree_scroll = Scrollbar(self.main_frame)
        self.tree_scroll.pack(side=RIGHT, fill=Y)
        self.tree = ttk.Treeview(self.main_frame, yscrollcommand=self.tree_scroll.set, selectmode="extended")
        self.tree.pack(fill=BOTH, expand=1)
        self.tree_scroll.config(command=self.tree.yview)
        self.tree["columns"] = ("HexIndex", "DataType", "AccessType", "Name", "Value")
        self.tree.column("#0", width=70, minwidth=45, stretch=NO)
        self.tree.column("HexIndex", width=70, minwidth=45, stretch=NO)
        self.tree.column("DataType", width=100, minwidth=45, stretch=NO)
        self.tree.column("AccessType", width=70, minwidth=45, stretch=NO)
        self.tree.column("Name", width=230, minwidth=200, stretch=NO)
        self.tree.column("Value", width=150, minwidth=130)
        self.tree.heading("#0", text="Index", anchor=W)
        self.tree.heading("HexIndex", text="HexIndex", anchor=W)
        self.tree.heading("DataType", text="DataType", anchor=W)
        self.tree.heading("AccessType", text="AccessType", anchor=W)
        self.tree.heading("Name", text="Name", anchor=W)
        self.tree.heading("Value", text="Value", anchor=W)
        try:  # offline
            for index in range(len(self.scope_objects_name)):
                self.tree.insert(parent="", index="end", iid=index, text=f"{index}",
                                 values=("-", "-", "-", self.scope_objects_name[index], "-"))
        except TypeError:
            pass

    def update(self):
        if self.control.get() == "run":
            for index in range(len(self.scope_objects_name)):
                try:
                    try:
                        self.data_type = self.data_type_dict[self.scope_objects_parameter[index]['DataType']]
                    except KeyError:
                        self.data_type = "0x{:04x}".format(self.scope_objects_parameter[index]['DataType'])
                    if "buffer" in self.scope_objects_name[index]:
                        self.tree.item(index,
                                       values=(
                                           f"{format(self.scope_objects_parameter[index]['index'], 'x').upper()}",
                                           self.data_type, self.scope_objects_parameter[index]['AccessType'],
                                           self.scope_objects_name[index], "Byte Array"))
                    else:
                        self.tree.item(index,
                                       values=(
                                           f"{format(self.scope_objects_parameter[index]['index'], 'x').upper()}",
                                           self.data_type, self.scope_objects_parameter[index]['AccessType'],
                                           self.scope_objects_name[index],
                                           self.co.get_sdo(self.scope_objects_name[index])))
                except canopen.sdo.exceptions.SdoAbortedError:  # Code 0x06020000, Object does not exist
                    self.tree.item(index, values=("-", "-", "-", self.scope_objects_name[index], "not exist"))
                except KeyError:  # Object was not found in Object Dictionary
                    self.tree.item(index, values=("-", "-", "-", self.scope_objects_name[index], "not found"))
        else:
            pass

    def start(self):
        self.control.set("run")

    def stop(self):
        self.control.set("pause")

    def open_file(self):
        file_open = filedialog.askopenfilename(filetypes=[("Text files", ".txt"), ("All files", ".*")])
        if file_open != "":
            self.txt_file = file_open
            self.part["text"] = os.path.basename(file_open)
            self.scope_objects_name = []
            self.scope_objects_parameter = []
            if self.show_value.get() == "part":
                with open(self.txt_file, "r") as f:
                    for line in f.readlines()[1:]:
                        data = line.strip().split("\t")
                        if data[0] == "1":
                            try:
                                self.scope_objects_name.append(data[1])
                            except IndexError:
                                self.scope_objects_name.append("")
                            try:
                                self.scope_objects_parameter.append(self.scope_objects[self.scope_objects_name[-1]])
                            except KeyError:
                                self.scope_objects_parameter.append({"index": 0, "DataType": 0, "AccessType": "-"})
                            except TypeError:
                                self.scope_objects_parameter.append({"index": 0, "DataType": 0, "AccessType": "-"})
                        else:
                            pass
                self.tree.delete(*self.tree.get_children())
                for index in range(len(self.scope_objects_name)):
                    self.tree.insert(parent="", index="end", iid=index, text=f"{index}",
                                     values=("-", "-", "-", self.scope_objects_name[index], "-"))

    def save_file(self):
        file_save = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", ".txt"),
                                                                                     ("All files", ".*")])
        scope_objects_name = list(self.scope_objects.keys())
        if file_save != "":
            with open(file_save, "w") as f:
                f.write(f"Show\t")
                f.write(f"ParameterName\t")
                f.write("\n")
                for index in range(len(scope_objects_name)):
                    if scope_objects_name[index] in self.scope_objects_name:
                        f.write("1\t")
                    else:
                        f.write("0\t")
                    f.write(scope_objects_name[index])
                    f.write("\n")
            f.close()

    def show(self, show_value):
        if show_value == "total":
            self.scope_objects_name = list(self.scope_objects.keys())
            self.scope_objects_parameter = list(self.scope_objects.values())
        elif show_value == "part":
            self.scope_objects_name = []
            self.scope_objects_parameter = []
            try:
                with open(self.txt_file, "r") as f:
                    for line in f:
                        data = line.strip().split("\t")
                        if data[0] == "1":
                            self.scope_objects_name.append(data[1])
                            try:
                                self.scope_objects_parameter.append(self.scope_objects[self.scope_objects_name[-1]])
                            except KeyError or TypeError:
                                self.scope_objects_parameter.append({"index": 0, "DataType": 0, "AccessType": "-"})
                        else:
                            pass
            except FileNotFoundError:
                self.open_file()
                if self.control.get() == "run" and self.txt_file == "":
                    self.show_value.set("total")
                    self.scope_objects_name = list(self.scope_objects.keys())
                    self.scope_objects_parameter = list(self.scope_objects.values())
        self.tree.delete(*self.tree.get_children())
        for index in range(len(self.scope_objects_name)):
            self.tree.insert(parent="", index="end", iid=index, text=f"{index}",
                             values=("-", "-", "-", self.scope_objects_name[index], "-"))

    def set_value(self, name, value):
        self.co.set_sdo(name, value)

    def app_start(self):
        if self.app_start_value.get() == "on":
            self.co.set_sdo(1, "app_start")
        elif self.app_start_value.get() == "off":
            self.torque.deselect()
            self.current.deselect()
            self.voltage.deselect()
            self.torque["state"] = NORMAL
            self.co.set_sdo(0, "app_start")
            self.co.set_sdo(0, "end_of_line_flag")

    def mode(self):
        if self.mode_value.get() == "torque":
            self.trq_ref_button["state"] = NORMAL
            self.trq_ref_entry["state"] = NORMAL
            self.q_ref_button["state"] = DISABLED
            self.q_ref_entry["state"] = DISABLED
            self.d_ref_button["state"] = DISABLED
            self.d_ref_entry["state"] = DISABLED
            self.co.set_sdo(2, "end_of_line_flag")
        elif self.mode_value.get() == "current":
            self.torque["state"] = DISABLED
            self.trq_ref_button["state"] = DISABLED
            self.trq_ref_entry["state"] = DISABLED
            self.q_ref_button["state"] = NORMAL
            self.q_ref_entry["state"] = NORMAL
            self.d_ref_button["state"] = NORMAL
            self.d_ref_entry["state"] = NORMAL
            self.q_ref_entry.delete(0, END)
            self.d_ref_entry.delete(0, END)
            self.co.set_sdo(0, "foc_q_ref_man")
            self.co.set_sdo(0, "foc_d_ref_man")
            time.sleep(0.5)
            self.co.set_sdo(11, "end_of_line_flag")
            self.q_ref_entry.insert(END, f"{self.co.get_sdo('foc_q_ref_man')}")
            self.d_ref_entry.insert(END, f"{self.co.get_sdo('foc_d_ref_man')}")
        elif self.mode_value.get() == "voltage":
            self.torque["state"] = DISABLED
            self.trq_ref_button["state"] = DISABLED
            self.trq_ref_entry["state"] = DISABLED
            self.q_ref_button["state"] = NORMAL
            self.q_ref_entry["state"] = NORMAL
            self.d_ref_button["state"] = NORMAL
            self.d_ref_entry["state"] = NORMAL
            self.q_ref_entry.delete(0, END)
            self.d_ref_entry.delete(0, END)
            self.co.set_sdo(0, "foc_q_ref_man")
            self.co.set_sdo(0, "foc_d_ref_man")
            time.sleep(0.5)
            self.co.set_sdo(10, "end_of_line_flag")
            self.q_ref_entry.insert(END, f"{self.co.get_sdo('foc_q_ref_man')}")
            self.d_ref_entry.insert(END, f"{self.co.get_sdo('foc_d_ref_man')}")

    def set_trq_ref(self):
        try:
            self.co.set_sdo(float(self.trq_ref_entry.get()), "motor_control_trq_ref")
        except ValueError:
            self.trq_ref_entry.delete(0, END)
            self.trq_ref_entry.insert(END, f"{self.co.get_sdo('motor_control_trq_ref')}")

    def set_q_ref(self):
        try:
            self.co.set_sdo(float(self.q_ref_entry.get()), "foc_q_ref_man")
        except ValueError:
            self.q_ref_entry.delete(0, END)
            self.q_ref_entry.insert(END, f"{self.co.get_sdo('foc_q_ref_man')}")

    def set_d_ref(self):
        try:
            self.co.set_sdo(float(self.d_ref_entry.get()), "foc_d_ref_man")
        except ValueError:
            self.d_ref_entry.delete(0, END)
            self.d_ref_entry.insert(END, f"{self.co.get_sdo('foc_d_ref_man')}")

    def set_degree(self):
        try:
            self.co.set_sdo(float(self.degree_entry.get()), "foc_deg_phi_offset")
        except ValueError:
            self.degree_entry.delete(0, END)
            self.degree_entry.insert(END, f"{self.co.get_sdo('foc_deg_phi_offset')}")

    def set_command(self):
        try:
            self.co.set_sdo(int(self.command_entry.get()), "torque_sensor_calib_command")
        except ValueError:
            self.command_entry.delete(0, END)
            self.command_entry.insert(END, f"{self.co.get_sdo('torque_sensor_calib_command')}")

    def set_load(self):
        try:
            self.co.set_sdo(int(self.load_entry.get()), "torque_sensor_calib_value")
        except ValueError:
            self.load_entry.delete(0, END)
            self.load_entry.insert(END, f"{self.co.get_sdo('torque_sensor_calib_value')}")
