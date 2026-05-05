from tkinter import *
import tkinter as tk
from tkinter import ttk
import customtkinter
import numpy as np
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from OMPython_Functionalities import getParameterModelica_Data, simulate, getContinuousModelica_Data, startModelica
from Config import Project_path, modelicafilename, modelicamodelname, resultfile, modelicafilelocation



SelectedParameterSim = pd.DataFrame(columns=["Parameter", "1. Durchlauf"])
SelectedParameterPlot = pd.DataFrame(columns=["Parameter"])

solver = 'ida'
startTime = '0'
stopTime = '300'
stepTime = '300'

def add_simulation_parameter(input_dict):
    global SelectedParameterSim

    parameter_name = input_dict['text']
    value = input_dict['values'][0]

    if not SelectedParameterSim['Parameter'].str.contains(parameter_name).any():
        new_row = pd.DataFrame({'Parameter': [parameter_name], 'Iteration 1': [value]})
        SelectedParameterSim = pd.concat([SelectedParameterSim, new_row], ignore_index=True)

def add_plot_parameter(input_dict):
    global SelectedParameterPlot

    parameter_name = input_dict['text']

    if not SelectedParameterPlot['Parameter'].str.contains(parameter_name).any():
        new_row = pd.DataFrame({'Parameter': [parameter_name]})
        SelectedParameterPlot = pd.concat([SelectedParameterPlot, new_row], ignore_index=True)

def remove_simulation_parameter(input_dict):
    global SelectedParameterSim

    parameter_name = input_dict['text']

    if SelectedParameterSim['Parameter'].str.contains(parameter_name).any():
        SelectedParameterSim = SelectedParameterSim[SelectedParameterSim['Parameter'] != parameter_name]
    else:
        return

def remove_plot_parameter(input_dict):
    global SelectedParameterPlot

    parameter_name = input_dict['text']

    if SelectedParameterPlot['Parameter'].str.contains(parameter_name).any():
        SelectedParameterPlot = SelectedParameterPlot[SelectedParameterPlot['Parameter'] != parameter_name]
    else:
        return

class TreeviewEdit(ttk.Treeview):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)

        self.bind("<Double-Button-1>", self.selectChoice)

    def selectChoice(self, event):
        # The Region that was clicked
        clickedRegion = self.identify_region(event.x, event.y)
        # Filter not needed Regions
        if clickedRegion != "cell":
            return

        column = self.identify_column(event.x)
        columnIndex = int(column[1:]) - 1
        selected_iid = self.focus()
        selectedValues = self.item(selected_iid)
        print(selectedValues)
        if selectedValues["values"] == '':
            return
        elif column in ("#0", "#1"):
            return
        else:
            selected_text = selectedValues.get("values")[columnIndex]

        if selected_text =='( )' and column == '#2':
            curren_values = self.item(selected_iid).get("values")
            curren_values[columnIndex] = '(X)'
            self.item(selected_iid, values=curren_values)
            add_simulation_parameter(selectedValues)
            ParameterSetupTab.refresh_all_tables()
            print(SelectedParameterSim)
        elif selected_text =='( )' and column == '#3':
            curren_values = self.item(selected_iid).get("values")
            curren_values[columnIndex] = '(X)'
            self.item(selected_iid, values=curren_values)
            add_plot_parameter(selectedValues)
            print(SelectedParameterPlot)
        elif selected_text =='(X)' and column== '#2':
            curren_values = self.item(selected_iid).get("values")
            curren_values[columnIndex] = '( )'
            self.item(selected_iid, values=curren_values)
            remove_simulation_parameter(selectedValues)
            ParameterSetupTab.refresh_all_tables()
            print(SelectedParameterSim)
        elif selected_text =='(X)' and column== '#3':
            curren_values = self.item(selected_iid).get("values")
            curren_values[columnIndex] = '( )'
            self.item(selected_iid, values=curren_values)
            remove_plot_parameter(selectedValues)
            print(SelectedParameterPlot)

class TreeviewEdit2(ttk.Treeview):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)

        self.bind("<Double-Button-1>", self.selectChoice)

    def selectChoice(self, event):
        # The Region that was clicked
        clickedRegion = self.identify_region(event.x, event.y)
        # Filter not needed Regions
        if clickedRegion != "cell":
            return

        column = self.identify_column(event.x)
        columnIndex = int(column[1:]) - 1
        selected_iid = self.focus()
        selectedValues = self.item(selected_iid)
        print(selectedValues)
        if selectedValues["values"] == '':
            return
        elif column in ("#0", "#1"):
            return
        else:
            selected_text = selectedValues.get("values")[columnIndex]

        if selected_text =='( )' and column == '#2':
            curren_values = self.item(selected_iid).get("values")
            curren_values[columnIndex] = '(X)'
            self.item(selected_iid, values=curren_values)
            add_plot_parameter(selectedValues)
            print(SelectedParameterPlot)
        elif selected_text =='(X)' and column== '#2':
            curren_values = self.item(selected_iid).get("values")
            curren_values[columnIndex] = '( )'
            self.item(selected_iid, values=curren_values)
            remove_plot_parameter(selectedValues)
            print(SelectedParameterPlot)

