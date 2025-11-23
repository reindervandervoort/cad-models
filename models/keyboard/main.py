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
import math

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
keyHeight = params['keyHeight']  # 6 mm (not used with STL)
keyCount = params['keyCount']  # 10
switchOffset = params.get('switchOffset', 0.5)  # mm below keycap
pitch = params['pitch']  # 45 degrees
handDiameter = params['handDiameter']  # 192 mm
horizontalSpace = params['horizontalSpace']  # 2 mm gap at key surface

# Ring radius and axis height
ringRadius = handDiameter / 2  # 96 mm
ringAxisZ = ringRadius  # Axis is at Z = 96mm (above origin)

# Calculate the angle between keys based on horizontalSpace at the key surface
# Arc length = u + horizontalSpace, so angle = arc_length / radius
arcLengthPerKey = u + horizontalSpace
angleBetweenKeys = arcLengthPerKey / ringRadius  # in radians

print(f"Parameters: u={u}mm, keyCount={keyCount}, switchOffset={switchOffset}mm")
print(f"Pitch: {pitch}°, handDiameter={handDiameter}mm, horizontalSpace={horizontalSpace}mm")
print(f"Ring radius: {ringRadius}mm, angle between keys: {math.degrees(angleBetweenKeys):.2f}°")

# Load STL files ONCE
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

# Position geometry for proper stacking and rotation:
# - XY centered at origin (for rotation around key center)
# - Keycap: bottom at Z=0 (extends upward) - this is the mounting point
# - Switch: top at Z=-switchOffset (extends downward with gap)
# This creates a natural pivot point at the keycap-switch interface

keycap_center_x = (keycap_bbox.XMin + keycap_bbox.XMax) / 2
keycap_center_y = (keycap_bbox.YMin + keycap_bbox.YMax) / 2
keycap_bottom_z = keycap_bbox.ZMin  # Bottom of keycap

switch_center_x = (switch_bbox.XMin + switch_bbox.XMax) / 2
switch_center_y = (switch_bbox.YMin + switch_bbox.YMax) / 2
switch_top_z = switch_bbox.ZMax  # Top of switch

print(f"Keycap original bounds: Z({keycap_bbox.ZMin:.2f} to {keycap_bbox.ZMax:.2f})")
print(f"Switch original bounds: Z({switch_bbox.ZMin:.2f} to {switch_bbox.ZMax:.2f})")

# Translate keycap: XY centered, bottom at Z=0
keycap_solid = keycap_solid.translated(FreeCAD.Vector(
    -keycap_center_x,
    -keycap_center_y,
    -keycap_bottom_z  # Move bottom to Z=0
))

# Translate switch: XY centered, top at Z=-switchOffset
switch_solid = switch_solid.translated(FreeCAD.Vector(
    -switch_center_x,
    -switch_center_y,
    -switch_top_z - switchOffset  # Move top to Z=-switchOffset
))

# Verify positioning
keycap_bbox_new = keycap_solid.BoundBox
switch_bbox_new = switch_solid.BoundBox
print(f"Keycap positioned: Z({keycap_bbox_new.ZMin:.2f} to {keycap_bbox_new.ZMax:.2f}) - bottom at 0")
print(f"Switch positioned: Z({switch_bbox_new.ZMin:.2f} to {switch_bbox_new.ZMax:.2f}) - top at {-switchOffset}")
print(f"Vertical gap between keycap bottom and switch top: {switchOffset}mm")

# Calculate the total angular span and center it
totalAngle = (keyCount - 1) * angleBetweenKeys
startAngle = -totalAngle / 2  # Center the keys around the bottom of the ring

# Create base geometry objects ONCE - these define the canonical shape
# All instances will reference these same shapes (backend detects via shape hash)
# The geometry is pre-positioned: keycap bottom at Z=0, switch top at Z=-switchOffset
keycap_base = doc.addObject("Part::Feature", "Keycap_Base")
keycap_base.Shape = keycap_solid

switch_base = doc.addObject("Part::Feature", "Switch_Base")
switch_base.Shape = switch_solid

# Create instances with pitch and ring arrangement
# Each instance references the same base shape - backend will detect via shape hash
print(f"Creating {keyCount} keycap and switch instances...")
for i in range(keyCount):
    # Calculate roll angle for this key (position on the ring)
    rollAngle = startAngle + i * angleBetweenKeys  # angle from bottom of ring

    # Calculate Y and Z position on the ring
    # Angle measured from -Z direction (bottom of ring), positive = counterclockwise from +X view
    # At rollAngle=0, key is at the bottom (Y=0, Z=0 relative to ring center)
    y_pos = ringRadius * math.sin(rollAngle)
    z_pos = ringAxisZ - ringRadius * math.cos(rollAngle)

    # Create rotation combining pitch and roll
    # Pitch: rotation around Y axis (top tilts back)
    # Roll: rotation around X axis (orient tangent to ring)
    pitchRotation = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), pitch)
    rollRotation = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), math.degrees(rollAngle))
    combinedRotation = rollRotation.multiply(pitchRotation)

    # Ring position in world coordinates
    ring_position = FreeCAD.Vector(0, y_pos, z_pos)

    if i == 0:
        # First instance - rename and use the base objects
        keycap_base.Label = "Keycap_1"
        switch_base.Label = "Switch_1"
        keycap_obj = keycap_base
        switch_obj = switch_base
    else:
        # Additional instances - create new objects referencing the same shape
        keycap_obj = doc.addObject("Part::Feature", f"Keycap_{i+1}")
        keycap_obj.Shape = keycap_base.Shape

        switch_obj = doc.addObject("Part::Feature", f"Switch_{i+1}")
        switch_obj.Shape = switch_base.Shape

    # Apply Placement: rotation around origin (geometry pre-positioned for stacking)
    keycap_obj.Placement = FreeCAD.Placement(ring_position, combinedRotation)
    switch_obj.Placement = FreeCAD.Placement(ring_position, combinedRotation)

    rollDeg = math.degrees(rollAngle)
    print(f"✓ Key {i+1} at roll={rollDeg:.1f}°, y={y_pos:.1f}mm, z={z_pos:.1f}mm")

# Recompute
doc.recompute()
print("✓ Document recomputed")

print(f"✓ Keyboard generated successfully with {len(doc.Objects)} object(s)")
print(f"SUCCESS: Keyboard model complete - {keyCount} keys generated")
