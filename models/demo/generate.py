#!/usr/bin/env python3
"""
Demo FreeCAD Model - Simple Cube
Demonstrates the basic structure of a FreeCAD generation script
"""

import FreeCAD
import Part
import sys

def generate_model():
    """
    Generate a simple cube with configurable size.
    This is the entry point called by the backend.
    """
    print("Starting demo model generation...")

    # Create new FreeCAD document
    doc = FreeCAD.newDocument("Demo")
    print("✓ Document created")

    # Create a simple cube (100x100x100 mm)
    cube = Part.makeBox(100, 100, 100)
    print("✓ Cube shape created")

    # Add to document
    obj = doc.addObject("Part::Feature", "Cube")
    obj.Shape = cube
    print("✓ Cube added to document")

    # Recompute
    doc.recompute()
    print("✓ Document recomputed")

    print(f"✓ Demo cube model generated successfully with {len(doc.Objects)} object(s)")
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
