import trigger_plot
import color
import time
import csv
import os
import struct
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from tkinter import *
from tkinter import filedialog
from ttkwidgets.autocomplete import AutocompleteCombobox
from ttkwidgets.frames import ScrolledFrame

matplotlib.use("TkAgg")
try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk


class TriggerMode:
    def __init__(self, notebook, co):
        self.co = co
        self.trigger_mode = Frame(notebook)
        self.trigger_mode.pack(fill=BOTH, expand=1)
        notebook.add(self.trigger_mode, text="Trigger mode")
        self.side_frame = Frame(self.trigger_mode)
        self.side_frame.pack(side=LEFT, fill=BOTH, expand=0)
        self.main_frame = Frame(self.trigger_mode)
        self.main_frame.pack(side=LEFT, fill=BOTH, expand=1)

        self.cycle_time = 1 / 20000 * 1000

        # Time_divider
        self.time_divider_record = 1

        # Trigger
        self.trigger_value = None

        # Channel
        self.number_of_channel = 4
        self.channel_index = 0
        self.channel_number_frame = []
        self.channel_button = []
        self.channel_checkbutton = []
        self.channel_check = [IntVar() for _ in range(self.number_of_channel)]
        self.channel_combobox = []
        self.value_number_frame = []
        self.value_label_min = []
        self.value_label_max = []
        self.offset_entry = []
        self.offset_value = [0.0 for _ in range(self.number_of_channel)]
        self.scale_entry = []
        self.scale_value = [1.0 for _ in range(self.number_of_channel)]
        self.channel_value = [None for _ in range(self.number_of_channel)]

        # Update
        self.block_data = []
        try:  # offline
            self.scope_objects = self.co.get_eds_content()
            self.scope_objects_name = list(self.scope_objects.keys())
        except AttributeError:
            self.scope_objects = None
            self.scope_objects_name = None

        # Plot
        self.plot_frame = Frame(self.main_frame)
        self.plot_frame.pack(fill=BOTH, expand=1)
        self.fig = plt.Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.trigger_plot = trigger_plot.TriggerPlot(self.ax, self.number_of_channel, self.value_label_min,
                                                     self.value_label_max, self.cycle_time, self.time_divider_record)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame, pack_toolbar=True)
        self.toolbar.update()
        self.fig.canvas.mpl_connect('key_press_event', key_press_handler)
        self.zoomFactory = self.zoom_factory(self.ax, base_scale=1.1)
        self.interactiveLegend = self.interactive_legend(self.ax)

        # Value
        self.value_frame = Frame(self.main_frame, height=50)
        self.value_frame.pack(fill=X, expand=0)

        # Control:
        self.plot_shift = IntVar()
        self.control_frame = LabelFrame(self.side_frame, text="Control")
        self.control_frame.pack(fill=X, expand=0)
        self.run = Button(self.control_frame, text="⏩", width=1, command=self.get_data)
        self.run.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.status = Label(self.control_frame, text="waiting", width=1)
        self.status.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.shift_scale = Scale(self.control_frame, variable=self.plot_shift, from_=0, to=1, label="shift →",
                                 length=50, sliderlength=25, orient=HORIZONTAL, showvalue=0, command=self.shift_plot)
        self.shift_scale.pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
        self.open_file_button = Button(self.control_frame, text="🗁", width=1, command=self.open_file)
        self.open_file_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.save_file_button = Button(self.control_frame, text="🖫", width=1, command=self.save_file)
        self.save_file_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        # Record:
        self.record_check = [IntVar() for _ in range(0, 2)]
        self.record_frame = LabelFrame(self.side_frame, text="Record")
        self.record_frame.pack(fill=X, expand=0)
        self.plot_button = Button(self.record_frame, text="🗁", command=self.plot)
        self.plot_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.record_button = Button(self.record_frame, text="⏺",
                                    command=lambda: self.trigger_plot.record(self.channel_value))
        self.record_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.csv = Checkbutton(self.record_frame, text="CSV .csv", variable=self.record_check[0],
                               offvalue=False, onvalue=True, indicator=2, width=1,
                               command=lambda: self.trigger_plot.check_record(self.record_check))
        self.csv.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.csv.select()
        self.excel = Checkbutton(self.record_frame, text="Excel .xlsx", variable=self.record_check[1],
                                 offvalue=False, onvalue=True, indicator=2, width=1,
                                 command=lambda: self.trigger_plot.check_record(self.record_check))
        self.excel.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.excel.select()

        # Show
        self.show_frame = LabelFrame(self.side_frame, text="Show")
        self.show_frame.pack(fill=X, expand=0)
        self.total = Button(self.show_frame, text="Total", width=1,
                            command=self.trigger_plot.show)
        self.total.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        # Position
        self.position_frame = LabelFrame(self.side_frame, text="Position")
        self.position_frame.pack(fill=X, expand=0)
        self.maxt_frame = Frame(self.position_frame)
        self.maxt_frame.pack(fill=X, expand=0)
        self.x_position_frame = Frame(self.position_frame)
        self.x_position_frame.pack(fill=X, expand=0)
        self.xlim_left_entry = Entry(self.x_position_frame, width=1)
        self.xlim_left_entry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.xlim_left_entry.bind('<Return>', lambda event: self.trigger_plot.zoom_x(float(self.xlim_left_entry.get()),
                                                                                     float(
                                                                                         self.xlim_right_entry.get())))
        self.xlim_right_entry = Entry(self.x_position_frame, width=1)
        self.xlim_right_entry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.xlim_right_entry.bind('<Return>', lambda event: self.trigger_plot.zoom_x(float(self.xlim_left_entry.get()),
                                                                                      float(
                                                                                          self.xlim_right_entry.get())))
        self.zoom_x_button = Button(self.x_position_frame, text="Zoom x", width=1,
                                    command=lambda: self.trigger_plot.zoom_x(float(self.xlim_left_entry.get()),
                                                                             float(self.xlim_right_entry.get())))
        self.zoom_x_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        self.y_position_frame = Frame(self.position_frame)
        self.y_position_frame.pack(fill=X, expand=0)
        self.ylim_left_entry = Entry(self.y_position_frame, width=1)
        self.ylim_left_entry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.ylim_left_entry.bind('<Return>', lambda event: self.trigger_plot.zoom_y(float(self.ylim_left_entry.get()),
                                                                                     float(
                                                                                         self.ylim_right_entry.get())))
        self.ylim_right_entry = Entry(self.y_position_frame, width=1)
        self.ylim_right_entry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.ylim_right_entry.bind('<Return>', lambda event: self.trigger_plot.zoom_y(float(self.ylim_left_entry.get()),
                                                                                      float(
                                                                                          self.ylim_right_entry.get())))
        self.zoom_y_button = Button(self.y_position_frame, text="Zoom y", width=1,
                                    command=lambda: self.trigger_plot.zoom_y(float(self.ylim_left_entry.get()),
                                                                             float(self.ylim_right_entry.get())))
        self.zoom_y_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        # Time_divider
        self.time_divider = IntVar()
        self.time_divider.set(1)
        self.time_divider_frame = Frame(self.side_frame)
        self.time_divider_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.time_divider_label = Label(self.time_divider_frame, text="Time/Div:")
        self.time_divider_label.pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
        self.time_divider_spinbox = Spinbox(self.time_divider_frame, textvariable=self.time_divider, from_=1, to=255,
                                            width=5, increment=1,
                                            command=lambda: self.get_time_divider_value(self.time_divider.get()))
        self.time_divider_spinbox.pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
        self.time_divider_unit_label = Label(self.time_divider_frame, text="ms")
        self.time_divider_unit_label.pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
        self.time_divider_scale = Scale(self.time_divider_frame, variable=self.time_divider, from_=1, to=255,
                                        orient=HORIZONTAL, showvalue=0, command=self.get_time_divider_value)
        self.time_divider_scale.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.time_divider_spinbox.bind('<Return>', lambda event: self.get_time_divider_value(self.time_divider.get()))

        # Trigger
        self.trigger_frame = LabelFrame(self.side_frame, text="Trigger")
        self.trigger_frame.pack(fill=X, expand=0)

        # Type
        self.trigger_type = StringVar()
        self.trigger_type.set("flash")
        self.trigger_type_frame = Frame(self.trigger_frame)
        self.trigger_type_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.trigger_type_label = Label(self.trigger_type_frame, text="Type:", width=7, anchor=W)
        self.trigger_type_label.pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
        self.single = Radiobutton(self.trigger_type_frame, text="Flash ↯", variable=self.trigger_type, value="flash",
                                  indicator=0, command=self.get_trigger_type_value)
        self.single.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.rising = Radiobutton(self.trigger_type_frame, text="Rising ⥌", variable=self.trigger_type,
                                  value="rising", indicator=0, command=self.get_trigger_type_value)
        self.rising.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.falling = Radiobutton(self.trigger_type_frame, text="Falling ⥍", variable=self.trigger_type,
                                   value="falling", indicator=0, command=self.get_trigger_type_value)
        self.falling.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        # Position
        self.position = IntVar()
        self.position.set(512)
        self.axv_position = list(range(0, 512))
        self.axv_position.reverse()
        self.axv_line = self.ax.axvline(
            x=round(self.axv_position[self.position.get() - 1] * self.cycle_time * float(self.time_divider.get()), 2),
            linestyle="dotted")
        self.trigger_position_frame = Frame(self.trigger_frame)
        self.trigger_position_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.trigger_position_label = Label(self.trigger_position_frame, text="Position:")
        self.trigger_position_label.pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
        self.trigger_position_spinbox = Spinbox(self.trigger_position_frame, textvariable=self.position, from_=1,
                                                to=512,
                                                width=5, increment=1,
                                                command=lambda: self.get_trigger_position_value(self.position.get()))
        self.trigger_position_spinbox.pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
        self.trigger_position_unit_label = Label(self.trigger_position_frame,
                                                 text=f"{round(self.axv_position[self.position.get() - 1] * self.cycle_time * float(self.time_divider.get()), 2)}ms",
                                                 width=10)
        self.trigger_position_unit_label.pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
        self.trigger_position_scale = Scale(self.trigger_position_frame, variable=self.position, from_=512, to=1,
                                            orient=HORIZONTAL, showvalue=0, command=self.get_trigger_position_value)
        self.trigger_position_scale.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.trigger_position_spinbox.bind('<Return>',
                                           lambda event: self.get_trigger_position_value(self.position.get()))

        # Level
        self.trigger_level_frame = Frame(self.trigger_frame)
        self.trigger_level_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.trigger_level_button = Button(self.trigger_level_frame, text="Level", width=7,
                                           command=self.get_trigger_level_value)
        self.trigger_level_button.pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
        self.trigger_level_entry = Entry(self.trigger_level_frame)
        self.trigger_level_entry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.trigger_level_entry.bind('<Return>', lambda event: self.get_trigger_level_value())

        # Source
        self.trigger_source_frame = Frame(self.trigger_frame)
        self.trigger_source_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.trigger_source_button = Button(self.trigger_source_frame, text="Source", width=7,
                                            command=self.get_trigger_source_value)
        self.trigger_source_button.pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
        self.trigger_source_combobox = AutocompleteCombobox(self.trigger_source_frame)
        self.trigger_source_combobox.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        try:  # offline
            self.trigger_source_combobox["completevalues"] = self.scope_objects_name
        except TypeError:
            pass
        self.trigger_source_combobox.bind('<Return>', lambda event: self.get_trigger_source_value())

        # Channel:
        self.channel_frame = LabelFrame(self.side_frame, text="Channel")
        self.channel_frame.pack(fill=BOTH, expand=0)
        self.channel_function_frame = Frame(self.channel_frame)
        self.channel_function_frame.pack(fill=X, expand=1)
        self.get_button = Button(self.channel_function_frame, text="Get/Set all", width=1,
                                 command=self.get_all_channel_values)
        self.get_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.clear_button = Button(self.channel_function_frame, text="Clear all", width=1,
                                   command=self.trigger_plot.clear_data)
        self.clear_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.channels_frame = ScrolledFrame(self.channel_frame, canvasheight=120)
        self.channels_frame.pack(fill=BOTH, expand=1, padx=2, pady=2)

        while self.channel_index < self.number_of_channel:
            self.channel_number_frame.append(Frame(self.channels_frame.interior))
            self.channel_number_frame[self.channel_index].pack(fill=X, expand=0)
            self.channel_button.append(Button(self.channel_number_frame[self.channel_index],
                                              text=f"CH{str(self.channel_index + 1)}",
                                              foreground=color.tableau_palette[self.channel_index],
                                              command=lambda i=self.channel_index:
                                              [self.get_channel_value(i), self.trigger_plot.zoom_y_ch(i)]))
            self.channel_button[self.channel_index].pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
            self.channel_checkbutton.append(Checkbutton(self.channel_number_frame[self.channel_index],
                                                        variable=self.channel_check[self.channel_index],
                                                        offvalue=False, onvalue=True,
                                                        command=lambda:
                                                        self.trigger_plot.check_channel(self.channel_check)))
            self.channel_checkbutton[self.channel_index].pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
            self.channel_checkbutton[self.channel_index].select()
            self.channel_combobox.append(AutocompleteCombobox(self.channel_number_frame[self.channel_index], width=25))
            self.channel_combobox[self.channel_index].pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
            self.offset_entry.append(Entry(self.channel_number_frame[self.channel_index], width=5))
            self.offset_entry[self.channel_index].pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
            self.offset_entry[self.channel_index].insert(END, 0)
            self.scale_entry.append(Entry(self.channel_number_frame[self.channel_index], width=5))
            self.scale_entry[self.channel_index].pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
            self.scale_entry[self.channel_index].insert(END, 1)
            try:  # offline
                self.channel_combobox[self.channel_index]["completevalues"] = self.scope_objects_name
            except TypeError:
                pass
            self.channel_combobox[self.channel_index]. \
                bind('<Return>', lambda event, i=self.channel_index: self.get_channel_value(i))
            self.offset_entry[self.channel_index].bind('<Return>',
                                                       lambda event, i=self.channel_index: self.get_offset_scale_value(i))
            self.scale_entry[self.channel_index].bind('<Return>',
                                                      lambda event, i=self.channel_index: self.get_offset_scale_value(i))

            self.value_number_frame.append(LabelFrame(self.value_frame, text=f"CH{self.channel_index + 1}",
                                                      foreground=color.tableau_palette[self.channel_index]))
            self.value_number_frame[self.channel_index].pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
            self.value_label_max.append(Label(self.value_number_frame[self.channel_index], text=f"Max: -", anchor='w'))
            self.value_label_max[self.channel_index].pack(fill=X, expand=0)
            self.value_label_min.append(Label(self.value_number_frame[self.channel_index], text=f"Min: -", anchor='w'))
            self.value_label_min[self.channel_index].pack(fill=X, expand=0)

            self.channel_index += 1

    def update(self):
        if self.co.get_sdo("scope_status_rx") == 2:
            self.co.set_sdo(0, "scope_status_rx")
            self.status.configure(text="done")
            self.plot_shift.set(0)
            self.shift_scale["label"] = "shift →"
            self.block_data = self.co.block_transfer(self.co.block_transfer_init(), self.scope_objects,
                                                     self.scope_objects_name, self.channel_value, self.number_of_channel)
            self.trigger_plot.set_data_to_line(self.block_data, self.time_divider_record)
            self.trigger_plot.show()

    def get_data(self):
        self.get_all_channel_values()
        self.get_trigger_source_value()
        self.get_time_divider_value(self.time_divider.get())
        self.get_trigger_type_value()
        self.get_trigger_position_value(self.position.get())
        self.get_trigger_level_value()
        self.co.set_sdo(1, "scope_trigger_reset")
        self.co.set_sdo(1, "scope_status_rx")  # Rising and Falling
        self.status.configure(text="pending")
        self.time_divider_record = self.co.get_sdo("scope_time_divider_tx")

    def open_file(self):
        data = []
        file_open = filedialog.askopenfilename(filetypes=[("Text files", ".txt"), ("All files", ".*")])
        if file_open != "":
            try:
                with open(file_open, "r") as txt_file:
                    line = txt_file.readlines()
                    trigger = line[1].strip().split("\t")
                    self.time_divider.set(f"{trigger[0]}")
                    if trigger[1] == "flash" or "rising" or "falling":
                        self.trigger_type.set(f"{trigger[1]}")
                    self.position.set(f"{trigger[2]}")
                    self.trigger_level_entry.delete(0, END)
                    self.trigger_level_entry.insert(END, f"{trigger[3]}")
                    self.trigger_source_combobox.delete(0, END)
                    self.trigger_source_combobox.insert(END, f"{trigger[4]}")
            except TclError:
                pass
            with open(file_open, "r") as txt_file:
                for index, line in enumerate(txt_file.readlines()[4:]):
                    if index < self.number_of_channel:
                        data.append(line.strip().split("\t"))
                        try:
                            if data[index][0] == "0" or data[index][0] == "1":
                                self.channel_check[index].set(int(data[index][0]))
                            else:
                                self.channel_check[index].set(1)
                        except IndexError:
                            self.channel_check[index].set(1)
                        self.offset_entry[index].delete(0, END)
                        try:
                            if data[index][1] == "":
                                self.offset_entry[index].insert(END, "0")
                            else:
                                self.offset_entry[index].insert(END, f"{data[index][1]}")
                        except IndexError:
                            self.offset_entry[index].insert(END, "0")
                        self.scale_entry[index].delete(0, END)
                        try:
                            if data[index][2] == "":
                                self.scale_entry[index].insert(END, "1")
                            else:
                                self.scale_entry[index].insert(END, f"{data[index][2]}")
                        except IndexError:
                            self.scale_entry[index].insert(END, "1")
                        self.channel_combobox[index].delete(0, END)
                        try:
                            self.channel_combobox[index].insert(END, f"{data[index][3]}")
                        except IndexError:
                            self.channel_combobox[index].insert(END, "")

    def save_file(self):
        file_save = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", ".txt"),
                                                                                     ("All files", ".*")])
        if file_save != "":
            with open(file_save, "w") as txt_file:
                txt_file.write(f"TimeDiv\t")
                txt_file.write(f"Type\t")
                txt_file.write(f"Pos.\t")
                txt_file.write(f"Level\t")
                txt_file.write(f"Source\t")
                txt_file.write("\n")
                txt_file.write(f"{self.time_divider.get()}\t")
                txt_file.write(f"{self.trigger_type.get()}\t")
                txt_file.write(f"{self.position.get()}\t")
                txt_file.write(f"{self.trigger_level_entry.get()}\t")
                txt_file.write(f"{self.trigger_source_combobox.get()}\t")
                txt_file.write("\n")
                txt_file.write("\n")
                txt_file.write(f"check\t")
                txt_file.write(f"offset\t")
                txt_file.write(f"scale\t")
                txt_file.write(f"name\t")
                txt_file.write("\n")
                for index in range(self.number_of_channel):
                    txt_file.write(f"{self.channel_check[index].get()}\t")
                    txt_file.write(f"{self.offset_entry[index].get()}\t")
                    txt_file.write(f"{self.scale_entry[index].get()}\t")
                    txt_file.write(f"{self.channel_combobox[index].get()}\t")
                    txt_file.write("\n")
            txt_file.close()

    @staticmethod
    def plot():
        data = []
        x = []
        y = []
        file_open = filedialog.askopenfilename(filetypes=[("CSV files", ".csv"), ("All files", ".*")])
        if file_open != "":
            plt.figure(time.time())
            with open(file_open, "r") as csv_file:
                csv_reader = csv.reader(csv_file)
                header = next(csv_reader)
                for row in csv_reader:
                    data.append(row)
            for name_index, name in enumerate(header):
                if name_index == 0:
                    pass
                elif name_index == 1:
                    for value_index, value in enumerate(data):
                        try:
                            x.append(float(value[name_index]))
                        except ValueError:
                            x.append(None)
                else:
                    for value_index, value in enumerate(data):
                        try:
                            y.append(float(value[name_index]))
                        except ValueError:
                            y.append(None)
                    if name != "":
                        plt.plot(x, y, label=name)
                    y = []
            plt.title(os.path.basename(file_open))
            plt.xlabel("Online: time in s / Trigger: time in ms")
            plt.legend()
            plt.grid(True)
            plt.show()

    def shift_plot(self, plot_shift):
        if plot_shift == "0":
            self.shift_scale["label"] = "shift →"
            for index in range(len(self.block_data)):
                self.block_data[index] = list(np.roll(self.block_data[index], -1))
        elif plot_shift == "1":
            self.shift_scale["label"] = "shift ←"
            for index in range(len(self.block_data)):
                self.block_data[index] = list(np.roll(self.block_data[index], 1))
        self.trigger_plot.set_data_to_line(self.block_data, self.time_divider_record)

    def get_time_divider_value(self, time_divider):
        self.time_divider.set(time_divider)
        self.trigger_plot.time_divider_record = float(time_divider)
        self.ax.set_xlim(0, 511 * self.cycle_time * float(time_divider))
        self.trigger_position_unit_label[
            "text"] = f"{round(self.axv_position[self.position.get() - 1] * self.cycle_time * float(time_divider), 2)}ms"
        self.axv_line.remove()
        self.axv_line = self.ax.axvline(
            x=round(self.axv_position[self.position.get() - 1] * self.cycle_time * float(self.time_divider.get()), 2),
            linestyle="dotted")
        self.ax.figure.canvas.draw()
        self.co.set_sdo(time_divider, "scope_time_divider_tx")

    def get_trigger_type_value(self):
        if self.trigger_type.get() == "flash":
            self.co.set_sdo(0, "scope_trigger_condition_tx")
        if self.trigger_type.get() == "rising":
            self.co.set_sdo(1, "scope_trigger_condition_tx")
        elif self.trigger_type.get() == "falling":
            self.co.set_sdo(2, "scope_trigger_condition_tx")

    def get_trigger_position_value(self, position):
        self.position.set(position)
        self.trigger_position_unit_label[
            "text"] = f"{round(self.axv_position[self.position.get() - 1] * self.cycle_time * float(self.time_divider.get()), 2)}ms"
        self.axv_line.remove()
        self.axv_line = self.ax.axvline(
            x=round(self.axv_position[self.position.get() - 1] * self.cycle_time * float(self.time_divider.get()), 2),
            linestyle="dotted")
        self.ax.figure.canvas.draw()
        self.co.set_sdo(position, "scope_trigger_position_tx")

    def get_trigger_level_value(self):
        try:
            try:
                if self.scope_objects[self.trigger_value]["DataType"] == 8:
                    self.co.set_sdo(struct.pack("f", float(self.trigger_level_entry.get())), "scope_trigger_level_tx")
                else:
                    self.co.set_sdo(float(self.trigger_level_entry.get()), "scope_trigger_level_tx")
            except KeyError:
                self.co.set_sdo(float(self.trigger_level_entry.get()), "scope_trigger_level_tx")
        except ValueError:
            self.trigger_level_entry.delete(0, END)
            self.trigger_level_entry.insert(END, "ValueError")

    def get_trigger_source_value(self):
        try:
            self.co.set_sdo(self.scope_objects[self.trigger_source_combobox.get()]["index"], "scope_data_source_tx",
                            "trigger_channel_source")
        except KeyError:
            self.co.set_sdo(0, "scope_data_source_tx", "trigger_channel_source")
        self.trigger_value = self.trigger_source_combobox.get()

    def get_all_channel_values(self):
        for index in range(self.number_of_channel):
            try:
                self.co.set_sdo(self.scope_objects[self.channel_combobox[index].get()]["index"], "scope_data_source_tx",
                                f"channel{index + 1}_source")
            except KeyError:
                self.co.set_sdo(0, "scope_data_source_tx", f"channel{index + 1}_source")
            self.channel_value[index] = self.channel_combobox[index].get()
            try:
                self.offset_value[index] = float(self.offset_entry[index].get())
            except ValueError:
                pass
            try:
                self.scale_value[index] = float(self.scale_entry[index].get())
            except ValueError:
                pass
        self.trigger_plot.get_offset_scale(self.offset_value, self.scale_value)

    def get_channel_value(self, index):
        try:
            self.co.set_sdo(self.scope_objects[self.channel_combobox[index].get()]["index"], "scope_data_source_tx",
                            f"channel{index + 1}_source")
        except KeyError:
            self.co.set_sdo(0, "scope_data_source_tx", f"channel{index + 1}_source")
        self.channel_value[index] = self.channel_combobox[index].get()
        self.get_offset_scale_value(index)

    def get_offset_scale_value(self, index):
        try:
            self.offset_value[index] = float(self.offset_entry[index].get())
        except ValueError:
            pass
        try:
            self.scale_value[index] = float(self.scale_entry[index].get())
        except ValueError:
            pass
        self.trigger_plot.get_offset_scale(self.offset_value, self.scale_value)

    def zoom_factory(self, ax, base_scale=2.):
        def zoom(event):
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()

            xdata = event.xdata  # get event x location
            ydata = event.ydata  # get event y location

            if event.button == 'down':
                # deal with zoom in
                scale_factor = 1 / base_scale
            elif event.button == 'up':
                # deal with zoom out
                scale_factor = base_scale
            else:
                # deal with something that should never happen
                scale_factor = 1

            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

            relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
            rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

            ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
            ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
            ax.figure.canvas.draw()

        self.fig.canvas.mpl_connect('scroll_event', zoom)

        return zoom

    @staticmethod
    def interactive_legend(ax):
        if ax is None:
            ax = plt.gca()
        if ax.legend_ is None:
            ax.legend()
        return InteractiveLegend(ax.get_legend())


