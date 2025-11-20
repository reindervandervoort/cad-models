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

print("Starting keyboard generation...")
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

# Position keycap so its TOP is at Z=0
# This means we need to translate it down by its max Z value
keycap_base = keycap_solid.copy()
keycap_base.translate(FreeCAD.Vector(0, 0, -keycap_bbox.ZMax))

# Position switch 25mm below the keycap top (which is now at Z=0)
switch_base = switch_solid.copy()
switch_base.translate(FreeCAD.Vector(0, 0, -25 - switch_bbox.ZMax))

# Center both in X and Y
keycap_x_offset = -(keycap_bbox.XMin + keycap_bbox.XMax) / 2
keycap_y_offset = -(keycap_bbox.YMin + keycap_bbox.YMax) / 2
keycap_base.translate(FreeCAD.Vector(keycap_x_offset, keycap_y_offset, 0))

switch_x_offset = -(switch_bbox.XMin + switch_bbox.XMax) / 2
switch_y_offset = -(switch_bbox.YMin + switch_bbox.YMax) / 2
switch_base.translate(FreeCAD.Vector(switch_x_offset, switch_y_offset, 0))

print("✓ Positioned keycap with top at Z=0")
print("✓ Positioned switch 25mm below keycap")

# Create instances with Placements for GPU instancing
print(f"Creating {keyCount} keycap and switch instances...")
for i in range(keyCount):
    # Calculate Y position for this instance
    y_pos = i * (u + keySpacing)

    # Add keycap with the SAME shape
    keycap_obj = doc.addObject("Part::Feature", f"Keycap_{i+1}")
    keycap_obj.Shape = keycap_base

    # Position using Placement
    keycap_obj.Placement = FreeCAD.Placement(
        FreeCAD.Vector(0, y_pos, 0),
        FreeCAD.Rotation(0, 0, 0)
    )

    # Add switch with the SAME shape
    switch_obj = doc.addObject("Part::Feature", f"Switch_{i+1}")
    switch_obj.Shape = switch_base

    # Position using Placement (same as keycap)
    switch_obj.Placement = FreeCAD.Placement(
        FreeCAD.Vector(0, y_pos, 0),
        FreeCAD.Rotation(0, 0, 0)
    )

    print(f"✓ Keycap and switch instance {i+1} placed at y={y_pos}mm")

# Recompute
doc.recompute()
print("✓ Document recomputed")

print(f"✓ Keyboard generated successfully with {len(doc.Objects)} object(s)")
print("SUCCESS: Model generation complete")
