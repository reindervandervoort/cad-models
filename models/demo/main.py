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
    # When run standalone, generate and display result
    doc = generate_model()
    print("SUCCESS: Model generation complete")
    # Note: Don't call sys.exit() as it prevents backend from exporting STL
