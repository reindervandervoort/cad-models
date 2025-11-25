#!/usr/bin/env python3
"""
Keyboard Model - Test keycap STL at its natural position
No transforms applied - just load and display the STL as-is
"""

import FreeCAD
import Part
import Mesh
import os

print("=== TEST: Keycap STL with no transforms ===")

# If running standalone (not from backend), create doc
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Keyboard")
    print("Created new document (standalone mode)")
else:
    print("Using provided document (backend mode)")

# Load keycap STL
script_dir = os.path.dirname(os.path.abspath(__file__))
keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")

print(f"Loading: {keycap_stl}")
keycap_mesh = Mesh.Mesh(keycap_stl)
keycap_shape = Part.Shape()
keycap_shape.makeShapeFromMesh(keycap_mesh.Topology, 0.1)

# Create object with NO transforms
keycap_obj = doc.addObject("Part::Feature", "Keycap")
keycap_obj.Shape = keycap_shape

bbox = keycap_shape.BoundBox
print(f"\nKeycap bounding box:")
print(f"  X: [{bbox.XMin:.2f}, {bbox.XMax:.2f}] - width: {bbox.XLength:.2f}mm")
print(f"  Y: [{bbox.YMin:.2f}, {bbox.YMax:.2f}] - depth: {bbox.YLength:.2f}mm")
print(f"  Z: [{bbox.ZMin:.2f}, {bbox.ZMax:.2f}] - height: {bbox.ZLength:.2f}mm")
print(f"  Center: ({(bbox.XMin+bbox.XMax)/2:.2f}, {(bbox.YMin+bbox.YMax)/2:.2f}, {(bbox.ZMin+bbox.ZMax)/2:.2f})")
print(f"\nPlacement: {keycap_obj.Placement}")
print(f"Shape valid: {keycap_obj.Shape.isValid()}")
print(f"Vertices: {len(keycap_obj.Shape.Vertexes)}, Faces: {len(keycap_obj.Shape.Faces)}")

doc.recompute()
print(f"\nSUCCESS: Model generation complete with {len(doc.Objects)} object(s)")
