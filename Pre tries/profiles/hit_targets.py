from .wp import *
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

well_data = get_well_data('s', 3000, kop=800, eob=1500, build_angle=45, eod=2400, set_start={'north': 123, 'east': 2000, 'depth': 0})
wellx, welly, wellz =  get_well_coods(well_data)

print(wellx, welly, wellz)

# initial_params = [3000, 800, 1500, 45, 1800, 2800, 100]
# fig = plt.figure()
# ax = plt.axes(projection='3d')
# plt.gca().invert_zaxis()
# ax.plot3D(wellx, welly, wellz, "blue")
# ax.set_xlabel("Eastings")
# ax.set_ylabel("Northenings")
# ax.set_zlabel("Vertical Depth")
# ax.view_init(elev=50, azim=(-42))
# ax.set_title("Build and hold profile")

# plt.show()
# well_data.to_excel('data.xlsx')
# print(well_data)