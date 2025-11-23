#!/usr/bin/env python3
"""
Keyboard Model
Creates a row of keycaps and switches from STL files
Uses kailh_choc_low_profile_keycap.stl and kailhlowprofilev102.stl
Backend provides 'doc' variable - we add objects to it

Transformation Hierarchy (inner to outer):
1. mesh_centering_transform - Centers STL geometry (XY centered, bottom at Z=0)
2. key_assembly_transform - Stacks keycap + switch with vertical gap
3. key_orientation_transform - Tilts key backward (pitch around Y)
4. row_position_transform - Positions key on ring arc (roll around X + translation)
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
# PRE-COMPUTE LEVEL 1 TRANSFORMS (mesh centering)
# =============================================================================

keycap_centering = mesh_centering_transform(
    (keycap_bbox.XMin, keycap_bbox.YMin, keycap_bbox.ZMin),
    (keycap_bbox.XMax, keycap_bbox.YMax, keycap_bbox.ZMax)
)

switch_centering = mesh_centering_transform(
    (switch_bbox.XMin, switch_bbox.YMin, switch_bbox.ZMin),
    (switch_bbox.XMax, switch_bbox.YMax, switch_bbox.ZMax)
)

# Apply centering to the base shapes (this is baked into the geometry)
keycap_solid = keycap_solid.translated(FreeCAD.Vector(
    keycap_centering[0, 3],
    keycap_centering[1, 3],
    keycap_centering[2, 3]
))

switch_solid = switch_solid.translated(FreeCAD.Vector(
    switch_centering[0, 3],
    switch_centering[1, 3],
    switch_centering[2, 3]
))

# Get switch height for assembly offset calculation
switch_height = switch_bbox.ZMax - switch_bbox.ZMin

print(f"Keycap centered: bottom at Z=0")
print(f"Switch centered: bottom at Z=0, height={switch_height:.2f}mm")

# =============================================================================
# PRE-COMPUTE LEVEL 2 TRANSFORMS (key assembly)
# =============================================================================

# Keycap: bottom at Z=0 (no additional offset needed after centering)
keycap_assembly = key_assembly_transform(0.0)

# Switch: position so its TOP is at Z = -switchOffset
# After centering, switch bottom is at Z=0, top at Z=switch_height
# We want top at -switchOffset, so translate by -(switch_height + switchOffset)
switch_assembly = key_assembly_transform(-(switch_height + switchOffset))

print(f"Assembly: keycap at Z=0, switch top at Z={-switchOffset}mm")

# =============================================================================
# CREATE BASE GEOMETRY OBJECTS
# =============================================================================

# Apply assembly transform to switch geometry (bake it in)
switch_solid = switch_solid.translated(FreeCAD.Vector(
    switch_assembly[0, 3],
    switch_assembly[1, 3],
    switch_assembly[2, 3]
))

keycap_base = doc.addObject("Part::Feature", "Keycap_Base")
keycap_base.Shape = keycap_solid

switch_base = doc.addObject("Part::Feature", "Switch_Base")
switch_base.Shape = switch_solid

# =============================================================================
# CREATE KEY INSTANCES WITH HIERARCHICAL TRANSFORMS
# =============================================================================

# Calculate angular span and center it
totalAngle = (keyCount - 1) * angleBetweenKeys
startAngle = -totalAngle / 2

print(f"Creating {keyCount} keycap and switch instances...")
print("Transform hierarchy: orientation (pitch) -> row position (roll)")

for i in range(keyCount):
    roll_rad = startAngle + i * angleBetweenKeys

    # Level 3: Key orientation (pitch)
    orientation = key_orientation_transform(pitch)

    # Level 4: Row position (roll on ring)
    row_pos = row_position_transform(roll_rad, ringRadius, ringAxisZ)

    # Compose transforms: orientation first, then row position
    # (Levels 1 and 2 are already baked into the geometry)
    final_transform = compose_transforms(orientation, row_pos)

    # Convert to FreeCAD Placement
    placement = matrix_to_placement(final_transform)

    if i == 0:
        # First instance - use the base objects
        keycap_base.Label = "Keycap_1"
        switch_base.Label = "Switch_1"
        keycap_obj = keycap_base
        switch_obj = switch_base
    else:
        # Additional instances
        keycap_obj = doc.addObject("Part::Feature", f"Keycap_{i+1}")
        keycap_obj.Shape = keycap_base.Shape

        switch_obj = doc.addObject("Part::Feature", f"Switch_{i+1}")
        switch_obj.Shape = switch_base.Shape

    # Apply the same placement to both keycap and switch
    keycap_obj.Placement = placement
    switch_obj.Placement = placement

    # Extract position for logging
    pos = final_transform[:3, 3]
    roll_deg = math.degrees(roll_rad)
    print(f"Key {i+1}: roll={roll_deg:+6.1f} deg, pos=({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")

# =============================================================================
# ADD VISUAL RING (hand rest cylinder)
# =============================================================================

ringLength = 200  # mm
ringThickness = 2  # mm

outerCylinder = Part.makeCylinder(
    ringRadius,
    ringLength,
    FreeCAD.Vector(0, -ringLength/2, ringAxisZ),
    FreeCAD.Vector(0, 1, 0)
)
innerCylinder = Part.makeCylinder(
    ringRadius - ringThickness,
    ringLength,
    FreeCAD.Vector(0, -ringLength/2, ringAxisZ),
    FreeCAD.Vector(0, 1, 0)
)
ringShape = outerCylinder.cut(innerCylinder)

ring_obj = doc.addObject("Part::Feature", "HandRing")
ring_obj.Shape = ringShape
print(f"Added hand ring: radius={ringRadius}mm, axis at Z={ringAxisZ}mm")

# =============================================================================
# FINALIZE
# =============================================================================

doc.recompute()
print("Document recomputed")

print(f"Keyboard generated successfully with {len(doc.Objects)} object(s)")
print(f"SUCCESS: Keyboard model complete - {keyCount} keys + ring generated")
