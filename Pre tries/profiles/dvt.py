import numpy as np
import matplotlib.pyplot as plt
from devito import *
from sympy import Symbol

# Define the target coordinates as a list of tuples (x, y, z)
targets = [(1000, 1000, 0), (1500, 1500, -500), (2000, 2000, -1000), (2500, 2500, -1500)]

# Create a symbolic curve that passes through the targets
x = Symbol('x')
y = Symbol('y')
z = Symbol('z')
curve = z - (x-1000)*(1500-x)*(2000-x)*(2500-x)/(10**9) - y*(y-1000)*(y-1500)*(y-2000)*(y-2500)/(10**9)

# Define the grid for the finite difference method
grid = Grid(shape=(81, 81, 81), extent=(4000., 4000., 3000.), origin=(0., 0., -1500.))

# Define the PDE for the finite difference method
pde = Eq(grad(z).dot(grad(z)) + curve**2, 1)

# Solve the PDE using the finite difference method
z_field = solve(pde, z, grid=grid, time_axis=None, stencil=ExtrapolationStencil(1))

# Extract the well path from the z_field
path = [(x, y, z_field.data[x, y]) for x in range(81) for y in range(81)]

# Plot the well path
fig, ax = plt.subplots()
ax.plot([p[0] for p in path], [p[1] for p in path])
plt.show()
