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

# Closing the connection to the database
conn.close()






