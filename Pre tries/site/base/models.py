from django.db import models
from . import interpolate
import numpy as np

class Well(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    edited_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    surface_coords = models.CharField(max_length=15, blank=True, null=True)
    kop = models.FloatField(blank=True, null=True)
    targets = models.FileField(upload_to='uploads/', blank=True, null=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        kop = self.get_targets_coords()[0][2] / 2 # Initially halve of first target's depth

    def get_targets_coords(self):
        """
        Returns the (x_coords, y_coords, z_coords) cooridnates of a well's targets
        """
        # with open(file_path, 'r') as f:
        #     x = 1
        #     y = 1
        #     x = 1
        target_coords = np.array([[238.21, 137.53, 1164.06],
                                [337.47, 194.84, 1223.73],
                                [1284.59, 741.66, 1677.21],
                                [759.59, 438.55, 1327.21]])
        sorted_target_indices = np.argsort(target_coords[:,2])
        target_coords = target_coords[sorted_target_indices]
        
        x = target_coords[:, 0]
        y = target_coords[:, 1]
        z = target_coords[:, 2]
        return (x, y, z)
    
    def get_surface_coords(self):
        """
        Returns x, y, z surface coordinates
        """
        x, y, z = self.surface_coords.split(',')
        return (float(x), float(y), float(z))

    def get_well_data(self):
        """
        Returns a pandas data frame of well coordinates and inclination and azimuth in rad ans deg
        """
        surface_coords = self.get_surface_coords()
        target_coords = self.get_targets_coords()
        well_data = interpolate.get_well_data(surface_coords, self.kop, target_coords)
        return well_data

    def get_well_coords(self):
        """"
        Returns a tuple of well coordinates in order (north_coords, east_coords, depth_coords)
        """
        well_data = self.get_well_data()
        north, east, tvd = well_data['North'], well_data['East'], well_data['TVD']
        return (north, east, tvd)

    def __str__(self):
        return f"Well on = {self.created_at} with {len(self.get_targets_coords())} targets"

