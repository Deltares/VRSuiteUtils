# import libraries
import numpy as np
import matplotlib.pyplot as plt
import csv
import re


# import data
traject_profiles_path = r'c:\VRM\Gegevens 38-1\profiles\traject_profiles_point.csv'

if traject_profiles_path.endswith("line.csv"):
    with open(traject_profiles_path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        header = next(reader)
        data = np.array(list(reader), dtype=float)

    x_coords = np.array(header[8:], dtype=float)

    # prevent figures from opening
    plt.ioff()

    for row in data:
        plt.figure(figsize=(16, 3))
        plt.plot(x_coords, row[8:])
        plt.xticks(np.arange(min(x_coords), max(x_coords)+6, 5))
        plt.xlim(min(x_coords), max(x_coords))
        plt.axvline(x=0, color='gray', linestyle='--')
        plt.grid(True)
        plt.gca().set_aspect('equal', adjustable='box')
        # add text above the plot that contains the M-value (row[3]) and the x-coordinate (row[1]) and the y-coordinate (row[2])
        plt.text(0.5, 1.1, 'M-value: {}, X-coordinate: {}, Y-coordinate: {}'.format(round(row[7],1),
                                                                                      round(row[5],1),
                                                                                      round(row[6],1)),
                 horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)
        # plt.show()
        plt.savefig(r'c:\VRM\Gegevens 38-1\profiles\profile_plots\profile_{}.png'.format(int(row[0])), dpi=300)

elif traject_profiles_path.endswith("point.csv"):
    with open(traject_profiles_path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        xx = []
        # skip header
        header = next(reader)
        for line in reader:
            x_coords = []
            y_coords = []
            z_coords = []
            x = np.zeros(len(line[7:]))
            x[0] = -float(line[6])
            for i, column in enumerate(line[7:]):
                values = re.split(r'\s+', column.strip("[]"))
                x_coords.append(float(values[0]))
                y_coords.append(float(values[1]))
                z_coords.append(float(values[2]))
                if i > 0:
                    x[i] = x[i-1] + np.sqrt((x_coords[i]-x_coords[i-1])**2 + (y_coords[i]-y_coords[i-1])**2)
            plt.figure(figsize=(16, 3))
            plt.plot(x, z_coords)
            plt.xticks(np.arange(min(x), max(x)+6, 5))
            plt.xlim(min(x), max(x))
            plt.ylim(np.floor(np.nanmin(z_coords))-1, np.ceil(np.nanmax(z_coords))+1)

            plt.axvline(x=0, color='gray', linestyle='--')
            plt.grid(True)
            plt.gca().set_aspect('equal', adjustable='box')
            # add text above the plot that contains the M-value (row[3]) and the x-coordinate (row[1]) and the y-coordinate (row[2])
            plt.text(0.5, 1.1, 'M-value: {}, X-coordinate: {}, Y-coordinate: {}'.format(round(float(line[5]),1),
                                                                                            round(float(line[3]),1),
                                                                                            round(float(line[4]),1)),
                        horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)
            # plt.show()
            plt.savefig(r'c:\VRM\Gegevens 38-1\profiles\profile_plots\profile_{}.png'.format(int(line[0])), dpi=300)

            xx.append(x)

# x slightly differs per profile:
# xx = np.array(xx)
# for i in range(0, len(xx[0])):
#     print(xx[:,i])

