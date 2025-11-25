#!/usr/bin/env python3
"""
Keyboard Model - SIMPLIFIED TEST CASE
Single keycap + switch pair at 45° pitch
Top center of keycap positioned at origin (0,0,0)

IMPORTANT: Transform Handling
=============================
All transformations must be COLLAPSED into a single 4x4 matrix before being
converted to a FreeCAD Placement. The backend exports each object's Placement
to assembly.json, which the Three.js frontend then applies to the loaded STL.

The STL geometry is NOT modified - all positioning is done via Placement.

Strategy for this test:
1. Load keycap STL and get its bounding box
2. Create transform that:
   - Centers keycap in XY
   - Positions TOP of keycap at Z=0 (not bottom)
   - Rotates 45° around Y axis (pitch)
3. Load switch STL and get its bounding box
4. Create transform for switch that:
   - Centers switch in XY
   - Positions it below keycap with proper gap
   - Applies SAME rotation as keycap
   - Ensures offset is applied in ROTATED local frame
"""

import FreeCAD
import Part
import Mesh
import json
import os
import math
import numpy as np
from scipy.spatial.transform import Rotation as R

# =============================================================================
# TRANSFORM HELPER FUNCTIONS
# =============================================================================

def compose_transforms(*matrices: np.ndarray) -> np.ndarray:
    """
    Compose multiple transformation matrices.

    Transforms are applied inner-to-outer (first argument is innermost).
    Mathematically: result = matrices[-1] @ ... @ matrices[1] @ matrices[0]

    Args:
        *matrices: Transformation matrices in order of application

    Returns:
        Combined 4x4 transformation matrix
    """
    result = np.eye(4)
    for m in matrices:
        result = m @ result
    return result


def matrix_to_placement(matrix: np.ndarray):
    """
    Convert 4x4 matrix to FreeCAD Placement.

    Extracts position and rotation from the matrix and creates a
    FreeCAD Placement object.

    Args:
        matrix: 4x4 homogeneous transformation matrix

    Returns:
        FreeCAD.Placement object
    """
    # Extract position
    position = FreeCAD.Vector(
        float(matrix[0, 3]),
        float(matrix[1, 3]),
        float(matrix[2, 3])
    )

    # Extract rotation as quaternion (more robust than Euler)
    rotation_scipy = R.from_matrix(matrix[:3, :3])
    quat = rotation_scipy.as_quat()  # [x, y, z, w] in scipy

    # FreeCAD Rotation from quaternion: (x, y, z, w)
    rotation = FreeCAD.Rotation(quat[0], quat[1], quat[2], quat[3])

    return FreeCAD.Placement(position, rotation)


# =============================================================================
# MAIN SCRIPT - SIMPLIFIED TEST
# =============================================================================

print("Starting SIMPLIFIED keyboard test: single keycap+switch at 45° pitch...")
print(f"Using document: {doc.Name if 'doc' in dir() else 'Creating new for standalone'}")

# If running standalone (not from backend), create doc
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Keyboard")
    print("Created new document (standalone mode)")
else:
    print("Using provided document (backend mode)")

# Load parameters from input.json
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "input.json")

with open(input_file, 'r') as f:
    params = json.load(f)

switchOffset = params.get('switchOffset', 0.5)  # mm below keycap
pitch = 45.0  # Fixed 45° for this test

print(f"Parameters: pitch={pitch}°, switchOffset={switchOffset}mm")
print("Goal: keycap top center at origin (0,0,0)")

# =============================================================================
# LOAD STL FILES
# =============================================================================

keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")
switch_stl = os.path.join(script_dir, "kailhlowprofilev102.stl")

print("Loading STL files...")

# Load keycap mesh
keycap_mesh = Mesh.Mesh(keycap_stl)
keycap_shape = Part.Shape()
keycap_shape.makeShapeFromMesh(keycap_mesh.Topology, 0.1)
try:
    keycap_solid = Part.makeSolid(keycap_shape)
    print("Keycap converted to solid")
except Exception:
    keycap_solid = keycap_shape
    print("Keycap loaded as shell (not solid)")

# Load switch mesh
switch_mesh = Mesh.Mesh(switch_stl)
switch_shape = Part.Shape()
switch_shape.makeShapeFromMesh(switch_mesh.Topology, 0.1)
try:
    switch_solid = Part.makeSolid(switch_shape)
    print("Switch converted to solid")
except Exception:
    switch_solid = switch_shape
    print("Switch loaded as shell (not solid)")

# Get original bounding boxes
keycap_bbox = keycap_solid.BoundBox
switch_bbox = switch_solid.BoundBox

print(f"Keycap bounds: X({keycap_bbox.XMin:.2f}, {keycap_bbox.XMax:.2f}), "
      f"Y({keycap_bbox.YMin:.2f}, {keycap_bbox.YMax:.2f}), "
      f"Z({keycap_bbox.ZMin:.2f}, {keycap_bbox.ZMax:.2f})")
print(f"Switch bounds: X({switch_bbox.XMin:.2f}, {switch_bbox.XMax:.2f}), "
      f"Y({switch_bbox.YMin:.2f}, {switch_bbox.YMax:.2f}), "
      f"Z({switch_bbox.ZMin:.2f}, {switch_bbox.ZMax:.2f})")

