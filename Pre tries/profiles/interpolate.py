import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import Akima1DInterpolator
from scipy.interpolate import interp1d as scipyinterp1d

# _______________________________________________________
target_coords = np.array([[238.21, 137.53, 1164.06],
                        [337.47, 194.84, 1223.73],
                        [1284.59, 741.66, 1677.21],
                        [759.59, 438.55, 1327.21]])
sorted_target_indices = np.argsort(target_coords[:,2])
target_coords = target_coords[sorted_target_indices]

surface_coords = [0, 0, 0]
surface_coords = np.array(surface_coords)

tvd_kop = 800
# _______________________________________________________

surface_x, surface_y, surface_z = surface_coords
kop_x, kop_y, kop_z = surface_x, surface_y, tvd_kop

targets_x = target_coords[:, 0]
targets_y = target_coords[:, 1]
targets_z = target_coords[:, 2]

interpolating_x = np.insert(targets_x, 0, kop_x)
interpolating_y = np.insert(targets_y, 0, kop_y)
interpolating_z = np.insert(targets_z, 0, kop_z)

def _interp1d(x_coords, y_coords, z_coords):
    f_x = scipyinterp1d(z_coords, x_coords, kind='cubic')
    f_y = scipyinterp1d(z_coords, y_coords, kind='cubic')
    f_z = scipyinterp1d(z_coords, z_coords, kind='cubic')

    # Define the z values along the curve
    z_interp = np.arange(z_coords[0], z_coords[-1], 10)

    # Calculate the x, y, and z coordinates along the curve
    x_interp = f_x(z_interp)
    y_interp = f_y(z_interp)
    z_interp = f_z(z_interp)

    return x_interp, y_interp, z_interp


def _akima1DInterp(x_coords, y_coords, z_coords):
    interp_func_x = Akima1DInterpolator(z_coords, x_coords)
    interp_func_y = Akima1DInterpolator(z_coords, y_coords)
    interp_func_z = Akima1DInterpolator(z_coords, z_coords)

    # Define the z values along the curve
    z_interp = np.arange(z_coords[0], z_coords[-1], 10)

    # Calculate the x, y, and z coordinates along the curve
    x_interp = interp_func_x(z_interp)
    y_interp = interp_func_y(z_interp)
    z_interp = interp_func_z(z_interp)

    return x_interp, y_interp, z_interp


def calAzimuthInc(x_coords, y_coords, z_coords) -> tuple():
    """
    Calculates the azimuth of a well
    Inputs: 
        x_coords: x coordinates of well
        y_coords: y coordinates of well
        z_coords: z coordinates of well
    Output:
        A tuple of the azimuth in rads and deg; inclination in rads and deg respectively
        ((azrad, azdeg), (incrad, incdeg))
    """
    delta_x = np.diff(x_coords)
    delta_y = np.diff(y_coords)
    delta_z = np.diff(z_coords)
    horizontal_distance = np.sqrt(delta_x**2 + delta_y**2)
    vertical_distance = delta_z

    incrad = np.arctan2(horizontal_distance, vertical_distance)
    incrad = np.concatenate((np.array([0]), incrad)) # Add zero to make the lenght == num_coords
    incdeg = np.rad2deg(incrad)    

    azrad = np.arctan2(delta_y, delta_x)
    azrad = np.concatenate((np.array([0]), (azrad))) # Add zero to make the lenght == num_coords
    azdeg = np.rad2deg(azrad)

    return ((incrad, incdeg), (azrad, azdeg))


x_coords, y_coords, z_coords = _akima1DInterp(interpolating_x, interpolating_y, interpolating_z) # Interpolated coordinates


# Add the vertical point's coordinates
surface_to_kop_zs = np.arange(surface_z, kop_z, 10)
z_coords = np.concatenate((surface_to_kop_zs, z_coords))
x_coords = np.concatenate((np.full((len(surface_to_kop_zs),), surface_x), x_coords))
y_coords = np.concatenate((np.full((len(surface_to_kop_zs),), surface_y), y_coords))

inclination, azimuth = calAzimuthInc(x_coords, y_coords, z_coords)

for idx, z in enumerate(z_coords):
    print(x_coords[idx], " ", y_coords[idx], " ", z, " ", inclination[0][idx], " ", inclination[1][idx], " ", azimuth[0][idx], " ", azimuth[1][idx])


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(targets_x, targets_y, targets_z , c='r', marker='o', label='Targets')
ax.plot(x_coords, y_coords, z_coords, label='Well Path Akim')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
plt.gca().invert_zaxis()
ax.legend()
plt.show()
