"""
OpenModelica interface utilities.

Provides functions to start a Modelica session, set parameters, run simulations,
and retrieve result files. Used by both Artefact 1 (Model_Initialization) and
Artefact 3 (Bayesian parameter adaptation).
"""

import os
import shutil
import time
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
from OMPython import OMCSessionZMQ
from OMPython import ModelicaSystem
from Config import (
    TEMP_PATH,
    MODELICA_FILE_DIR,
    RESULT_FILE_NAME,
    MODELICA_MODEL_NAME,
    MODELICA_FILE_NAME,
    MODEL_BUILD_DIR,
    SIMULATION_RESULTS_DIR,
)


def start_modelica():
    """Create and return an initialized Modelica system object.

    Returns:
        ModelicaSystem: Loaded and built Modelica model ready for simulation.
    """
    omc = OMCSessionZMQ()
    print("Loading Modelica model...")
    print(omc.sendExpression("getVersion()"))
    print(omc.sendExpression("cd()"))
    modelica_file = str(MODELICA_FILE_DIR / MODELICA_FILE_NAME)
    mod = ModelicaSystem(modelica_file, MODELICA_MODEL_NAME)
    print(modelica_file)
    mod.setSimulationOptions(["outputFormat=csv"])
    mod.getSimulationOptions()
    mod.buildModel()
    return mod


def get_modelica_parameter_data(mod):
    """Retrieve all component parameters from the loaded Modelica model.

    Args:
        mod: ModelicaSystem instance.

    Returns:
        List of component dicts, each augmented with its parameter key-value pairs.
    """
    components = get_components_dict(mod)
    parameters = mod.getParameters()
    print(parameters)
    for element in components:
        name = element["Name"]
        for key, value in parameters.items():
            if key.startswith(name + "."):
                element[key] = value
    return components


def change_to_temporary_directory():
    """Change the working directory to a model-specific temp directory."""
    tmp_dir = tempfile.mkdtemp(
        dir=str(MODEL_BUILD_DIR),
        prefix=MODELICA_MODEL_NAME + "_",
        suffix="",
    )
    os.chdir(tmp_dir)
    print(f"Working in {tmp_dir}")


def change_to_project_directory():
    """Change the working directory back to the Modelica model directory."""
    os.chdir(str(MODELICA_FILE_DIR))
    print(f"Working in {MODELICA_FILE_DIR}")


def get_modelica_continuous_data(mod):
    """Retrieve all continuous (state/output) variables from the loaded model.

    Args:
        mod: ModelicaSystem instance.

    Returns:
        List of component dicts augmented with continuous variable values.
    """
    components = get_components_dict(mod)
    continuous  = mod.getContinuous()
    for element in components:
        name = element["Name"]
        for key, value in continuous.items():
            if key.startswith(name + "."):
                element[key] = value
    return components


def set_parameters(mod, parameter_dict):
    """Apply a parameter dictionary to the Modelica model.

    Accepts either a list of component dicts (GUI format) or a flat key-value
    dict (Initialize_Simulation format).

    Args:
        mod: ModelicaSystem instance.
        parameter_dict: List of component dicts or a flat {param: value} dict.
    """
    for element in parameter_dict:
        if isinstance(element, dict) and "Name" in element:
            name = element["Name"]
            for key, value in element.items():
                if key.startswith(name + "."):
                    mod.setParameters(f"{key}={value}")
        else:
            for key, value in parameter_dict.items():
                mod.setParameters(f"{key}={value}")


