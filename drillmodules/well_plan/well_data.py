"""
Well data Module
----------------

This module contains functions for generating the well data
"""
import pandas as pd
import numpy as np
from .interpolate import WPInterpolator


def calAzimuthInc(x, y, z) -> dict:
    """
    Calculates the azimuth and inlination along a well

    Inputs:
    -------
        x: x coordinates of well
        y: y coordinates of well
        z: z coordinates of well

    Output:
    -------
        A dictionary of the azimuth and inclination in rad
        result['azimuth'] = np array
        result['inclination'] = np array
    """
    inclination = np.arctan2(np.sqrt(y**2 + x**2), z)
    azimuth = np.rad2deg(np.arctan2(x, y))

    return (azimuth, inclination)


def calMeasuredDepths(x, y, z):
    """
    Calculates the measured depths from the eastings, northings and depths

    Inputs:
    -------
        x: x coordinates of well
        y: y coordinates of well
        z: z coordinates of well

    Output:
    -------
        An np array of the measured depth at every station of the coordinates
    """
    measured_depths = np.sqrt(y**2 + x**2 + z**2)

    return measured_depths


def calDLS(pre_md, md, pre_azi, azi, pre_incli, incli):
    """Calculates DLS"""
    DOGLEG_AT_EVERY = 100
    delta_md = md-pre_md

    md_dls = np.arccos(
        np.cos(pre_incli) * np.cos(incli)
        + np.sin(pre_incli) * np.sin(incli) * np.cos((azi - pre_azi))
    )

    if delta_md == 0:
        return 0
    return (DOGLEG_AT_EVERY / delta_md) * md_dls


def calWellDLS(measured_depth, inclination, azimuth):
    """
    Calculates the dogleg along the well

    Inputs:
    -------
        md: measured depth
        incli: inclination
        azi: azimuth

    Output:
    -------
        An np array of the dogleg sevierity at every station of the well
    """
    dls = np.array([])

    pre_azi, pre_incli, pre_md = 0, 0, 0
    for md, incli, azi in zip(measured_depth, inclination, azimuth):
        dls_ = calDLS(
            pre_md=pre_md,
            md=md,
            pre_azi=pre_azi,
            azi=azi,
            pre_incli=pre_incli,
            incli=incli,
        )
        dls = np.concatenate((dls, np.array([dls_])), axis=0)

    return dls


def get_well_data(
    surface_coords,
    tvd_kop,
    target_coords,
    station_delta=10,
    method="Akima1DInterpolator",
    *args,
    **kwargs
):
    """
    Computes well data

    Inputs:
    -------
        surface_coords:  Surface coodinates as an np arr[x, y, z]
        target_coords: Target coodinates as an np arr[[x, y, z] for each target]
        tvd_kop: Depth to kick off point
        Input interpolator params

    Output:
    -------
        Two Pd data frame with eastings, northings, depths,
        inclination(rad) and azimuth (rad), dls (deg per 100 feet)
    """
    surface_x, surface_y, surface_z = surface_coords
    kop_x, kop_y, kop_z = (
        surface_x,
        surface_y,
        tvd_kop,
    )
    targets_x = np.array([t[0] for t in target_coords])
    targets_y = np.array([t[1] for t in target_coords])
    targets_z = np.array([t[2] for t in target_coords])
    

    # Interpolation starts at kop to last target.
    x = np.insert(targets_x, 0, kop_x)
    y = np.insert(targets_y, 0, kop_y)
    z = np.insert(targets_z, 0, kop_z)

    interpolator = WPInterpolator(x, y, z)

    interp_coords = interpolator.interpolate1D(
        station_delta=station_delta, method=method, *args, **kwargs
    )  # Interpolated coordinates

    final_x, final_y, final_z = interp_coords
    # Add the vertical point section's coordinates
    # For depths, it's just increasing by 10; eastings and northings, it's
    # maintaing surface values
    surface_to_kop_z_coords = np.arange(surface_z, kop_z, station_delta)
    final_z = np.concatenate((surface_to_kop_z_coords, final_z))
    final_x = np.concatenate(
        (np.full((len(surface_to_kop_z_coords),), surface_x), final_x)
    )
    final_y = np.concatenate(
        (np.full((len(surface_to_kop_z_coords),), surface_y), final_y)
    )

    azimuths, inclinations = calAzimuthInc(final_x, final_y, final_z)
    measured_depths = calMeasuredDepths(final_x, final_y, final_z)
    dls = calWellDLS(
        measured_depth=measured_depths,
        inclination=inclinations,
        azimuth=azimuths,
    )

    well_data = {
        "X": final_x,
        "Y": final_y,
        "Z": final_z,
        "azimuth": azimuths,
        "inclination": inclinations,
        "md": measured_depths,
        "dls": dls,
    }

    return pd.DataFrame(well_data)
