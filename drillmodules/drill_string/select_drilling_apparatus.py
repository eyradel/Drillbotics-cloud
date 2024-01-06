"""
Select Drill string model

This model is used in selecting the best drill string based
on drill data or well plan data
"""
import os
import pandas as pd
import numpy as np

from .drill_pipe import DrillPipe
from .drill_collar import DrillCollar


class SelectDrillPipe:
    """
    This model selects the best drill string from the given drill
    strings with respect to the plan or RSS data
    """

    def __init__(
        self,
        friction_co,
        string_force,
        youngs_modulus,
        internal_fluid_pressure,
        external_fluid_pressure,
        hole_diameter,
        inner_mud_weight,
        outer_mud_weight,
        buoyancy_factor,
        drill_strings_data: pd.Series,
        well_data: pd.Series,
    ):
        """
        Initializes the drill strings

        Parameters
        ----------
            - friction_co: Friction coefficient
            - string_force: Force on string
            - youngs_modulus: Young's modulus
            - internal_fluid_pressure: Internal fluid pressure
            - external_fluid_pressure: External fluid pressure- inner_mud_weight: Inner mud weight
            - hole_diameter: Diameter of hole
            - inner_mud_weight: Inner mud weight
            - outer_mud_weight: Outer mud weight
            - buoyancy_factor: Buoyancy factor
            - drill_strings_data: pd dataframe of the available drill strings with first 3 columns,
                    ['pipe_weight', 'pipe_outer_diameter', 'pipe_inner_diameter']...

            - well_data: pd dataframe of the well path with columns,
                    ['inclination', 'azimuth', 'md']
        """

        _drill_strings_data = [
            {
                "friction_co": friction_co,
                "string_force": string_force,
                "youngs_modulus": youngs_modulus,
                "internal_fluid_pressure": internal_fluid_pressure,
                "external_fluid_pressure": external_fluid_pressure,
                "hole_diameter": hole_diameter,
                "inner_mud_weight": inner_mud_weight,
                "outer_mud_weight": outer_mud_weight,
                "buoyancy_factor": buoyancy_factor,
                "pipe_weight": string_data[0],
                "pipe_outer_diameter": string_data[1],
                "pipe_inner_diameter": string_data[2],
                "more_info": {
                    "Connection": string_data[3],
                    "Grade": string_data[4],
                    "Range": string_data[5],
                    "Wall (in)": string_data[6],
                    "Adjusted Weight (lb/ft)": string_data[7],
                    "TJ OD (in)": string_data[8],
                    "TJ ID (in)": string_data[9],
                    "TJ YIELD (ft-lbs)": string_data[10],
                    "MUT Min (ft-lbs)": string_data[11],
                    "MUT Max (ft-lbs)": string_data[12],
                    "Prem Tube Tensile (lbs)": string_data[13],
                },
            }
            for string_data in drill_strings_data.itertuples(name=None, index=False)
        ]

        self.drill_string_objs = np.array([])
        axial_force = 6.5  # NOTE: Note right
        for stringData in _drill_strings_data:
            ds = DrillPipe(**stringData)
            torques, drags, bucklings = np.array([]), np.array([]), np.array([])

            incs, azis, mds = (
                np.array(well_data["inclination"]),
                np.array(well_data["azimuth"]),
                np.array(well_data["md"]),
            )

            pre_incl, pre_azi, pre_md = incs[0], azis[0], mds[0]
            for inc, azi, md in zip(incs, azis, mds):
                delta_l = md - pre_md

                torque = np.array([ds.get_torque(pre_azi, azi)])
                drag = np.array([ds.get_drag(pre_azi, azi, pre_incl, inc, delta_l)])
                buckling = np.array([ds.buckling(axial_force, azi)])

                torques = np.concatenate((torques, torque), axis=0)
                drags = np.concatenate((drags, drag), axis=0)
                bucklings = np.concatenate((bucklings, buckling), axis=0)

                pre_incl, pre_azi, pre_md = inc, azi, md

            ds.__setattr__("torques", torques)
            ds.__setattr__("drags", drags)
            ds.__setattr__("buckles", bucklings)
            ds.__setattr__("total_score", 0)

            self.drill_string_objs = np.concatenate(
                (self.drill_string_objs, np.array([ds])), axis=0
            )

        tmp_strings = self.drill_string_objs.copy()

        # Remove all strings that buckle at atleast one station
        self.drill_string_objs = np.array(
            [obj for obj in self.drill_string_objs if np.nansum(obj.buckles) == 0]
        )

        # If all strings buckle, then return all of them
        if len(self.drill_string_objs) == 0:
            self.drill_string_objs = tmp_strings

    def _sorted_drill_strings(self, tw=0.1, dw=0.1, bw=0.8):
        """
        Sorts drillstrings in decending order of the optimum
        one for the given well

        Input
        -----
            - tw: Torque weight
            - dw: Drag weight
            - bw: Buckling weight

        Note
        ----
            tw, dw, and bw are a way of setting priority of which factor should
            be considered more in the selection. E.G, torque would be scaled to
            tw / (tw + dw + bw).

        Return
        ------
            All drill strings sorted in accending order of best
        """

        # max_buckle is 1 since it's a boolean at each station
        max_torque = 0
        max_drag = 0

        for string_obj in self.drill_string_objs:
            max_torque = np.nanmax(
                np.concatenate((string_obj.torques, np.array([max_torque])), axis=0)
            )
            max_drag = np.nanmax(
                np.concatenate((string_obj.drags, np.array([max_drag])), axis=0)
            )

        for string in self.drill_string_objs:
            # All values are normalized to 0-1
            normalised_weighted_torques = (
                (string.torques / max_torque) * (tw / (tw + dw + bw))
                if max_torque > 0
                else string.torques
            )

            normalised_weighted_drags = (
                (string.drags / max_drag) * (dw / (tw + dw + bw))
                if max_drag > 0
                else string.drags
            )

            normalised_weighted_buckles = string.buckles * bw / (tw + dw + bw)

            score_at_stations = np.nanmean(
                [
                    normalised_weighted_drags,
                    normalised_weighted_torques,
                    normalised_weighted_buckles,
                ],
                axis=0,
            )
            score = np.nanmean(score_at_stations)
            string.total_score = score

        # Note that the higher the score, the less valuable the string is
        sorted_indices = np.argsort(
            [instance.total_score for instance in self.drill_string_objs]
        )
        sorted_strings = self.drill_string_objs[sorted_indices]

        return sorted_strings

    def get_optimum(self, quantity=5):
        """
        Returns a dict with data for string selection
        Other data includes: Best score, Worst score, Average score, Worst strings, Best strings
        Number of Worst and Best strings returned is `quantity`
        """
        strings = self._sorted_drill_strings()
        data = {
            "Best score": strings[0].total_score,
            "Worst score": strings[-1].total_score,
            "Average score": np.nanmean([s.total_score for s in strings]),
            f"Worst strings": strings[-quantity - 1 :],
            f"Best strings": strings[:quantity],
        }

        return data


