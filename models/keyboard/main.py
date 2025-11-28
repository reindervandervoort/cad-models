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
pitch_angle = params.get('pitch', 45)  # Pitch in degrees

print(f"\nParameters:")
print(f"  Hand diameter: {hand_diameter}mm (radius: {hand_radius}mm)")
print(f"  Key count: {key_count}")
print(f"  Unit spacing: {u}mm")
print(f"  Pitch angle: {pitch_angle}°")

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
from FreeCAD import Matrix

for i in range(key_count):
    print(f"\n=== Keycap {i+1}/{key_count} ===")

    # Load fresh mesh for this keycap
    mesh = Mesh.Mesh(keycap_stl)
    print(f"  Loaded mesh: {len(mesh.Facets)} facets")

    # Step 1: Center at origin (top at 0,0,0)
    mesh.translate(base_offset_x, base_offset_y, base_offset_z)
    print(f"  Step 1: Centered at origin")

    # Step 2: Pitch rotation around Y axis (at origin, which is top center)
    pitch_matrix = Matrix()
    pitch_matrix.rotateY(math.radians(pitch_angle))
    mesh.transform(pitch_matrix)
    print(f"  Step 2: Pitched {pitch_angle}° around Y axis")

    # Step 3: Roll rotation around elevated X axis
    # Translate down so roll axis is at origin
    mesh.translate(0, 0, -roll_axis_height)

    # Rotate around X axis
    roll_matrix = Matrix()
    roll_matrix.rotateX(math.radians(roll_angle))
    mesh.transform(roll_matrix)

    # Translate back up
    mesh.translate(0, 0, roll_axis_height)
    print(f"  Step 3: Rolled {roll_angle}° around elevated X axis (height={roll_axis_height}mm)")

    # Step 4: Position in row along Y axis
    row_offset_y = (i - (key_count - 1) / 2) * u
    mesh.translate(0, row_offset_y, 0)
    print(f"  Step 4: Positioned at Y={row_offset_y:.1f}mm")

    # Convert to shape
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Topology, 0.1)

    # Create object with unique name
    obj = doc.addObject("Part::Feature", f"Keycap_{i+1:02d}")
    obj.Shape = shape

    final_bbox = obj.Shape.BoundBox
    print(f"  Final bbox: X[{final_bbox.XMin:.1f},{final_bbox.XMax:.1f}] Y[{final_bbox.YMin:.1f},{final_bbox.YMax:.1f}] Z[{final_bbox.ZMin:.1f},{final_bbox.ZMax:.1f}]")
    print(f"  Object name: {obj.Name}")

doc.recompute()
print(f"\nSUCCESS: Created {len(doc.Objects)} keycaps")