def ParameterSelectTab(element_list, tabview):

    treeview = TreeviewEdit(master=tabview.tab("Select Simulation Parameter"))
    treeview.pack(expand=True, fill=tk.BOTH)

    treeview["columns"] = ("Parameter", "Load to Simulation Setup", "Plot")
    treeview.column("#0", width=150, minwidth=150)
    treeview.column("Parameter", anchor="w", width=100)
    treeview.column("Load to Simulation Setup", anchor="w", width=150)
    treeview.column("Plot", anchor="w", width=50)

    treeview.heading("#0", text="Name", anchor="w")
    treeview.heading("Parameter", text="Parameter", anchor="w")
    treeview.heading("Load to Simulation Setup", text="Load to Simulation Setup", anchor="w")
    treeview.heading("Plot", text="Plot", anchor="w")

    for element in element_list:
        name = element.pop("Name")
        item_id = treeview.insert(parent="", index=tk.END, text=name)

        for key, value in element.items():
            treeview.insert(item_id, index=tk.END, text=key, values=(value, '( )', '( )'))

def PlotSelectTab(element_list, tabview):

    treeview = TreeviewEdit2(master=tabview.tab("Select Plot Variable"))
    treeview.pack(expand=True, fill=tk.BOTH)

    treeview["columns"] = ("Continuous Variable Value", "Plot")
    treeview.column("#0", width=150, minwidth=150)
    treeview.column("Continuous Variable Value", anchor="w", width=50)
    treeview.column("Plot", anchor="w", width=50)

    treeview.heading("#0", text="Name", anchor="w")
    treeview.heading("Continuous Variable Value", text="Continuous Variable Value", anchor="w")
    treeview.heading("Plot", text="Plot", anchor="w")

    for element in element_list:
        name = element.pop("Name")
        item_id = treeview.insert(parent="", index=tk.END, text=name)

        for key, value in element.items():
            treeview.insert(item_id, index=tk.END, text=key, values=(value,'( )'))

