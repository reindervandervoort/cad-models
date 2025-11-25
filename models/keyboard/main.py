#!/usr/bin/env python3
"""
Keyboard Model - MINIMAL TEST
Testing if basic geometry export works at all
"""

import FreeCAD
import Part

print("=== MINIMAL TEST: Simple box at origin ===")

# If running standalone (not from backend), create doc
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Keyboard")
    print("Created new document (standalone mode)")
else:
    print("Using provided document (backend mode)")

# Create a simple 10mm cube at the origin
box = Part.makeBox(10, 10, 10, FreeCAD.Vector(-5, -5, -5))
box_obj = doc.addObject("Part::Feature", "TestBox")
box_obj.Shape = box

print(f"Created box: {box_obj.Label}")
print(f"  Shape valid: {box_obj.Shape.isValid()}")
print(f"  BoundBox: X[{box_obj.Shape.BoundBox.XMin:.1f}, {box_obj.Shape.BoundBox.XMax:.1f}], "
      f"Y[{box_obj.Shape.BoundBox.YMin:.1f}, {box_obj.Shape.BoundBox.YMax:.1f}], "
      f"Z[{box_obj.Shape.BoundBox.ZMin:.1f}, {box_obj.Shape.BoundBox.ZMax:.1f}]")
print(f"  Placement: {box_obj.Placement}")

doc.recompute()
print(f"\nTotal objects: {len(doc.Objects)}")
print("SUCCESS: Model generation complete")
