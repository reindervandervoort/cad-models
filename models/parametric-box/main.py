#!/usr/bin/env python3
"""
Parametric Box Model
A hollow box with configurable dimensions and wall thickness
Backend provides 'doc' variable - we add objects to it
"""

import FreeCAD
import Part

print("Starting parametric box generation...")
print(f"Using document: {doc.Name if 'doc' in dir() else 'Creating new for standalone'}")

# If running standalone (not from backend), create doc
if 'doc' not in dir():
    doc = FreeCAD.newDocument("ParametricBox")
    print("✓ Created new document (standalone mode)")
else:
    print("✓ Using provided document (backend mode)")

# Parameters (can be customized)
length = 150  # mm
width = 100   # mm
height = 50   # mm
wall = 3      # mm wall thickness

print(f"Parameters: {length}x{width}x{height}mm, wall={wall}mm")

# Create outer box
outer = Part.makeBox(length, width, height)
print("✓ Outer box created")

# Create inner cavity
inner = Part.makeBox(
    length - 2*wall,
    width - 2*wall,
    height - wall,
    FreeCAD.Vector(wall, wall, wall)
)
print("✓ Inner cavity created")

# Subtract inner from outer to create hollow box
hollow_box = outer.cut(inner)
print("✓ Hollow box created")

# Add to document
obj = doc.addObject("Part::Feature", "HollowBox")
obj.Shape = hollow_box
print("✓ Box added to document")

# Recompute
doc.recompute()
print("✓ Document recomputed")

print(f"✓ Parametric box generated successfully with {len(doc.Objects)} object(s)")
print("SUCCESS: Model generation complete")
