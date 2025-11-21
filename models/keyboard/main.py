#!/usr/bin/env python3
"""
Keyboard Model
Creates a row of keycaps and switches from STL files
Uses kailh_choc_low_profile_keycap.stl and kailhlowprofilev102.stl
Backend provides 'doc' variable - we add objects to it
"""

import FreeCAD
import Part
import Mesh
import json
import os

print("Starting keyboard generation with STL files...")
print(f"Using document: {doc.Name if 'doc' in dir() else 'Creating new for standalone'}")

# If running standalone (not from backend), create doc
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Keyboard")
    print("✓ Created new document (standalone mode)")
else:
    print("✓ Using provided document (backend mode)")

# Load parameters from input.json
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "input.json")

with open(input_file, 'r') as f:
    params = json.load(f)

u = params['u']  # 18 mm
keyHeight = params['keyHeight']  # 5 mm (not used with STL)
keySpacing = params['keySpacing']  # 2 mm
keyCount = params['keyCount']  # 9

print(f"Parameters: u={u}mm, keySpacing={keySpacing}mm, keyCount={keyCount}")

# Load STL files
keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")
switch_stl = os.path.join(script_dir, "kailhlowprofilev102.stl")

print("Loading STL files...")
# Load as mesh first to convert to solid
keycap_mesh = Mesh.Mesh(keycap_stl)
switch_mesh = Mesh.Mesh(switch_stl)

# Convert mesh to solid shape
keycap_shape = Part.Shape()
keycap_shape.makeShapeFromMesh(keycap_mesh.Topology, 0.1)
# Try to create solid, fall back to shell if it fails
try:
    keycap_solid = Part.makeSolid(keycap_shape)
    print("✓ Keycap converted to solid")
except:
    keycap_solid = keycap_shape
    print("✓ Keycap loaded as shell (not solid)")

switch_shape = Part.Shape()
switch_shape.makeShapeFromMesh(switch_mesh.Topology, 0.1)
# Try to create solid, fall back to shell if it fails
try:
    switch_solid = Part.makeSolid(switch_shape)
    print("✓ Switch converted to solid")
except:
    switch_solid = switch_shape
    print("✓ Switch loaded as shell (not solid)")

print(f"✓ Loaded keycap STL: {keycap_stl}")
print(f"✓ Loaded switch STL: {switch_stl}")

# Get bounding boxes to understand dimensions
keycap_bbox = keycap_solid.BoundBox
switch_bbox = switch_solid.BoundBox

print(f"Keycap bounds: X({keycap_bbox.XMin:.2f}, {keycap_bbox.XMax:.2f}), "
      f"Y({keycap_bbox.YMin:.2f}, {keycap_bbox.YMax:.2f}), "
      f"Z({keycap_bbox.ZMin:.2f}, {keycap_bbox.ZMax:.2f})")
print(f"Switch bounds: X({switch_bbox.XMin:.2f}, {switch_bbox.XMax:.2f}), "
      f"Y({switch_bbox.YMin:.2f}, {switch_bbox.YMax:.2f}), "
      f"Z({switch_bbox.ZMin:.2f}, {switch_bbox.ZMax:.2f})")

# Calculate offsets to position models correctly via Placement
# Using ENGINEERING coordinates (Z-up):
#   X: horizontal (left-right)
#   Y: horizontal (row direction - keys spaced along Y)
#   Z: vertical (height - keycap top at Z=0, switch below)

# Keycap: center in X/Y, top at Z=0
keycap_x_offset = -(keycap_bbox.XMin + keycap_bbox.XMax) / 2
keycap_y_offset = -(keycap_bbox.YMin + keycap_bbox.YMax) / 2
keycap_z_offset = -keycap_bbox.ZMax  # Put top at Z=0

# Switch: use SAME X/Y centering as keycap so they align, top at Z=-25
# We want switch centered at same X/Y world position as keycap
switch_x_offset = -(switch_bbox.XMin + switch_bbox.XMax) / 2
switch_y_offset = -(switch_bbox.YMin + switch_bbox.YMax) / 2
switch_z_offset = -25 - switch_bbox.ZMax  # Put top at Z=-25

