#!/usr/bin/env python3
"""
Fresh Start: Single Keycap at Origin with Pitch
Position keycap with top center at (0, 0, 0), then rotate around Y axis.
No FreeCAD Placement transforms - all transforms applied to mesh vertices.
"""

import FreeCAD
import Part
import Mesh
import os
import math

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

# Apply pitch rotation around Y axis (45 degrees)
pitch_angle = 45  # degrees
print(f"\nApplying {pitch_angle}° pitch rotation around Y axis")

# Create rotation matrix for Y axis rotation
# Rotation happens around origin, which is now at the top center of the keycap
rotation_axis = FreeCAD.Vector(0, 1, 0)
rotation_angle = math.radians(pitch_angle)
keycap_mesh.rotate(0, 0, 0, rotation_axis.x, rotation_axis.y, rotation_axis.z, rotation_angle)

# Verify the rotation
bbox_rotated = keycap_mesh.BoundBox
print(f"\nAfter rotation:")
print(f"  X: [{bbox_rotated.XMin:.2f}, {bbox_rotated.XMax:.2f}]")
print(f"  Y: [{bbox_rotated.YMin:.2f}, {bbox_rotated.YMax:.2f}]")
print(f"  Z: [{bbox_rotated.ZMin:.2f}, {bbox_rotated.ZMax:.2f}]")

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
