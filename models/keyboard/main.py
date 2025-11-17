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

# Create a single key box
def create_key(position_y):
    """Create a single key centered in x, at given y position, flush with z=0 plane"""
    # Center in x direction means x starts at -u/2
    box = Part.makeBox(u, u, keyHeight, FreeCAD.Vector(-u/2, position_y, 0))
    return box

# Create all keys in a row along y axis
print(f"Creating {keyCount} keys...")
for i in range(keyCount):
    # Calculate y position: spacing between keys
    y_pos = i * (u + keySpacing)

    # Create key
    key_shape = create_key(y_pos)

    # Add to document
    obj = doc.addObject("Part::Feature", f"Key_{i+1}")
    obj.Shape = key_shape
    print(f"✓ Key {i+1} created at y={y_pos}mm")

# Recompute
doc.recompute()
print("✓ Document recomputed")

print(f"✓ Keyboard generated successfully with {len(doc.Objects)} object(s)")
print("SUCCESS: Model generation complete")
