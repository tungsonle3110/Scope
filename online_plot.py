import color
import pandas as pd
import time
import math
import statistics
from matplotlib.lines import Line2D
from tkinter import messagebox


class OnlinePlot:
    def __init__(self, ax, number_of_channel, value_label_min, value_label_max, maxt=100, dt=1):
        self.ax = ax
        self.number_of_channel = number_of_channel
        self.value_label_min = value_label_min
        self.value_label_max = value_label_max
        self.maxt = maxt
        self.dt = dt

        self.temp = 0
        self.mint = 0
        self.tdata_s = []
        self.tdata = []
        self.ydata = [[] for _ in range(self.number_of_channel)]
        self.line = [type(None)] * self.number_of_channel
        self.add_line_to_ax()
        self.ax.set(title="Online Mode", xlabel="", ylabel="")
        self.ax.legend(bbox_to_anchor=(0.5, -0.07), loc="upper center", labelcolor=color.tableau_palette,
                       fontsize=8, handlelength=2.0, handletextpad=0.8, columnspacing=2.0,
                       ncol=self.number_of_channel)
        self.ax.grid(True)
        self.ax.set_xlim(0, self.maxt)
        self.ax.callbacks.connect('xlim_changed', self.on_xlim_change)
        self.xlim = [0, self.maxt]

        self.record_check = [1 for _ in range(0, 2)]
        self.show_value = "total"
        self.mode_value = "dynamic"
        self.channel_check = [1 for _ in range(self.number_of_channel)]
        self.offset_value = [0.0 for _ in range(self.number_of_channel)]
        self.scale_value = [0.0 for _ in range(self.number_of_channel)]

    def update(self, y):
        try:
            t = self.tdata[-1] + self.dt
        except IndexError:
            t = 0
        self.tdata.append(t)
        ydata_show = self.set_data_to_line(y)
        if self.show_value == "current":
            if self.mode_value == "static":
                if self.temp >= self.maxt:
                    self.mint = self.tdata[-1]
                    try:
                        self.ax.set_xlim(self.tdata[-1], self.tdata[-1] + self.maxt)  # show apart
                    except IndexError:
                        self.ax.set_xlim(0, self.maxt)  # show apart
            elif self.mode_value == "dynamic":
                y_min, y_max = [], []
                for i in range(len(ydata_show)):
                    try:
                        if self.channel_check[i] == 1:
                            y_min.append(min(i1 for i1 in ydata_show[i] if i1 is not None))
                            y_max.append(max(i1 for i1 in ydata_show[i] if i1 is not None))
                    except ValueError:
                        pass
                try:
                    self.ax.set_ylim(min(y_min), max(y_max))
                except ValueError:
                    pass
                if self.temp >= self.maxt:
                    self.mint = self.tdata[-1]
                    try:
                        self.ax.set_xlim(self.tdata[-1], self.tdata[-1] + self.maxt)  # show apart
                    except IndexError:
                        self.ax.set_xlim(0, self.maxt)  # show apart
        elif self.show_value == "total":
            if self.mode_value == "static":
                try:
                    self.ax.set_xlim(self.tdata[0], self.tdata[-1])  # show all
                except IndexError:
                    self.ax.set_xlim(0, self.maxt)
            elif self.mode_value == "dynamic":
                y_min, y_max = [], []
                for i in range(len(ydata_show)):
                    try:
                        if self.channel_check[i] == 1:
                            y_min.append(min(i1 for i1 in ydata_show[i] if i1 is not None))
                            y_max.append(max(i1 for i1 in ydata_show[i] if i1 is not None))
                    except ValueError:
                        pass
                try:
                    self.ax.set_xlim(self.tdata[0], self.tdata[-1])
                except IndexError:
                    self.ax.set_xlim(0, self.maxt)
                try:
                    self.ax.set_ylim(min(y_min), max(y_max))
                except ValueError:
                    pass
        if self.temp >= self.maxt:
            self.temp = 0
        self.temp += self.dt
        self.ax.figure.canvas.draw()
        for index in range(self.number_of_channel):
            try:
                self.value_label_max[index]['text'] = \
                    f"Max: {round(max(i - self.offset_value[index] for i in ydata_show[index] if i is not None), 2)}"
            except ValueError:
                self.value_label_max[index]['text'] = f"Max: -"
            try:
                self.value_label_min[index]['text'] = \
                    f"Min: {round(min(i - self.offset_value[index] for i in ydata_show[index] if i is not None), 2)}"
            except ValueError:
                self.value_label_min[index]['text'] = f"Min: -"
        return self.line

    def add_line_to_ax(self):
        for index in range(self.number_of_channel):
            self.line[index] = Line2D(self.tdata, self.ydata[index], label=f"CH{index + 1}",
                                      color=f'{color.tableau_palette[index]}')
            self.ax.add_line(self.line[index])

    def set_data_to_line(self, y):
        ydata_show = [[] for _ in range(self.number_of_channel)]
        mean_ydata = []
        for index in range(self.number_of_channel):
            self.ydata[index].append(y[index])
            try:
                mean_ydata.append(statistics.mean(
                    [float(i) for i in self.ydata[index] if
                     i is not None and type(i) is not str and type(i) is not bytes]))
            except statistics.StatisticsError:
                mean_ydata.append(None)
            for element in self.ydata[index]:
                if element is None or type(element) is str or type(element) is bytes:
                    ydata_show[index].append(None)
                elif element == mean_ydata[index]:
                    ydata_show[index].append(element + self.offset_value[index])
                elif element > mean_ydata[index]:
                    ydata_show[index].append(
                        mean_ydata[index] + abs(element - mean_ydata[index]) * self.scale_value[index] +
                        self.offset_value[index])
                elif element < mean_ydata[index]:
                    ydata_show[index].append(
                        mean_ydata[index] - abs(element - mean_ydata[index]) * self.scale_value[index] +
                        self.offset_value[index])
            self.line[index].set_data(self.tdata, ydata_show[index])
        return ydata_show

    def on_xlim_change(self, event_ax):
        self.xlim = list(event_ax.get_xlim())
        self.xlim.sort()
        self.xlim = [math.floor(self.xlim[0]), math.ceil(self.xlim[1])]

    def tdata_time(self, total_time):
        self.tdata_s.append(total_time)

    def check_record(self, record_check):
        for index in range(len(record_check)):
            self.record_check[index] = record_check[index].get()

    def record(self, channel_value):
        type_name = ""
        value_name = ""
        xlim = self.xlim.copy()
        tdata_s = [i - self.tdata_s[0] for i in self.tdata_s]
        ydata = [[] for _ in range(self.number_of_channel)]
        current_time = time.strftime("%Y%m%d_%H%M%S")
        try:
            if xlim[0] < self.tdata[0]:
                xlim[0] = self.tdata[0]
        except IndexError:
            pass
        try:
            if xlim[1] > self.tdata[-1]:
                xlim[1] = self.tdata[-1]
        except IndexError:
            pass
        dictionary = {"index": self.tdata[xlim[0]:xlim[1] + 1], "time": tdata_s[xlim[0]:xlim[1] + 1]}
        for index in range(self.number_of_channel):
            ydata[index] = self.ydata[index][xlim[0]:xlim[1] + 1]
            dictionary[channel_value[index]] = ydata[index]
        data_frame = pd.DataFrame(dictionary)
        if self.record_check[0] == 1:
            data_frame.to_csv(f"{current_time}_online_scope.csv", index=False)
            type_name += "\tCSV .csv"
        if self.record_check[1] == 1:
            data_frame.to_excel(f"{current_time}_online_scope.xlsx", index=False)
            type_name += "\tExcel. xlsx"
        for i in list(dictionary.keys()):
            value_name += f"\t{i}\n"
        if not self.tdata:
            messagebox.showinfo(title="Record", message=f"Recorded"
                                                        f"\nname:\t{current_time}_online_scope"
                                                        f"\ntype:{type_name}"
                                                        f"\nrecord:\tnothing"
                                                        f"\nvalues:{value_name}")
        else:
            messagebox.showinfo(title="Record", message=f"Recorded"
                                                        f"\nname:\t{current_time}_online_scope"
                                                        f"\ntype:{type_name}"
                                                        f"\nrecord:\tfrom {xlim[0]} to {xlim[1]}"
                                                        f"\nvalues:{value_name}")

    def show(self, show_value):
        self.show_value = show_value
        if self.show_value == "current":
            try:
                self.ax.set_xlim(self.tdata[-1] - self.temp + self.dt, self.tdata[-1] + self.maxt - self.temp + self.dt)
            except IndexError:
                self.ax.set_xlim(0, self.maxt)
        elif self.show_value == "total":
            try:
                self.ax.set_xlim(self.tdata[0], self.tdata[-1])  # show all
            except IndexError:
                self.ax.set_xlim(0, self.maxt)
        self.ax.figure.canvas.draw()

    def mode(self, mode_value):
        self.mode_value = mode_value
        ydata_show = [[] for _ in range(self.number_of_channel)]
        mean_ydata = []
        for index in range(self.number_of_channel):
            try:
                mean_ydata.append(statistics.mean(
                    [float(i) for i in self.ydata[index] if
                     i is not None and type(i) is not str and type(i) is not bytes]))
            except statistics.StatisticsError:
                mean_ydata.append(None)
            for element in self.ydata[index]:
                if element is None or type(element) is str or type(element) is bytes:
                    ydata_show[index].append(None)
                elif element == mean_ydata[index]:
                    ydata_show[index].append(element + self.offset_value[index])
                elif element > mean_ydata[index]:
                    ydata_show[index].append(mean_ydata[index] + abs(element - mean_ydata[index]) *
                                             self.scale_value[index] + self.offset_value[index])
                elif element < mean_ydata[index]:
                    ydata_show[index].append(mean_ydata[index] - abs(element - mean_ydata[index]) *
                                             self.scale_value[index] + self.offset_value[index])
        if self.show_value == "current":
            if self.mode_value == "static":
                try:
                    self.ax.set_xlim(self.tdata[-1] - self.temp + self.dt,
                                     self.tdata[-1] + self.maxt - self.temp + self.dt)
                except IndexError:
                    self.ax.set_xlim(0, self.maxt)
            elif self.mode_value == "dynamic":
                y_min, y_max = [], []
                for i in range(len(ydata_show)):
                    try:
                        if self.channel_check[i] == 1:
                            y_min.append(min(i1 for i1 in ydata_show[i] if i1 is not None))
                            y_max.append(max(i1 for i1 in ydata_show[i] if i1 is not None))
                    except ValueError:
                        pass
                try:
                    self.ax.set_ylim(min(y_min), max(y_max))
                except ValueError:
                    pass
                try:
                    self.ax.set_xlim(self.tdata[-1] - self.temp + self.dt,
                                     self.tdata[-1] + self.maxt - self.temp + self.dt)
                except IndexError:
                    self.ax.set_xlim(0, self.maxt)
        elif self.show_value == "total":
            if self.mode_value == "static":
                try:
                    self.ax.set_xlim(self.tdata[0], self.tdata[-1])  # show all
                except IndexError:
                    self.ax.set_xlim(0, self.maxt)
            elif self.mode_value == "dynamic":
                y_min, y_max = [], []
                for i in range(len(ydata_show)):
                    try:
                        if self.channel_check[i] == 1:
                            y_min.append(min(i1 for i1 in ydata_show[i] if i1 is not None))
                            y_max.append(max(i1 for i1 in ydata_show[i] if i1 is not None))
                    except ValueError:
                        pass
                try:
                    self.ax.set_ylim(min(y_min), max(y_max))
                except ValueError:
                    pass
                try:
                    self.ax.set_xlim(self.tdata[0], self.tdata[-1])
                except IndexError:
                    self.ax.set_xlim(0, self.maxt)
        self.ax.figure.canvas.draw()

    def set_maxt(self, maxt):
        self.maxt = maxt
        self.ax.set_xlim(self.mint, self.mint + self.maxt)
        self.ax.figure.canvas.draw()

    def zoom_x(self, xlim_left, xlim_right):
        self.ax.set_xlim(xlim_left, xlim_right)
        self.ax.figure.canvas.draw()

    def zoom_y(self, ylim_left, ylim_right):
        self.ax.set_ylim(ylim_left, ylim_right)
        self.ax.figure.canvas.draw()

    def clear_data(self):
        self.temp = 0
        self.mint = 0
        self.tdata_s = []
        self.tdata = []
        self.ydata = [[] for _ in range(self.number_of_channel)]
        self.ax.set_xlim(0, self.maxt)
        for index in range(self.number_of_channel):
            self.line[index].set_data(self.tdata, self.ydata[index])
            try:
                self.value_label_max[index]['text'] = \
                    f"Max: {round(max(i - self.offset_value[index] for i in self.ydata[index] if i is not None), 2)}"
            except ValueError:
                self.value_label_max[index]['text'] = f"Max: -"
            try:
                self.value_label_min[index]['text'] = \
                    f"Min: {round(min(i - self.offset_value[index] for i in self.ydata[index] if i is not None), 2)}"
            except ValueError:
                self.value_label_min[index]['text'] = f"Min: -"
        self.ax.figure.canvas.draw()

    def check_channel(self, channel_check):
        for index in range(self.number_of_channel):
            self.channel_check[index] = channel_check[index].get()

    def zoom_y_ch(self, index_show):
        ydata_show = [[] for _ in range(self.number_of_channel)]
        mean_ydata = []
        for index in range(self.number_of_channel):
            try:
                mean_ydata.append(statistics.mean(
                    [float(i) for i in self.ydata[index] if
                     i is not None and type(i) is not str and type(i) is not bytes]))
            except statistics.StatisticsError:
                mean_ydata.append(None)
            for element in self.ydata[index]:
                if element is None or type(element) is str or type(element) is bytes:
                    ydata_show[index].append(None)
                elif element == mean_ydata[index]:
                    ydata_show[index].append(element + self.offset_value[index])
                elif element > mean_ydata[index]:
                    ydata_show[index].append(
                        mean_ydata[index] + abs(element - mean_ydata[index]) * self.scale_value[index] +
                        self.offset_value[index])
                elif element < mean_ydata[index]:
                    ydata_show[index].append(
                        mean_ydata[index] - abs(element - mean_ydata[index]) * self.scale_value[index] +
                        self.offset_value[index])
            self.line[index].set_data(self.tdata, ydata_show[index])
        try:
            self.ax.set_ylim(min(i for i in ydata_show[index_show] if i is not None),
                             max(i for i in ydata_show[index_show] if i is not None))
        except ValueError:
            self.ax.set_ylim(0, 1)
        self.ax.figure.canvas.draw()

    def get_offset_scale(self, offset_value, scale_value):
        self.offset_value = offset_value
        self.scale_value = scale_value
        ydata_show = [[] for _ in range(self.number_of_channel)]
        mean_ydata = []
        for index in range(self.number_of_channel):
            try:
                mean_ydata.append(statistics.mean(
                    [float(i) for i in self.ydata[index] if
                     i is not None and type(i) is not str and type(i) is not bytes]))
            except statistics.StatisticsError:
                mean_ydata.append(None)
            for element in self.ydata[index]:
                if element is None or type(element) is str or type(element) is bytes:
                    ydata_show[index].append(None)
                elif element == mean_ydata[index]:
                    ydata_show[index].append(element + self.offset_value[index])
                elif element > mean_ydata[index]:
                    ydata_show[index].append(
                        mean_ydata[index] + abs(element - mean_ydata[index]) * self.scale_value[index] +
                        self.offset_value[index])
                elif element < mean_ydata[index]:
                    ydata_show[index].append(
                        mean_ydata[index] - abs(element - mean_ydata[index]) * self.scale_value[index] +
                        self.offset_value[index])
            self.line[index].set_data(self.tdata, ydata_show[index])
            try:
                self.value_label_max[index]['text'] = \
                    f"Max: {round(max(i - self.offset_value[index] for i in ydata_show[index] if i is not None), 2)}"
            except ValueError:
                self.value_label_max[index]['text'] = f"Max: -"
            try:
                self.value_label_min[index]['text'] = \
                    f"Min: {round(min(i - self.offset_value[index] for i in ydata_show[index] if i is not None), 2)}"
            except ValueError:
                self.value_label_min[index]['text'] = f"Min: -"
        self.ax.figure.canvas.draw()
