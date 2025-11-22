#!/usr/bin/env python3
"""
Keyboard Model
Creates a row of keycaps with parametric dimensions
Backend provides 'doc' variable - we add objects to it
"""

import FreeCAD
import Part
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

import math

u = params['u']  # 18 mm
keyHeight = params['keyHeight']  # 6 mm
keyCount = params['keyCount']  # 9
pitch = params['pitch']  # 45 degrees
handDiameter = params['handDiameter']  # 192 mm
horizontalSpace = params['horizontalSpace']  # 2 mm gap at key surface

# Ring radius and axis height
ringRadius = handDiameter / 2  # 96 mm
ringAxisZ = ringRadius  # Axis is at Z = 96mm (above origin)

# Calculate the angle between keys based on horizontalSpace at the key surface
# After pitch, the effective key width at the surface is u (top face width)
# Arc length = u + horizontalSpace, so angle = arc_length / radius
arcLengthPerKey = u + horizontalSpace
angleBetweenKeys = arcLengthPerKey / ringRadius  # in radians

print(f"Parameters: u={u}mm, keyHeight={keyHeight}mm, keyCount={keyCount}")
print(f"Pitch: {pitch}°, handDiameter={handDiameter}mm, horizontalSpace={horizontalSpace}mm")
print(f"Ring radius: {ringRadius}mm, angle between keys: {math.degrees(angleBetweenKeys):.2f}°")

# Create a single key box at origin, centered in X and Y
def create_key_at_origin():
    """Create a single key centered in X and Y, with base at Z=0"""
    box = Part.makeBox(u, u, keyHeight, FreeCAD.Vector(-u/2, -u/2, 0))
    return box

# Create all keys arranged on a ring
print(f"Creating {keyCount} keys...")

# Calculate the total angular span and center it
totalAngle = (keyCount - 1) * angleBetweenKeys
startAngle = -totalAngle / 2  # Center the keys around the bottom of the ring

for i in range(keyCount):
    # Create key at origin
    key_shape = create_key_at_origin()

    # Step 1: Apply pitch rotation (around Y axis, top tilts back)
    pitchRad = math.radians(pitch)
    pitchRotation = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), pitch)
    key_shape = key_shape.transformGeometry(
        FreeCAD.Matrix(pitchRotation.toMatrix())
    )

    # Step 2: Position on the ring
    # The ring axis is parallel to X at Z = ringAxisZ
    # Keys are positioned around this axis, centered at the bottom
    rollAngle = startAngle + i * angleBetweenKeys  # angle from bottom of ring

    # Position: key sits on the ring surface at given angle
    # Angle measured from -Z direction (bottom of ring), going positive = counterclockwise when viewed from +X
    # At rollAngle=0, key is at the bottom (Y=0, Z=0 relative to ring center)
    y_pos = ringRadius * math.sin(rollAngle)
    z_pos = ringAxisZ - ringRadius * math.cos(rollAngle)

    # Apply roll rotation (around X axis) to orient key tangent to ring
    rollRotation = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), math.degrees(rollAngle))
    key_shape = key_shape.transformGeometry(
        FreeCAD.Matrix(rollRotation.toMatrix())
    )

    # Translate to final position
    key_shape.translate(FreeCAD.Vector(0, y_pos, z_pos))

    # Add to document
    obj = doc.addObject("Part::Feature", f"Key_{i+1}")
    obj.Shape = key_shape
    rollDeg = math.degrees(rollAngle)
    print(f"✓ Key {i+1} created at roll={rollDeg:.1f}°, y={y_pos:.1f}mm, z={z_pos:.1f}mm")

# Recompute
doc.recompute()
print("✓ Document recomputed")

print(f"✓ Keyboard generated successfully with {len(doc.Objects)} object(s)")
print("SUCCESS: Model generation complete")
