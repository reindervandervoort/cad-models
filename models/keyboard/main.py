#!/usr/bin/env python3
"""
Keyboard Row: Multiple Keycaps with Roll
Create a row of keycaps, each rotated with roll (around X axis).
Track transformation matrices for each keycap.
"""

import FreeCAD
import Part
import Mesh
import os
import math

print("=== Keyboard row with roll rotation ===")

# Document setup
if 'doc' not in dir():
    doc = FreeCAD.newDocument("Keyboard")
    print("Created new document (standalone mode)")
else:
    print("Using provided document (backend mode)")

# Load parameters from input.json
script_dir = os.path.dirname(os.path.abspath(__file__))
import json
input_file = os.path.join(script_dir, "input.json")
with open(input_file, 'r') as f:
    params = json.load(f)

hand_diameter = params.get('handDiameter', 192)
hand_radius = hand_diameter / 2
print(f"\nLoaded parameters:")
print(f"  Hand diameter: {hand_diameter}mm")
print(f"  Hand radius: {hand_radius}mm")

# Load keycap STL once to get dimensions
keycap_stl = os.path.join(script_dir, "kailh_choc_low_profile_keycap.stl")

print(f"\nLoading template: {keycap_stl}")
template_mesh = Mesh.Mesh(keycap_stl)

# Get original bounding box
bbox = template_mesh.BoundBox
print(f"\nOriginal STL bounding box:")
print(f"  X: [{bbox.XMin:.2f}, {bbox.XMax:.2f}] width: {bbox.XLength:.2f}mm")
print(f"  Y: [{bbox.YMin:.2f}, {bbox.YMax:.2f}] depth: {bbox.YLength:.2f}mm")
print(f"  Z: [{bbox.ZMin:.2f}, {bbox.ZMax:.2f}] height: {bbox.ZLength:.2f}mm")

# Calculate base offset to center keycap with top at origin
base_offset_x = -(bbox.XMin + bbox.XMax) / 2
base_offset_y = -(bbox.YMin + bbox.YMax) / 2
base_offset_z = -bbox.ZMax

print(f"\nBase offset for centering: ({base_offset_x:.2f}, {base_offset_y:.2f}, {base_offset_z:.2f})")

# Configuration for keyboard row
num_keycaps = 2  # Start with 2 for debugging
keycap_spacing = 19.0  # mm between keycap centers (standard Cherry MX spacing)
roll_angle = 10  # degrees, rotation around X axis
roll_axis_height = hand_radius  # mm above the keycap top (hand pivot point)

print(f"\nCreating row of {num_keycaps} keycaps with {roll_angle}° roll")
print(f"Spacing: {keycap_spacing}mm")
print(f"Roll axis height: {roll_axis_height}mm above keycap top (hand radius)")
print(f"DEBUG: hand_diameter={hand_diameter}, hand_radius={hand_radius}")

# Track transformation matrices
transformations = []

# Create each keycap
for i in range(num_keycaps):
    print(f"\n--- Keycap {i+1}/{num_keycaps} ---")

    # Load fresh mesh for this keycap
    keycap_mesh = Mesh.Mesh(keycap_stl)

    # Step 1: Center at origin (top center at 0,0,0)
    keycap_mesh.translate(base_offset_x, base_offset_y, base_offset_z)

    # Step 2: Apply roll rotation around X axis elevated above keycap
    # The roll axis is parallel to X axis but at height roll_axis_height above keycap top
    # To rotate around elevated axis:
    # - Translate down by roll_axis_height (move rotation center to origin)
    # - Rotate around X axis at origin
    # - Translate back up by roll_axis_height
    from FreeCAD import Matrix

    # Move down to put roll axis at origin
    keycap_mesh.translate(0, 0, -roll_axis_height)

    # Rotate around X axis at origin
    roll_matrix = Matrix()
    roll_matrix.rotateX(math.radians(roll_angle))
    keycap_mesh.transform(roll_matrix)

    # Move back up
    keycap_mesh.translate(0, 0, roll_axis_height)

    # Step 3: Translate to position in row
    # Position along Y axis, centered around origin
    row_offset_y = (i - (num_keycaps - 1) / 2) * keycap_spacing
    keycap_mesh.translate(0, row_offset_y, 0)

    # Record the combined transformation
    combined_matrix = Matrix()
    # Translation to center
    combined_matrix.move(FreeCAD.Vector(base_offset_x, base_offset_y, base_offset_z))
    # Roll rotation
    combined_matrix = combined_matrix.multiply(roll_matrix)
    # Row position translation
    combined_matrix = combined_matrix.multiply(translation_matrix)

    transformations.append({
        'keycap_index': i,
        'position': (0, row_offset_y, 0),
        'roll_degrees': roll_angle,
        'matrix': combined_matrix
    })

    print(f"  Position: Y={row_offset_y:.2f}mm")
    print(f"  Roll: {roll_angle}°")
    print(f"  Matrix: {combined_matrix}")

    # Convert to shape
    keycap_shape = Part.Shape()
    keycap_shape.makeShapeFromMesh(keycap_mesh.Topology, 0.1)

    # Create object
    keycap_obj = doc.addObject("Part::Feature", f"Keycap_{i+1}")
    keycap_obj.Shape = keycap_shape

    bbox_final = keycap_obj.Shape.BoundBox
    print(f"  Final bbox: X[{bbox_final.XMin:.1f}, {bbox_final.XMax:.1f}] "
          f"Y[{bbox_final.YMin:.1f}, {bbox_final.YMax:.1f}] "
          f"Z[{bbox_final.ZMin:.1f}, {bbox_final.ZMax:.1f}]")

doc.recompute()

print(f"\n=== Transformation Summary ===")
for t in transformations:
    print(f"Keycap {t['keycap_index']+1}: position Y={t['position'][1]:.2f}mm, roll={t['roll_degrees']}°")

print(f"\nSUCCESS: Created {len(doc.Objects)} keycaps")