class SelectDrillCollar:
    def __init__(
        self,
        youngs_modulus,
        hole_diameter,
        inner_mud_weight,
        outer_mud_weight,
        drill_collars_data: pd.Series,
        well_data: pd.Series,
    ):
        """
        Initializes the drill collars

        Parameters
        ----------
            - youngs_modulus: Young's modulus
            - hole_diameter: Diameter of hole
            - inner_mud_weight: Inner mud weight
            - outer_mud_weight: Outer mud weight
            - drill_collars_data: pd dataframe of the available drill strings with first 3 columns,
                    ['collar_weight', 'collar_outer_diameter', 'collar_inner_diameter']

            - well_data: pd dataframe of the well path with columns,
                    ['inclination', 'azimuth', 'md']
        """


        _drill_collars_data = [
            {
                "youngs_modulus": youngs_modulus,
                "hole_diameter": hole_diameter,
                "inner_mud_weight": inner_mud_weight,
                "outer_mud_weight": outer_mud_weight,
                "collar_weight": collar_data[0],
                "collar_outer_diameter": collar_data[1],
                "collar_inner_diameter": collar_data[2],
                "more_info": {
                    "Connection": collar_data[3],
                    "MUT Min (ft-lbs)": collar_data[4],
                    "MUT Max (ft-lbs)": collar_data[5],
                    "Type": collar_data[6],
                },
            }
            for collar_data in drill_collars_data.itertuples(name=None, index=False)
        ]

        self.drill_collar_objs = np.array([])
        axial_force = 234  # NOTE: Note right
        for collarData in _drill_collars_data:
            dc = DrillCollar(**collarData)
            bucklings = np.array([])

            incs, azis, mds = (
                np.array(well_data["inclination"]),
                np.array(well_data["azimuth"]),
                np.array(well_data["md"]),
            )

            for inc, azi, md in zip(incs, azis, mds):

                buckling = np.array([dc.buckling(axial_force, azi)])
                bucklings = np.concatenate((bucklings, buckling), axis=0)

            dc.__setattr__("buckles", bucklings)
            dc.__setattr__("total_score", 0)

            self.drill_collar_objs = np.concatenate(
                (self.drill_collar_objs, np.array([dc])), axis=0
            )

        tmp_strings = self.drill_collar_objs.copy()

        # Remove all collars that buckle at atleast one station
        self.drill_collar_objs = np.array(
            [obj for obj in self.drill_collar_objs if np.nansum(obj.buckles) == 0]
        )

        # If all collars buckle, then consider all of them
        if len(self.drill_collar_objs) == 0:
            self.drill_collar_objs = tmp_strings

    def _sorted_drill_collars(self):
        """
        Sorts drillcollars in decending order of the optimum
        one for the given well

        Return
        ------
            All drill collars sorted in accending order of best
        """

        for collar in self.drill_collar_objs:
            collar.total_score = np.sum(collar.buckles)
            
        # Note that the higher the score, the less valuable the string is
        sorted_indices = np.argsort(
            [instance.total_score for instance in self.drill_collar_objs]
        )
        sorted_strings = self.drill_collar_objs[sorted_indices]

        return sorted_strings

    def get_optimum(self, quantity=5):
        """
        Returns a dict with data for collar selection
        Other data includes: Best score, Worst score, Average score, Worst collars, Best collars
        Number of Worst and Best collars returned is `quantity`
        """
        collars = self._sorted_drill_collars()
        data = {
            "Best score": collars[0].total_score,
            "Worst score": collars[-1].total_score,
            "Average score": np.nanmean([s.total_score for s in collars]),
            f"Worst collars": collars[-quantity - 1 :],
            f"Best collars": collars[:quantity],
        }

        return data