class InteractiveLegend(object):
    def __init__(self, legend):
        self.legend = legend
        self.fig = legend.axes.figure

        self.visible = True
        self.lookup_artist, self.lookup_handle = self._build_lookups(legend)
        self._setup_connections()

        self.update()

    def _setup_connections(self):
        for artist in self.legend.texts + self.legend.legendHandles:
            artist.set_picker(10)  # 10 points tolerance

        self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)

    @staticmethod
    def _build_lookups(legend):
        labels = [t.get_text() for t in legend.texts]
        handles = legend.legendHandles
        label2handle = dict(zip(labels, handles))
        handle2text = dict(zip(handles, legend.texts))

        lookup_artist = {}
        lookup_handle = {}
        for artist in legend.axes.get_children():
            if artist.get_label() in labels:
                handle = label2handle[artist.get_label()]
                lookup_handle[artist] = handle
                lookup_artist[handle] = artist
                lookup_artist[handle2text[handle]] = artist

        lookup_handle.update(zip(handles, handles))
        lookup_handle.update(zip(legend.texts, handles))

        return lookup_artist, lookup_handle

    def on_pick(self, event):
        handle = event.artist
        if handle in self.lookup_artist:
            artist = self.lookup_artist[handle]
            artist.set_visible(not artist.get_visible())
            self.update()

    def on_click(self, event):
        if event.button == 2:
            self.visible = not self.visible
        else:
            return

        for artist in self.lookup_artist.values():
            artist.set_visible(self.visible)
        self.update()

    def update(self):
        for artist in self.lookup_artist.values():
            handle = self.lookup_handle[artist]
            if artist.get_visible():
                handle.set_visible(True)
            else:
                handle.set_visible(False)
        self.fig.canvas.draw()
