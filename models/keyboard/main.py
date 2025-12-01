#!/usr/bin/env python3
"""
Keyboard Row: Keycaps with Switches on Circular Arc
Keycaps and switches positioned on curved row with pitch and roll

Version 2.0: Refined switch positioning and mesh repair
"""

import FreeCAD
import Part
import Mesh
import os
import math
import json

# Golden ratio constant
PHI = (1 + math.sqrt(5)) / 2  # Approximately 1.618...

print("=== Keyboard row with keycaps and switches ===")

# Document setup
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Keyboard")
else:
    print("Using backend mode")

# Load parameters
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "input.json")
with open(input_file, 'r') as f:
    params = json.load(f)

hand_diameter = params.get('handDiameter', 192)
hand_radius = hand_diameter / 2
roll_diameter = params.get('rollDiameter', 192)
roll_radius = roll_diameter / 2
key_count = params.get('keyCount', 5)
row_count = params.get('rowCount', 6)
row_spacing = params.get('rowSpacing', 30)
spiral_start_angle = params.get('spiralStartAngle', math.pi)
u = params.get('u', 18)
pitch_angle = params.get('pitch', 45)
switch_offset = params.get('switchOffset', 1)  # mm below keycap top

print(f"\nParameters: keyCount={key_count}, rowCount={row_count}, u={u}mm, pitch={pitch_angle}°")
print(f"  hand_radius={hand_radius}mm, roll_radius={roll_radius}mm, switchOffset={switch_offset}mm")
print(f"  rowSpacing={row_spacing}mm, spiralStartAngle={spiral_start_angle:.3f} rad")

# Helper function to calculate placement for any component
def calculate_placement(position_index, key_count, u, hand_radius, pitch_angle):
    """
    Calculate placement for a component on the circular arc.

    Args:
        position_index: Position in row (0 to key_count-1)
        key_count: Total number of keys
        u: Spacing between keys
        hand_radius: Radius of circular arc
        pitch_angle: Pitch angle in degrees

    Returns:
        (FreeCAD.Placement, angle_deg) tuple
    """
    # Calculate arc angle for this position
    row_offset_y_linear = (position_index - (key_count - 1) / 2) * u
    keycap_angle = row_offset_y_linear / hand_radius  # radians
    keycap_angle_deg = math.degrees(keycap_angle)

    # Position on the circular arc around X axis at height hand_radius
    pos_x = 0
    pos_y = hand_radius * math.sin(keycap_angle)
    pos_z = hand_radius * (1 - math.cos(keycap_angle))

    # Rotations: roll by the arc angle first, THEN pitch around Y
    roll_rot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), keycap_angle_deg)
    pitch_rot = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), pitch_angle)
    combined_rot = roll_rot.multiply(pitch_rot)

    return FreeCAD.Placement(FreeCAD.Vector(pos_x, pos_y, pos_z), combined_rot), keycap_angle_deg