def selected_drill_pipes(
    well_data,
    friction_co=0.2,
    string_force=324,
    youngs_modulus=30000000,
    inner_mud_weight=15,
    outer_mud_weight=7.3,
    hole_diameter=10,
    internal_fluid_pressure=12800,
    external_fluid_pressure=4790,
    buoyancy_factor=0.8,
):
    drill_strings_api_sheet_path = os.path.dirname(os.path.realpath(__file__))
    drill_strings_data = pd.read_excel(
        os.path.join(drill_strings_api_sheet_path, "drill_pipes_api_sheet.xlsx")
    )
    drill_strings_data = drill_strings_data[
        [
            "Nominal Weight (lb/ft)",
            "OD (in)",
            "TUBE ID (in)",
            "Connection",
            "Grade",
            "Range",
            "Wall (in)",
            "Adjusted Weight (lb/ft)",
            "TJ OD (in)",
            "TJ ID (in)",
            "TJ YIELD (ft-lbs)",
            "MUT Min (ft-lbs) ",
            "MUT Max (ft-lbs)",
            "Prem Tube Tensile (lbs)",
        ]
    ]
    # TODO: Investigate removing above reordering
    drill_strings_data[
        ["Nominal Weight (lb/ft)", "OD (in)", "TUBE ID (in)"]
    ] = drill_strings_data[
        ["Nominal Weight (lb/ft)", "OD (in)", "TUBE ID (in)"]
    ].astype(
        "float"
    )

    string_selection = SelectDrillPipe(
        friction_co=friction_co,
        string_force=string_force,
        youngs_modulus=youngs_modulus,
        inner_mud_weight=inner_mud_weight,
        outer_mud_weight=outer_mud_weight,
        hole_diameter=hole_diameter,
        internal_fluid_pressure=internal_fluid_pressure,
        external_fluid_pressure=external_fluid_pressure,
        buoyancy_factor=buoyancy_factor,
        well_data=well_data,
        drill_strings_data=drill_strings_data,
    )

    return string_selection


def selected_drill_collars(
    well_data,
    youngs_modulus=30000000,
    inner_mud_weight=15,
    outer_mud_weight=7.3,
    hole_diameter=10,
):
    drill_collars_api_sheet_path = os.path.dirname(os.path.realpath(__file__))
    drill_collars_data = pd.read_excel(
        os.path.join(drill_collars_api_sheet_path, "drill_collars_api_sheet.xlsx")
    )
    drill_collars_data = drill_collars_data[
        [
            "Adjusted Weight (lb/ft)",
            "OD (in)",
            "Collar ID (in)",
            "Connection",
            "MUT Min (ft-lbs)",
            "MUT Max (ft-lbs)",
            "Type",
        ]
    ]
    # TODO: Investigate removing above reordering
    drill_collars_data[
        ["Adjusted Weight (lb/ft)", "OD (in)", "Collar ID (in)"]
    ] = drill_collars_data[
        ["Adjusted Weight (lb/ft)", "OD (in)", "Collar ID (in)"]
    ].astype(
        "float"
    )

    collar_selection = SelectDrillCollar(
        youngs_modulus=youngs_modulus,
        inner_mud_weight=inner_mud_weight,
        outer_mud_weight=outer_mud_weight,
        hole_diameter=hole_diameter,
        well_data=well_data,
        drill_collars_data=drill_collars_data,
    )

    return collar_selection
