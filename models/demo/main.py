#!/usr/bin/env python3
"""
Simple Demo Model - Creates a basic cube
Backend provides 'doc' variable - we add objects to it
"""

import FreeCAD
import Part

# Backend provides 'doc' variable via exec()
# Don't create a new document - use the one provided!

print("Starting demo model generation...")
print(f"Using document: {doc.Name if 'doc' in dir() else 'Creating new for standalone'}")

# If running standalone (not from backend), create doc
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Demo")
    print("✓ Created new document (standalone mode)")
else:
    print("✓ Using provided document (backend mode)")

# Create a cube (100x100x100 mm)
cube_shape = Part.makeBox(100, 100, 100)
print("✓ Cube shape created")

# Add cube to the document
cube_obj = doc.addObject("Part::Feature", "DemoCube")
cube_obj.Shape = cube_shape
print("✓ Cube object added to document")

# Recompute to ensure everything is updated
doc.recompute()
print("✓ Document recomputed")

print(f"✓ Demo model completed with {len(doc.Objects)} object(s)")
print("SUCCESS: Model generation complete")
