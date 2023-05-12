import numpy as np
from shapely.geometry import LineString, Point
import matplotlib.pyplot as plt

def determine_dike_angle(point1, point2):
    """Calculate angle between two points in radians and degrees"""
    angle = np.arctan2(point2.y - point1.y, point2.x - point1.x)
    return angle

# create a function that draws points with a given angle and radius
def create_transect_points(point, angle, radius):
    """Draw point with a given with a given angle and radius"""
    x = point.x + radius * np.cos(angle)
    y = point.y + radius * np.sin(angle)
    return Point(x, y)

# create function that creates a line between two points and returns a linestring with points at each given step
def create_cross_section_coordinates(transect_point1, transect_point2, step):
    """Create a line between two points and return a linestring with points at each given step"""
    temp_line = LineString([transect_point1, transect_point2])
    distance = temp_line.length
    x_coords = np.linspace(transect_point1.x, transect_point2.x, int(distance / step) + 1)
    y_coords = np.linspace(transect_point1.y, transect_point2.y, int(distance / step) + 1)
    return LineString([Point(x, y) for x, y in zip(x_coords, y_coords)])

A = Point(152240.147, 423529.088)
B = Point(152239.779, 423530.018)

# A = Point(0, 0)
# B = Point(-1,0)

alpha = determine_dike_angle(A, B)
print(alpha)

radius = 10
gamma = create_transect_points(A, alpha-0.5*np.pi, radius)
delta = create_transect_points(A, alpha+0.5*np.pi, radius)




line = create_cross_section_coordinates(gamma, delta, 1)

# print all x coordinates of a line string
print(line.xy[0][0], line.xy[1][0])
print(gamma.x, gamma.y)


print(list(zip(list(line.xy[0]), list(line.xy[1])))
# print([x, y for x, y in line.xy])
print(delta.x, delta.y)

print(len(line.xy[0]))

# plt.figure()
# plt.plot(A.x, A.y, 'o', label='A')
# plt.plot(B.x, B.y, 'o', label='B')
# plt.plot(gamma.x, gamma.y, 'o', label='gamma', zorder=10)
# plt.plot(delta.x, delta.y, 'o', label='delta', zorder=10)
# plt.plot(line.xy[0], line.xy[1], 'o', label='line')
# plt.legend()
# plt.grid(True)
# # make sure x and y cells are same size
# plt.gca().set_aspect('equal', adjustable='box')
# plt.show()


