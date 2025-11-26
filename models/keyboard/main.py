#!/usr/bin/env python3
"""
Simple Keyboard Alignment - BAKED TRANSFORMS
Aligns keycap and switch STL files:
- Keycap: top center at origin (0, 0, 0)
- Switch: centered at z = -0.75mm below origin

IMPORTANT: Transforms are BAKED into the geometry, not set as Placement.
The backend exports obj.Shape which includes any Placement transforms,
causing double transformation. So we transform the geometry directly.
"""

import FreeCAD
import Part
import Mesh
import os

print("Starting fresh keyboard alignment...")

# If running standalone (not from backend), create doc
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Keyboard")
    print("Created new document (standalone mode)")
else:
    print("Using provided document (backend mode)")

# =============================================================================
# LOAD STL FILES
# =============================================================================

script_dir = os.path.dirname(os.path.abspath(__file__))
keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")
switch_stl = os.path.join(script_dir, "kailhlowprofilev102.stl")

print("\n=== Loading STL files ===")

# Load keycap mesh
keycap_mesh = Mesh.Mesh(keycap_stl)
keycap_shape = Part.Shape()
keycap_shape.makeShapeFromMesh(keycap_mesh.Topology, 0.1)
try:
    keycap_solid = Part.makeSolid(keycap_shape)
    print("Keycap converted to solid")
except Exception:
    keycap_solid = keycap_shape
    print("Keycap loaded as shell")

# Load switch mesh
switch_mesh = Mesh.Mesh(switch_stl)
switch_shape = Part.Shape()
switch_shape.makeShapeFromMesh(switch_mesh.Topology, 0.1)
try:
    switch_solid = Part.makeSolid(switch_shape)
    print("Switch converted to solid")
except Exception:
    switch_solid = switch_shape
    print("Switch loaded as shell")

# Get bounding boxes
keycap_bbox = keycap_solid.BoundBox
switch_bbox = switch_solid.BoundBox

print(f"\n=== Original Bounding Boxes ===")
print(f"Keycap: X({keycap_bbox.XMin:.2f} to {keycap_bbox.XMax:.2f}), "
      f"Y({keycap_bbox.YMin:.2f} to {keycap_bbox.YMax:.2f}), "
      f"Z({keycap_bbox.ZMin:.2f} to {keycap_bbox.ZMax:.2f})")

print(f"Switch: X({switch_bbox.XMin:.2f} to {switch_bbox.XMax:.2f}), "
      f"Y({switch_bbox.YMin:.2f} to {switch_bbox.YMax:.2f}), "
      f"Z({switch_bbox.ZMin:.2f} to {switch_bbox.ZMax:.2f})")

# =============================================================================
# TRANSFORM GEOMETRY DIRECTLY (BAKE TRANSFORMS)
# =============================================================================

print(f"\n=== Baking Transforms into Geometry ===")

# KEYCAP: Transform so top center is at origin (0, 0, 0)
keycap_center_x = (keycap_bbox.XMin + keycap_bbox.XMax) / 2
keycap_center_y = (keycap_bbox.YMin + keycap_bbox.YMax) / 2
keycap_top_z = keycap_bbox.ZMax

keycap_transform = FreeCAD.Vector(
    -keycap_center_x,  # Center X
    -keycap_center_y,  # Center Y
    -keycap_top_z       # Top at Z=0
)

print(f"Keycap transform: ({keycap_transform.x:.2f}, {keycap_transform.y:.2f}, {keycap_transform.z:.2f})")

# Apply transform to keycap geometry
keycap_transformed = keycap_solid.copy()
keycap_transformed.translate(keycap_transform)

# SWITCH: Transform so center is at z = -0.75mm
switch_center_x = (switch_bbox.XMin + switch_bbox.XMax) / 2
switch_center_y = (switch_bbox.YMin + switch_bbox.YMax) / 2
switch_center_z = (switch_bbox.ZMin + switch_bbox.ZMax) / 2
switch_target_z = -0.75

switch_transform = FreeCAD.Vector(
    -switch_center_x,
    -switch_center_y,
    switch_target_z - switch_center_z
)

