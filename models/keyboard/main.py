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

u = params['u']  # 18 mm
keyHeight = params['keyHeight']  # 5 mm
keySpacing = params['keySpacing']  # 2 mm
keyCount = params['keyCount']  # 9

print(f"Parameters: u={u}mm, keyHeight={keyHeight}mm, keySpacing={keySpacing}mm, keyCount={keyCount}")

# Create ONE keycap shape at origin (centered in X, flush with Z=0)
# This single shape will be instanced 9 times with different Placements
keycap_shape = Part.makeBox(u, u, keyHeight, FreeCAD.Vector(-u/2, 0, 0))
print(f"✓ Created base keycap shape: {u}mm × {u}mm × {keyHeight}mm")

# Add the same shape to document 9 times with different Placements
# This enables GPU instancing because all objects have identical geometry
print(f"Creating {keyCount} keycap instances...")
for i in range(keyCount):
    # Calculate Y position for this instance
    y_pos = i * (u + keySpacing)

    # Add object with the SAME shape
    obj = doc.addObject("Part::Feature", "Keycap")
    obj.Shape = keycap_shape

    # Position it using Placement (not baked into geometry)
    obj.Placement = FreeCAD.Placement(
        FreeCAD.Vector(0, y_pos, 0),  # Position
        FreeCAD.Rotation(0, 0, 0)      # Rotation (none)
    )

    print(f"✓ Keycap instance {i+1} placed at y={y_pos}mm")

# Recompute
doc.recompute()
print("✓ Document recomputed")

print(f"✓ Keyboard generated successfully with {len(doc.Objects)} object(s)")
print("SUCCESS: Model generation complete")
