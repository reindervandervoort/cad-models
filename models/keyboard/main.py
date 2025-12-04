#!/usr/bin/env python3
"""
Keyboard: Left-hand split 60% with embossed labels
Variable key widths, multiple rows on golden spiral

Version 3.0: Layout-based configuration with embossed text
"""

import FreeCAD
import Part
import Mesh
import Draft
import os
import math
import json

# Golden ratio constant
PHI = (1 + math.sqrt(5)) / 2  # Approximately 1.618...

print("=== Left-hand split keyboard with embossed labels ===")

# Document setup
try:
    # Check if doc is already provided (backend mode)
    doc
    print("Using backend mode")
except NameError:
    # Running in FreeCAD GUI or console mode
    doc = FreeCAD.newDocument("Keyboard")

# Load parameters
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "input.json")
with open(input_file, 'r') as f:
    params = json.load(f)

hand_diameter = params.get('handDiameter', 192)
hand_radius = hand_diameter / 2
roll_diameter = params.get('rollDiameter', 192)
roll_radius = roll_diameter / 2
row_spacing = params.get('rowSpacing', 30)
spiral_start_angle = params.get('spiralStartAngle', math.pi)
u = params.get('u', 18)  # 1u key size in mm
pitch_angle = params.get('pitch', 45)
switch_offset = params.get('switchOffset', 1)
mount_offset = params.get('mountOffset', 17.5)
enable_labels = params.get('enableLabels', False)
text_height = params.get('textHeight', 3)  # mm tall
text_depth = params.get('textDepth', 0.5)  # mm emboss depth
layout = params.get('layout', [])

print(f"\nParameters: u={u}mm, pitch={pitch_angle}°, rows={len(layout)}")
print(f"  hand_radius={hand_radius}mm, roll_radius={roll_radius}mm")
print(f"  rowSpacing={row_spacing}mm, spiralStartAngle={spiral_start_angle:.3f} rad")
print(f"  switchOffset={switch_offset}mm, mountOffset={mount_offset}mm")
print(f"  textHeight={text_height}mm, textDepth={text_depth}mm")


def create_embossed_text(label, keycap_width_mm, text_height_mm, text_depth_mm):
    """
    Create embossed text for a keycap.

    Args:
        label: Text to emboss
        keycap_width_mm: Width of keycap in mm
        text_height_mm: Height of text in mm
        text_depth_mm: Depth of embossing in mm

    Returns:
        Part.Shape of the embossed text, or None if failed
    """
    try:
        # Create text shape using Draft module
        font_file = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if not os.path.exists(font_file):
            # Fallback to any available font
            font_file = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

        # Create the text string shape
        text_obj = Draft.makeShapeString(
            String=label,
            FontFile=font_file,
            Size=text_height_mm,
            Tracking=0
        )

        if not text_obj or not hasattr(text_obj, 'Shape'):
            print(f"  WARNING: Could not create text shape for '{label}'")
            return None

        text_shape = text_obj.Shape
        doc.removeObject(text_obj.Name)  # Clean up temporary object

        # Get text bounding box to center it
        bbox = text_shape.BoundBox
        text_width = bbox.XMax - bbox.XMin
        text_actual_height = bbox.YMax - bbox.YMin

        # Scale to fit keycap (leave some margin)
        max_text_width = keycap_width_mm * 0.7
        if text_width > max_text_width:
            scale_factor = max_text_width / text_width
            scale_matrix = FreeCAD.Matrix()
            scale_matrix.scale(FreeCAD.Vector(scale_factor, scale_factor, scale_factor))
            text_shape = text_shape.transformGeometry(scale_matrix)
            bbox = text_shape.BoundBox
            text_width = bbox.XMax - bbox.XMin
            text_actual_height = bbox.YMax - bbox.YMin

        # Center the text using transform matrix
        offset_x = -text_width / 2
        offset_y = -text_actual_height / 2
        translate_matrix = FreeCAD.Matrix()
        translate_matrix.move(FreeCAD.Vector(offset_x, offset_y, 0))
        text_shape = text_shape.transformGeometry(translate_matrix)

        # Extrude the text to create 3D embossing
        text_3d = text_shape.extrude(FreeCAD.Vector(0, 0, text_depth_mm))

        # Validate the extruded shape
        if not text_3d or text_3d.isNull():
            print(f"  WARNING: Extruded text shape for '{label}' is null")
            return None

        return text_3d

    except Exception as e:
        print(f"  WARNING: Failed to create text '{label}': {e}")
        return None


