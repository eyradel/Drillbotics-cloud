from collections import namedtuple
import numpy as np
from scipy.optimize import minimize

from drillmodules.bit.bit_model import rop_tob_drillbotics
from drillmodules.well_plan.well_data import calDLS


SECS_IN_HOUR = 3600


SimulatedStation = namedtuple(
    "SimulatedStation",
    [
        "coordinates",
        "rop_axial",
        "rop_lateral",
        "tob",
        "wob",
        "md",
        "rpm",
        "buckling",
        "azimuth",
        "inclination",
        "dls",
    ],
)


class Pad:
    def __init__(self, angle):
        self.angle = angle
        self.mag = 1

    def get_xy(self):
        return self.mag * np.array([np.cos(self.angle), np.sin(self.angle)])


class RSS:
    def __init__(
        self,
        max_force,
        initial_pos,
        minimization_args,
        t_delta=5,
    ):
        """
        RSS model
        Inputs
        ------
            max_force: maximum force for each RSS pad
            initial_pos: initial RSS position
            target_pos: Target position to reach
            rop_axial: The axial rop of the bit
            t_delta: The differences in time between rss simulation loops
            minimization_args: dict of args for minimization method
            defualts to {method:'slsqp'}. See scipy.optimze.minimise for more info
            well_data: X, Y, and Z coordinates of well at every survey station
        """
        self.current_pos = initial_pos

        self.minimization_args = minimization_args
        self.rop_axial = None
        self.target_pos = None
        self.t_delta = t_delta
        self.bounds = [(10000, max_force)] * 3
        self.pad1_force = Pad(angle=0)
        self.pad2_force = Pad(angle=2 * np.pi / 3)
        self.pad3_force = Pad(angle=4 * np.pi / 3)

    def _delta_z(self):
        """Change in z cooridnates"""
        return self.rop_axial * self.t_delta / SECS_IN_HOUR

    def _objective_func(self, x):
        """
        Finds the distance from a point to the target point for some
        set magnitudes of the RSS pads
        Inputs
        ------
            x: array like magnitudes of the RSS pads
        """
        mag1, mag2, mag3 = x
        self.pad1_force.mag = mag1
        self.pad2_force.mag = mag2
        self.pad3_force.mag = mag3

        new_p0 = (
            self.pad1_force.get_xy()
            + self.pad2_force.get_xy()
            + self.pad3_force.get_xy()
            + self.current_pos[:2]
        )
        return np.linalg.norm([self.target_pos[:2] - new_p0])

    def _set_mags(self, minimization_args):
        """
        Sets the appropriate magnitudes of the RSS pads' magnitudes
        Minimizes the objective funtion to archive the appropriate magnitudes
        Inputs:
        -------
            - minimization_args: a dictionary of args for the minimiztion
                See scipy.optimize.minimise for usage
        """

        result = minimize(
            self._objective_func, [50, 50, 50], **minimization_args, bounds=self.bounds
        )
        self.pad1_force.mag, self.pad2_force.mag, self.pad3_force.mag = result.x

    def get_coords(self):
        """Returns next coordinates from current position to the Target"""

        self._set_mags(self.minimization_args)
        new_2d_p0 = (
            self.pad1_force.get_xy()
            + self.pad2_force.get_xy()
            + self.pad3_force.get_xy()
            + self.current_pos[:2]
        )
        self.current_pos = np.concatenate(
            (new_2d_p0, np.array([self._delta_z() + self.current_pos[2]]))
        )

        return self.current_pos


