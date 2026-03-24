import pymeshlab
import pyvista as pv
from pathlib import Path

Path(".out").mkdir(exist_ok=True)

ms = pymeshlab.MeshSet()
ms.load_new_mesh("mesh/apple.obj")

m = ms.current_mesh()
print(f"Vertices : {m.vertex_number()}")
print(f"Faces    : {m.face_number()}")

# Geometric measures (area, volume, bounding box)
measures = ms.get_geometric_measures()
print(f"Surface area : {measures['surface_area']:.4f}")
print(f"Volume       : {measures['mesh_volume']:.4f}")
bbox = measures['bbox']
print(f"Bounding box : min={bbox.min()}, max={bbox.max()}, diag={bbox.diagonal():.4f}")

print(f"\nHas vertex color : {m.has_vertex_color()}")

# Paint all vertices gold
ms.set_color_per_vertex(color1=pymeshlab.Color(255, 200, 0))
print("Painted gold!")

ms.save_current_mesh(".out/apple_gold.ply")
print("Saved: .out/apple_gold.ply")

# View
mesh = pv.read(".out/apple_gold.ply")
mesh.plot(rgb=True)
