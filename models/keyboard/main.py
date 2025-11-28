#!/usr/bin/env python3
"""
Fresh Start: Single Keycap at Origin
Position keycap with top center at (0, 0, 0) by translating the mesh vertices.
No FreeCAD Placement transforms.
"""

import FreeCAD
import Part
import Mesh
import os

print("=== Fresh start: Keycap positioning ===")

# Document setup
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Keyboard")
    print("Created new document (standalone mode)")
else:
    print("Using provided document (backend mode)")

# Load keycap STL
script_dir = os.path.dirname(os.path.abspath(__file__))
keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")

print(f"\nLoading: {keycap_stl}")
keycap_mesh = Mesh.Mesh(keycap_stl)

# Get original bounding box
bbox = keycap_mesh.BoundBox
print(f"\nOriginal STL bounding box:")
print(f"  X: [{bbox.XMin:.2f}, {bbox.XMax:.2f}] width: {bbox.XLength:.2f}mm")
print(f"  Y: [{bbox.YMin:.2f}, {bbox.YMax:.2f}] depth: {bbox.YLength:.2f}mm")
print(f"  Z: [{bbox.ZMin:.2f}, {bbox.ZMax:.2f}] height: {bbox.ZLength:.2f}mm")

# Calculate offset to position top center at origin
# Target: top center at (0, 0, 0)
offset_x = -(bbox.XMin + bbox.XMax) / 2  # Center X at 0
offset_y = -(bbox.YMin + bbox.YMax) / 2  # Center Y at 0
offset_z = -bbox.ZMax                     # Top at Z=0

print(f"\nApplying offset: ({offset_x:.2f}, {offset_y:.2f}, {offset_z:.2f})")

# Translate mesh vertices
keycap_mesh.translate(offset_x, offset_y, offset_z)

# Verify the translation
bbox_after = keycap_mesh.BoundBox
print(f"\nAfter translation:")
print(f"  X: [{bbox_after.XMin:.2f}, {bbox_after.XMax:.2f}]")
print(f"  Y: [{bbox_after.YMin:.2f}, {bbox_after.YMax:.2f}]")
print(f"  Z: [{bbox_after.ZMin:.2f}, {bbox_after.ZMax:.2f}]")
print(f"  Top center: ({(bbox_after.XMin+bbox_after.XMax)/2:.2f}, "
      f"{(bbox_after.YMin+bbox_after.YMax)/2:.2f}, {bbox_after.ZMax:.2f})")

# Convert to shape
keycap_shape = Part.Shape()
keycap_shape.makeShapeFromMesh(keycap_mesh.Topology, 0.1)

# Create object with identity placement
keycap_obj = doc.addObject("Part::Feature", "Keycap")
keycap_obj.Shape = keycap_shape

print(f"\nFinal object:")
print(f"  Placement: {keycap_obj.Placement}")
print(f"  Valid: {keycap_obj.Shape.isValid()}")
print(f"  Vertices: {len(keycap_obj.Shape.Vertexes)}")
print(f"  Faces: {len(keycap_obj.Shape.Faces)}")

doc.recompute()
print(f"\nSUCCESS: {len(doc.Objects)} object(s) created")
