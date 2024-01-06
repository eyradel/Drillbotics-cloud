from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib import messages

from .models import Well

from . import wp

import plotly.graph_objs as go
import plotly.offline as pio
import numpy as np
import plotly.express as px
import pandas as pd


class Index(TemplateView):
    template_name = 'base/index.html'


class FindProfile(TemplateView):
    template_name = 'base/findprofile.html'
    model = Well
    context_object_name = 'well'    

    def get(self, request, *args, **kwargs):
        context = super().get_context_data()
        context['plot'] = self.plot()
        context['tvd_kop'] = self.get_well_object(**kwargs).kop # Allows kop to be visible on the front end
        context['start'] = self.get_well_object(**kwargs).surface_coords # Allows start coords to be visible at the front end
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        well = self.get_well_object(**kwargs)
        form = request.POST
        if 'done' in form:
            final_data = well.get_well_data()
            final_data.to_csv('Final_well_data.csv')
            messages.success(request, "Done. Coordinates Gotten!!!")

        tvd_kop = form.get('tvd_kop')
        start = form.get('set_start')
        if start.count(',') == 2:            
            well.kop = float(tvd_kop)
            try:
                n, e, d = start.split(',')
                # See if there're convertible to floats to make sure they're valid
                float(n)
                float(e)
                float(d)
                well.surface_coords = start
                well.save()
            except:
                messages.error(request, "Invalid set Start! Please enter in this format: x,y,z")
        else:
            messages.error(request, "Invalid set Start! Please enter in this format: x,y,z")

        return self.get(request, *args, **kwargs)

    
    def get_well_object(self, **kwargs):
        # self.kwargs.pop('pk')
        well = Well.objects.get(pk='1')
        return well

    def plot(self, **kwargs):
        """
        Takes well coords from get_well_coods and creats a plot obj
        """
        well = self.get_well_object(**kwargs)
        
        x, y, z = well.get_well_coords()
        well_x = x.values
        well_y = y.values
        well_z = z.values        
        targets_x, targets_y, targets_z = well.get_targets_coords()

        # Create the trace object for the well coordinates
        well_trace = go.Scatter3d(
            x=well_x,
            y=well_y,
            z=well_z,
            mode='lines',
            line=dict(
                color='blue',
                width=3
            )
        )
        
        t = pd.Series([])

        # Create the trace object for the target points to have different colors
        target_trace = go.Scatter3d(
            x=targets_x,
            y=targets_y,
            z=targets_z,
            mode='markers',
            marker=dict(
                size=6,
                color='red',
                opacity=0.8
            )
        )


        # Create the layout for the plot
        layout = go.Layout(
            scene=dict(
                xaxis=dict(title='X Axis'),
                yaxis=dict(title='Y Axis'),
                zaxis=dict(title='Z Axis', autorange='reversed')
            ),
            margin=dict(l=0, r=0, b=0, t=0)
        )

        # Create the figure and plot the traces
        fig = go.Figure(data=[well_trace, target_trace], layout=layout)
        plot_div = pio.plot(fig, auto_open=False, output_type='div')

        return plot_div
    


# class _FindProfile(TemplateView):
#     template_name = 'base/findprofile.html'

#     targets_coods = [[238.21, 137.53, 1164.06],
#                     [337.47, 194.84, 1223.73],
#                     [759.59, 438.55, 1327.21],
#                     [1284.59, 741.66, 1677.21]]
    
#     profile_type = 's'
#     target_depth = targets_coods[-1][2] # Depth of last target
#     kop = 800
#     eob = 1500
#     build_angle = 45
#     sod = 0
#     eod = 2400
#     units = 'metric',
#     cells_no = 100
#     set_start = {'north': 0, 'east': 0, 'depth': 0}

#     def get(self, request, *args, **kwargs):
#         context = super().get_context_data()
#         context['plot'] = self.plot()        
#         return render(request, self.template_name, context)
    
#     def post(self, request, *args, **kwargs):
#         form = self.request.POST

#         profile = form.get('profile')        
#         start = form.get('set_start')
#         if start.count(',') == 2:
#             north, east, depth = form.get('set_start').split(',')
#             self.set_start = {'north': int(north), 'east': int(east), 'depth': int(depth)}            
#             self.cells_no = int(form.get('cells_no'))                    

#             if profile == 'v':
#                 pass # Already set since all other profiles takes v's parameters
#             else:
#                 # All other takes eob and kop and build angle
#                 self.kop = int(form.get("kop"))
#                 self.eob = int(form.get("eob"))
#                 self.build_angle = int(form.get("build_angle"))

#                 if profile == 'j' or profile == 'hds' or profile == 'hcs':
#                     pass # Already satisfied                
#                 elif profile == 's':                    
#                     self.sod = int(form.get("sod"))
#                     self.eod = int(form.get("eod"))            
#             self.profile_type = profile            
#         else:
#             messages.error(request, "Invalid start coordinates! Enter in this format[east, north, depth]; 123,32,43")                    

#         context = super().get_context_data()
#         context['plot'] = self.plot()
#         return render(request, self.template_name, context)


#     def get_well_coods(self):
#         """"
#         Returns a tuple of well coordinats in order [x, y, z]
#         """
#         well_data = wp.get_well_data(
#             profile_type=self.profile_type,
#             target_depth=self.target_depth,
#             kop=self.kop,
#             eob=self.eob,
#             build_angle=self.build_angle,
#             sod=self.sod,
#             eod=self.eod,
#             units='metric',
#             cells_no=self.cells_no,
#             set_start=self.set_start)
        
#         return wp.get_well_coods(well_data)

#     def plot(self):
#         """
#         Takes well coods from get_well_coods and creats a plot obj
#         """
#         x, y, z = self.get_well_coods()
        
#         # Create a trace for the scatter plot
#         trace1 = go.Scatter3d(
#             x=x,
#             y=y,
#             z=z,
#             mode='markers',
#             marker=dict(
#                 size=2,
#                 color=z,
#                 colorscale='Viridis',
#                 opacity=0.8
#             )
#         )
        
#         trace2 = go.Scatter3d(
#             x=[i[0] for i in self.targets_coods],
#             y=[i[1] for i in self.targets_coods],
#             z=[i[2] for i in self.targets_coods],
#             mode='markers',
#             marker=dict(
#                 size=4,
#                 color='red',
#                 opacity=0.8
#             )
#         )

#         # Create the layout for the plot with an inverted z-axis
#         layout = go.Layout(
#             scene=dict(
#                 xaxis=dict(title='X Axis'),
#                 yaxis=dict(title='Y Axis'),
#                 zaxis=dict(title='Z Axis', range=[np.max([i[2] for i in self.targets_coods]), np.min(z)])
#             ),
#             margin=dict(l=0, r=0, b=0, t=0)
#         )

#         # Create the figure and plot the trace
#         fig = go.Figure(data=[trace1, trace2], layout=layout)
        
#         plot_div = opy.plot(fig, auto_open=False, output_type='div')
#         return plot_div
    