class RSSDataGenerator:
    def __init__(
        self,
        plan,
        drillcollar,
        drillpipe,
        max_force=50000,
        formation_aggressiveness=[(0, 0.6)],
        CCS=[(0, 30000)],
        bit_aggressiveness_factor=1.2,
        initial_WOB=list(zip(range(0, 1000), range(50000, 52000, 2))), # Not used!
        RPM=130,
        Eff=0.35,
        D=12.25,
        side_cutting_factor=1.1,
        t_delta=5,
        minimization_args={"method": "slsqp"},
    ):
        stations = []
        for _, row in plan[["X", "Y", "Z"]].iterrows():
            stations.append((row["X"], row["Y"], row["Z"]))

        self.stations = stations
        self.formation_aggressiveness_data = formation_aggressiveness
        self.bit_aggressiveness_factor = bit_aggressiveness_factor
        
        well_depth = stations[-1][-1]
        delta_station = stations[1][-1] - stations[0][-1]
        num_steps = well_depth // delta_station
        
        start_WOB = 1000
        end_WOB = 80000
        delta_WOB = (end_WOB - start_WOB) / num_steps
        self.pre_WOB = list(zip(range(0, well_depth, delta_station), [start_WOB + i*delta_WOB for i in range(num_steps)]))

        self.RPM_data = RPM
        self.Eff = Eff
        self.D = D
        self.CCS_data = CCS
        self.side_cutting_factor = side_cutting_factor
        self.drillcollar = drillcollar
        self.drillpipe = drillpipe

        self.rss = RSS(
            max_force=max_force,
            initial_pos=stations[0],
            t_delta=t_delta,
            minimization_args=minimization_args,
        )
        self.current_pos = 0

    def _get_current_value(self, values):
        """
        Given a list of tuples of formation, some_property,
        chooses the current property based on the self current formation
        """
        current_form = self.stations[self.current_pos][-1]
        for idx, i in enumerate(values):
            if i[0] <= current_form:
                try:
                    if values[idx + 1][0] > current_form:
                        return i[1]
                except IndexError:
                    return i[1]

    @property
    def formation_aggressiveness(self):
        return self._get_current_value(self.formation_aggressiveness_data)

    @property
    def WOB(self):
        return self._get_current_value(self.pre_WOB)

    @property
    def RPM(self):
        return self.RPM_data * np.random.uniform(0.75, 1)

    @property
    def CCS(self):
        return self._get_current_value(self.CCS_data)

    @property
    def side_force(self):
        return self.drillpipe.get_side_cutting_factor()

    def _getRopAxialRopLatTob(self):
        """Calculates rop, rop_lateral, and tob"""
        rop, rop_lat, tob = rop_tob_drillbotics(
            formation_aggressiveness=self.formation_aggressiveness,
            bit_aggressiveness_factor=self.bit_aggressiveness_factor,
            WOB=self.WOB,
            RPM=self.RPM,
            Eff=self.Eff,
            D=self.D,
            CCS=self.CCS,
            side_force=self.side_force,
            side_cutting_factor=self.side_cutting_factor,
        )

        return rop, rop_lat, tob

    def data(self):
        current_z = 0
        pre_sim_coords = np.array([0, 0, 0])
        pre_md, pre_incli, pre_azi = 0, 0, 0
        last_tvd = self.stations[-1][-1]

        while last_tvd > current_z:
            rop_axial, rop_lat, tob = self._getRopAxialRopLatTob()

            self.rss.rop_axial = rop_axial
            self.rss.target_pos = self.stations[self.current_pos]

            sim_coords = self.rss.get_coords()

            squared_diff = np.square(sim_coords - pre_sim_coords)
            squared_distance = np.sum(squared_diff, axis=-1)
            delta_md = np.sqrt(squared_distance)
            md = pre_md + delta_md

            x, y, z = sim_coords
            cur_inclination = np.arctan2(z, np.sqrt(y**2 + x**2))
            cur_azimuth = np.arctan2(x, y)
            buckling = self.drillpipe._paslay_buckling(cur_azimuth)
            dls = calDLS(
                pre_md=pre_md,
                md=md,
                pre_azi=pre_azi,
                azi=cur_azimuth,
                pre_incli=pre_incli,
                incli=cur_inclination,
            )

            _data = SimulatedStation(
                coordinates=sim_coords,
                rop_axial=rop_axial,
                rop_lateral=rop_lat,
                tob=tob,
                wob=self.WOB,
                md=md,
                rpm=self.RPM,
                buckling=buckling,
                azimuth=cur_azimuth,
                inclination=cur_inclination,
                dls=dls,
            )

            current_z = sim_coords[-1]
            pre_sim_coords = sim_coords
            pre_md, pre_incli, pre_azi = md, cur_inclination, cur_azimuth

            if current_z >= self.stations[self.current_pos][2]:
                # If we've reached a station, change to the next
                self.current_pos += 1

            yield _data