def create_golden_spiral(start_diameter, arc_length_radians, tube_radius, center, plane_normal='xz', num_segments=100):
    """
    Create a golden spiral as a swept tube.

    Args:
        start_diameter: Initial diameter of the spiral
        arc_length_radians: Total angular length in radians (e.g., 2*pi for one full turn)
        tube_radius: Radius of the circular cross-section tube
        center: FreeCAD.Vector for the center of the spiral
        plane_normal: Plane orientation ('xz' for X-Z plane, 'xy' for X-Y plane, etc.)
        num_segments: Number of segments to approximate the spiral curve

    Returns:
        Part.Shape of the spiral tube
    """
    print(f"\n=== Creating Golden Spiral ===")
    print(f"Start diameter: {start_diameter}mm")
    print(f"Arc length: {arc_length_radians:.3f} radians ({math.degrees(arc_length_radians):.1f}°)")
    print(f"Tube radius: {tube_radius}mm")
    print(f"Center: ({center.x}, {center.y}, {center.z})")
    print(f"Plane: {plane_normal}")

    # Starting radius
    a = start_diameter / 2

    # Generate spiral points using golden spiral formula: r(θ) = a × φ^(-θ/(π/2))
    points = []
    for i in range(num_segments + 1):
        theta = (arc_length_radians / num_segments) * i

        # Golden spiral radius formula
        r = a * (PHI ** (-theta / (math.pi / 2)))

        # Calculate point coordinates based on plane orientation
        if plane_normal.lower() == 'xz':
            # Spiral in X-Z plane (perpendicular to Y-axis)
            # Flipped horizontally by negating x
            x = -r * math.cos(theta)
            y = 0
            z = r * math.sin(theta)
        elif plane_normal.lower() == 'xy':
            # Spiral in X-Y plane (perpendicular to Z-axis)
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            z = 0
        elif plane_normal.lower() == 'yz':
            # Spiral in Y-Z plane (perpendicular to X-axis)
            x = 0
            y = r * math.cos(theta)
            z = r * math.sin(theta)
        else:
            raise ValueError(f"Unknown plane orientation: {plane_normal}")

        # Offset by center
        point = FreeCAD.Vector(center.x + x, center.y + y, center.z + z)
        points.append(point)

    # Create the spiral path using BSpline
    spiral_curve = Part.BSplineCurve()
    spiral_curve.interpolate(points)
    spiral_edge = spiral_curve.toShape()

    # Create circular cross-section for the tube
    circle_center = points[0]

    # Calculate the tangent at the start to orient the circle perpendicular to the curve
    tangent = points[1] - points[0]
    tangent.normalize()

    # Create a normal vector perpendicular to the tangent
    if plane_normal.lower() == 'xz':
        # For XZ plane, use Y-axis as reference
        reference = FreeCAD.Vector(0, 1, 0)
    elif plane_normal.lower() == 'xy':
        # For XY plane, use Z-axis as reference
        reference = FreeCAD.Vector(0, 0, 1)
    else:  # yz
        # For YZ plane, use X-axis as reference
        reference = FreeCAD.Vector(1, 0, 0)

    # Cross product to get perpendicular vector
    normal = tangent.cross(reference)
    if normal.Length < 0.001:
        # If tangent is parallel to reference, use different reference
        reference = FreeCAD.Vector(1, 0, 0) if plane_normal.lower() != 'yz' else FreeCAD.Vector(0, 1, 0)
        normal = tangent.cross(reference)
    normal.normalize()

    # Create circle perpendicular to the starting tangent
    circle = Part.makeCircle(tube_radius, circle_center, normal)
    circle_wire = Part.Wire(circle)

    # Sweep the circle along the spiral path to create the tube
    spiral_tube = Part.Wire([spiral_edge]).makePipeShell([circle_wire], True, False)

    end_radius = a * (PHI ** (-arc_length_radians / (math.pi / 2)))
    print(f"End radius: {end_radius:.3f}mm (shrunk by factor of {a/end_radius:.3f})")
    print(f"Golden spiral created with {num_segments} segments")

    return spiral_tube


def spiral_radius_at_angle(theta, start_diameter):
    """Calculate radius of golden spiral at given angle theta."""
    a = start_diameter / 2
    return a * (PHI ** (-theta / (math.pi / 2)))


def spiral_position_at_angle(theta, start_diameter, center=FreeCAD.Vector(0, 0, 0)):
    """Calculate 3D position on spiral at given angle in X-Z plane."""
    r = spiral_radius_at_angle(theta, start_diameter)
    x = -r * math.cos(theta)  # Negative for horizontal flip
    y = 0
    z = r * math.sin(theta)
    return FreeCAD.Vector(center.x + x, center.y + y, center.z + z)


def spiral_tangent_at_angle(theta, start_diameter):
    """
    Calculate tangent vector to the spiral at given angle.
    For r(θ) = a × φ^(-θ/(π/2)), the tangent in polar coords is:
    dr/dθ = -a × ln(φ)/(π/2) × φ^(-θ/(π/2))
    """
    a = start_diameter / 2
    r = a * (PHI ** (-theta / (math.pi / 2)))
    dr_dtheta = -a * math.log(PHI) / (math.pi / 2) * (PHI ** (-theta / (math.pi / 2)))

    # Convert polar tangent to Cartesian (for flipped spiral in X-Z plane)
    # dx/dθ = -dr/dθ * cos(θ) + r * sin(θ)  (with flip)
    # dz/dθ = dr/dθ * sin(θ) + r * cos(θ)
    dx_dtheta = -dr_dtheta * math.cos(theta) + r * math.sin(theta)
    dz_dtheta = dr_dtheta * math.sin(theta) + r * math.cos(theta)

    tangent = FreeCAD.Vector(dx_dtheta, 0, dz_dtheta)
    tangent.normalize()
    return tangent


def spiral_normal_at_angle(theta, start_diameter):
    """
    Calculate outward normal vector to the spiral at given angle (in X-Z plane).
    Normal is perpendicular to tangent, pointing away from center.
    """
    tangent = spiral_tangent_at_angle(theta, start_diameter)
    # In X-Z plane, Y-axis is perpendicular to the plane
    y_axis = FreeCAD.Vector(0, 1, 0)
    # Normal = tangent × y_axis (right-hand rule)
    normal = tangent.cross(y_axis)
    normal.normalize()
    return normal


