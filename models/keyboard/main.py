#!/usr/bin/env python3
"""
Debug: Single keycap only
"""

import FreeCAD
import Part
import Mesh
import os

print("=== DEBUG: Single keycap ===")

# Document setup
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Keyboard")
else:
    print("Using backend mode")

# Load keycap
script_dir = os.path.dirname(os.path.abspath(__file__))
keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")

print(f"Loading: {keycap_stl}")
keycap_mesh = Mesh.Mesh(keycap_stl)

# Get bbox
bbox = keycap_mesh.BoundBox
print(f"Bbox: X[{bbox.XMin:.1f}, {bbox.XMax:.1f}] Y[{bbox.YMin:.1f}, {bbox.YMax:.1f}] Z[{bbox.ZMin:.1f}, {bbox.ZMax:.1f}]")

# Center at origin
offset_x = -(bbox.XMin + bbox.XMax) / 2
offset_y = -(bbox.YMin + bbox.YMax) / 2
offset_z = -bbox.ZMax

print(f"Offset: ({offset_x:.1f}, {offset_y:.1f}, {offset_z:.1f})")
keycap_mesh.translate(offset_x, offset_y, offset_z)

# Convert to shape
keycap_shape = Part.Shape()
keycap_shape.makeShapeFromMesh(keycap_mesh.Topology, 0.1)

# Create object
keycap_obj = doc.addObject("Part::Feature", "Keycap")
keycap_obj.Shape = keycap_shape

doc.recompute()
print(f"SUCCESS: Created {len(doc.Objects)} object(s)")
