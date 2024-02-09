'''
This script is used to retreive information from the (relational) database and present it in a readable and
understandable format.
'''

# Importing necessary libraries
import sqlite3
import pandas as pd
from pathlib import Path

# Defining the path to the database
db_path = Path(r'n:\Projects\11209000\11209353\B. Measurements and calculations\008 - Resultaten Proefvlucht\ZZL\7-2\databases\database_bekleding_bovengrens\traject_7_2_afgeknipt.db')

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
# measures for optimization run id = 1.
sql_query = 'SELECT * FROM OptimizationSelectedMeasure WHERE optimization_run_id = 1'
selected_optimization_measure = pd.read_sql_query(sql_query, conn)
print(selected_optimization_measure)

# create a list of ids in the selected_optimization_measure
selected_measure_ids = selected_optimization_measure["measure_result_id"].tolist()

# retrieve from the database tab "OptimizationStep" all rows where optimization_selected_measure_id is in selected_measure_ids
sql_query = 'SELECT * FROM OptimizationStep WHERE optimization_selected_measure_id IN ({})'.format(
    ', '.join([str(i) for i in selected_measure_ids]))
optimization_step = pd.read_sql_query(sql_query, conn)
print(optimization_step)

# Closing the connection to the database
conn.close()






