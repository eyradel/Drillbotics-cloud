import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import Akima1DInterpolator

# Define the four target coordinates
target_values = [[238.21, 137.53, 1164.06],
                # [337.47, 194.84, 1223.73],
                [759.59, 438.55, 1327.21],
                [1284.59, 741.66, 1677.21]]

targets_x = [i[0] for i in target_values]
targets_y = [i[1] for i in target_values]
targets_z = [i[2] for i in target_values]

def lineEq(point1, point2):
    """
    Parameters
        Two coodinate points, point1, point2
    
    Returns a function for the equation of a line
    """

    def Eq(x):
        m = (point1[1] - point2[1]) / (point1[0] - point2[0]) # Gradient
        c = point1[1] - (point1[0] * m) # Constant
        y = (m * x) + c
        return y

    return Eq


surface_coord = target_values[0].copy()
surface_coord[0] -= 200 # Move back 200. Was seen to be suitable
surfacex = surface_coord[0]
cal_surY = lineEq((targets_x[0], targets_y[0]), (targets_x[-1], targets_y[-1]))
surface_coord[1] = cal_surY(surfacex)
surface_coord[2] = 0 # Change the depth to zero

kop_coords = surface_coord.copy()
kop_coords[2] = target_values[0][2] * 0.50 # 50 % of first target

# Create slow curving points from the kop to first target
sp1 = kop_coords.copy()
sp1[0] += 20 # smaller than how far surface-x moved
sp1[1] = ((targets_y[0] - kop_coords[1]) * 0.10) + kop_coords[1] # Move 30% from kop towards first target
sp1[2] = kop_coords[2] * 1.30
sp2 = sp1.copy()
sp2[0] += 66 # smaller than how far surface-x moved
sp2[1] = ((targets_y[0] - kop_coords[1]) * 0.30) + kop_coords[1] # Move 30% from kop towards first target
sp2[2] = kop_coords[2] * 1.60

# Create a list of coordinates from surface to kop space at 10
surface_to_kop_coords = [[surface_coord[0], surface_coord[1], i] \
                        for i in range(0, int(kop_coords[2]), 10)]

# Interpolate from the kop through to sp1 and sp2 to every target
interpolating_x = targets_x.copy()
interpolating_x.insert(0, sp2[0])
interpolating_x.insert(0, sp1[0])
interpolating_x.insert(0, surface_to_kop_coords[-1][0])
interpolating_y = targets_y.copy()
interpolating_y.insert(0, sp2[1])
interpolating_y.insert(0, sp1[1])
interpolating_y.insert(0, (surface_to_kop_coords[-1][1]))
interpolating_z = targets_z.copy()
interpolating_z.insert(0, sp2[2])
interpolating_z.insert(0, sp1[2])
interpolating_z.insert(0, (surface_to_kop_coords[-1][2]))

# Interpolate each of the x, y, and z coordinates separately
interp_x = Akima1DInterpolator(np.arange(len(interpolating_x)), interpolating_x)
interp_y = Akima1DInterpolator(np.arange(len(interpolating_y)), interpolating_y)
interp_z = Akima1DInterpolator(np.arange(len(interpolating_z)), interpolating_z)

# Create a dense grid of indices for the interpolated curve
num_points = (target_values[-1][2] - kop_coords[2]) / 10 # difference 10 from kop to last target
dense_idx = np.linspace(0, len(interpolating_x) - 1, int(num_points))

# Evaluate the interpolated curve at the dense indices
curve_x = interp_x(dense_idx)
curve_y = interp_y(dense_idx)
curve_z = interp_z(dense_idx)

curve_x = np.insert(curve_x, 0, [i[0] for i in surface_to_kop_coords])
curve_y = np.insert(curve_y, 0, [i[1] for i in surface_to_kop_coords])
curve_z = np.insert(curve_z, 0, [i[2] for i in surface_to_kop_coords])

print(curve_z)

# Plot the curve passing through the target coordinates
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter([sp1[0], sp2[0]] + targets_x, [sp1[1], sp2[1]] + targets_y, [sp1[2], sp2[2]] + targets_z , c='r', marker='o', label='Targets')
ax.plot(curve_x, curve_y, curve_z, label='Well Path')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
plt.gca().invert_zaxis()
ax.legend()
plt.show()