def create_keycap_with_label(base_keycap_shape, label, key_width_u, text_height_mm, text_depth_mm, u_mm):
    """
    Create a keycap with embossed label by scaling base keycap and adding text.

    Args:
        base_keycap_shape: Base keycap shape (1u)
        label: Text label
        key_width_u: Key width in units (1.0, 1.5, 2.0, etc.)
        text_height_mm: Height of text
        text_depth_mm: Depth of embossing
        u_mm: Size of 1u in mm

    Returns:
        Part.Shape of the keycap with label
    """
    # Scale keycap horizontally if needed (Y-axis in our coordinate system)
    if abs(key_width_u - 1.0) > 0.01:
        # Scale only in Y direction
        scale_matrix = FreeCAD.Matrix()
        scale_matrix.scale(FreeCAD.Vector(1.0, key_width_u, 1.0))
        keycap = base_keycap_shape.transformGeometry(scale_matrix)
    else:
        keycap = base_keycap_shape.copy()

    # Create embossed text
    if label:
        text_shape = create_embossed_text(label, key_width_u * u_mm, text_height_mm, text_depth_mm)
        if text_shape and not text_shape.isNull():
            # Position text on top of keycap (slightly below surface for embossing)
            position_matrix = FreeCAD.Matrix()
            position_matrix.move(FreeCAD.Vector(0, 0, -text_depth_mm * 0.5))
            text_shape = text_shape.transformGeometry(position_matrix)

            # Validate shape again after translation
            if not text_shape.isNull():
                # Fuse text with keycap
                try:
                    keycap = keycap.fuse(text_shape)
                except Exception as e:
                    print(f"  WARNING: Could not fuse text '{label}': {e}")

    return keycap


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


def calculate_row_layout(keys, u_mm):
    """
    Calculate the position offsets and total width for a row of keys.

    Args:
        keys: List of key dicts with 'width' and 'label'
        u_mm: Size of 1u in mm

    Returns:
        (positions, total_width) where positions is list of (offset, width) tuples
    """
    positions = []
    current_offset = 0

    for key in keys:
        width_u = key.get('width', 1.0)
        width_mm = width_u * u_mm

        # Center of this key is at current_offset + width/2
        key_center = current_offset + width_mm / 2
        positions.append((key_center, width_u))

        # Next key starts after this one
        current_offset += width_mm

    total_width = current_offset

    # Center the entire row (adjust all positions)
    center_offset = total_width / 2
    positions = [(pos - center_offset, width) for pos, width in positions]

    return positions, total_width


def create_golden_spiral(start_diameter, arc_length_radians, tube_radius, center, plane_normal='xz', num_segments=100):
    """Create a golden spiral as a swept tube."""
    print(f"\n=== Creating Golden Spiral ===")
    print(f"Start diameter: {start_diameter}mm, Arc length: {arc_length_radians:.3f} rad")

    a = start_diameter / 2

    # Generate spiral points
    points = []
    for i in range(num_segments + 1):
        theta = (arc_length_radians / num_segments) * i
        r = a * (PHI ** (-theta / (math.pi / 2)))

        if plane_normal.lower() == 'xz':
            x = -r * math.cos(theta)
            y = 0
            z = r * math.sin(theta)
        else:
            raise ValueError(f"Unknown plane orientation: {plane_normal}")

        point = FreeCAD.Vector(center.x + x, center.y + y, center.z + z)
        points.append(point)

    # Create spiral curve
    spiral_curve = Part.BSplineCurve()
    spiral_curve.interpolate(points)
    spiral_edge = spiral_curve.toShape()

    # Create tube cross-section
    tangent = points[1] - points[0]
    tangent.normalize()
    reference = FreeCAD.Vector(0, 1, 0)
    normal = tangent.cross(reference)
    normal.normalize()

    circle = Part.makeCircle(tube_radius, points[0], normal)
    circle_wire = Part.Wire(circle)

    # Sweep to create tube
    spiral_tube = Part.Wire([spiral_edge]).makePipeShell([circle_wire], True, False)

    print(f"Golden spiral created with {num_segments} segments")
    return spiral_tube


