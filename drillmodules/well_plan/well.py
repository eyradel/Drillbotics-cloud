"""
Well module

This module contains the class that defines a well
"""
import numpy as np
import pandas as pd
from .well_data import get_well_data


class InterpWell:
    """
    Generates well profile data using interpolation

    Attributes:
    -----------
        - surface_coordinates [x, y, z] (list)
        - target_coordinates [[x, y, z] for each target] (list of list)
        - station_delta = 10
        - interpolator = "Akima1DInterpolator"
        - min_kop = 600
        - kop = 0
        - kop_form_aggr = 0.6 (Suitable formation aggresiveness for kickoff)
        - interp_args = {} Extra kwargs for the interpolator choosen

    Interpolator Choices
    --------------------
        - Akima1DInterpolator
        - PchipInterpolator
    """

    # - InterpolatedUnivariateSpline
    # - interp1d
    # - CubicSpline
    # - Rbf (radial basis function)
    ### - LinearNDInterpolator
    ### - CloughTocher2DInterpolator
    ### - NearestNDInterpolator

    def __init__(self):
        """Initializes a default well"""
        self.surface_coordinates = np.array([0, 0, 0])
        self.target_coordinates = np.array(
            [
                [0, 0, 0],
            ]
        )
        self.station_delta = 10
        self.interpolator = "PchipInterpolator"
        self.min_kop = 0  # TODO Should be unit depending
        self.kop = 0
        self.kop_form_aggr = 0.6  # Suitable formation aggresiveness for kickoff
        self.interp_args = {}
        self.form_aggr = np.array([[0, 0]])
        self.ccs = np.array([[0, 0]])

    def suggest_kop(self):
        for station in self.form_aggr[:]:
            if (
                station[0] >= self.min_kop
                and station[1] >= self.kop_form_aggr
                and station[0] <= self.target_coordinates[0][-1]
            ):
                self.kop = station[0]
                break

    @property
    def output_data(self):
        """
        Returns a turple of well data and targets coordinates

        Well data columns
        -----------------
        X: Well X
        Y: Well Y
        Z: Well Z
        Azimuth[rad]: Azimuth in radians
        Inclination[rad]: Inclination in radians
        MD: Measured depth
        DLS: Dogleg sevierity

        Targets Coordinates
        -------------------
        X: Targets X
        Y: Targets Y
        Z: Targets Z
        """
        if self.target_coordinates[0][-1] <= self.surface_coordinates[-1]:
            self.target_coordinates[0] = (
                self.target_coordinates[0][0],
                self.target_coordinates[0][1],
                self.target_coordinates[0][2] + np.finfo(float).eps,
            )
            pass

        well_data = get_well_data(
            surface_coords=self.surface_coordinates,
            tvd_kop=self.kop,
            target_coords=self.target_coordinates,
            station_delta=self.station_delta,
            method=self.interpolator,
            **self.interp_args,
        )
        targets_data = pd.DataFrame(self.target_coordinates, columns=["X", "Y", "Z"])

        return well_data, targets_data
