#!/usr/bin/env python3
"""
Keyboard Row: Keycaps with Pitch and Roll using Placement
Use FreeCAD Placement for transformations so they export correctly to assembly.json
"""

import FreeCAD
import Part
import Mesh
import os
import math
import json

print("=== Keyboard row with Placement transforms ===")

# Document setup
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Keyboard")
else:
    print("Using backend mode")

# Load parameters
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "input.json")
with open(input_file, 'r') as f:
    params = json.load(f)

hand_diameter = params.get('handDiameter', 192)
hand_radius = hand_diameter / 2
key_count = params.get('keyCount', 5)
u = params.get('u', 18)
pitch_angle = params.get('pitch', 45)

print(f"\nParameters: keyCount={key_count}, u={u}mm, pitch={pitch_angle}°, hand_radius={hand_radius}mm")

# Load and prepare base keycap mesh (centered at origin with top at Z=0)
keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")
print(f"Loading: {keycap_stl}")

base_mesh = Mesh.Mesh(keycap_stl)
bbox = base_mesh.BoundBox

# Center the base mesh
offset_x = -(bbox.XMin + bbox.XMax) / 2
offset_y = -(bbox.YMin + bbox.YMax) / 2
offset_z = -bbox.ZMax
base_mesh.translate(offset_x, offset_y, offset_z)

print(f"Base mesh centered at origin (top at Z=0)")

# Convert to base shape (will be reused)
base_shape = Part.Shape()
base_shape.makeShapeFromMesh(base_mesh.Topology, 0.1)

# Create keycaps with Placement transforms
roll_angle = 10  # degrees

for i in range(key_count):
    print(f"\n=== Keycap {i+1}/{key_count} ===")

    # Create object with base shape
    obj = doc.addObject("Part::Feature", f"Keycap_{i+1:02d}")
    obj.Shape = base_shape

    # Calculate row position
    row_offset_y = (i - (key_count - 1) / 2) * u
    print(f"  Row position: Y={row_offset_y:.1f}mm")

    # For rotation around elevated X axis:
    # The keycap at (0, Y, 0) rotates around axis at (0, Y, hand_radius)
    # After roll rotation by angle θ:
    # - Y stays the same
    # - Z = hand_radius - hand_radius * cos(θ) = hand_radius * (1 - cos(θ))
    # This gives the arc position

    roll_rad = math.radians(roll_angle)

    # Position after roll around elevated axis
    pos_x = 0
    pos_y = row_offset_y
    pos_z = hand_radius * (1 - math.cos(roll_rad))

    # Rotations: pitch around Y, then roll around X
    pitch_rot = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), pitch_angle)
    roll_rot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), roll_angle)
    combined_rot = pitch_rot.multiply(roll_rot)

    # Create placement
    placement = FreeCAD.Placement(FreeCAD.Vector(pos_x, pos_y, pos_z), combined_rot)

    obj.Placement = placement

    print(f"  Placement: Base=({pos_x:.1f}, {pos_y:.1f}, {pos_z:.1f})")
    print(f"  Rotation: Pitch={pitch_angle}° + Roll={roll_angle}°")
    print(f"  BBox: Y[{obj.Shape.BoundBox.YMin:.1f}, {obj.Shape.BoundBox.YMax:.1f}] Z[{obj.Shape.BoundBox.ZMin:.1f}, {obj.Shape.BoundBox.ZMax:.1f}]")

doc.recompute()
print(f"\nSUCCESS: Created {len(doc.Objects)} keycaps with Placement transforms")