class ParameterSetupTab:
    instances = []  # Klassenvariable, die alle Instanzen speichert
    def __init__(self, tab1, mod):
        global SelectedParameterSim
        global SelectedParameterPlot
        global solver
        global startTime
        global stopTime
        global stepTime
        ParameterSetupTab.instances.append(self)
        self.input_fields = []
        self.iteration_labels = []
        self.checkbuttons = []
        self.check_vars = []
        self.tabview = tab1
        self.mod = mod
        self.input_fields = []
        self.new_window = None

        self.tabview.columnconfigure(0, weight=1)
        self.tabview.columnconfigure(1, weight=1)
        self.tabview.columnconfigure(2, weight=1)
        self.tabview.columnconfigure(3, weight=1)
        self.tabview.rowconfigure(0, weight=1)
        self.tabview.rowconfigure(1, weight=1)
        self.tabview.rowconfigure(2, weight=1)
        self.tabview.rowconfigure(3, weight=1)
        #self.tabview.grid(sticky='nsew')

        self.tree = ttk.Treeview(master=self.tabview)

        self.iteration_frame = tk.LabelFrame(self.tabview, text='Edit Iteration Parameters')
        self.iteration_frame.grid(row=3, column=0, columnspan=4, sticky="nesw", padx=20, pady=20)

        self.refresh_columns()
        self.refresh_table()
        #remove empty column that is the identifier of the item
        self.tree['show'] = 'headings'
        #self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.grid(row=1, column=0, columnspan=4, sticky = 'nswe', padx=20, pady=20)



        self.refresh_input_fields()

        # LabelFrame Simulation Buttons
        simulation_frame = tk.LabelFrame(self.tabview)
        simulation_frame.grid(row=2, column=0, columnspan=4, sticky="nesw", padx=20, pady=20)
        spalten_button = ttk.Button(master=simulation_frame, text="Add Column", command=self.add_column)
        spalten_button.grid(row=2, column=0, padx=10, pady=10)

        entfernen_button = ttk.Button(master=simulation_frame, text="Remove Last Column", command=self.remove_column)
        entfernen_button.grid(row=2, column=1, padx=10, pady=10)

        aktualisieren_button = ttk.Button(master=simulation_frame, text="Update Values", command=self.update_values)
        aktualisieren_button.grid(row=2, column=2, padx=10, pady=10)

        simulate_button = ttk.Button(master=simulation_frame, text="Start Simulation", command=self.simulate)
        simulate_button.grid(row=2, column=3, padx=10, pady=10)

        def Selection_Solver(event):
            global solver
            solver = solver_choice.get()
            print(f"Selected solver: {solver}")

        def write_SimSetting(event):
            global startTime
            global stopTime
            global stepTime

            startTime = startTimeEntry.get()
            stopTime = stopTimeEntry.get()
            stepTime = stepTimeEntry.get()
            print(f"Simulation parameters set — StartTime: {startTime}; StopTime: {stopTime}; StepTime: {stepTime}")

        def open_new_window(event):
            if self.new_window is None or not tk.Toplevel.winfo_exists(self.new_window):
                self.new_window = tk.Toplevel()
                self.new_window.title("Plot Window")
            else:
                self.new_window.destroy()
                self.new_window = None


        button = ttk.Button(master=simulation_frame, text="Plot Window")  # , command = write_SimSetting()
        button.grid(row=2, column=4, padx=10, pady=10)
        button.bind('<Button-1>', open_new_window)

        simulationsetup_frame = tk.LabelFrame(self.tabview, text='Simulation Parameter')
        simulationsetup_frame.grid(row=0, column=0, columnspan=4, sticky="nesw", padx=20, pady=20)

        solver_choice = ttk.Combobox(simulationsetup_frame, values=["ida", "cvode", "dassl"])
        solver_choice.grid(row=1, column=2, padx=10, pady=10)
        title_solver_choice = ttk.Label(simulationsetup_frame, text='Solver')
        title_solver_choice.grid(row=0, column=2, padx=10, pady=5)
        solver_choice.bind('<<ComboboxSelected>>', Selection_Solver)

        # Start Time Choice
        title_start_time= ttk.Label(simulationsetup_frame, text='StartTime')
        title_start_time.grid(row=0, column=0, padx=10, pady=5)
        startTimeEntry = ttk.Entry(simulationsetup_frame)
        startTimeEntry.insert(0, '0')
        # Focus the range that will be selected
        startTimeEntry.select_range(0, tk.END)
        # Focus cursor on selected range
        #startTime.focus()
        startTimeEntry.grid(row=1, column=0, padx=10, pady=10)

        # Stop Time Choice
        title_stop_time = ttk.Label(simulationsetup_frame, text='StopTime')
        title_stop_time.grid(row=0, column=1, padx=10, pady=5)
        stopTimeEntry = ttk.Entry(simulationsetup_frame)
        stopTimeEntry.insert(0, '300')
        # Focus the range that will be selected
        stopTimeEntry.select_range(0, tk.END)
        # Focus cursor on selected range
        # stopTime.focus()
        stopTimeEntry.grid(row=1, column=1, padx=10, pady=10)

        # Step Time Choice
        title_step_time = ttk.Label(simulationsetup_frame, text='Number of Steps')
        title_step_time.grid(row=0, column=3, padx=10, pady=5)
        stepTimeEntry = ttk.Entry(simulationsetup_frame)
        stepTimeEntry.insert(0, '300')
        # Focus the range that will be selected
        stepTimeEntry.select_range(0, tk.END)
        # Focus cursor on selected range
        # stepTime.focus()
        stepTimeEntry.grid(row=1, column=3, padx=10, pady=10)

        # Confirm Simulation Parameter
        button = ttk.Button(simulationsetup_frame, text="Confirm Parameter") #, command = write_SimSetting()
        button.grid(row=1, column=4, padx=10, pady=10)
        button.bind('<Button-1>', write_SimSetting)



    def simulate(self):
        mod = self.mod
        simulate(SelectedParameterSim, SelectedParameterPlot, solver, startTime, stopTime, stepTime, mod)

    def plot_result(self, var, number):
        mod = self.mod
        if var.get() == 1:
            if not hasattr(self, 'fig'):
                self.fig = Figure(figsize=(5, 4), dpi=100)
                self.ax = self.fig.add_subplot(111)

            if not hasattr(self, 'plot_refs'):
                self.plot_refs = {}

            if number in self.plot_refs:
                for line in self.plot_refs[number]:
                    line.remove()
                del self.plot_refs[number]

            self.plot_refs[number] = []
            for index, row in SelectedParameterPlot.iterrows():
                try:
                    time_var, parameter = mod.getSolutions(['time', row['Parameter']],
                                                           resultfile=f"{Project_path}/{modelicamodelname}{number}.mat")
                    line, = self.ax.plot(time_var, parameter, label=f"{row['Parameter']} {number}")
                    self.plot_refs[number].append(line)
                except Exception as e:
                    print("Simulation not yet started or an error occurred:", e)

            self.ax.relim()
            self.ax.autoscale_view()
            self.ax.legend()
            if not hasattr(self, 'canvas'):
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.new_window)
                self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            self.canvas.draw()
        else:
            if hasattr(self, 'plot_refs') and number in self.plot_refs:
                for line in self.plot_refs[number]:
                    line.remove()
                del self.plot_refs[number]

                self.ax.relim()
                self.ax.autoscale_view()
                self.ax.legend()
                self.canvas.draw()

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, row in SelectedParameterSim.iterrows():
            row_values = tuple(row)
            self.tree.insert("", tk.END, values=row_values)
        self.tree['show'] = 'headings'

    def refresh_columns(self):
        self.tree["columns"] = list(SelectedParameterSim.columns)
        for col in SelectedParameterSim.columns:
            self.tree.column(col,stretch=NO, width=150)
            self.tree.heading(col, text=col)
        self.tree['show'] = 'headings'

    def add_column(self):
        new_column = f"Iteration {len(SelectedParameterSim.columns)}"
        SelectedParameterSim[new_column] = pd.NA
        self.refresh_columns()
        self.refresh_table()
        self.refresh_input_fields()

    def remove_column(self):
        if len(SelectedParameterSim.columns) > 2:
            SelectedParameterSim.drop(columns=[SelectedParameterSim.columns[-1]], inplace=True)
            self.refresh_columns()
            self.refresh_table()
            self.refresh_input_fields()

    def refresh_input_fields(self):
        for entry in self.input_fields:
            entry.destroy()
        self.input_fields.clear()

        if hasattr(self, 'iteration_labels'):
            for label in self.iteration_labels:
                label.destroy()
            self.iteration_labels.clear()
        else:
            self.iteration_labels = []

        if len(SelectedParameterSim.columns[1:]) < len(self.checkbuttons):
            self.checkbuttons[-1].destroy()
            self.checkbuttons.pop()
            self.check_vars.pop()

        for i, col in enumerate(SelectedParameterSim.columns[1:], start=1):
            entry = ttk.Entry(master=self.iteration_frame)
            entry.grid(row=1, column=i - 1, padx=10, pady=10)
            self.input_fields.append(entry)

            label = ttk.Label(master=self.iteration_frame, text=f"Iteration {i}")
            label.grid(row=0, column=i - 1, padx=10, pady=10)
            self.iteration_labels.append(label)

            if i > len(self.checkbuttons):
                check_var = tk.IntVar()
                plot_checkbutton = tk.Checkbutton(master=self.iteration_frame, text=f"Plot Iteration {i}",
                                                  variable=check_var,
                                                  command=lambda i=i: self.plot_result(check_var, i))
                plot_checkbutton.grid(row=2, column=i - 1, padx=10, pady=10)
                self.checkbuttons.append(plot_checkbutton)
                self.check_vars.append(check_var)


    def update_values(self):
        selected_row = self.tree.selection()
        if selected_row:
            item = self.tree.item(selected_row)
            parameter = item['values'][0]
            new_values = [entry.get() for entry in self.input_fields]
            for i, col in enumerate(SelectedParameterSim.columns[1:], start=1):
                if i <= len(new_values):
                    SelectedParameterSim.loc[SelectedParameterSim["Parameter"] == parameter, col] = new_values[i - 1]
            self.refresh_table()
            print(SelectedParameterSim)

    @classmethod
    def refresh_all_tables(cls):
        for instance in cls.instances:
            instance.refresh_table()
            instance.refresh_columns()

class ApplicationGUI:
    def __init__(self):
        ctk.set_appearance_mode("light")  # Modes: system (default), light, dark
        ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

        self.root = tk.Tk()
        self.root.title("Parameter Simulation Center - Modelica")
        self.root.geometry("1200x800")

        self.tabview = ctk.CTkTabview(master=self.root, fg_color="#F0F0F0", border_color='#BDBDBD', border_width=1, width=1100, height=600)
        self.tabview.pack(padx=20, pady=20)

        self.tabview.add("Select Simulation Parameter")
        self.tabview.add("Select Plot Variable")
        self.tab1 = self.tabview.add("Simulation Setup")

        mod = startModelica()
        ParameterSelectTab(getParameterModelica_Data(mod), self.tabview)
        PlotSelectTab(getContinuousModelica_Data(mod), self.tabview)
        self.parameter_setup_tab = ParameterSetupTab(self.tab1, mod)

    def run(self):
        self.root.mainloop()