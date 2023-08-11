import matplotlib, os, sys
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.interpolate import interp1d

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from pathlib import Path
import itertools


class DFlowSlideCharacteristicPointsSimple():
    def __init__(self, df, name):
        self.df = df
        self.name = name
        self.derive_profile_properties()
        self.correct_profile = True
        self.window_size = 3

    def derive_profile_properties(self):
        '''
        Bepaal typische eigenschappen van het profiel. Zoek de hoogste en laagste Z-waarde, en sla de index op.
        Zoek het maximum altijd in de buurt van de keringlijn. Aanname: 50 punten links en rechts. Afhankelijk
        van de resolutie zou dit genoeg moeten zijn (bij 0.5 m resolutie is het 25 m links en rechts, bij 1.0 m
        resolutie 50m links en rechts). In dit script is de keringlijn niet bekend, dus zoeken we t.o.v. het
        midden, want de dwp-lijnen hebben wel getekend t.o.v. de keringlijn, en hebben aan beide kanten dezelfde
        afstand gehad.
        '''

        # get the index of the nearest point to x=0
        self.i_xnull = self.df['X'].iloc[(self.df['X'] - 0).abs().argsort()[:1]].index[0]

    def derive_characteristic_points(self):
        self.preprocess_characteristic_points()
        self.derive_profile_variables()
        self.detect_outer_crest()
        self.detect_breakpoints()
        self.detect_inner_crest()
        self.check_crests()
        self.update_crest_points()
        if self.correct_profile:
            self.optimize_outer_slope()
            self.optimize_inner_slope()
            self.sort_characteristic_points()


    def preprocess_characteristic_points(self):
        self.CharacteristicPointCollection = pd.DataFrame(columns=['X', 'Z', 'profile_index', 'name'])

    def sort_characteristic_points(self):
        '''
        Sort the characteristic points in the correct order
        '''
        # sort the characteristic points in ascending order for X
        self.CharacteristicPointCollection.sort_values(by=['X'], inplace=True)

    def derive_profile_variables(self):
        '''
        Determine typical properties of the profile, variance, covariance, derivative and second derivative
        '''
        # Standard calculate over a window of 3 points (one left, one right, and one in the middle) the variance.
        self.df['variance'] = self.df['Z'].rolling(window=self.window_size, center=True).cov()


    def detect_outer_crest(self):
        '''
        This function detects the outer crest of the dike. First it finds the maximum in the profile, within 20m from
         x=0.
        '''
        # find the maximum in the profile, 10 m around x=0
        range_around_x = 20 # dx = 0.5 meter, so 20*0.5m = 10m left and right of x = 0
        self.id_crest_max = self.df.loc[self.i_xnull - range_around_x:self.i_xnull + range_around_x, 'Z'].idxmax()
        self.crest_max = self.df.loc[self.id_crest_max, 'Z']
        # normalize the variance between the range around x. This prevents that large variance on foreland or polder
        # cause points to be missed
        self.normalize_factor = self.df.loc[self.i_xnull - range_around_x:self.i_xnull + range_around_x, 'variance'].max()
        # self.normalize_factor = self.df['variance'].max()

        # from the maximum we go left step by step and find the first point where the variance is larger than the treshold
        self.variance_treshold = 0.05
        for i in range(self.id_crest_max, 0, -1):
            if self.df.loc[i, 'variance']/self.normalize_factor > self.variance_treshold:
                self.id_outer_crest = i
                # add this point to the characteristic point collection, using pandas.concat
                self.CharacteristicPointCollection = pd.concat([self.CharacteristicPointCollection,
                                                                pd.DataFrame({'X': self.df.loc[i, 'X'],
                                                                              'Z': self.df.loc[i, 'Z'],
                                                                              'profile_index': i,
                                                                              'name': 'BUK'},
                                                                             index=[0])],
                                                                ignore_index=True)
                break
            else:
                self.id_outer_crest = None

    def detect_breakpoints(self):
        '''
        This function finds start and endpoints of the slopes of the dike: breakpoints.
        '''
        # append index to slope list if variance/normalize_factor > self.variance_treshold. Use list comprehension
        slope = [i for i in range(len(self.df)) if
                            self.df.loc[i, 'variance'] / self.normalize_factor >= self.variance_treshold]

        if slope[0] == 0:
            self.slope_start = [0]
            self.slope_start = [slope[i] for i in range(1, len(slope)) if slope[i - 1] != slope[i] - 1]
        else:
            self.slope_start = [slope[i] for i in range(len(slope)) if slope[i - 1] != slope[i] - 1]

        # determine self.slope_end which happens if slope[i+1] != slope[i] + 1 or if i = len(slope)
        self.slope_end = [slope[i] for i in range(len(slope)) if i == len(slope) - 1 or slope[i + 1] != slope[i] + 1]

        # merge self.slope_start and self.slope_end into self.breakpoints using 1 line of code
        self.breakpoints = [self.slope_start[i] for i in range(len(self.slope_start))] + \
                            [self.slope_end[i] for i in range(len(self.slope_end))]
        self.breakpoints.sort()

    def detect_inner_crest(self):
        '''
        This function detects the outer crest of the dike. First it finds the maximum in the profile, within 20m from
         x=0.
        '''
        # find the maximum in the profile, 10 m around x=0
        z_range_around_crest = 0.25 # meter
        # find the last consecutive self.breakpoints where Z is still within self.df.loc[self.id_outer_crest, 'Z'] +- z_range_around_crest
        # use list comprehension
        # only look at points right of the outer crest: self.breakpoints[:self.breakpoints.index(self.id_outer_crest)]
        self.inner_break_points = np.unique([self.breakpoints[i] for i in range(len(self.breakpoints)) if
                                            self.breakpoints[i] > self.id_outer_crest])
        if len(self.inner_break_points) > 1:
            for i in range(len(self.inner_break_points) - 1):
                if (abs(self.df.loc[self.inner_break_points[i], 'Z'] - self.df.loc[
                    self.id_outer_crest, 'Z']) <= z_range_around_crest) and (abs(
                        self.df.loc[self.inner_break_points[i + 1], 'Z'] - self.df.loc[
                            self.id_outer_crest, 'Z']) > z_range_around_crest):
                    self.id_inner_crest = self.inner_break_points[i]
                    self.CharacteristicPointCollection = pd.concat([self.CharacteristicPointCollection,
                                                                    pd.DataFrame({'X': self.df.loc[self.id_inner_crest, 'X'],
                                                                                  'Z': self.df.loc[self.id_outer_crest, 'Z'],
                                                                                  'profile_index': i,
                                                                                  'name': 'BIK'},
                                                                                 index=[0])],
                                                                   ignore_index=True)
                    break
                else:
                    self.id_inner_crest = None
        else:
            self.id_inner_crest = None

    def check_crests(self):
    # abort mission if outer or inner crest point is missing
        if (self.id_outer_crest is None) or (self.id_inner_crest is None):
            # print('Outer or inner crest point is missing. Aborting mission.') # better if this goes into logging file?
            self.correct_profile = False
            return

    # Check if outer and inner crest are less than 20m apart
        if abs(self.df.loc[self.id_outer_crest, 'X'] - self.df.loc[self.id_inner_crest, 'X']) > 20:
            # print('Outer and inner crest are too far apart. Aborting mission.') # better if this goes into logging file?
            self.correct_profile = False
            return

    # Check if tehere are points on the foreland and hinterland that are higher than the maximum between the crest points
        if self.df.loc[self.id_outer_crest:self.id_inner_crest, 'Z'].max() < self.df['Z'].max():
            # print('There are higher points in foreland or hinterland than the crests. Aborting mission.') # better if this goes into logging file?
            self.correct_profile = False
            return

    def update_crest_points(self):
        # set z value of self.CharacteristicPoint BIK and BUK to the maximum z between the inner and outer crest point
        self.CharacteristicPointCollection.loc[self.CharacteristicPointCollection['name'] == 'BIK', 'Z'] = \
            self.df.loc[self.id_outer_crest:self.id_inner_crest, 'Z'].max()
        self.CharacteristicPointCollection.loc[self.CharacteristicPointCollection['name'] == 'BUK', 'Z'] = \
            self.df.loc[self.id_outer_crest:self.id_inner_crest, 'Z'].max()


    def optimize_outer_slope(self):
        '''
        This function fits a simplified slope to the actual outer slope of the dike.
        '''

        self.z_outer_bound = self.df.loc[0, 'Z'] # z value of the outer bound
        self.z_outer_crest = self.CharacteristicPointCollection.loc[self.CharacteristicPointCollection["name"] == "BUK", "Z"].values[0]

        # find minimum z between the outer crest and the outer bound, because z_outer_bound is not always the lowest
        self.z_outer_min = self.df.loc[0:self.id_outer_crest, 'Z'].min()


        # self.outer_breakpoints is where self.breakpoints < self.id_outer_crest. Save only unique values
        self.outer_breakpoints = np.unique([self.breakpoints[i] for i in range(len(self.breakpoints)) if
                                  self.breakpoints[i] < self.id_outer_crest])

        possible_break_points = np.empty((1, len(self.outer_breakpoints) * 2))

        for i in np.arange(len(self.outer_breakpoints)):
            possible_break_points[:, int(i*2)] = np.repeat(self.df.loc[self.outer_breakpoints[i], 'X'], 1)
            possible_break_points[:, i * 2 + 1] = self.df.loc[self.outer_breakpoints[i], 'Z']


        all_variables = [np.asarray(list(zip(possible_break_points[:, i*2], possible_break_points[:, i*2+1]))) for i in range(len(self.outer_breakpoints))]

        # Get all possible combinations
        all_combinations = []
        for r in range(1, min(len(self.outer_breakpoints)+1, 4)):
            for combination in itertools.combinations(range(len(all_variables)), r):
                variable_combinations = itertools.product(*(all_variables[i] for i in combination))
                # all_combinations.extend(variable_combinations)
                all_combinations.extend(
                    [np.array(c) for c in variable_combinations])  # Convert each coordinate to numpy array


        all_combinations_filtered = []

        for combination in all_combinations:
            coordinates = np.array(combination)  # Convert combination to numpy array
            if len(coordinates) == 1:
                all_combinations_filtered.append(coordinates)
            elif np.all(coordinates[1:, 1] >= coordinates[:-1, 1]):
                all_combinations_filtered.append(coordinates)

        # coords_outer_three
        performance = np.zeros((len(all_combinations_filtered)))

        for i in range(len(all_combinations_filtered)):

            x_coords = all_combinations_filtered[i][:, 0].tolist()
            z_coords = all_combinations_filtered[i][:, 1].tolist()

            # interpolate the line
            line_outer = interp1d([self.df.loc[0, 'X']] + x_coords + [self.df.loc[self.id_outer_crest, 'X']],
                                  [self.z_outer_bound] + z_coords + [self.z_outer_crest])
            performance[i] = rmse(line_outer, self.df.loc[0:self.id_outer_crest,['X','Z']], len(all_combinations_filtered[i]))

        # plot the best line for coords_outer_three
        index_best_performance = np.argmin(performance)

        # add the points to self.CharacteristicPoints
        for i in range(len(all_combinations_filtered[index_best_performance])):
            # find the index where self.df is closest to self.df.loc[all_combinations_filtered[index_best_performance][:, 0][i], 'X']
            index_x = np.argmin(np.abs(self.df['X'] - all_combinations_filtered[index_best_performance][:, 0][i]))
            self.CharacteristicPointCollection = pd.concat([self.CharacteristicPointCollection,
                                                            pd.DataFrame({'X': all_combinations_filtered[index_best_performance][:, 0][i],
                                                                          'Z': all_combinations_filtered[index_best_performance][:, 1][i],
                                                                          'profile_index': index_x,
                                                                          'name': 'outer_slope{}'.format(i)},
                                                                         index=[0])])

    def optimize_inner_slope(self):
        '''
        This function fits a simplified slope to the actual outer slope of the dike.
        '''

        self.z_inner_crest = self.CharacteristicPointCollection.loc[self.CharacteristicPointCollection["name"] == "BIK", "Z"].values[0]
        # obstain the last point of the inner slope
        self.id_inner_bound = len(self.df)-1
        self.z_inner_bound = self.df.iloc[self.id_inner_bound]['Z']


        # find minimum z between the inner crest and the inner bound, because z_inner_bound is not always the lowest
        self.z_inner_min = self.df.loc[self.id_inner_crest:self.id_inner_bound, 'Z'].min()

        # self.outer_breakpoints is where self.breakpoints < self.id_outer_crest. Save only unique values
        self.inner_breakpoints = np.unique([self.breakpoints[i] for i in range(len(self.breakpoints)) if
                                  self.breakpoints[i] > self.id_inner_crest])

        possible_break_points = np.empty((1, len(self.inner_breakpoints) * 2))

        for i in np.arange(len(self.inner_breakpoints)):
            possible_break_points[:, int(i*2)] = np.repeat(self.df.loc[self.inner_breakpoints[i], 'X'], 1)
            possible_break_points[:, i * 2 + 1] = self.df.loc[self.inner_breakpoints[i], 'Z']


        all_variables = [np.asarray(list(zip(possible_break_points[:, i*2], possible_break_points[:, i*2+1]))) for i in range(len(self.inner_breakpoints))]

        # Get all possible combinations
        all_combinations = []
        for r in range(1, min(len(self.inner_breakpoints)+1, 4)):
            for combination in itertools.combinations(range(len(all_variables)), r):
                variable_combinations = itertools.product(*(all_variables[i] for i in combination))
                # all_combinations.extend(variable_combinations)
                all_combinations.extend(
                    [np.array(c) for c in variable_combinations])  # Convert each coordinate to numpy array

        all_combinations_filtered = []

        for combination in all_combinations:
            coordinates = np.array(combination)  # Convert combination to numpy array
            if len(coordinates) == 1:
                all_combinations_filtered.append(coordinates)

            elif np.all(coordinates[1:, 1] < coordinates[:-1, 1]):
                all_combinations_filtered.append(coordinates)

        # coords_outer_three
        performance = np.zeros((len(all_combinations_filtered)))

        for i in range(len(all_combinations_filtered)):
            x_coords = all_combinations_filtered[i][:, 0].tolist()
            z_coords = all_combinations_filtered[i][:, 1].tolist()


            # interpolate the line
            line_inner = interp1d([self.df.loc[self.id_inner_crest, 'X']] + x_coords + [self.df.loc[self.id_inner_bound, 'X']],
                                   [self.z_inner_crest] + z_coords + [self.z_inner_bound])
            performance[i] = rmse(line_inner, self.df.loc[self.id_inner_crest:self.id_inner_bound,['X','Z']], len(all_combinations_filtered[i]))

        # plot the best line for coords_outer_three
        index_best_performance = np.argmin(performance)

        # add the points to self.CharacteristicPoints
        for i in range(len(all_combinations_filtered[index_best_performance])):
            # find the index where self.df is closest to self.df.loc[all_combinations_filtered[index_best_performance][:, 0][i], 'X']
            index_x = np.argmin(np.abs(self.df['X'] - all_combinations_filtered[index_best_performance][:, 0][i]))
            self.CharacteristicPointCollection = pd.concat([self.CharacteristicPointCollection,
                                                            pd.DataFrame({'X': all_combinations_filtered[index_best_performance][:, 0][i],
                                                                          'Z': all_combinations_filtered[index_best_performance][:, 1][i],
                                                                          'profile_index': index_x,
                                                                          'name': 'inner_slope{}'.format(i)},
                                                                         index=[0])])

    def plot_profile(self, output_directory):
        '''
        This function creates a plot with several axes (shared x axis) and plots the profile in the upper graph,
        the second graph plots the variance, the third the covariance, the fourth the derivative and the fifth
        plots the second derivative.
        don't interpolate between missing points, leave parts with nan blank
        '''
        # create a figure with 5 subplots
        fig, axs = plt.subplots(1, figsize=(16, 8))

        # plot the profile
        axs.plot(self.df['X'], self.df['Z'])
        # plot the characteristic points
        axs.plot(self.CharacteristicPointCollection['X'], self.CharacteristicPointCollection['Z'], 'ko', label = 'characteristic points')
        # plot all the breakpoints vlines (vertical lines) at the x position of the breakpoints
        plt.plot(self.df.loc[self.breakpoints, 'X'],
                 np.ones(len(self.breakpoints)) * (self.df['Z'].min()-.5), 'kd')
        # plot a line between characteristic points
        axs.plot(self.CharacteristicPointCollection['X'], self.CharacteristicPointCollection['Z'], 'k',
                 label='characteristic profile')
        # place a
        # grid
        axs.grid()
        # set the labels
        axs.set_ylabel('Z [m]')
        # set ylim
        axs.set_ylim([self.df['Z'].min()-.5, self.df['Z'].max()+.5])
        # set xlim
        axs.set_xlim([self.df['X'].min(), self.df['X'].max()])

        # save the figure
        plt.savefig(os.path.join(output_directory, self.name + '.png'), dpi=300)
        plt.close()