def spiral_radius_at_angle(theta, start_diameter):
    """Calculate radius of golden spiral at given angle theta."""
    a = start_diameter / 2
    return a * (PHI ** (-theta / (math.pi / 2)))


def spiral_position_at_angle(theta, start_diameter, center=FreeCAD.Vector(0, 0, 0)):
    """Calculate 3D position on spiral at given angle in X-Z plane."""
    r = spiral_radius_at_angle(theta, start_diameter)
    x = -r * math.cos(theta)
    y = 0
    z = r * math.sin(theta)
    return FreeCAD.Vector(center.x + x, center.y + y, center.z + z)


def spiral_tangent_at_angle(theta, start_diameter):
    """Calculate tangent vector to the spiral at given angle."""
    a = start_diameter / 2
    r = a * (PHI ** (-theta / (math.pi / 2)))
    dr_dtheta = -a * math.log(PHI) / (math.pi / 2) * (PHI ** (-theta / (math.pi / 2)))

    dx_dtheta = -dr_dtheta * math.cos(theta) + r * math.sin(theta)
    dz_dtheta = dr_dtheta * math.sin(theta) + r * math.cos(theta)

    tangent = FreeCAD.Vector(dx_dtheta, 0, dz_dtheta)
    tangent.normalize()
    return tangent


def spiral_normal_at_angle(theta, start_diameter):
    """Calculate outward normal vector to the spiral at given angle."""
    tangent = spiral_tangent_at_angle(theta, start_diameter)
    y_axis = FreeCAD.Vector(0, 1, 0)
    normal = tangent.cross(y_axis)
    normal.normalize()
    return normal


def find_theta_at_arc_distance(start_theta, arc_distance, start_diameter, tolerance=0.01, max_iterations=100):
    """Find angle theta along spiral where arc length from start_theta equals arc_distance."""
    def arc_length_from_start(end_theta, num_segments=50):
        length = 0.0
        for i in range(num_segments):
            t1 = start_theta + (end_theta - start_theta) * i / num_segments
            t2 = start_theta + (end_theta - start_theta) * (i + 1) / num_segments
            p1 = spiral_position_at_angle(t1, start_diameter)
            p2 = spiral_position_at_angle(t2, start_diameter)
            length += p1.distanceToPoint(p2)
        return length

    theta_min = start_theta
    theta_max = start_theta + 2 * math.pi

    for iteration in range(max_iterations):
        theta_mid = (theta_min + theta_max) / 2
        arc_len = arc_length_from_start(theta_mid)

        if abs(arc_len - arc_distance) < tolerance:
            return theta_mid

        if arc_len < arc_distance:
            theta_min = theta_mid
        else:
            theta_max = theta_mid

    return (theta_min + theta_max) / 2


# Load base keycap mesh
keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")
print(f"\nLoading keycap: {keycap_stl}")

keycap_mesh = Mesh.Mesh(keycap_stl)
bbox = keycap_mesh.BoundBox

# Center the keycap mesh (top at Z=0)
offset_x = -(bbox.XMin + bbox.XMax) / 2
offset_y = -(bbox.YMin + bbox.YMax) / 2
offset_z = -bbox.ZMax
keycap_mesh.translate(offset_x, offset_y, offset_z)

