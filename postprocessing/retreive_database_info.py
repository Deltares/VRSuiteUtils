'''
This script is used to retreive information from the (relational) database and present it in a readable and
understandable format.
'''

# Importing necessary libraries
import sqlite3
import pandas as pd
from pathlib import Path

# Defining the path to the database
db_path = Path(r'n:\Projects\11209000\11209353\B. Measurements and calculations\008 - Resultaten Proefvlucht\ZZL\7-2\databases\database_bekleding_bovengrens\traject_7_2.db')

# Connecting to the database
conn = sqlite3.connect(db_path)

# obtain a list of all tables in the database
tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)

print("The database consists of the following", len(tables), "tables:")
print(tables)
print()

# Defining an SQL query
table_name_id = 26 # this is the optimization run
sql_query = 'SELECT * FROM {}'.format(tables.iloc[table_name_id].values[0])

# Retrieving the data from the database and write the optimization_type name and optimization_type_id to a dictionary:
optimization_type = pd.read_sql_query(sql_query, conn)
optimization_type_dict = dict(zip(optimization_type["name"], optimization_type["optimization_type_id"]))
print(optimization_type_dict)

# Retrieve from the database tab "OptimizationSelectedMeasure" the id and investment_year for all the
# measures for optimization_run_id = 1.
optimization_run_id = 1 # 1 is VRM, 2 is DSM
sql_query = 'SELECT * FROM OptimizationSelectedMeasure WHERE optimization_run_id = {}'.format(optimization_run_id)
selected_optimization_measure = pd.read_sql_query(sql_query, conn)
print(selected_optimization_measure)

# create a list of ids in the selected_optimization_measure
selected_measure_ids = selected_optimization_measure["id"].tolist()

# retrieve from the database tab "OptimizationStep" all rows where optimization_selected_measure_id is in selected_measure_ids
sql_query = 'SELECT * FROM OptimizationStep WHERE optimization_selected_measure_id IN ({})'.format(
    ', '.join([str(i) for i in selected_measure_ids]))
optimization_step = pd.read_sql_query(sql_query, conn)
# sort optimizationStep by id
optimization_step = optimization_step.sort_values(by="id")
print(optimization_step)

sql_query = 'SELECT * FROM OptimizationSelectedMeasure WHERE id IN ({})'.format(
    ', '.join([str(i) for i in optimization_step["optimization_selected_measure_id"].tolist()]))
optimization_selected_measure = pd.read_sql_query(sql_query, conn)


# add the "measure_result_id" + "investment_year" to the optimization_step dataframe. These can be found in the
# optimization_selected_measure dataframe. Don't add anything else from the optimization_selected_measure dataframe
# to the optimization_step dataframe.
optimization_step = pd.merge(optimization_step, optimization_selected_measure[["id", "measure_result_id", "investment_year"]],
                                left_on="optimization_selected_measure_id", right_on="id", how="left")
# drop the "id_y" column
optimization_step = optimization_step.drop(columns="id_y")
# rename the "id_x" column to "id"
optimization_step = optimization_step.rename(columns={"id_x": "id"})

# add MeasureResult where id matches optimization_step["measure_result_id"] to the optimization_step dataframe
sql_query = 'SELECT * FROM MeasureResult WHERE id IN ({})'.format(
    ', '.join([str(i) for i in optimization_step["measure_result_id"].tolist()]))
measure_result = pd.read_sql_query(sql_query, conn)
# add the "name" column from the measure_result dataframe to the optimization_step dataframe
optimization_step = pd.merge(optimization_step, measure_result[["id", "measure_per_section_id"]],
                                left_on="measure_result_id", right_on="id", how="left")


# add MeasurePerSection where id matches optimization_step["measure_per_section_id"] to the optimization_step dataframe
sql_query = 'SELECT * FROM MeasurePerSection WHERE id IN ({})'.format(
    ', '.join([str(i) for i in optimization_step["measure_per_section_id"].tolist()]))
measure_per_section = pd.read_sql_query(sql_query, conn)
# add the "section_id", "measure_id" column from the measure_per_section dataframe to the optimization_step dataframe
optimization_step = pd.merge(optimization_step, measure_per_section[["id", "section_id", "measure_id"]],
                                left_on="measure_per_section_id", right_on="id", how="left")