def simulate(simulation_setup, selected_plot_params, solver, start_time, stop_time,
             step_count, mod, usage="GUI", output_format="csv"):
    """Run one or more Modelica simulations and retrieve the result files.

    Args:
        simulation_setup: DataFrame of parameters to sweep (GUI mode) or None.
        selected_plot_params: DataFrame of variables to plot (GUI mode) or None.
        solver: Modelica solver name (e.g. 'dassl').
        start_time: Simulation start time as string.
        stop_time: Simulation stop time as string.
        step_count: Number of communication points as string.
        mod: ModelicaSystem instance.
        usage: 'GUI' for parameter sweep mode; 'Initialize_Simulation' for single run.
        output_format: 'csv' or 'mat'.
    """
    print("Starting simulation...")
    if usage == "GUI":
        for i, iteration in enumerate(simulation_setup.columns[1:], start=1):
            print(f"Status: {iteration}")
            for _, row in simulation_setup.iterrows():
                print(f"Parameter: {row['Parameter']}, value: {row[iteration]}")
                mod.setParameters(f"{row['Parameter']}={row[iteration]}")
                print(mod.getParameters(f"{row['Parameter']}"))
            print("---")
            step_size = (int(stop_time) - int(start_time)) / int(step_count)
            mod.setSimulationOptions([
                f"startTime={start_time}",
                f"stopTime={stop_time}",
                f"stepSize={step_size}",
                f"solver={solver}",
                f"outputFormat={output_format}",
            ])
            print(mod.getSimulationOptions())
            mod.buildModel()
            t_start = time.time()
            result_file = f"{MODELICA_MODEL_NAME}{i}.mat"
            mod.simulate(resultfile=result_file)
            print(f"{round(time.time() - t_start, 2)} seconds.")
            get_result_file(result_file)
            print(f"{round(time.time() - t_start, 2)} seconds total.")
        plt.show()

    elif usage == "Initialize_Simulation":
        step_size = (int(stop_time) - int(start_time)) / int(step_count)
        mod.setSimulationOptions([
            f"startTime={start_time}",
            f"stopTime={stop_time}",
            f"stepSize={step_size}",
            f"solver={solver}",
            f"outputFormat={output_format}",
        ])
        print(mod.getSimulationOptions())
        mod.buildModel()
        t_start = time.time()
        result_file = f"{MODELICA_MODEL_NAME}_res.{output_format}"
        mod.simulate(resultfile=result_file)
        print(f"Simulation finished. Result file: {result_file}")
        print(f"{round(time.time() - t_start, 2)} seconds.")
        get_result_file(result_file)
        print(f"Total: {round(time.time() - t_start, 2)} seconds.")
        plt.show()


def get_simulation_results(mod, variables_of_interest, resultfile):
    """Return simulation results as a Pandas DataFrame.

    Args:
        mod: ModelicaSystem instance.
        variables_of_interest: Variable name or list of names to extract.
        resultfile: Path to the result file.

    Returns:
        DataFrame with the requested variables.
    """
    return mod.getSolutions(["time", variables_of_interest], resultfile=resultfile)


def get_result_file(file):
    """Find the most recently written simulation result in the temp directory and move it.

    OpenModelica writes result files to a system temp directory. This function
    locates the newest matching file and moves it to SIMULATION_RESULTS_DIR.

    Args:
        file: File name to search for (e.g. 'TFS_Gasentspannung_res.csv').
    """
    latest_file_path = None
    latest_mod_time  = 0

    for root, dirs, files in os.walk(str(TEMP_PATH)):
        for fname in files:
            if fname == file:
                full_path = os.path.join(root, fname)
                mod_time  = os.path.getmtime(full_path)
                if mod_time > latest_mod_time:
                    latest_mod_time  = mod_time
                    latest_file_path = full_path

    if latest_file_path:
        destination = os.path.join(str(SIMULATION_RESULTS_DIR), file)
        print(f"Moving result file from {latest_file_path} to {destination}")
        shutil.move(latest_file_path, destination)
    else:
        print(f"No file named '{file}' found in {TEMP_PATH}.")


def get_components_dict(mod):
    """Parse the Modelica model's component list into a list of name/role dicts.

    Args:
        mod: ModelicaSystem instance.

    Returns:
        List of dicts with 'RoleType' and 'Name' keys for each model component.
    """
    components_raw = str(mod.sendExpression(f"getComponents({MODELICA_MODEL_NAME})"))
    components_raw = components_raw[1:-1]
    objects = components_raw.split("), (")

    df = pd.DataFrame(columns=[
        "RoleType", "Name", "Unknown", "Scope",
        "Bool1", "Bool2", "Bool3", "Bool4",
        "Specification", "Unknown2", "OutputType", "Unknown3",
    ])

    for obj in objects:
        obj = obj.strip("()")
        attributes = obj.split(", ")
        parsed = []
        for attr in attributes:
            if attr.startswith("'") and attr.endswith("'"):
                parsed.append(attr.strip("'"))
            elif attr == "True":
                parsed.append(True)
            elif attr == "False":
                parsed.append(False)
            elif attr == "()":
                parsed.append(None)
            else:
                parsed.append(attr)
        df.loc[len(df)] = parsed

    desired_keys = {"RoleType", "Name"}
    return [
        {k: v for k, v in record.items() if k in desired_keys}
        for record in df.to_dict("records")
    ]


def main():
    change_to_project_directory()
    mod = start_modelica()
    parameter_dict = get_modelica_parameter_data(mod)
    print(parameter_dict)
    simulate(
        simulation_setup=None,
        selected_plot_params=None,
        solver="ida",
        start_time="0",
        stop_time="100",
        step_count="100",
        mod=mod,
        usage="Initialize_Simulation",
    )


if __name__ == "__main__":
    main()
