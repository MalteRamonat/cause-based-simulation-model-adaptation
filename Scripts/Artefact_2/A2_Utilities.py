import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pandas as pd
import Config
from sensor_simvar_mapping import create_mapping_table


def createNameList(inputList,indices):
   counter = 0
   outList = ['']*len(inputList)
   for name in inputList:
      for i in indices:
         if outList[counter] == None:
            outList[counter]+=name[i]
         else:
            outList[counter]+=name[i]
      counter+=1
   return outList 


def create_Testcase_from_Comparison_Results(
    comparison_result_file_scaled=Config.comparison_result_file_scaled, 
    Mapping_File=Config.Mapping_file_between_Comparison_and_RCA, 
    designations_file=Config.rca_designations,
    residual_output_file=Config.residual_output_file,
    deviation_output_file=Config.deviation_output_file,
    tolerance_threshold=Config.tolerance_threshold,
    testcase_directory=Config.testcase_directory,
    testcase_number=1
    ):
    # load dataframes
    comparison_results_df= pd.read_csv(comparison_result_file_scaled)
    designations_df = pd.read_excel(designations_file)
    mapping_df = pd.read_excel(Mapping_File)
    #Column 'Name' needs an additional "_mae" at the end of each row name because the comparison_results_df has this naming convention
    mapping_df['Name'] = mapping_df['Name'] + '_mae'
    # 1. Filter Dataframe based on the required sensors found in config
    # keep only those columns in the df that are in column 'Name' of the designations_df
    filter_columns = mapping_df['Name'].tolist()
    # filter the comparison_results_df based on the filter_columns
    comparison_results_df = comparison_results_df[filter_columns]
    # 2. bring Dataframe into the order needed in the ModVA_Designations.xlsx found in config
    designations_df['Combined_Name'] = designations_df['Type'] + designations_df['Tag'].astype(str) + designations_df['Suffix']
    # 2. Erstelle ein Mapping von den Namen in comparison_results_df zu den Namen in designations_df

    mapping_dict = dict(zip(mapping_df['Name'], mapping_df['A2_Name']))
    # 3. Filtere die Spalten in comparison_results_df basierend auf den gemappten Namen
    comparison_results_df = comparison_results_df.rename(columns=mapping_dict)
    # 4. Sortiere die Spalten in comparison_results_df entsprechend der Reihenfolge in designations_df
    ordered_columns = designations_df['Combined_Name'].tolist()
    # delete all entries from ordered columns that are not in the columns of comparison_results_df but do not change the order of the entries in ordered_columns
    ordered_columns = [col for col in ordered_columns if col in comparison_results_df.columns]
    
    
    comparison_results_df = comparison_results_df[ordered_columns]
    # Aufteilen in Aktoren und Sensoren, Aktoren haben "State" in ihrem Namen
    actuator_columns = [col for col in comparison_results_df.columns if '_State' in col]
    sensor_columns = [col for col in comparison_results_df.columns if col not in actuator_columns]
    # 5. Erstelle ein neues DataFrame mit den Aktoren und Sensoren in separaten Spalten
    sensor_df = comparison_results_df[sensor_columns]
    
    # 3. Save dataframe as xlsx file without headers and index
    sensor_df.to_excel(f'{testcase_directory}/Testcase_{testcase_number}/{residual_output_file}', index=False, header=False)
    print(f"Saved residual file for Testcase {testcase_number} as {residual_output_file} in {testcase_directory}/Testcase_{testcase_number}/")
    # 4. Set a tolerance threshold in the config and set all values above this threshold to 1 and all values below to 0
    sensor_df = sensor_df.applymap(lambda x: 1 if x > tolerance_threshold else 0)
    # 5. save the dataframe as an xlsx file with headers and index  
    sensor_df.to_excel(f'{testcase_directory}/Testcase_{testcase_number}/{deviation_output_file}', index=False, header=False)
    print(f"Saved deviation file for Testcase {testcase_number} as {deviation_output_file} in {testcase_directory}/Testcase_{testcase_number}/")


    
def create_actuator_file_for_testcase(
   actuator_raw_file=Config.comparison_result_actuator_positions_file,
   Mapping_File=Config.Mapping_file_between_Comparison_and_RCA, 
   designations_file=Config.rca_designations,
   actuator_output_file=Config.actuator_output_file,
   testcase_directory=Config.testcase_directory,
   testcase_number=1
   ):
   #1 load the actuator file from the comparison results
   actuator_df = pd.read_csv(actuator_raw_file)
   #2 translate columns to clearnames via mapping_df
   mapping_table = create_mapping_table()
   #2.1 create a mapping dict from the mapping_table
   mapping_dict = dict(zip(mapping_table['Sensor_OPCUA_Node_ID'], mapping_table['Name']))
   #2.2 rename the columns of the actuator_df based on the mapping_dict
   actuator_df = actuator_df.rename(columns=mapping_dict)
   #3 create a mapping dict between clearnames and the designations based on the Mapping_File
   rca_mapping_table = pd.read_excel(Mapping_File)
   #3.1 create a mapping dict from the mapping_table
   rca_mapping_dict = dict(zip(rca_mapping_table['Name'], rca_mapping_table['A2_Name']))
   #3.2 rename the columns of the actuator_df based on the mapping_dict
   actuator_df = actuator_df.rename(columns=rca_mapping_dict)
   #form a comined column in the  designations_df
   designations_df= pd.read_excel(designations_file)
   designations_df['Combined_Name'] = designations_df['Type'] + designations_df['Tag'].astype(str) + designations_df['Suffix']
   #keep only those entries in designations_df that have the value "_State" in the column 'Combined_Name'
   designations_df = designations_df[designations_df['Combined_Name'].str.contains('_State')]
   #4. filter the actuator_df: only keep the columns that are in the designations_df['Combined_Name']
   actuator_df = actuator_df[designations_df['Combined_Name'].tolist()]
   actuator_df = actuator_df * 100 # scale from fraction to percentage
   # Choke valve has a much smaller range; apply additional 10× scaling
   actuator_df['V301_State'] = actuator_df['V301_State'] * 10
   # 5. Save dataframe as xlsx file without headers and index
   actuator_df.to_excel(f'{testcase_directory}/Testcase_{testcase_number}/{actuator_output_file}', index=False, header=False)
   print(f"Saved actuator file for Testcase {testcase_number} as {actuator_output_file} in {testcase_directory}/Testcase_{testcase_number}/")
   

    
    
def main():
    
   create_actuator_file_for_testcase(testcase_number=5)
   create_Testcase_from_Comparison_Results(testcase_number=5)

if __name__ == "__main__":
    main()