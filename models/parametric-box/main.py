#!/usr/bin/env python3
"""
Parametric Box Model
A hollow box with configurable dimensions and wall thickness
"""

import FreeCAD
import Part
import sys

def generate_model():
    """
    Generate a parametric hollow box.

    Parameters can be modified to create different box sizes.
    """
    print("Starting parametric box generation...")

    # Parameters (can be customized)
    length = 150  # mm
    width = 100   # mm
    height = 50   # mm
    wall = 3      # mm wall thickness

    print(f"Parameters: {length}x{width}x{height}mm, wall={wall}mm")

    # Create new FreeCAD document
    doc = FreeCAD.newDocument("ParametricBox")
    print("✓ Document created")

    # Create outer box
    outer = Part.makeBox(length, width, height)
    print("✓ Outer box created")

    # Create inner cavity
    inner = Part.makeBox(
        length - 2*wall,
        width - 2*wall,
        height - wall,
        FreeCAD.Vector(wall, wall, wall)
    )
    print("✓ Inner cavity created")

    # Subtract inner from outer to create hollow box
    hollow_box = outer.cut(inner)
    print("✓ Hollow box created")

    # Add to document
    obj = doc.addObject("Part::Feature", "HollowBox")
    obj.Shape = hollow_box
    print("✓ Box added to document")

    # Recompute
    doc.recompute()
    print("✓ Document recomputed")

    print(f"✓ Parametric box generated successfully with {len(doc.Objects)} object(s)")
    return doc

if __name__ == "__main__":
    try:
        doc = generate_model()
        print("SUCCESS: Model generation complete")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
