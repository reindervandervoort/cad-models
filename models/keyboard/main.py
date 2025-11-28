#!/usr/bin/env python3
"""
Keyboard Row: Keycaps with Switches on Circular Arc
Keycaps and switches positioned on curved row with pitch and roll
"""

import FreeCAD
import Part
import Mesh
import os
import math
import json

print("=== Keyboard row with keycaps and switches ===")

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
switch_offset = 6  # mm below keycap top

print(f"\nParameters: keyCount={key_count}, u={u}mm, pitch={pitch_angle}°, hand_radius={hand_radius}mm")

# Helper function to calculate placement for any component
def calculate_placement(position_index, key_count, u, hand_radius, pitch_angle, z_offset=0):
    """
    Calculate placement for a component on the circular arc.

    Args:
        position_index: Position in row (0 to key_count-1)
        key_count: Total number of keys
        u: Spacing between keys
        hand_radius: Radius of circular arc
        pitch_angle: Pitch angle in degrees
        z_offset: Additional Z offset from keycap top (negative = below)

    Returns:
        FreeCAD.Placement object
    """
    # Calculate arc angle for this position
    row_offset_y_linear = (position_index - (key_count - 1) / 2) * u
    keycap_angle = row_offset_y_linear / hand_radius  # radians
    keycap_angle_deg = math.degrees(keycap_angle)

    # Position on the circular arc around X axis at height hand_radius
    pos_x = 0
    pos_y = hand_radius * math.sin(keycap_angle)
    pos_z = hand_radius * (1 - math.cos(keycap_angle)) + z_offset

    # Rotations: roll by the arc angle first, THEN pitch around Y
    roll_rot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), keycap_angle_deg)
    pitch_rot = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), pitch_angle)
    combined_rot = roll_rot.multiply(pitch_rot)

    return FreeCAD.Placement(FreeCAD.Vector(pos_x, pos_y, pos_z), combined_rot), keycap_angle_deg


# Load and prepare base keycap mesh
keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")
print(f"\nLoading keycap: {keycap_stl}")

keycap_mesh = Mesh.Mesh(keycap_stl)
bbox = keycap_mesh.BoundBox

# Center the keycap mesh (top at Z=0)
offset_x = -(bbox.XMin + bbox.XMax) / 2
offset_y = -(bbox.YMin + bbox.YMax) / 2
offset_z = -bbox.ZMax
keycap_mesh.translate(offset_x, offset_y, offset_z)

keycap_shape = Part.Shape()
keycap_shape.makeShapeFromMesh(keycap_mesh.Topology, 0.1)

# Load and prepare base switch mesh
switch_stl = os.path.join(script_dir, "kailhlowprofilev102.stl")
print(f"Loading switch: {switch_stl}")

try:
    switch_mesh = Mesh.Mesh(switch_stl)
    switch_bbox = switch_mesh.BoundBox

    print(f"Switch original bbox: X[{switch_bbox.XMin:.1f}, {switch_bbox.XMax:.1f}] Y[{switch_bbox.YMin:.1f}, {switch_bbox.YMax:.1f}] Z[{switch_bbox.ZMin:.1f}, {switch_bbox.ZMax:.1f}]")

    # Center the switch mesh (top at Z=0)
    switch_offset_x = -(switch_bbox.XMin + switch_bbox.XMax) / 2
    switch_offset_y = -(switch_bbox.YMin + switch_bbox.YMax) / 2
    switch_offset_z = -switch_bbox.ZMax

    print(f"Switch offset: ({switch_offset_x:.1f}, {switch_offset_y:.1f}, {switch_offset_z:.1f})")

    switch_mesh.translate(switch_offset_x, switch_offset_y, switch_offset_z)

    # Convert to shape with looser tolerance to avoid degenerate geometry
    switch_shape = Part.Shape()
    switch_shape.makeShapeFromMesh(switch_mesh.Topology, 0.5)  # Increased from 0.1 to 0.5

    # Simplify/fix the shape
    if not switch_shape.isValid():
        print("WARNING: Switch shape invalid, attempting to fix...")
        switch_shape = switch_shape.removeSplitter()

    print(f"Switch shape created successfully")

except Exception as e:
    print(f"ERROR loading switch: {e}")
    import traceback
    traceback.print_exc()
    # Create a dummy box as fallback
    switch_shape = Part.makeBox(10, 10, 5)
    print("Using fallback box for switch")

# Create keycaps and switches
for i in range(key_count):
    print(f"\n=== Key {i+1}/{key_count} ===")

    # Create keycap
    keycap_obj = doc.addObject("Part::Feature", f"Keycap_{i+1:02d}")
    keycap_obj.Shape = keycap_shape
    keycap_placement, angle = calculate_placement(i, key_count, u, hand_radius, pitch_angle, z_offset=0)
    keycap_obj.Placement = keycap_placement

    # Create switch (6mm below keycap top)
    switch_obj = doc.addObject("Part::Feature", f"Switch_{i+1:02d}")
    switch_obj.Shape = switch_shape
    switch_placement, _ = calculate_placement(i, key_count, u, hand_radius, pitch_angle, z_offset=-switch_offset)
    switch_obj.Placement = switch_placement

    print(f"  Arc angle: {angle:.2f}°")
    print(f"  Keycap pos: ({keycap_placement.Base.x:.1f}, {keycap_placement.Base.y:.1f}, {keycap_placement.Base.z:.1f})")
    print(f"  Switch pos: ({switch_placement.Base.x:.1f}, {switch_placement.Base.y:.1f}, {switch_placement.Base.z:.1f})")

doc.recompute()
print(f"\nSUCCESS: Created {key_count} keycaps and {key_count} switches ({len(doc.Objects)} objects total)")
