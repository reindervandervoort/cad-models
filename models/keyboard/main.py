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
#
# IMPORTANT: Backend does NOT center X/Y in exported STL - geometry stays at
# native position. But Placement values go into assembly.json and frontend
# adds them to STL geometry. So we must include X/Y centering offsets to
# ensure keycap and switch end up at same world X/Y position.

# Keycap offsets: center X/Y, put top at Z=0
keycap_x_center = (keycap_bbox.XMin + keycap_bbox.XMax) / 2
keycap_y_center = (keycap_bbox.YMin + keycap_bbox.YMax) / 2
keycap_x_offset = -keycap_x_center  # Cancel out native X position
keycap_y_offset = -keycap_y_center  # Cancel out native Y position
keycap_z_height = keycap_bbox.ZMax - keycap_bbox.ZMin
keycap_z_offset = -keycap_z_height / 2  # After Z centering, move down by half height

# Switch offsets: center X/Y, put top at Z=0 (same as keycap - overlapping)
switch_x_center = (switch_bbox.XMin + switch_bbox.XMax) / 2
switch_y_center = (switch_bbox.YMin + switch_bbox.YMax) / 2
switch_x_offset = -switch_x_center  # Cancel out native X position (should be ~0)
switch_y_offset = -switch_y_center  # Cancel out native Y position (should be ~0)
switch_z_height = switch_bbox.ZMax - switch_bbox.ZMin
switch_z_offset = -switch_z_height / 2  # After Z centering, top at Z=0 (overlapping with keycap)

print(f"Keycap center: ({keycap_x_center:.2f}, {keycap_y_center:.2f}), Z height: {keycap_z_height:.2f}")
print(f"Keycap offsets: X={keycap_x_offset:.2f}, Y={keycap_y_offset:.2f}, Z={keycap_z_offset:.2f}")
print(f"Switch center: ({switch_x_center:.2f}, {switch_y_center:.2f}), Z height: {switch_z_height:.2f}")
print(f"Switch offsets: X={switch_x_offset:.2f}, Y={switch_y_offset:.2f}, Z={switch_z_offset:.2f}")

# Create instances with Placements for GPU instancing
# Placement values go into assembly.json; frontend adds them to STL geometry
# Engineering coords: X=left-right, Y=row direction, Z=height
print(f"Creating {keyCount} keycap and switch instances...")
for i in range(keyCount):
    # Calculate Y position for this instance (along the row)
    y_pos = i * (u + keySpacing)

    # Add keycap with the original shape
    keycap_obj = doc.addObject("Part::Feature", f"Keycap_{i+1}")
    keycap_obj.Shape = keycap_solid

    # Position using Placement - include X/Y centering offsets
    # Final world position = STL_geometry + Placement = centered at (0, y_pos)
    keycap_obj.Placement = FreeCAD.Placement(
        FreeCAD.Vector(keycap_x_offset, keycap_y_offset + y_pos, keycap_z_offset),
        FreeCAD.Rotation(0, 0, 0)
    )

    # Add switch with the original shape
    switch_obj = doc.addObject("Part::Feature", f"Switch_{i+1}")
    switch_obj.Shape = switch_solid

    # Position using Placement - include X/Y centering offsets
    # Final world position = STL_geometry + Placement = centered at (0, y_pos)
    switch_obj.Placement = FreeCAD.Placement(
        FreeCAD.Vector(switch_x_offset, switch_y_offset + y_pos, switch_z_offset),
        FreeCAD.Rotation(0, 0, 0)
    )

    print(f"Keycap {i+1} at ({keycap_x_offset:.1f}, {keycap_y_offset + y_pos:.1f}, {keycap_z_offset:.1f})")
    print(f"Switch {i+1} at ({switch_x_offset:.1f}, {switch_y_offset + y_pos:.1f}, {switch_z_offset:.1f})")

# Recompute
doc.recompute()
print("✓ Document recomputed")

print(f"✓ Keyboard generated successfully with {len(doc.Objects)} object(s)")
print("SUCCESS: Model generation complete")
