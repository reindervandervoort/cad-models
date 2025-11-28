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

    # Strategy for rotation around elevated axis:
    # The keycap starts at origin (top at 0,0,0)
    # We want to:
    # 1. Move it to (0, row_offset_y, 0)
    # 2. Apply pitch rotation around Y axis passing through that point
    # 3. Apply roll rotation around X axis that's hand_radius ABOVE that point
    #    i.e., around point (0, row_offset_y, hand_radius)

    # Step 1: Position in row
    pos = FreeCAD.Vector(0, row_offset_y, 0)

    # Step 2: Pitch rotation (around Y axis at the keycap position)
    pitch_rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), pitch_angle)

    # Step 3: Roll rotation around elevated X axis
    # To rotate around (0, row_offset_y, hand_radius):
    # - Translate by (0, 0, -hand_radius) so rotation point is at (0, row_offset_y, 0)
    # - Rotate around X axis
    # - Translate by (0, 0, hand_radius) back up

    roll_rotation = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), roll_angle)

    # Combine rotations: pitch first, then roll
    combined_rotation = pitch_rotation.multiply(roll_rotation)

    # For roll around elevated axis, we need to offset the position
    # When we rotate around X axis elevated by hand_radius,
    # the Y position stays the same, but Z position changes

    # Create placement: rotation at origin, then translate
    # But we need to account for the offset caused by rotating around elevated axis
    # The keycap top (at Z=0) rotates around axis at Z=hand_radius
    # After rotation, the center needs adjustment

    placement = FreeCAD.Placement(pos, combined_rotation)

    # Adjust for rotation around elevated axis:
    # Move down by hand_radius before rotation conceptually happens
    # This means we need to shift the final position
    # After roll rotation, translate to account for the elevated rotation point
    placement.Base = FreeCAD.Vector(0, row_offset_y, hand_radius * (1 - math.cos(math.radians(roll_angle))))

    obj.Placement = placement

    print(f"  Placement: Base={placement.Base}")
    print(f"  BBox: Y[{obj.Shape.BoundBox.YMin:.1f}, {obj.Shape.BoundBox.YMax:.1f}] Z[{obj.Shape.BoundBox.ZMin:.1f}, {obj.Shape.BoundBox.ZMax:.1f}]")

doc.recompute()
print(f"\nSUCCESS: Created {len(doc.Objects)} keycaps with Placement transforms")