def rmse(line, df, n_breakpoints):
    # calculate the squared error between the interpolated points and the actual points in self.df
    # the number of breakpoints is used as penalty for the additional degrees of freedom
    squared_error = np.zeros(len(df))
    weigh_factor = [1, 1.5, 2.0]
    for i in range(len(df)):
        squared_error[i] = weigh_factor[n_breakpoints - 1] * (
                    df.loc[df.index[i], 'Z'] - line(df.loc[df.index[i], 'X'])) ** 2
    # calculate the root mean squared error
    root_mean_squared_error = np.sqrt(np.mean(squared_error))
    return root_mean_squared_error

def obtain_characteristic_profiles(input_dir: Path,
                                   output_dir: Path):
    # input_dir = Path(r'c:\VRM\Gegevens 38-1\profiles5\profile_csv')
    # output_dir = Path(r'c:\VRM\Gegevens 38-1\profiles\profile_csv\output3')

    for dwp, file in enumerate(os.listdir(input_dir)):
        if file.endswith('.csv'):

            df_line = pd.read_csv(os.path.join(input_dir, file), header=None, delimiter=",")
            column_name = file.split('.')[0]

            # set up a new df for each measurement at t
            df = pd.DataFrame()
            df['X'] = df_line.iloc[0]
            df['Z'] = df_line.iloc[1]

            # if df['Z'] contains too many NaNs (more than 15%), skip the profile
            # if df['Z'].isna().sum() > 0.15*len(df['Z']):
            #     continue
            # else:
            #     pass

            # fill Nans by interpolation
            df['Z'] = df['Z'].interpolate(method='linear', limit_direction='both')
            # remove NaNs
            # df.dropna(inplace=True)
            # reset index
            # df.reset_index(inplace=True)


            DFS_CharPoints = DFlowSlideCharacteristicPointsSimple(df, name=column_name)
            DFS_CharPoints.derive_characteristic_points()
            if DFS_CharPoints.correct_profile:
                # plot the profile
                DFS_CharPoints.plot_profile(output_dir)
                # write DFS_CharPoints.CharacteristicPointCollection to csv
                DFS_CharPoints.CharacteristicPointCollection.to_csv(os.path.join(output_dir, column_name + '.csv'), index=False)


#
# run_comparison()
