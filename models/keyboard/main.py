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

    # Build transformation using FreeCAD Placement
    # Order: translate to row position, then pitch, then roll around elevated axis

    # Start with translation to row position
    placement = FreeCAD.Placement()
    placement.Base = FreeCAD.Vector(0, row_offset_y, 0)

    # Apply pitch rotation (around Y axis at origin)
    pitch_rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), pitch_angle)
    placement.Rotation = pitch_rotation

    # For roll: rotate around X axis elevated by hand_radius
    # This requires: translate down, rotate, translate up
    # In Placement terms: first move to (0, row_offset_y, -hand_radius),
    # then apply rotations, then move up by hand_radius

    # Combined rotation: pitch then roll
    roll_rotation = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), roll_angle)
    combined_rotation = pitch_rotation.multiply(roll_rotation)

    # Apply rotations first, then translate
    # Final position needs to account for roll axis elevation
    placement.Rotation = combined_rotation
    placement.Base = FreeCAD.Vector(0, row_offset_y, 0)

    # Apply placement
    obj.Placement = placement

    print(f"  Placement: Base={placement.Base}, Rotation=Pitch{pitch_angle}°+Roll{roll_angle}°")
    print(f"  BBox: Y[{obj.Shape.BoundBox.YMin:.1f}, {obj.Shape.BoundBox.YMax:.1f}]")

doc.recompute()
print(f"\nSUCCESS: Created {len(doc.Objects)} keycaps with Placement transforms")
