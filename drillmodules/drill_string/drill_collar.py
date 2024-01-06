"""
Drill Collar Module
"""

import numpy as np
import math

# from .base_drillstring import DrillStringObjBase


class DrillCollar:
    """
    Drill String Model: Represents a drill string instance

    Parameters
    ----------
        - youngs_modulus: Young's modulus of the drill string in psi
        - hole_diameter: Diameter of hole
        - inner_mud_weight: Initial mud weight
        - outer_mud_weight: Final mud weight
        - pip_weight: Weight of the drill pipe in pounds
        - collar_outer_diameter: Outer diameter of pipe
        - collar_inner_diameter: Inner diameter of pipe
        - more_info: A dictionary containg other info of the drill string such as grade
    """

    def __init__(
        self,
        youngs_modulus,
        hole_diameter,
        inner_mud_weight,
        outer_mud_weight,
        collar_weight,
        collar_outer_diameter,
        collar_inner_diameter,
        more_info={},
    ):
        self.youngs_modulus = youngs_modulus
        self.hole_diameter = hole_diameter
        self.inner_mud_weight = inner_mud_weight
        self.outer_mud_weight = outer_mud_weight
        self.collar_weight = collar_weight
        self.collar_outer_diameter = collar_outer_diameter
        self.collar_inner_diameter = collar_inner_diameter
        self.info = more_info

    def more_info(self):
        """
        Returns a dict with more infomation about drill collar
        OD (in), Connection, Collar ID (in), Adjusted Weight (lb/ft),
        MUT Min (ft-lbs), MUT Max (ft-lbs),	Type

        """
        info = self.info
        info["weight"] = self.collar_weight
        info["collar_inner_diameter"] = self.collar_inner_diameter
        info["collar_outer_diameter"] = self.collar_outer_diameter

        return info

    @property
    def pipe_radius(self):
        return self.collar_outer_diameter / 2

    @property
    def inertia(self):
        return (math.pi / 64) * (
            self.collar_outer_diameter**4 - self.collar_inner_diameter**4
        )

    @property
    def buoyed_pipe_weight(self):
        return np.abs(
            self.collar_weight
            + 0.0408
            * (
                (self.inner_mud_weight * self.collar_inner_diameter**2)
                - (self.outer_mud_weight * self.collar_outer_diameter**2)
            )
        )

    def _paslay_buckling(self, curr_azimuth) -> float:
        """
        Calculates the paslay buckling on the drill string

        Parameters
        ----------
            curr_azimuth: Current azimuth

        Returns
        -------
            value of buckling on the string
        """
        numerator = (
            self.youngs_modulus
            * self.inertia
            * self.buoyed_pipe_weight
            * np.sin(curr_azimuth)
        )
        denominator = self.pipe_radius
        numerator = 0 if numerator < 0 else numerator
        buckling_val = 2 * np.sqrt(numerator / denominator)

        return buckling_val

    def critical_buckling(self, drillcollar_length):
        """
        Calculates critical buckling force

        Parameters
        ----------
            drillcollar_length: legnth of drillcollar

        Returns
        -------
            value of buckling force
        """

        critical_buckling_force_val = (
            np.pi * self.youngs_modulus * self.inertia / drillcollar_length ** 2
        )

        return critical_buckling_force_val

    def buckling(self, drillcollar_length, curr_azimuth):
        """
        Determines if there's buckling

        Parameters
        ----------
            axial_force: Axial force
            curr_azimuth: current azimuth

        Returns
        -------
            `True` if there's buckling else `False`
        """

        return self.critical_buckling(drillcollar_length) < self._paslay_buckling(curr_azimuth)

