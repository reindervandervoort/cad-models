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
key_count = params.get('keyCount', 5)
u = params.get('u', 18)
pitch_angle = params.get('pitch', 45)
switch_offset = params.get('switchOffset', 1)  # mm below keycap top

print(f"\nParameters: keyCount={key_count}, u={u}mm, pitch={pitch_angle}°, hand_radius={hand_radius}mm, switchOffset={switch_offset}mm")

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
            x = r * math.cos(theta)
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

# Create keycaps and switches
for i in range(key_count):
    print(f"\n=== Key {i+1}/{key_count} ===")

    # Calculate base placement (same for both keycap and switch)
    base_placement, angle = calculate_placement(i, key_count, u, hand_radius, pitch_angle)

    # Create keycap at base placement
    keycap_obj = doc.addObject("Part::Feature", f"Keycap_{i+1:02d}")
    keycap_obj.Shape = keycap_shape
    keycap_obj.Placement = base_placement

    # Create switch offset in LOCAL coordinate system
    # The switch needs to be 6mm below in the -Z direction of the rotated coordinate system
    local_offset = FreeCAD.Vector(0, 0, -switch_offset)
    # Rotate the offset vector by the same rotation as the keycap
    global_offset = base_placement.Rotation.multVec(local_offset)
    # Create switch placement: same rotation, but offset position
    switch_pos = base_placement.Base.add(global_offset)
    switch_placement = FreeCAD.Placement(switch_pos, base_placement.Rotation)

    switch_obj = doc.addObject("Part::Feature", f"Switch_{i+1:02d}")
    switch_obj.Shape = switch_shape
    switch_obj.Placement = switch_placement

    print(f"  Arc angle: {angle:.2f}°")
    print(f"  Keycap pos: ({base_placement.Base.x:.1f}, {base_placement.Base.y:.1f}, {base_placement.Base.z:.1f})")
    print(f"  Switch pos: ({switch_placement.Base.x:.1f}, {switch_placement.Base.y:.1f}, {switch_placement.Base.z:.1f})")

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
print(f"\nSUCCESS: Created {key_count} keycaps, {key_count} switches, and 1 golden spiral ({len(doc.Objects)} objects total)")
