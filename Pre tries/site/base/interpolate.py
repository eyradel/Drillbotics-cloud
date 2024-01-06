import numpy as np
import pandas as pd

# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import Akima1DInterpolator
from scipy.interpolate import interp1d as scipyinterp1d


def _interp1d(x_coords, y_coords, z_coords):
    """
    Recieves a set of coordinates and interpolates them using scipyinterp1d
    """
    f_x = scipyinterp1d(z_coords, x_coords, kind="cubic")
    f_y = scipyinterp1d(z_coords, y_coords, kind="cubic")
    f_z = scipyinterp1d(z_coords, z_coords, kind="cubic")

    # Define the z values along the curve
    z_interp = np.arange(z_coords[0], z_coords[-1], 10)

    # Calculate the x, y, and z coordinates along the curve
    x_interp = f_x(z_interp)
    y_interp = f_y(z_interp)
    z_interp = f_z(z_interp)

    return x_interp, y_interp, z_interp


def _akima1DInterp(x_coords, y_coords, z_coords):
    """
    Recieves a set of coordinates and interpolates them using Akima1DInterpolator
    """
    # Z coords is the vertical distance

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


def calAzimuthInc(x_coords, y_coords, z_coords) -> tuple:
    """
    Calculates the azimuth and inlination of a well
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
    horizontal_delta = np.sqrt(delta_x**2 + delta_y**2)
    vertical_delta = delta_z

    rad_inclination = np.arctan2(horizontal_delta, vertical_delta)
    rad_inclination = np.concatenate(
        (np.array([0]), rad_inclination)
    )  # Add zero to make the lenght == num_coords
    deg_inclination = np.rad2deg(rad_inclination)

    rad_azimuth = np.arctan2(delta_y, delta_x)
    rad_azimuth = np.concatenate(
        (np.array([0]), rad_azimuth)
    )  # Add zero to make the lenght == num_coords
    deg_azimuth = np.rad2deg(rad_azimuth)

    return ((rad_inclination, deg_inclination), (rad_azimuth, deg_azimuth))


def get_well_data(surface_coords, tvd_kop, target_coords):
    """
    Computes well data
    Inputs:
        surface_coords:  Surface coodinates as an np arr[x, y, z]
        target_coords: Target coodinates as an np arr[x_coords, y_coords, z_coords]
        tvd_kop: Depth to kick off point
    Output:
        Pd data frame with x coordinates, y coordinates, z coordinates,
        inclination in rad and deg and azimuth in deg and rad
    """
    surface_x, surface_y, surface_z = surface_coords
    kop_x, kop_y, kop_z = surface_x, surface_y, tvd_kop
    targets_x, targets_y, targets_z = target_coords

    # Interpolation starts at kop to targets. NOTE: Might change
    interpolating_x = np.insert(targets_x, 0, kop_x)
    interpolating_y = np.insert(targets_y, 0, kop_y)
    interpolating_z = np.insert(targets_z, 0, kop_z)

    x_coords, y_coords, z_coords = _akima1DInterp(
        interpolating_x, interpolating_y, interpolating_z
    )  # Interpolated coordinates

    # Add the vertical point section's coordinates
    # For z, it's just increasing by 10, x and y, it's just maintaing surface x and y for
    # the number of z points to the kop
    surface_to_kop_z_coords = np.arange(surface_z, kop_z, 10)
    z_coords = np.concatenate((surface_to_kop_z_coords, z_coords))
    x_coords = np.concatenate(
        (np.full((len(surface_to_kop_z_coords),), surface_x), x_coords)
    )
    y_coords = np.concatenate(
        (np.full((len(surface_to_kop_z_coords),), surface_y), y_coords)
    )

    inclination, azimuth = calAzimuthInc(x_coords, y_coords, z_coords)

    well_data = {
        "North": [],
        "East": [],
        "TVD": [],
        "Inclination[rad]": [],
        "Inclination[deg]": [],
        "Azimuth[rad]": [],
        "Azimuth[deg]": [],
    }

    for idx, _ in enumerate(z_coords):
        well_data["North"].append(x_coords[idx])
        well_data["East"].append(y_coords[idx])
        well_data["TVD"].append(z_coords[idx])
        well_data["Inclination[rad]"].append(inclination[0][idx])
        well_data["Inclination[deg]"].append(inclination[1][idx])
        well_data["Azimuth[rad]"].append(azimuth[0][idx])
        well_data["Azimuth[deg]"].append(azimuth[1][idx])

    well_data = pd.DataFrame(well_data)
    return well_data


# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.scatter(targets_x, targets_y, targets_z , c='r', marker='o', label='Targets')
# ax.plot(x_coords, y_coords, z_coords, label='Well Path Akim')
# ax.set_xlabel('X')
# ax.set_ylabel('Y')
# ax.set_zlabel('Z')
# plt.gca().invert_zaxis()
# ax.legend()
# plt.show()