print(f"Switch transform: ({switch_transform.x:.2f}, {switch_transform.y:.2f}, {switch_transform.z:.2f})")

# Apply transform to switch geometry
switch_transformed = switch_solid.copy()
switch_transformed.translate(switch_transform)

# =============================================================================
# CREATE OBJECTS WITH TRANSFORMED GEOMETRY (NO PLACEMENT)
# =============================================================================

print(f"\n=== Creating Objects (transforms baked into geometry) ===")

# Create keycap object with transformed geometry, NO Placement
keycap_obj = doc.addObject("Part::Feature", "Keycap")
keycap_obj.Shape = keycap_transformed
# Placement left at default (identity) - geometry already positioned

# Create switch object with transformed geometry, NO Placement
switch_obj = doc.addObject("Part::Feature", "Switch")
switch_obj.Shape = switch_transformed
# Placement left at default (identity) - geometry already positioned

doc.recompute()

# =============================================================================
# VERIFY ALIGNMENT
# =============================================================================

print(f"\n=== Verifying Alignment ===")

keycap_final_bbox = keycap_obj.Shape.BoundBox
switch_final_bbox = switch_obj.Shape.BoundBox

print(f"Keycap final bbox:")
print(f"  X: {keycap_final_bbox.XMin:.2f} to {keycap_final_bbox.XMax:.2f} (center: {(keycap_final_bbox.XMin + keycap_final_bbox.XMax)/2:.2f})")
print(f"  Y: {keycap_final_bbox.YMin:.2f} to {keycap_final_bbox.YMax:.2f} (center: {(keycap_final_bbox.YMin + keycap_final_bbox.YMax)/2:.2f})")
print(f"  Z: {keycap_final_bbox.ZMin:.2f} to {keycap_final_bbox.ZMax:.2f} (top: {keycap_final_bbox.ZMax:.2f})")

print(f"\nSwitch final bbox:")
print(f"  X: {switch_final_bbox.XMin:.2f} to {switch_final_bbox.XMax:.2f} (center: {(switch_final_bbox.XMin + switch_final_bbox.XMax)/2:.2f})")
print(f"  Y: {switch_final_bbox.YMin:.2f} to {switch_final_bbox.YMax:.2f} (center: {(switch_final_bbox.YMin + switch_final_bbox.YMax)/2:.2f})")
print(f"  Z: {switch_final_bbox.ZMin:.2f} to {switch_final_bbox.ZMax:.2f} (center: {(switch_final_bbox.ZMin + switch_final_bbox.ZMax)/2:.2f})")

print(f"\n=== Alignment Check ===")
keycap_top_center = (
    (keycap_final_bbox.XMin + keycap_final_bbox.XMax) / 2,
    (keycap_final_bbox.YMin + keycap_final_bbox.YMax) / 2,
    keycap_final_bbox.ZMax
)
switch_center = (
    (switch_final_bbox.XMin + switch_final_bbox.XMax) / 2,
    (switch_final_bbox.YMin + switch_final_bbox.YMax) / 2,
    (switch_final_bbox.ZMin + switch_final_bbox.ZMax) / 2
)

print(f"Keycap top center: ({keycap_top_center[0]:.3f}, {keycap_top_center[1]:.3f}, {keycap_top_center[2]:.3f})")
print(f"  Target: (0.000, 0.000, 0.000)")
print(f"  Deviation: ({abs(keycap_top_center[0]):.3f}, {abs(keycap_top_center[1]):.3f}, {abs(keycap_top_center[2]):.3f})")

print(f"\nSwitch center: ({switch_center[0]:.3f}, {switch_center[1]:.3f}, {switch_center[2]:.3f})")
print(f"  Target: (0.000, 0.000, -0.750)")
print(f"  Deviation: ({abs(switch_center[0]):.3f}, {abs(switch_center[1]):.3f}, {abs(switch_center[2] + 0.75):.3f})")

print(f"\nSUCCESS: Alignment complete!")
print(f"Total objects: {len(doc.Objects)}")
