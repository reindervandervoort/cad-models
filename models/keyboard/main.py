#!/usr/bin/env python3
"""
Keyboard Model
Creates a row of keycaps and switches from STL files
Uses kailh_choc_low_profile_keycap.stl and kailhlowprofilev102.stl
Backend provides 'doc' variable - we add objects to it

IMPORTANT: Transform Handling
=============================
All transformations must be COLLAPSED into a single 4x4 matrix before being
converted to a FreeCAD Placement. The backend exports each object's Placement
to assembly.json, which the Three.js frontend then applies to the loaded STL.

The STL geometry is NOT modified - all positioning is done via Placement.
Each object (keycap, switch) gets its own Placement that includes ALL transforms
from the hierarchy below, collapsed into one matrix.

Transformation Hierarchy (inner to outer):
1. mesh_centering_transform - Centers STL geometry (XY centered, bottom at Z=0)
2. key_assembly_transform - Stacks keycap + switch with vertical gap
3. key_orientation_transform - Tilts key backward (pitch around Y)
4. row_position_transform - Positions key on ring arc (roll around X + translation)

For each instance, we compute:
  final_matrix = row_position @ orientation @ assembly @ centering

Then convert final_matrix to FreeCAD.Placement for that object.
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
# TRANSFORM FUNCTIONS - Hierarchical transformation system
# Each returns a 4x4 homogeneous transformation matrix
# =============================================================================


def mesh_centering_transform(bbox_min: tuple, bbox_max: tuple) -> np.ndarray:
    """
    Level 1: Center mesh geometry.

    Translates mesh so that:
    - XY is centered at origin
    - Bottom (Z min) is at Z=0

    Args:
        bbox_min: (xmin, ymin, zmin) of original mesh
        bbox_max: (xmax, ymax, zmax) of original mesh

    Returns:
        4x4 translation matrix
    """
    center_x = (bbox_min[0] + bbox_max[0]) / 2
    center_y = (bbox_min[1] + bbox_max[1]) / 2
    bottom_z = bbox_min[2]

    matrix = np.eye(4)
    matrix[0, 3] = -center_x  # Center X
    matrix[1, 3] = -center_y  # Center Y
    matrix[2, 3] = -bottom_z  # Move bottom to Z=0

    return matrix


def key_assembly_transform(z_offset: float) -> np.ndarray:
    """
    Level 2: Position component in key assembly stack.

    For keycap: z_offset = 0 (bottom at Z=0)
    For switch: z_offset = -switch_height - gap (top below keycap bottom)

    Args:
        z_offset: Vertical offset for this component

    Returns:
        4x4 translation matrix
    """
    matrix = np.eye(4)
    matrix[2, 3] = z_offset
    return matrix


def key_orientation_transform(pitch_deg: float) -> np.ndarray:
    """
    Level 3: Tilt key backward (pitch rotation).

    Rotates around the Y axis so the top of the key tilts away
    from the user (toward -X in local coordinates).

    Args:
        pitch_deg: Pitch angle in degrees (positive = top tilts back)

    Returns:
        4x4 rotation matrix
    """
    rotation = R.from_euler('Y', pitch_deg, degrees=True)

    matrix = np.eye(4)
    matrix[:3, :3] = rotation.as_matrix()
    return matrix


def row_position_transform(
    roll_rad: float,
    ring_radius: float,
    ring_axis_z: float
) -> np.ndarray:
    """
    Level 4: Position key on the ring arc.

    Combines:
    - Rotation around X axis (roll) to orient tangent to ring
    - Translation to position on the ring circumference

    The ring axis is along Y at height Z=ring_axis_z.
    At roll_rad=0, the key is at the bottom of the ring (Y=0, Z=0).

    Args:
        roll_rad: Angular position on ring in radians (from bottom)
        ring_radius: Radius of the ring
        ring_axis_z: Z position of the ring axis

    Returns:
        4x4 transformation matrix (rotation + translation)
    """
    # Rotation around X axis
    rotation = R.from_euler('X', roll_rad, degrees=False)

    # Position on ring circumference
    # At roll=0: Y=0, Z=ring_axis_z - ring_radius (bottom of ring)
    y_pos = ring_radius * math.sin(roll_rad)
    z_pos = ring_axis_z - ring_radius * math.cos(roll_rad)

    matrix = np.eye(4)
    matrix[:3, :3] = rotation.as_matrix()
    matrix[0, 3] = 0.0      # X stays at 0 (keys in YZ plane)
    matrix[1, 3] = y_pos
    matrix[2, 3] = z_pos

    return matrix


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

    Extracts position and rotation (as Euler angles) from the matrix
    and creates a FreeCAD Placement object.

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
# MAIN SCRIPT
# =============================================================================

print("Starting keyboard generation with STL files...")
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

u = params['u']  # 18 mm
keyHeight = params['keyHeight']  # 6 mm (not used with STL)
keyCount = params['keyCount']  # 10
switchOffset = params.get('switchOffset', 0.5)  # mm below keycap
pitch = params['pitch']  # 45 degrees
handDiameter = params['handDiameter']  # 192 mm
horizontalSpace = params['horizontalSpace']  # 2 mm gap at key surface

# Ring parameters
ringRadius = handDiameter / 2  # 96 mm
ringAxisZ = ringRadius  # Axis is at Z = 96mm (above origin)

# Calculate angle between keys based on arc length
arcLengthPerKey = u + horizontalSpace
angleBetweenKeys = arcLengthPerKey / ringRadius  # radians

print(f"Parameters: u={u}mm, keyCount={keyCount}, switchOffset={switchOffset}mm")
print(f"Pitch: {pitch} deg, handDiameter={handDiameter}mm, horizontalSpace={horizontalSpace}mm")
print(f"Ring radius: {ringRadius}mm, angle between keys: {math.degrees(angleBetweenKeys):.2f} deg")

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
# PRE-COMPUTE TRANSFORMS (all applied via Placement, NOT baked into geometry)
# =============================================================================

# Get dimensions for transform calculations
switch_height = switch_bbox.ZMax - switch_bbox.ZMin
keycap_height = keycap_bbox.ZMax - keycap_bbox.ZMin

# Level 1: Centering transforms (moves mesh so XY centered, bottom at Z=0)
# IMPORTANT: Both keycap and switch are centered at origin with bottom at Z=0
# This ensures rotations affect them identically
keycap_centering = mesh_centering_transform(
    (keycap_bbox.XMin, keycap_bbox.YMin, keycap_bbox.ZMin),
    (keycap_bbox.XMax, keycap_bbox.YMax, keycap_bbox.ZMax)
)

switch_centering = mesh_centering_transform(
    (switch_bbox.XMin, switch_bbox.YMin, switch_bbox.ZMin),
    (switch_bbox.XMax, switch_bbox.YMax, switch_bbox.ZMax)
)

# Level 2: Assembly offset in LOCAL space
# Both keycap and switch will use THE SAME world transform (rotation + position)
# The offset is applied by translating the switch's geometry BEFORE centering
# This ensures they move together as a rigid body

print(f"Switch height: {switch_height:.2f}mm, Keycap height: {keycap_height:.2f}mm")
print(f"Assembly offset: switch positioned {switch_height + switchOffset:.2f}mm below keycap in local Z")

# =============================================================================
# CREATE BASE GEOMETRY WITH ASSEMBLY OFFSET BAKED IN
# =============================================================================

# Keycap: use original geometry
keycap_base = doc.addObject("Part::Feature", "Keycap_Base")
keycap_base.Shape = keycap_solid

# Switch: use original geometry (NO translation!)
switch_base = doc.addObject("Part::Feature", "Switch_Base")
switch_base.Shape = switch_solid

print(f"Switch will be positioned {switchOffset:.2f}mm below keycap using transform offset")

# =============================================================================
# CREATE KEY INSTANCES WITH HIERARCHICAL TRANSFORMS
# =============================================================================

# Calculate angular span and center it
totalAngle = (keyCount - 1) * angleBetweenKeys
startAngle = -totalAngle / 2

# =============================================================================
# CREATE KEY INSTANCES WITH FULL TRANSFORM HIERARCHY
# =============================================================================
print(f"Creating {keyCount} keycap and switch instances...")
print("All transforms collapsed into single Placement per object")

for i in range(keyCount):
    roll_rad = startAngle + i * angleBetweenKeys

    # Level 3: Key orientation (pitch)
    orientation = key_orientation_transform(pitch)

    # Level 4: Row position (roll on ring)
    row_pos = row_position_transform(roll_rad, ringRadius, ringAxisZ)

    # Compose ALL transforms for each part:
    #
    # For rigid body attachment, both parts must rotate identically, then
    # the assembly offset is applied IN THE ROTATED FRAME.
    #
    # Strategy:
    # 1. Both centered at origin (same point)
    # 2. Both rotate with same orientation + row_pos
    # 3. Switch gets additional offset in LOCAL Z (rotated frame)
    #
    # To apply offset in local frame after rotation:
    # - Compute the combined rotation matrix
    # - Rotate the offset vector [0, 0, -offset] by that rotation
    # - Add as translation after everything else

    # Combined rotation (pitch then roll)
    combined_rotation = compose_transforms(orientation, row_pos)

    # Keycap transform: centering + rotation
    keycap_final = compose_transforms(
        keycap_centering,
        combined_rotation
    )

    # Switch transform: Use SAME centering as keycap!
    # This ensures both start from the exact same reference point
    # Then add the offset in the rotated frame

    # Extract rotation matrix (without translation)
    rotation_only = np.eye(4)
    rotation_only[:3, :3] = combined_rotation[:3, :3]

    # Rotate the local offset vector (0, 0, -(switch_height + switchOffset)) by the rotation
    local_offset = np.array([0, 0, -(switch_height + switchOffset), 0])  # w=0 for direction
    rotated_offset = rotation_only @ local_offset

    # Switch transform = KEYCAP centering + combined rotation + rotated offset
    # Using keycap centering ensures both objects start from the same reference point!
    switch_before_offset = compose_transforms(
        keycap_centering,  # Use KEYCAP centering, not switch centering!
        combined_rotation
    )

    switch_final = switch_before_offset.copy()
    switch_final[0, 3] += rotated_offset[0]
    switch_final[1, 3] += rotated_offset[1]
    switch_final[2, 3] += rotated_offset[2]

    # Convert to FreeCAD Placements
    keycap_placement = matrix_to_placement(keycap_final)
    switch_placement = matrix_to_placement(switch_final)

    if i == 0:
        # First instance - use the base objects
        keycap_base.Label = "Keycap_1"
        switch_base.Label = "Switch_1"
        keycap_obj = keycap_base
        switch_obj = switch_base
    else:
        # Additional instances - new objects with same Shape
        keycap_obj = doc.addObject("Part::Feature", f"Keycap_{i+1}")
        keycap_obj.Shape = keycap_base.Shape

        switch_obj = doc.addObject("Part::Feature", f"Switch_{i+1}")
        switch_obj.Shape = switch_base.Shape

    # Apply the collapsed Placement to each object
    keycap_obj.Placement = keycap_placement
    switch_obj.Placement = switch_placement

    # Log
    roll_deg = math.degrees(roll_rad)
    keycap_pos = keycap_final[:3, 3]
    switch_pos = switch_final[:3, 3]
    print(f"Key {i+1}: roll={roll_deg:+.1f}°, "
          f"keycap=({keycap_pos[0]:.1f},{keycap_pos[1]:.1f},{keycap_pos[2]:.1f}), "
          f"switch=({switch_pos[0]:.1f},{switch_pos[1]:.1f},{switch_pos[2]:.1f})")

# =============================================================================
# ADD VISUAL RING (hand rest cylinder) - DISABLED for visibility
# =============================================================================

# ringLength = 200  # mm
# ringThickness = 2  # mm
#
# outerCylinder = Part.makeCylinder(
#     ringRadius,
#     ringLength,
#     FreeCAD.Vector(0, -ringLength/2, ringAxisZ),
#     FreeCAD.Vector(0, 1, 0)
# )
# innerCylinder = Part.makeCylinder(
#     ringRadius - ringThickness,
#     ringLength,
#     FreeCAD.Vector(0, -ringLength/2, ringAxisZ),
#     FreeCAD.Vector(0, 1, 0)
# )
# ringShape = outerCylinder.cut(innerCylinder)
#
# ring_obj = doc.addObject("Part::Feature", "HandRing")
# ring_obj.Shape = ringShape
print("Hand ring DISABLED for visibility")

# =============================================================================
# FINALIZE
# =============================================================================

doc.recompute()
print("Document recomputed")

print(f"Keyboard generated successfully with {len(doc.Objects)} object(s)")
print(f"SUCCESS: Keyboard model complete - {keyCount} keys + ring generated")