base_keycap_shape = Part.Shape()
base_keycap_shape.makeShapeFromMesh(keycap_mesh.Topology, 0.1)

print(f"Base keycap loaded: {bbox.XLength:.1f} x {bbox.YLength:.1f} x {bbox.ZLength:.1f} mm")

# Load switch mesh
switch_stl = os.path.join(script_dir, "kailhlowprofilev102_fixed.stl")
print(f"Loading switch: {switch_stl}")

try:
    switch_mesh = Mesh.Mesh(switch_stl)
    switch_bbox = switch_mesh.BoundBox

    switch_offset_x = -(switch_bbox.XMin + switch_bbox.XMax) / 2
    switch_offset_y = -(switch_bbox.YMin + switch_bbox.YMax) / 2
    switch_offset_z = -switch_bbox.ZMax

    switch_mesh.translate(switch_offset_x, switch_offset_y, switch_offset_z)

    switch_shape = Part.Shape()
    switch_shape.makeShapeFromMesh(switch_mesh.Topology, 0.1)

    print(f"Switch loaded successfully")
except Exception as e:
    print(f"ERROR loading switch: {e}")
    switch_base = Part.makeBox(14, 14, 3.5, FreeCAD.Vector(-7, -7, -3.5))
    switch_top = Part.makeBox(12, 12, 1.5, FreeCAD.Vector(-6, -6, 0))
    switch_shape = switch_base.fuse(switch_top)
    print("Using parametric fallback switch")

# Load switchplate mesh
switchplate_stl = os.path.join(script_dir, "switchplate.stl")
print(f"Loading switchplate: {switchplate_stl}")

try:
    switchplate_mesh = Mesh.Mesh(switchplate_stl)
    switchplate_bbox = switchplate_mesh.BoundBox

    switchplate_offset_x = -(switchplate_bbox.XMin + switchplate_bbox.XMax) / 2
    switchplate_offset_y = -(switchplate_bbox.YMin + switchplate_bbox.YMax) / 2
    switchplate_offset_z = -switchplate_bbox.ZMax

    switchplate_mesh.translate(switchplate_offset_x, switchplate_offset_y, switchplate_offset_z)

    switchplate_shape = Part.Shape()
    switchplate_shape.makeShapeFromMesh(switchplate_mesh.Topology, 0.1)

    print(f"Switchplate loaded successfully")
except Exception as e:
    print(f"ERROR loading switchplate: {e}")
    switchplate_shape = None
    print("Switchplate will not be included")

# Calculate row positions along the spiral
print(f"\n=== Calculating {len(layout)} row positions along spiral ===")
row_thetas = [spiral_start_angle]
for row_idx in range(1, len(layout)):
    arc_dist = row_spacing * row_idx
    theta = find_theta_at_arc_distance(spiral_start_angle, arc_dist, hand_diameter)
    row_thetas.append(theta)
    print(f"Row {row_idx + 1}: theta={theta:.4f} rad ({math.degrees(theta):.1f}°), arc_dist={arc_dist}mm")