print(f"Keycap offset (engineering X,Y,Z): ({keycap_x_offset:.2f}, {keycap_y_offset:.2f}, {keycap_z_offset:.2f})")
print(f"Switch offset (engineering X,Y,Z): ({switch_x_offset:.2f}, {switch_y_offset:.2f}, {switch_z_offset:.2f})")

# Create instances with Placements for GPU instancing
# Use original shapes - transforms go in Placement for assembly.json
# Engineering coords: X=left-right, Y=row direction, Z=height
print(f"Creating {keyCount} keycap and switch instances...")
for i in range(keyCount):
    # Calculate Y position for this instance (along the row)
    y_pos = i * (u + keySpacing)

    # Add keycap with the original shape
    keycap_obj = doc.addObject("Part::Feature", f"Keycap_{i+1}")
    keycap_obj.Shape = keycap_solid

    # Position using Placement (X=center, Y=row position, Z=height)
    keycap_obj.Placement = FreeCAD.Placement(
        FreeCAD.Vector(keycap_x_offset, keycap_y_offset + y_pos, keycap_z_offset),
        FreeCAD.Rotation(0, 0, 0)
    )

    # Add switch with the original shape
    switch_obj = doc.addObject("Part::Feature", f"Switch_{i+1}")
    switch_obj.Shape = switch_solid

    # Position using Placement (X=center, Y=row position, Z=height)
    switch_obj.Placement = FreeCAD.Placement(
        FreeCAD.Vector(switch_x_offset, switch_y_offset + y_pos, switch_z_offset),
        FreeCAD.Rotation(0, 0, 0)
    )

    print(f"✓ Keycap at ({keycap_x_offset:.1f}, {keycap_y_offset + y_pos:.1f}, {keycap_z_offset:.1f})")
    print(f"✓ Switch at ({switch_x_offset:.1f}, {switch_y_offset + y_pos:.1f}, {switch_z_offset:.1f})")

# Add axis indicators for debugging coordinate system
# X axis: Red box extending in +X direction
# Y axis: Green box extending in +Y direction (should be UP in Three.js)
# Z axis: Blue box extending in +Z direction
axis_length = 50
axis_thickness = 2

# X axis indicator (red) - horizontal
x_axis = Part.makeBox(axis_length, axis_thickness, axis_thickness)
x_axis_obj = doc.addObject("Part::Feature", "Axis_X_Red")
x_axis_obj.Shape = x_axis
x_axis_obj.Placement = FreeCAD.Placement(
    FreeCAD.Vector(0, 0, 0),
    FreeCAD.Rotation(0, 0, 0)
)

# Y axis indicator (green) - should be vertical/UP in Three.js
y_axis = Part.makeBox(axis_thickness, axis_length, axis_thickness)
y_axis_obj = doc.addObject("Part::Feature", "Axis_Y_Green")
y_axis_obj.Shape = y_axis
y_axis_obj.Placement = FreeCAD.Placement(
    FreeCAD.Vector(0, 0, 0),
    FreeCAD.Rotation(0, 0, 0)
)

# Z axis indicator (blue) - depth in Three.js
z_axis = Part.makeBox(axis_thickness, axis_thickness, axis_length)
z_axis_obj = doc.addObject("Part::Feature", "Axis_Z_Blue")
z_axis_obj.Shape = z_axis
z_axis_obj.Placement = FreeCAD.Placement(
    FreeCAD.Vector(0, 0, 0),
    FreeCAD.Rotation(0, 0, 0)
)

print("✓ Added axis indicators: X(red), Y(green/UP), Z(blue)")

# Recompute
doc.recompute()
print("✓ Document recomputed")

print(f"✓ Keyboard generated successfully with {len(doc.Objects)} object(s)")
print("SUCCESS: Model generation complete")