# Where id in SectionData matches section_id in optimization_step dataframe, add the "section_name" column to the
# optimization_step dataframe
sql_query = 'SELECT * FROM SectionData WHERE id IN ({})'.format(
    ', '.join([str(i) for i in optimization_step["section_id"].tolist()]))
section_data = pd.read_sql_query(sql_query, conn)
# add the "section_name" column from the section_data dataframe to the optimization_step dataframe
optimization_step = pd.merge(optimization_step, section_data[["id", "section_name"]],
                                left_on="section_id", right_on="id", how="left")
# drop the "id_y" column
optimization_step = optimization_step.drop(columns="id_y")
# rename the "id_x" column to "id"
optimization_step = optimization_step.rename(columns={"id_x": "id"})

# Where id in Measure matches measure_id  in optimization_step dataframe, add all columns (except id) to the
# optimization_step dataframe
sql_query = 'SELECT * FROM Measure WHERE id IN ({})'.format(
    ', '.join([str(i) for i in optimization_step["measure_id"].tolist()]))
measure = pd.read_sql_query(sql_query, conn)
# add the "section_name" column from the section_data dataframe to the optimization_step dataframe
optimization_step = pd.merge(optimization_step, measure, left_on="measure_id", right_on="id", how="left")
# drop the "id_y" column
optimization_step = optimization_step.drop(columns="id_y")
# rename the "id_x" column to "id"
optimization_step = optimization_step.rename(columns={"id_x": "id"})
print(optimization_step)

# get all unique values from the "name" column in measure_result_parameter
sql_query = 'SELECT DISTINCT name FROM MeasureResultParameter'
measure_result_parameter = pd.read_sql_query(sql_query, conn)
# print them as a list
print(measure_result_parameter["name"].tolist())
# add new columns to optimization_step named after measure_result_parameter["name"].tolist() and fill it with the value -999.0
for name in measure_result_parameter["name"].tolist():
    optimization_step[name] = -999.0

# now find for each id in optimization_step database where "measure_result_id" corresponds with "measure_result_id" in
# MeasureResultParameter. If the name in the column "name" in MeasureResultParameter corresponds with a column in
# optimization_step, fill the value from the "value" column in MeasureResultParameter in the corresponding column in
# optimization_step
sql_query = 'SELECT * FROM MeasureResultParameter WHERE measure_result_id IN ({})'.format(
    ', '.join([str(i) for i in optimization_step["measure_result_id"].tolist()]))
measure_result_parameter = pd.read_sql_query(sql_query, conn)
for index, row in measure_result_parameter.iterrows():
    if row["name"] in optimization_step.columns:
        optimization_step.loc[optimization_step["measure_result_id"] == row["measure_result_id"], row["name"]] = row["value"]

optimization_step.head()

# copy optimization_step to a new dataframe called "df_copy"
df_copy = optimization_step.copy()
# sort by optimization_selected_measure_id
df_copy = df_copy.sort_values(by="optimization_selected_measure_id")
# print df_copy where optimization_selected_measure_id ==703
print(df_copy[df_copy["optimization_selected_measure_id"] == 703])

# determine cost for optimization_step with id = 230. Subtract total_lcc where id = 230 from total_lcc where id = 229
# and print the result
print(df_copy[df_copy["id"] == 230]["total_lcc"].values[0] - df_copy[df_copy["id"] == 229]["total_lcc"].values[0])

# find the cost from MeasureResultSection where the measure_result_id matches measure_result_id in optimization_step df
# Then select only the cost where time = 0 and add these to a new column in optimization_step
sql_query = 'SELECT * FROM MeasureResultSection WHERE measure_result_id IN ({})'.format(
    ', '.join([str(i) for i in optimization_step["measure_result_id"].tolist()]))
measure_result_section = pd.read_sql_query(sql_query, conn)
# measure_result_section = measure_result_section[measure_result_section["time"] == 0] # klopt het om time=0 te gebruiken, of moet time gelijk zijn aan investment_year?
# the above line is incorrect. We don't want time == 0, but we want to select the cost where time == investment_year
# add the "cost" column from the measure_result_section dataframe to the optimization_step dataframe
# measure_result_section = measure_result_section[measure_result_section["time"] == optimization_step["investment_year"].values[0]]
# merge on measure_result_id, and add the cost column to optimization_step. The cost has several time steps. Merge on where
# time is equal to investment_year
optimization_step = pd.merge(optimization_step, measure_result_section[measure_result_section["time"] == optimization_step["investment_year"].values[0]][["measure_result_id", "cost"]],
                                left_on="measure_result_id", right_on="measure_result_id", how="left")