# Create keycaps, switches, and switchplates for all rows
total_keys = 0
for row_idx, row_config in enumerate(layout):
    theta = row_thetas[row_idx]
    keys = row_config.get('keys', [])

    print(f"\n=== Row {row_idx + 1}/{len(layout)} with {len(keys)} keys ===")

    # Calculate key positions for this row
    key_positions, row_total_width = calculate_row_layout(keys, u)

    # Get spiral position and orientation
    spiral_pos = spiral_position_at_angle(theta, hand_diameter)
    normal = spiral_normal_at_angle(theta, hand_diameter)

    # Create consistent orientation for all rows
    y_axis = FreeCAD.Vector(0, 1, 0)
    z_axis = normal
    x_axis = z_axis.cross(y_axis)
    x_axis.normalize()
    z_axis = x_axis.cross(y_axis)
    z_axis.normalize()

    local_to_global = FreeCAD.Rotation(
        FreeCAD.Matrix(
            x_axis.x, y_axis.x, z_axis.x, 0,
            x_axis.y, y_axis.y, z_axis.y, 0,
            x_axis.z, y_axis.z, z_axis.z, 0,
            0, 0, 0, 1
        )
    )

    print(f"  Spiral pos: ({spiral_pos.x:.1f}, {spiral_pos.y:.1f}, {spiral_pos.z:.1f})")

    # Create each key in this row
    for key_idx, (key, (key_offset_y, key_width_u)) in enumerate(zip(keys, key_positions)):
        label = key.get('label', '')

        print(f"  Key {key_idx + 1}: '{label}' @ {key_offset_y:.1f}mm, {key_width_u}u")

        # Calculate position along the curved row
        keycap_angle = key_offset_y / roll_radius
        keycap_angle_deg = math.degrees(keycap_angle)

        local_pos_x = 0
        local_pos_y = roll_radius * math.sin(keycap_angle)
        local_pos_z = roll_radius * (1 - math.cos(keycap_angle))

        # Local rotations
        roll_rot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), keycap_angle_deg)
        pitch_rot = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), pitch_angle)
        local_rot = roll_rot.multiply(pitch_rot)

        # Transform to global coordinates
        global_rotation = local_to_global.multiply(local_rot)
        local_vec = FreeCAD.Vector(local_pos_x, local_pos_y, local_pos_z)
        global_offset = local_to_global.multVec(local_vec)
        global_position = spiral_pos.add(global_offset)

        # Create keycap with label (only if labels enabled)
        keycap_label = label if enable_labels else None
        keycap_with_label = create_keycap_with_label(
            base_keycap_shape, keycap_label, key_width_u, text_height, text_depth, u
        )

        final_placement = FreeCAD.Placement(global_position, global_rotation)

        keycap_obj = doc.addObject("Part::Feature", f"Key_R{row_idx + 1:02d}_K{key_idx + 1:02d}_{label}")
        keycap_obj.Shape = keycap_with_label
        keycap_obj.Placement = final_placement

        # Create switch
        local_switch_offset = FreeCAD.Vector(0, 0, -switch_offset)
        global_switch_offset = global_rotation.multVec(local_switch_offset)
        switch_position = global_position.add(global_switch_offset)
        switch_placement = FreeCAD.Placement(switch_position, global_rotation)

        switch_obj = doc.addObject("Part::Feature", f"Switch_R{row_idx + 1:02d}_K{key_idx + 1:02d}")
        switch_obj.Shape = switch_shape
        switch_obj.Placement = switch_placement

        # Create switchplate
        if switchplate_shape is not None:
            local_switchplate_offset = FreeCAD.Vector(0, 0, -mount_offset)
            global_switchplate_offset = global_rotation.multVec(local_switchplate_offset)
            switchplate_position = global_position.add(global_switchplate_offset)
            switchplate_placement = FreeCAD.Placement(switchplate_position, global_rotation)

            switchplate_obj = doc.addObject("Part::Feature", f"Plate_R{row_idx + 1:02d}_K{key_idx + 1:02d}")
            switchplate_obj.Shape = switchplate_shape
            switchplate_obj.Placement = switchplate_placement

        total_keys += 1

    print(f"  Created {len(keys)} keys in row {row_idx + 1}")

# Create golden spiral
spiral_shape = create_golden_spiral(
    start_diameter=hand_diameter,
    arc_length_radians=2 * math.pi,
    tube_radius=5.0,
    center=FreeCAD.Vector(0, 0, 0),
    plane_normal='xz',
    num_segments=200
)

spiral_obj = doc.addObject("Part::Feature", "GoldenSpiral")
spiral_obj.Shape = spiral_shape

doc.recompute()
print(f"\nSUCCESS: Created {len(layout)} rows with {total_keys} total keys")
print(f"  {total_keys} keycaps + {total_keys} switches + {total_keys} switchplates + 1 spiral = {len(doc.Objects)} objects")