def find_theta_at_arc_distance(start_theta, arc_distance, start_diameter, tolerance=0.01, max_iterations=100):
    """
    Find the angle theta along the spiral where the arc length from start_theta equals arc_distance.
    Uses numerical integration to compute arc length.

    Args:
        start_theta: Starting angle in radians
        arc_distance: Target arc length in mm
        start_diameter: Initial diameter of spiral
        tolerance: Convergence tolerance in mm
        max_iterations: Maximum iterations for binary search

    Returns:
        Angle theta in radians where arc length equals arc_distance
    """
    def arc_length_from_start(end_theta, num_segments=50):
        """Numerically integrate arc length from start_theta to end_theta."""
        length = 0.0
        for i in range(num_segments):
            t1 = start_theta + (end_theta - start_theta) * i / num_segments
            t2 = start_theta + (end_theta - start_theta) * (i + 1) / num_segments
            p1 = spiral_position_at_angle(t1, start_diameter)
            p2 = spiral_position_at_angle(t2, start_diameter)
            length += p1.distanceToPoint(p2)
        return length

    # Binary search for the correct theta
    theta_min = start_theta
    theta_max = start_theta + 2 * math.pi  # Search up to one full rotation ahead

    for iteration in range(max_iterations):
        theta_mid = (theta_min + theta_max) / 2
        arc_len = arc_length_from_start(theta_mid)

        if abs(arc_len - arc_distance) < tolerance:
            return theta_mid

        if arc_len < arc_distance:
            theta_min = theta_mid
        else:
            theta_max = theta_mid

    # Return best estimate if not converged
    return (theta_min + theta_max) / 2


# Load and prepare base keycap mesh
keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")
print(f"\nLoading keycap: {keycap_stl}")

keycap_mesh = Mesh.Mesh(keycap_stl)
bbox = keycap_mesh.BoundBox

# Center the keycap mesh (top at Z=0)
offset_x = -(bbox.XMin + bbox.XMax) / 2
offset_y = -(bbox.YMin + bbox.YMax) / 2
offset_z = -bbox.ZMax
keycap_mesh.translate(offset_x, offset_y, offset_z)

keycap_shape = Part.Shape()
keycap_shape.makeShapeFromMesh(keycap_mesh.Topology, 0.1)

# Load and prepare base switch mesh
switch_stl = os.path.join(script_dir, "kailhlowprofilev102_fixed.stl")
print(f"Loading switch: {switch_stl}")

try:
    switch_mesh = Mesh.Mesh(switch_stl)
    switch_bbox = switch_mesh.BoundBox

    print(f"Switch original bbox: X[{switch_bbox.XMin:.1f}, {switch_bbox.XMax:.1f}] Y[{switch_bbox.YMin:.1f}, {switch_bbox.YMax:.1f}] Z[{switch_bbox.ZMin:.1f}, {switch_bbox.ZMax:.1f}]")

    # Center the switch mesh (top at Z=0)
    switch_offset_x = -(switch_bbox.XMin + switch_bbox.XMax) / 2
    switch_offset_y = -(switch_bbox.YMin + switch_bbox.YMax) / 2
    switch_offset_z = -switch_bbox.ZMax

    print(f"Switch offset: ({switch_offset_x:.1f}, {switch_offset_y:.1f}, {switch_offset_z:.1f})")

    switch_mesh.translate(switch_offset_x, switch_offset_y, switch_offset_z)

    # Convert using same method as keycap
    switch_shape = Part.Shape()
    switch_shape.makeShapeFromMesh(switch_mesh.Topology, 0.1)

    print(f"Switch shape created successfully with {len(switch_shape.Faces)} faces")

except Exception as e:
    print(f"ERROR loading switch: {e}")
    import traceback
    traceback.print_exc()
    # Create a simple parametric fallback
    switch_base = Part.makeBox(14, 14, 3.5, FreeCAD.Vector(-7, -7, -3.5))
    switch_top = Part.makeBox(12, 12, 1.5, FreeCAD.Vector(-6, -6, 0))
    switch_shape = switch_base.fuse(switch_top)
    print("Using parametric fallback switch shape")

# Calculate row positions along the spiral
print(f"\n=== Calculating {row_count} row positions along spiral ===")
row_thetas = [spiral_start_angle]
for row_idx in range(1, row_count):
    arc_dist = row_spacing * row_idx
    theta = find_theta_at_arc_distance(spiral_start_angle, arc_dist, hand_diameter)
    row_thetas.append(theta)
    print(f"Row {row_idx + 1}: theta={theta:.4f} rad ({math.degrees(theta):.1f}°), arc_dist={arc_dist}mm")

