import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pandas as pd
import Bayesian_Config


class DataProcessor:
    def __init__(self, eval_csv_location, bounds_csv_location):
        self.eval_csv_location = eval_csv_location
        self.bounds_csv_location = bounds_csv_location
        self.combined_df = None

    def load_and_combine_data(self):
        # Lade die CSV-Dateien
        eval_df = pd.read_csv(self.eval_csv_location)
        bounds_df = pd.read_csv(self.bounds_csv_location)

        # Sortiere das eval_df nach 'Improvement_of_Deviation' in absteigender Reihenfolge
        eval_df = eval_df.sort_values(by='Improvement_of_Deviation', ascending=False)

        # Merge the DataFrames based on the 'Parameter' column
        self.combined_df = pd.merge(eval_df, bounds_df, on='Parameter', how='left')
        return self.combined_df

    def filter_columns(self):
        columns_to_display = ['Parameter', 'Value', 'Value_after_single_Param_Optimization', 'Improvement_of_Deviation', 'Min_Bound', 'Max_Bound']
        self.combined_df = self.combined_df[columns_to_display]
        return self.combined_df

    def save_selected_data(self, selected_indices, output_location):
        if self.combined_df is not None:
            selected_df = self.combined_df.iloc[selected_indices]
            selected_df.to_csv(output_location, index=False)


class ApplicationGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Select Modelparameter and Bounds")
        self.root.geometry("1200x800")

        self.data_processor = DataProcessor(Bayesian_Config.evaluation_results_file_path, Bayesian_Config.current_bounds_file_path)
        self.evaluation_results_df = self.data_processor.load_and_combine_data()
        self.evaluation_results_df = self.data_processor.filter_columns()

        self.check_vars = []
        self.original_min_bounds = self.evaluation_results_df['Min_Bound'].copy()
        self.original_max_bounds = self.evaluation_results_df['Max_Bound'].copy()

        self.create_table()
        self.create_save_button()
        self.create_generate_bounds_button()
        self.create_move_buttons()
        self.entry = None
        self.current_item = None
        self.current_column = None

    def create_table(self):
        self.tree = ttk.Treeview(self.root, columns=("check", *self.evaluation_results_df.columns), show='headings')
        self.tree.pack(expand=True, fill='both')

        self.tree.heading("check", text="Select", anchor=tk.CENTER)
        for col in self.evaluation_results_df.columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, anchor=tk.CENTER, width=100)

        for index, row in self.evaluation_results_df.iterrows():
            check_var = tk.BooleanVar(value=True)
            self.check_vars.append(check_var)
            values = ["True" if check_var.get() else "False"] + list(row)
            self.tree.insert("", tk.END, values=values, tags=(str(index),))
            self.tree.tag_bind(str(index), "<ButtonRelease-1>", lambda event, idx=index: self.on_row_click(event, idx))
            self.tree.tag_bind(str(index), "<Double-1>", self.on_double_click)

        for col in self.tree["columns"]:
            self.tree.column(col, anchor=tk.CENTER)

    def create_move_buttons(self):
        move_up_button = tk.Button(self.root, text="Move Parameter up", command=self.move_selected_up)
        move_up_button.pack(pady=5)
        move_down_button = tk.Button(self.root, text="Move Parameter down", command=self.move_selected_down)
        move_down_button.pack(pady=5)

    def move_selected_up(self):
        selected_items = self.tree.selection()
        for item in selected_items:
            index = self.tree.index(item)
            if index > 0:
                self.tree.move(item, self.tree.parent(item), index - 1)
                self.evaluation_results_df = self.swap_rows(self.evaluation_results_df, index, index - 1)
        self.update_table()

    def move_selected_down(self):
        selected_items = self.tree.selection()
        for item in reversed(selected_items):
            index = self.tree.index(item)
            if index < len(self.tree.get_children()) - 1:
                self.tree.move(item, self.tree.parent(item), index + 1)
                self.evaluation_results_df = self.swap_rows(self.evaluation_results_df, index, index + 1)
        self.update_table()

    def swap_rows(self, df, index1, index2):
        df.iloc[[index1, index2]] = df.iloc[[index2, index1]].values
        return df

    def update_table(self):
        for i, item in enumerate(self.tree.get_children()):
            values = ["True" if self.check_vars[i].get() else "False"] + list(self.evaluation_results_df.iloc[i])
            self.tree.item(item, values=values)
    
    
    def on_row_click(self, event, index):
        column = self.tree.identify_column(event.x)
        if column == '#1':  # '#1' is the first column, which corresponds to 'check'
            self.check_vars[index].set(not self.check_vars[index].get())
            item = self.tree.selection()[0]
            values = list(self.tree.item(item, "values"))
            values[0] = "True" if self.check_vars[index].get() else "False"
            self.tree.item(item, values=values)

    def on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            col_num = int(column.replace("#", "")) - 1
            col_name = self.tree["columns"][col_num]
            if col_name in ["Min_Bound", "Max_Bound"]:
                self.edit_cell(item, col_num, col_name)

    def edit_cell(self, item, col_num, col_name):
        x, y, width, height = self.tree.bbox(item, column=f"#{col_num + 1}")
        value = self.tree.item(item, "values")[col_num]  # +1 because of the checkbox column

        self.entry = tk.Entry(self.root)
        self.entry.place(x=x, y=y, width=width, height=height)
        self.entry.insert(0, value)
        self.entry.focus()

        self.current_item = item
        self.current_column = col_num  # +1 because values list includes the checkbox column
        self.current_col_name = col_name

        self.entry.bind("<Return>", self.save_edit)

    def save_edit(self, event):
        new_value = self.entry.get()
        values = list(self.tree.item(self.current_item, "values"))
        values[self.current_column] = new_value
        self.tree.item(self.current_item, values=values)
        self.update_dataframe(self.current_item, self.current_col_name, new_value)
        self.entry.destroy()
        self.entry = None

    def update_dataframe(self, item, col_name, new_value):
        row_id = int(self.tree.item(item, "tags")[0])
        try:
            new_value = float(new_value)
        except ValueError:
            pass  # Handle the case where new_value is not a float
        self.evaluation_results_df.at[row_id, col_name] = new_value

    def create_save_button(self):
        save_button = tk.Button(self.root, text="Save", command=self.save_selected_rows)
        save_button.pack(pady=20)

    def create_generate_bounds_button(self):
        generate_button = tk.Button(self.root, text="Generate new Bounds based on Value after Optimization", command=self.generate_conti_bounds)
        generate_button.pack(pady=20)

    def generate_conti_bounds(self):
        if 'generated' not in self.__dict__:
            self.generated = False
        if not self.generated:
            self.conti_bounds_df = self.evaluation_results_df.copy()
            set_sigma = 0.1  # Beispielwert
            min_sigma = 0.05  # Beispielwert

            for index, row in self.conti_bounds_df.iterrows():
                parameter_value = float(row['Value_after_single_Param_Optimization'])
                sigma = abs(set_sigma * parameter_value)
                if parameter_value == 0:
                    min_bound = -3 * min_sigma
                    max_bound = 3 * min_sigma
                else:
                    min_bound = parameter_value - 3 * sigma
                    max_bound = parameter_value + 3 * sigma

                self.conti_bounds_df.at[index, 'Min_Bound'] = min_bound
                self.conti_bounds_df.at[index, 'Max_Bound'] = max_bound

            self.evaluation_results_df['Min_Bound'] = self.conti_bounds_df['Min_Bound']
            self.evaluation_results_df['Max_Bound'] = self.conti_bounds_df['Max_Bound']
            self.generated = True
        else:
            self.evaluation_results_df['Min_Bound'] = self.original_min_bounds
            self.evaluation_results_df['Max_Bound'] = self.original_max_bounds
            self.generated = False

        self.update_table()

    def update_table(self):
        for i, item in enumerate(self.tree.get_children()):
            values = ["True" if self.check_vars[i].get() else "False"] + list(self.evaluation_results_df.iloc[i])
            self.tree.item(item, values=values)

    def save_selected_rows(self):
        selected_indices = [i for i, var in enumerate(self.check_vars) if var.get()]
        if selected_indices:
            output_location = Bayesian_Config.user_defined_evaluation_results_file_path
            selected_df = self.evaluation_results_df.iloc[selected_indices]
            print(selected_df)
            selected_df.to_csv(output_location, index=False)
            messagebox.showinfo("Success", f"Selected rows saved to {output_location}.")
        else:
            messagebox.showwarning("Warning", "No rows selected.")

    def run(self):
        # Startet die Tkinter event loop
        self.root.mainloop()
        
        
if __name__ == "__main__":
    app = ApplicationGUI()
    app.run()