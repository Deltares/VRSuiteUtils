
from pathlib import Path
import pandas as pd


class MeasureConfiguration:
    """
    Class to handle the configuration of measures for a traject."""

    def __init__(self, vakindeling_shape):
        self.vakindeling_shape = vakindeling_shape
        self._generic_data_dir = Path(__file__).absolute().parent.parent.joinpath('generic_data')
        self._measure_names = pd.read_csv(self._generic_data_dir.joinpath('base_measures_totaal.csv'), index_col=0).index.tolist()
        self._columns = ['objectid', 'vaknaam'] + self._measure_names

    def adjust_sections_revetments(self):
        #if there is a value for bekledingen in vakindeling_shape, then the value should be True, otherwise it should be False
        #if in_analyse is 0 then all measures should be False
        for i, row in self.vakindeling_shape.iterrows():
            if row.in_analyse == 0:
                #set all measures to False
                self.measure_configuration.loc[i, self._measure_names] = False
            elif pd.isna(row['bekledingen']) or str(row['bekledingen']).lower() == 'nan':
                    self.measure_configuration.at[i, 'Aanpassing bekleding'] = False
            else:
                pass
                


    def generate_measure_configuration(self):
        """Generate a DataFrame with the configuration of measures."""
        measures_df = pd.DataFrame(columns=self._columns)
        measures_df['objectid'] = self.vakindeling_shape['objectid']
        measures_df['vaknaam'] = self.vakindeling_shape['vaknaam']

        #turn off everything that has buitenwaarts in the column name. Turn on all the others
        for measure in self._measure_names:
            if 'buitenwaarts' in measure.lower():
                measures_df[measure] = False
            else:
                measures_df[measure] = True

        self.measure_configuration = measures_df
        self.adjust_sections_revetments()
        return measures_df
    
    def write_to_csv(self, output_path: Path):
        """Write the measure configuration to a CSV file."""
        measures_df = self.generate_measure_configuration()
        measures_df.to_csv(output_path, index=False)
        print(f"Measure configuration written to {output_path}")