# Create keycaps and switches for all rows
total_keys = 0
for row_idx in range(row_count):
    theta = row_thetas[row_idx]
    print(f"\n=== Row {row_idx + 1}/{row_count} at theta={theta:.4f} rad ===")

    # Get spiral position at this angle
    spiral_pos = spiral_position_at_angle(theta, hand_diameter)
    normal = spiral_normal_at_angle(theta, hand_diameter)    # Normal to spiral (for offset direction)

    # Use CONSISTENT orientation for all rows (not tangent-based)
    # All rows should be parallel, oriented in the same direction
    # Y-axis: Global Y direction (row runs left-to-right in global coords)
    # Z-axis: Use spiral normal for perpendicular direction
    # X-axis: Complete the right-hand coordinate system

    y_axis = FreeCAD.Vector(0, 1, 0)  # Fixed global Y direction for all rows
    z_axis = normal                    # Perpendicular to spiral (points outward)
    x_axis = z_axis.cross(y_axis)
    x_axis.normalize()

    # Re-orthogonalize to ensure perfect perpendicularity
    z_axis = x_axis.cross(y_axis)
    z_axis.normalize()

    # Create rotation matrix from local axes
    # All rows will have the same orientation, just different positions along the spiral
    local_to_global = FreeCAD.Rotation(
        FreeCAD.Matrix(
            x_axis.x, y_axis.x, z_axis.x, 0,
            x_axis.y, y_axis.y, z_axis.y, 0,
            x_axis.z, y_axis.z, z_axis.z, 0,
            0, 0, 0, 1
        )
    )

    print(f"  Spiral pos: ({spiral_pos.x:.1f}, {spiral_pos.y:.1f}, {spiral_pos.z:.1f})")
    print(f"  Normal: ({normal.x:.3f}, {normal.y:.3f}, {normal.z:.3f})")
    print(f"  Row orientation: Y-axis={y_axis}, Z-axis=({z_axis.x:.3f}, {z_axis.y:.3f}, {z_axis.z:.3f})")

    # Create keys in this row
    for key_idx in range(key_count):
        # Calculate placement within the row's local coordinate system
        local_placement, arc_angle = calculate_placement(key_idx, key_count, u, roll_radius, pitch_angle)

        # Transform local placement to global coordinates
        # The local placement is in a coordinate system where:
        # - Origin is at the row center
        # - Y-axis is along the row
        # - Z-axis is perpendicular to the row (away from center of curvature)
        # We need to:
        # 1. Apply the local rotation
        # 2. Offset by the spiral position
        # 3. Apply the spiral orientation

        # Combine rotations: first the local key rotation, then the spiral orientation
        global_rotation = local_to_global.multiply(local_placement.Rotation)

        # Transform local position to global
        global_offset = local_to_global.multVec(local_placement.Base)
        global_position = spiral_pos.add(global_offset)

        # Create final placement
        final_placement = FreeCAD.Placement(global_position, global_rotation)

        # Create keycap
        keycap_obj = doc.addObject("Part::Feature", f"Keycap_R{row_idx + 1:02d}_K{key_idx + 1:02d}")
        keycap_obj.Shape = keycap_shape
        keycap_obj.Placement = final_placement

        # Create switch with offset
        local_switch_offset = FreeCAD.Vector(0, 0, -switch_offset)
        global_switch_offset = global_rotation.multVec(local_switch_offset)
        switch_position = global_position.add(global_switch_offset)
        switch_placement = FreeCAD.Placement(switch_position, global_rotation)

        switch_obj = doc.addObject("Part::Feature", f"Switch_R{row_idx + 1:02d}_K{key_idx + 1:02d}")
        switch_obj.Shape = switch_shape
        switch_obj.Placement = switch_placement

        total_keys += 1

    print(f"  Created {key_count} keys in row {row_idx + 1}")

# Create golden spiral
# Parameters:
# - Start diameter = handDiameter (from input.json)
# - Arc length = 2π radians (one full revolution)
# - Tube radius = 5mm
# - Center at origin (0, 0, 0)
# - Plane: X-Z (perpendicular to the Y-axis row direction)
spiral_shape = create_golden_spiral(
    start_diameter=hand_diameter,
    arc_length_radians=2 * math.pi,
    tube_radius=5.0,
    center=FreeCAD.Vector(0, 0, 0),
    plane_normal='xz',
    num_segments=200  # Higher resolution for smooth spiral
)

spiral_obj = doc.addObject("Part::Feature", "GoldenSpiral")
spiral_obj.Shape = spiral_shape

doc.recompute()
print(f"\nSUCCESS: Created {row_count} rows with {key_count} keys each ({total_keys} total keys)")
print(f"  {total_keys} keycaps + {total_keys} switches + 1 golden spiral = {len(doc.Objects)} objects total")
