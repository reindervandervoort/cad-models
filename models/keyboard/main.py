#!/usr/bin/env python3
"""
Keyboard Row: Multiple Keycaps with Roll
Create a row of keycaps, each rotated with roll (around X axis).
Roll axis is elevated by hand radius above keycap top.
"""

import FreeCAD
import Part
import Mesh
import os
import math
import json

print("=== Keyboard row with roll rotation ===")

# Document setup
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Keyboard")
    print("Created new document (standalone mode)")
else:
    print("Using provided document (backend mode)")

# Load parameters from input.json
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "input.json")
with open(input_file, 'r') as f:
    params = json.load(f)

hand_diameter = params.get('handDiameter', 192)
hand_radius = hand_diameter / 2
key_count = params.get('keyCount', 5)
u = params.get('u', 18)  # Unit size in mm

print(f"\nParameters:")
print(f"  Hand diameter: {hand_diameter}mm (radius: {hand_radius}mm)")
print(f"  Key count: {key_count}")
print(f"  Unit spacing: {u}mm")

# Load keycap STL once to get dimensions
keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")
print(f"\nLoading template: {keycap_stl}")
template_mesh = Mesh.Mesh(keycap_stl)

# Get original bounding box
bbox = template_mesh.BoundBox
print(f"Original STL bbox: X[{bbox.XMin:.1f}, {bbox.XMax:.1f}] Y[{bbox.YMin:.1f}, {bbox.YMax:.1f}] Z[{bbox.ZMin:.1f}, {bbox.ZMax:.1f}]")

# Calculate base offset to center keycap with top at origin
base_offset_x = -(bbox.XMin + bbox.XMax) / 2
base_offset_y = -(bbox.YMin + bbox.YMax) / 2
base_offset_z = -bbox.ZMax

print(f"Base offset: ({base_offset_x:.1f}, {base_offset_y:.1f}, {base_offset_z:.1f})")

# Configuration
roll_angle = 10  # degrees
roll_axis_height = hand_radius  # mm above keycap top

print(f"\nCreating {key_count} keycaps:")
print(f"  Roll angle: {roll_angle}°")
print(f"  Roll axis height: {roll_axis_height}mm")
print(f"  Spacing: {u}mm")

# Create each keycap
for i in range(key_count):
    print(f"\nKeycap {i+1}/{key_count}:")

    # Load fresh mesh
    keycap_mesh = Mesh.Mesh(keycap_stl)

    # Step 1: Center at origin (top at 0,0,0)
    keycap_mesh.translate(base_offset_x, base_offset_y, base_offset_z)

    # Step 2: Roll rotation around elevated X axis
    # Translate down so roll axis is at origin
    keycap_mesh.translate(0, 0, -roll_axis_height)

    # Rotate around X axis
    from FreeCAD import Matrix
    roll_matrix = Matrix()
    roll_matrix.rotateX(math.radians(roll_angle))
    keycap_mesh.transform(roll_matrix)

    # Translate back up
    keycap_mesh.translate(0, 0, roll_axis_height)

    # Step 3: Position in row along Y axis
    row_offset_y = (i - (key_count - 1) / 2) * u
    keycap_mesh.translate(0, row_offset_y, 0)

    print(f"  Position Y: {row_offset_y:.1f}mm")

    # Convert to shape
    keycap_shape = Part.Shape()
    keycap_shape.makeShapeFromMesh(keycap_mesh.Topology, 0.1)

    # Create object
    keycap_obj = doc.addObject("Part::Feature", f"Keycap_{i+1}")
    keycap_obj.Shape = keycap_shape

    final_bbox = keycap_obj.Shape.BoundBox
    print(f"  Final bbox: Y[{final_bbox.YMin:.1f}, {final_bbox.YMax:.1f}] Z[{final_bbox.ZMin:.1f}, {final_bbox.ZMax:.1f}]")

doc.recompute()
print(f"\nSUCCESS: Created {len(doc.Objects)} keycaps")
