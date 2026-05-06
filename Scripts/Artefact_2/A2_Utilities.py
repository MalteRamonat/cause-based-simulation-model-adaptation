import sys
import os
from typing import Dict, List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pandas as pd
import Config
from sensor_simvar_mapping import create_mapping_table


def createNameList(input_list: List[str], indices: List[int]) -> List[str]:
    """Extract characters at given indices from each string and concatenate them.

    Args:
        input_list: List of strings to process.
        indices: Character positions to extract from each string.

    Returns:
        List of concatenated substrings, one per input string.
    """
    return [''.join(name[i] for i in indices) for name in input_list]


def _load_and_map_columns(df: pd.DataFrame, mapping_dict: Dict[str, str],
                          ordered_columns: List[str]) -> pd.DataFrame:
    """Rename columns and return only those present in ordered_columns (preserving order).

    Args:
        df: Source DataFrame.
        mapping_dict: Mapping from current column names to new names.
        ordered_columns: Desired column order; columns not in df are silently skipped.

    Returns:
        Renamed and reordered DataFrame.
    """
    df = df.rename(columns=mapping_dict)
    ordered_columns = [col for col in ordered_columns if col in df.columns]
    return df[ordered_columns]


def create_Testcase_from_Comparison_Results(
    comparison_result_file_scaled=Config.comparison_result_file_scaled,
    Mapping_File=Config.Mapping_file_between_Comparison_and_RCA,
    designations_file=Config.rca_designations,
    residual_output_file=Config.residual_output_file,
    deviation_output_file=Config.deviation_output_file,
    tolerance_threshold=Config.tolerance_threshold,
    testcase_directory=Config.testcase_directory,
    testcase_number: int = 1
) -> None:
    """Convert scaled comparison results to residual and deviation Excel files for a test case.

    Args:
        comparison_result_file_scaled: Path to the scaled MAE comparison CSV.
        Mapping_File: Excel file mapping comparison column names to RCA names.
        designations_file: Excel file defining sensor ordering and naming.
        residual_output_file: Output filename for the residual Excel file.
        deviation_output_file: Output filename for the deviation (0/1) Excel file.
        tolerance_threshold: Values above this are flagged as 1 (deviation), others as 0.
        testcase_directory: Root directory containing per-testcase subdirectories.
        testcase_number: Index of the testcase subdirectory to write into.
    """
    comparison_results_df = pd.read_csv(comparison_result_file_scaled)
    designations_df = pd.read_excel(designations_file)
    mapping_df = pd.read_excel(Mapping_File)

    # Append the '_mae' suffix used by the comparison results naming convention
    mapping_df['Name'] = mapping_df['Name'] + '_mae'
    comparison_results_df = comparison_results_df[mapping_df['Name'].tolist()]

    designations_df['Combined_Name'] = (
        designations_df['Type'] + designations_df['Tag'].astype(str) + designations_df['Suffix']
    )
    mapping_dict = dict(zip(mapping_df['Name'], mapping_df['A2_Name']))
    ordered_columns = designations_df['Combined_Name'].tolist()

    comparison_results_df = _load_and_map_columns(comparison_results_df, mapping_dict, ordered_columns)

    sensor_columns = [col for col in comparison_results_df.columns if '_State' not in col]
    sensor_df = comparison_results_df[sensor_columns]

    out_dir = f'{testcase_directory}/Testcase_{testcase_number}'
    sensor_df.to_excel(f'{out_dir}/{residual_output_file}', index=False, header=False)
    print(f"Saved residual file for Testcase {testcase_number} as {residual_output_file} in {out_dir}/")

    deviation_df = sensor_df.map(lambda x: 1 if x > tolerance_threshold else 0)
    deviation_df.to_excel(f'{out_dir}/{deviation_output_file}', index=False, header=False)
    print(f"Saved deviation file for Testcase {testcase_number} as {deviation_output_file} in {out_dir}/")


def create_actuator_file_for_testcase(
    actuator_raw_file=Config.comparison_result_actuator_positions_file,
    Mapping_File=Config.Mapping_file_between_Comparison_and_RCA,
    designations_file=Config.rca_designations,
    actuator_output_file=Config.actuator_output_file,
    testcase_directory=Config.testcase_directory,
    testcase_number: int = 1,
    scale_factor: float = 100.0,
    special_scaling: Optional[Dict[str, float]] = None
) -> None:
    """Extract and scale actuator positions into an Excel file for a test case.

    Args:
        actuator_raw_file: Path to the CSV with raw actuator positions (0–1 range).
        Mapping_File: Excel file mapping comparison names to RCA names.
        designations_file: Excel file defining actuator ordering and naming.
        actuator_output_file: Output filename for the actuator Excel file.
        testcase_directory: Root directory containing per-testcase subdirectories.
        testcase_number: Index of the testcase subdirectory to write into.
        scale_factor: Multiplier to convert 0–1 fraction to percentage. Default 100.
        special_scaling: Optional per-column extra scaling applied after scale_factor.
            Defaults to {'V301_State': 10} for the choke valve's smaller range.
    """
    if special_scaling is None:
        special_scaling = {'V301_State': 10}

    mapping_table = create_mapping_table()
    opcua_mapping = dict(zip(mapping_table['Sensor_OPCUA_Node_ID'], mapping_table['Name']))

    rca_mapping_df = pd.read_excel(Mapping_File)
    rca_mapping_dict = dict(zip(rca_mapping_df['Name'], rca_mapping_df['A2_Name']))

    designations_df = pd.read_excel(designations_file)
    designations_df['Combined_Name'] = (
        designations_df['Type'] + designations_df['Tag'].astype(str) + designations_df['Suffix']
    )
    state_columns = designations_df[
        designations_df['Combined_Name'].str.contains('_State')
    ]['Combined_Name'].tolist()

    actuator_df = pd.read_csv(actuator_raw_file)
    # Two-step rename: OPC UA node IDs → clear names → RCA names, then filter to State columns
    actuator_df = actuator_df.rename(columns=opcua_mapping)
    actuator_df = _load_and_map_columns(actuator_df, rca_mapping_dict, state_columns)

    actuator_df = actuator_df * scale_factor
    for col, extra in special_scaling.items():
        if col in actuator_df.columns:
            actuator_df[col] = actuator_df[col] * extra

    out_dir = f'{testcase_directory}/Testcase_{testcase_number}'
    actuator_df.to_excel(f'{out_dir}/{actuator_output_file}', index=False, header=False)
    print(f"Saved actuator file for Testcase {testcase_number} as {actuator_output_file} in {out_dir}/")


def main() -> None:
    create_actuator_file_for_testcase(testcase_number=5)
    create_Testcase_from_Comparison_Results(testcase_number=5)


if __name__ == "__main__":
    main()