# optimization_step = pd.merge(optimization_step, measure_result_section[["measure_result_id", "cost"]],
#                                 left_on="measure_result_id", right_on="measure_result_id", how="left")
# rename cost to standalone_cost
optimization_step = optimization_step.rename(columns={"cost": "standalone_cost"})
optimization_step.head()

import numpy as np
# get a list of the unique sorted section_id in optimization_step
section_id_list = np.sort(optimization_step["section_id"].unique())
print(section_id_list)
# get a list of the unique sorted measure_type_id in optimization_step
measure_type_id_list = np.sort(optimization_step["measure_type_id"].unique())
print(measure_type_id_list)

# now add a column "marginal_cost" to optimization_step and fill it with the value -999.0
optimization_step["marginal_cost"] = -999.0
# for each section_id in section_id_list, find the rows in optimization_step where section_id == section_id. The
# marginal_cost is the difference between the standalone_cost of the current row and the standalone_cost of the previous
# with the same measure_type_id. If there is no previous row with the same measure_type_id, the marginal_cost is the same
# as the standalone_cost. Fill the marginal_cost column with the calculated values.
for section_id in section_id_list:
    for measure_type_id in measure_type_id_list:
        mask = (optimization_step["section_id"] == section_id) & (optimization_step["measure_type_id"] == measure_type_id)
        optimization_step.loc[mask, "marginal_cost"] = optimization_step[mask]["standalone_cost"].diff()
        optimization_step.loc[mask, "marginal_cost"] = optimization_step[mask]["marginal_cost"].fillna(optimization_step[mask]["standalone_cost"])

# add a colum "check_cost_total" to optimization_step and fill it with the value -999.0
# now per time step, calculate the check_cost_total for each step_number. The check_cost_total is the sum of the
# marginal_cost for each step_number. Fill the check_cost_total column with the calculated values.
optimization_step["check_cost_total"] = -999.0
# loop through the unique and sorted values of step_number in optimization_step
for step_number in np.sort(optimization_step["step_number"].unique()):
    # sum marginal costs of the current step_number
    step_cost = optimization_step[optimization_step["step_number"] == step_number]["marginal_cost"].sum()
    # fill the check_cost_total column with the calculated values + the check_cost_total of the previous step_number
    # if there is no previous step_number, fill the check_cost_total with the calculated value
    if step_number == 0:
        optimization_step.loc[optimization_step["step_number"] == step_number, "check_cost_total"] = step_cost
    else:
        optimization_step.loc[optimization_step["step_number"] == step_number, "check_cost_total"] = step_cost + optimization_step[optimization_step["step_number"] == step_number - 1]["check_cost_total"].values[0]

# find the exact step numbers this is not true: optimization_step["total_lcc"] == optimization_step["check_cost_total"]
# and save them to a list
step_number_list = optimization_step[optimization_step["total_lcc"] != optimization_step["check_cost_total"]]["step_number"].unique()


# now in optimization_step add a column check_cost, where check_cost is accumulated cost for each optimization_step
# so the first row will have the same value as cost, the second row will have the sum of the first and second row, etc.
optimization_step["check_cost"] = optimization_step["cost"].cumsum()
optimization_step.head()

# check if the check_cost column is equal to the total_lcc column
print(optimization_step["check_cost"] == optimization_step["total_lcc"])

# print last check_cost - total_lcc
print(optimization_step["check_cost_total"].values[-1] - optimization_step["total_lcc"].values[-1])

# count number of unique measure_result_id in optimization_step
print(optimization_step["measure_result_id"].nunique())

# now for

# get the discount_rate from OptimizationRun
optimization_run_id
sql_query = 'SELECT * FROM OptimizationRun WHERE optimization_run_id = {}'.format(optimization_run_id)
optimization_run = pd.read_sql_query(sql_query, conn)
discount_rate = optimization_run["discount_rate"].values[0]


# Closing the connection to the database
conn.close()






