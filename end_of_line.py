import json
import ast
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from ttkwidgets.autocomplete import AutocompleteCombobox

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk


class EndOfLine:
    def __init__(self, notebook):
        self.end_of_line = Frame(notebook)
        self.end_of_line.pack(fill=BOTH, expand=1)
        notebook.add(self.end_of_line, text="End of line")
        self.side_frame = Frame(self.end_of_line, width=150)
        self.side_frame.pack(side=LEFT, fill=BOTH, expand=0)
        self.main_frame = Frame(self.end_of_line)
        self.main_frame.pack(side=LEFT, fill=BOTH, expand=1)

        # Tree
        self.data = None
        self.tree_scroll = Scrollbar(self.main_frame)
        self.tree_scroll.pack(side=RIGHT, fill=Y)
        self.tree = ttk.Treeview(self.main_frame, yscrollcommand=self.tree_scroll.set, selectmode="extended")
        self.tree.pack(fill=BOTH, expand=1)
        self.tree_scroll.config(command=self.tree.yview)
        self.tree.bind("<Double-1>", lambda event: self.on_double_click())

        self.tree["columns"] = ("Name", "Value", "Type")
        self.tree.column("#0", width=100, minwidth=50, stretch=NO)
        self.tree.column("Name", width=250, minwidth=200, stretch=NO)
        self.tree.column("Value", width=150, minwidth=130)
        self.tree.heading("#0", text="Index", anchor=W)
        self.tree.heading("Name", text="Name", anchor=W)
        self.tree.heading("Value", text="Value", anchor=W)
        self.tree.heading("Type", text="Type", anchor=W)

        # Control
        self.control = StringVar()
        self.control_frame = LabelFrame(self.side_frame, text="Control")
        self.control_frame.pack(fill=X, expand=0)
        self.open_file_button = Button(self.control_frame, text="🗁", width=1, command=self.open_file)
        self.open_file_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.save_file_button = Button(self.control_frame, text="🖫", width=1, command=self.save_file)
        self.save_file_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        # Set Value
        self.value_frame = LabelFrame(self.side_frame, text="Set Value")
        self.value_frame.pack(fill=BOTH, expand=0, padx=2, pady=2)
        self.group_combobox = AutocompleteCombobox(self.value_frame, state="readonly", width=25)
        self.group_combobox.pack(fill=X, expand=0, padx=2, pady=2)
        self.group_combobox.bind("<<ComboboxSelected>>", lambda event: self.get_name())
        self.name_combobox = AutocompleteCombobox(self.value_frame, state="readonly", width=25)
        self.name_combobox.pack(fill=X, expand=0, padx=2, pady=2)
        self.name_combobox.bind("<<ComboboxSelected>>", lambda event: self.get_parameter())
        self.parameter_combobox = AutocompleteCombobox(self.value_frame, state="readonly", width=25)
        self.parameter_combobox.pack(fill=X, expand=0, padx=2, pady=2)
        self.parameter_combobox.bind("<<ComboboxSelected>>", lambda event: self.get_value())
        self.set_entry = Entry(self.value_frame)
        self.set_entry.pack(fill=X, expand=0, padx=2, pady=2)
        self.set_entry.bind('<Return>', lambda event: self.set_value())
        self.set_button = Button(self.value_frame, text="Set", state=DISABLED, command=lambda: self.set_value())
        self.set_button.pack(fill=X, expand=0, padx=2, pady=2)

    def open_file(self):
        file_open = filedialog.askopenfilename(filetypes=[("JSON files", ".json"), ("All files", ".*")])
        if file_open != "":
            with open(file_open) as json_file:
                self.data = json.load(json_file)
            self.tree.delete(*self.tree.get_children())
            for group_index, group in enumerate(self.data):
                group_tree = self.tree.insert(parent="", index="end", iid=f"{group_index}g", text=f"{group_index}",
                                              values=(group, f"{len(self.data[group])}", "Objects"))
                for name_index, name in enumerate(self.data[group]):
                    try:
                        name_tree = self.tree.insert(parent=group_tree, index="end", iid=f"{group_index}g{name_index}n",
                                                     text=f"{name_index}",
                                                     values=(name, f"{self.data[group][name]['value']}",
                                                             f"{type(self.data[group][name]['value'])}"))
                    except KeyError:
                        name_tree = self.tree.insert(parent=group_tree, index="end", iid=f"{group_index}g{name_index}n",
                                                     text=f"{name_index}",
                                                     values=(name, f"{len(self.data[group][name])}", "Objects"))
                    for parameter_index, parameter in enumerate(self.data[group][name]):
                        self.tree.insert(parent=name_tree, index="end",
                                         iid=f"{group_index}g{name_index}n{parameter_index}p",
                                         text=f"{parameter_index}",
                                         values=(parameter, f"{self.data[group][name][parameter]}",
                                                 f"{type(self.data[group][name][parameter])}"))
            self.get_group()

    def save_file(self):
        file_save = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("JSON files", ".json"), ("All files", ".*")])

        if file_save != "":
            with open(file_save, "w") as json_file:
                json.dump(self.data, json_file, indent="\t")
            json_file.close()

    def get_group(self):
        self.group_combobox["values"] = list(self.data)
        self.group_combobox.set("")
        self.name_combobox["values"] = []
        self.name_combobox.set("")
        self.parameter_combobox["values"] = []
        self.parameter_combobox.set("")
        self.set_entry.delete(0, END)
        self.set_button["state"] = DISABLED

    def get_name(self):
        self.name_combobox["values"] = list(self.data[self.group_combobox.get()])
        self.name_combobox.set("")
        self.parameter_combobox["values"] = []
        self.parameter_combobox.set("")
        self.set_entry.delete(0, END)
        self.set_entry.insert(END, f"{len(self.name_combobox['values'])} Objects")
        self.set_button["state"] = DISABLED

    def get_parameter(self):
        self.parameter_combobox["values"] = list(self.data[self.group_combobox.get()][self.name_combobox.get()])
        self.parameter_combobox.set("")
        self.set_entry.delete(0, END)
        try:
            self.set_entry.insert(END,
                                  f"{self.data[self.group_combobox.get()][self.name_combobox.get()]['value']} "
                                  f"{type(self.data[self.group_combobox.get()][self.name_combobox.get()]['value'])}")
        except KeyError:
            self.set_entry.insert(END, f"{len(self.parameter_combobox['values'])} Objects")
        self.set_button["state"] = DISABLED

    def get_value(self):
        self.set_entry.delete(0, END)
        self.set_entry. \
            insert(END,
                   f"{self.data[self.group_combobox.get()][self.name_combobox.get()][self.parameter_combobox.get()]}")
        if self.parameter_combobox.get() == "value":
            self.set_button["state"] = NORMAL
        else:
            self.set_button["state"] = DISABLED

    def set_value(self):
        if self.parameter_combobox.get() == "value":
            if type(self.data[self.group_combobox.get()][self.name_combobox.get()][
                        self.parameter_combobox.get()]) != str:
                self.data[self.group_combobox.get()][self.name_combobox.get()][self.parameter_combobox.get()] = \
                    ast.literal_eval(self.set_entry.get())
            else:
                self.data[self.group_combobox.get()][self.name_combobox.get()][self.parameter_combobox.get()] = \
                    self.set_entry.get()
            for group_index, group in enumerate(self.data):
                self.tree.item(f"{group_index}g", values=(group, f"{len(self.data[group])}", "Objects"))
                for name_index, name in enumerate(self.data[group]):
                    self.tree.item(f"{group_index}g{name_index}n",
                                   values=(name, f"{len(self.data[group][name])}", "Objects"))
                    for parameter_index, parameter in enumerate(self.data[group][name]):
                        self.tree.item(f"{group_index}g{name_index}n{parameter_index}p",
                                       values=(parameter, f"{self.data[group][name][parameter]}",
                                               f"{type(self.data[group][name][parameter])}"))

    def on_double_click(self):
        child_iid = self.tree.focus()
        parent_iid = self.tree.parent(child_iid)
        grandparent_iid = self.tree.parent(parent_iid)
        if self.tree.parent(child_iid) == "":
            group = self.tree.item(child_iid, "values")
            self.group_combobox["values"] = list(self.data)
            self.group_combobox.set(f"{group[0]}")
            self.name_combobox["values"] = list(self.data[self.group_combobox.get()])
            self.name_combobox.set("")
            self.parameter_combobox["values"] = []
            self.parameter_combobox.set("")
            self.set_entry.delete(0, END)
            self.set_entry.insert(END, f"{group[1]} {group[2]}")
            self.set_button["state"] = DISABLED
        else:
            if self.tree.parent(parent_iid) == "":
                group = self.tree.item(parent_iid, "values")
                name = self.tree.item(child_iid, "values")
                self.group_combobox["values"] = list(self.data)
                self.group_combobox.set(f"{group[0]}")
                self.name_combobox["values"] = list(self.data[self.group_combobox.get()])
                self.name_combobox.set(f"{name[0]}")
                self.parameter_combobox["values"] = list(self.data[self.group_combobox.get()][self.name_combobox.get()])
                self.parameter_combobox.set("")
                self.set_entry.delete(0, END)
                self.set_entry.insert(END, f"{name[1]} {name[2]}")
                self.set_button["state"] = DISABLED
            else:
                if self.tree.parent(grandparent_iid) == "":
                    group = self.tree.item(grandparent_iid, "values")
                    name = self.tree.item(parent_iid, "values")
                    parameter = self.tree.item(child_iid, "values")
                    self.group_combobox["values"] = list(self.data)
                    self.group_combobox.set(f"{group[0]}")
                    self.name_combobox["values"] = list(self.data[self.group_combobox.get()])
                    self.name_combobox.set(f"{name[0]}")
                    self.parameter_combobox["values"] = \
                        list(self.data[self.group_combobox.get()][self.name_combobox.get()])
                    self.parameter_combobox.set(f"{parameter[0]}")
                    self.set_entry.delete(0, END)
                    self.set_entry.insert(END, f"{parameter[1]}")
                    if self.parameter_combobox.get() == "value":
                        self.set_button["state"] = NORMAL
                    else:
                        self.set_button["state"] = DISABLED