# =============================================================================
# COMPUTE TRANSFORMS FOR SINGLE KEYCAP + SWITCH PAIR
# =============================================================================

# Get dimensions for transform calculations
switch_height = switch_bbox.ZMax - switch_bbox.ZMin
keycap_height = keycap_bbox.ZMax - keycap_bbox.ZMin

print(f"Keycap height: {keycap_height:.2f}mm, Switch height: {switch_height:.2f}mm")

# KEYCAP TRANSFORM
# ----------------
# Goal: top center of keycap at origin (0,0,0) with 45° pitch
#
# Strategy:
# 1. Translate keycap so its top center is at origin
# 2. Rotate 45° around Y axis (rotation happens at origin, so top center stays there)
#
# This way rotation happens around the point we care about (top center).

keycap_center_x = (keycap_bbox.XMin + keycap_bbox.XMax) / 2
keycap_center_y = (keycap_bbox.YMin + keycap_bbox.YMax) / 2
keycap_top_z = keycap_bbox.ZMax

# Step 1: Translate so top center is at origin
center_translation = np.eye(4)
center_translation[0, 3] = -keycap_center_x
center_translation[1, 3] = -keycap_center_y
center_translation[2, 3] = -keycap_top_z

# Step 2: Rotate 45° around Y axis (at origin, where top center now is)
pitch_rotation = R.from_euler('Y', pitch, degrees=True)
pitch_matrix = np.eye(4)
pitch_matrix[:3, :3] = pitch_rotation.as_matrix()

# Compose: first translate to center, then rotate around that center
keycap_final = compose_transforms(center_translation, pitch_matrix)

# Verify: apply transform to original top center point to see where it ends up
top_center_point = np.array([keycap_center_x, keycap_center_y, keycap_top_z, 1.0])
transformed_top_center = keycap_final @ top_center_point

print(f"Keycap transform:")
print(f"  Original top center: ({keycap_center_x:.2f}, {keycap_center_y:.2f}, {keycap_top_z:.2f})")
print(f"  Translation: move top to origin")
print(f"  Rotation: 45° pitch around Y at origin")
print(f"  Transformed top center position: ({transformed_top_center[0]:.2f}, {transformed_top_center[1]:.2f}, {transformed_top_center[2]:.2f})")
print(f"  Final transform translation component: ({keycap_final[0,3]:.2f}, {keycap_final[1,3]:.2f}, {keycap_final[2,3]:.2f})")

# SWITCH TRANSFORM
# ----------------
# Goal: positioned below keycap with same rotation
#
# Strategy:
# The switch top should be positioned (switchOffset) mm below the keycap bottom
# in the keycap's local frame, then rotated with the same pitch.
#
# In the original mesh coordinates:
# - Keycap bottom is at keycap_bbox.ZMin
# - Switch top should be at keycap_bbox.ZMin - switchOffset
# - Switch's actual top is at switch_bbox.ZMax
#
# Steps:
# 1. Translate switch so its top center aligns with target position (below keycap)
# 2. Rotate with same 45° pitch

switch_center_x = (switch_bbox.XMin + switch_bbox.XMax) / 2
switch_center_y = (switch_bbox.YMin + switch_bbox.YMax) / 2
switch_top_z = switch_bbox.ZMax

# Where the switch top should be in the assembly (in original mesh coords)
switch_target_z = keycap_bbox.ZMin - switchOffset

# Translation to position switch top at target location
switch_translation = np.eye(4)
switch_translation[0, 3] = keycap_center_x - switch_center_x  # Align X with keycap
switch_translation[1, 3] = keycap_center_y - switch_center_y  # Align Y with keycap
switch_translation[2, 3] = switch_target_z - switch_top_z     # Position Z below keycap

# Apply same rotation as keycap
switch_final = compose_transforms(switch_translation, pitch_matrix)

print(f"Switch transform:")
print(f"  Original switch top center: ({switch_center_x:.2f}, {switch_center_y:.2f}, {switch_top_z:.2f})")
print(f"  Target Z position: {switch_target_z:.2f} (keycap bottom {keycap_bbox.ZMin:.2f} - gap {switchOffset:.2f})")
print(f"  Final transform translation: ({switch_final[0,3]:.2f}, {switch_final[1,3]:.2f}, {switch_final[2,3]:.2f})")

# =============================================================================
# CREATE OBJECTS WITH TRANSFORMS
# =============================================================================

# Create keycap object
keycap_obj = doc.addObject("Part::Feature", "Keycap")
keycap_obj.Shape = keycap_solid
keycap_obj.Placement = matrix_to_placement(keycap_final)

# Create switch object
switch_obj = doc.addObject("Part::Feature", "Switch")
switch_obj.Shape = switch_solid
switch_obj.Placement = matrix_to_placement(switch_final)

print("Created single keycap+switch pair with 45° pitch")
print("Keycap top center should be at origin (0,0,0)")

# =============================================================================
# FINALIZE
# =============================================================================

doc.recompute()
print("Document recomputed")

print(f"Model generated successfully with {len(doc.Objects)} object(s)")
print("SUCCESS: Model generation complete")
